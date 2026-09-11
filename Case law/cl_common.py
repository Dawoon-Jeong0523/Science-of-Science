"""Paths and the shared citation graph for the Case law metric notebooks, on Midway.

Mirrors PatentView/pv_common.py and OpenAlex/oa_common.py so the three metric families read
the same way. The inputs are two files and nothing else:

    Edge_list.parquet   47,519,638 edges as (source, target) case ids
    metadata.csv        5,179,698 cases

EDGE DIRECTION.  `source` CITES `target`. Verified rather than assumed: over a 2M-edge sample
joined to decision years, 1,766,441 edges have source newer than target, 64,106 are same-year,
and **zero** have source older than target. So `c_from = source` (citing) and `c_to = target`
(cited), the same orientation pv_common and oa_common use, and `out_idx` is "what this case
cites" while `in_idx` is "what cites this case".

CODE SPACE.  Case ids run 1..12,707,012 but only 5,179,698 exist, so ids are mapped to their
position in the sorted unique id array — dense codes for array indexing, exactly as `uni_mag`
does in the other two projects. Every one of the 47.5M edges has both endpoints in
metadata.csv (measured: 0 missing on either side), so no edge is dropped in the mapping.

    import cl_common as cl
    cl.preflight()
    c_from, c_to, year, uni = cl.load_graph()
"""
from __future__ import annotations

import os
import time

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

BASE  = "/project/jevans/Dawoon/Science of Science/Case law"
EDGES = f"{BASE}/Edge_list.parquet"
META  = f"{BASE}/metadata.csv"
OUT   = f"{BASE}/output"          # every notebook writes its parquet here
CACHE = f"{BASE}/cache"           # derived graph/CSR, not results
for _d in (OUT, CACHE):
    os.makedirs(_d, exist_ok=True)

# ── The analysis floor, and the court strata ──────────────────────────────────────────────
# Every ANALYSIS starts at 1800. The graph does not: 1,795 cases (0.035%) predate 1800, but
# 14,047 citation edges point AT them, and a case decided in 1805 really did cite its 1790
# antecedents. Dropping those edges would corrupt the ref_count, CD and F/E/G of the 1800s
# cases that made them. So the graph stays whole and the floor is applied to the population
# that gets reported.
YEAR_MIN = 1800

# jurisdiction == 'U.S.' is the federal jurisdiction; these fifty are the states. The rest --
# D.C., P.R., V.I., Guam, Am. Samoa, N. Mar. I., Tribal, Navajo Nation, Dakota Territory and
# two U.K. cases, 63,867 in total -- are neither, and are reported as 'Other' rather than
# folded into 'State', which would make "state law" mean something it does not.
STATES = ("Ala.", "Alaska", "Ariz.", "Ark.", "Cal.", "Colo.", "Conn.", "Del.", "Fla.", "Ga.",
          "Haw.", "Idaho", "Ill.", "Ind.", "Iowa", "Kan.", "Ky.", "La.", "Me.", "Md.",
          "Mass.", "Mich.", "Minn.", "Miss.", "Mo.", "Mont.", "Neb.", "Nev.", "N.H.", "N.J.",
          "N.M.", "N.Y.", "N.C.", "N.D.", "Ohio", "Okla.", "Or.", "Pa.", "R.I.", "S.C.",
          "S.D.", "Tenn.", "Tex.", "Utah", "Vt.", "Va.", "Wash.", "W. Va.", "Wis.", "Wyo.")

# THE HIGHEST COURT OF A JURISDICTION IS THE ONE WHOSE ABBREVIATION EQUALS THE JURISDICTION'S.
# That is the CAP convention and it is the only rule that works here: not one court name in
# the corpus contains the word "Supreme" (measured: 0 of 5.18M), so a name match finds
# nothing, and a match on "Sup. Ct." is actively wrong -- `N.Y. Sup. Ct.` is New York's TRIAL
# court, 80,530 cases, while its highest court is the Court of Appeals, abbreviated `N.Y.`.
# Under this rule: U.S./U.S. = the Supreme Court of the United States (51,702 cases from
# 1800), and each state's own line is its supreme court (42.6% of state cases).
def strata_sql(alias: str = "m") -> str:
    """SQL fragment adding `level` (Federal/State/Other) and `is_supreme` to a metadata scan."""
    states = ", ".join(f"'{s}'" for s in STATES)
    return (f"CASE WHEN {alias}.jurisdiction = 'U.S.' THEN 'Federal' "
            f"WHEN {alias}.jurisdiction IN ({states}) THEN 'State' ELSE 'Other' END AS level, "
            f"({alias}.court = {alias}.jurisdiction) AS is_supreme")


GRAPH_NPZ = f"{CACHE}/case_graph.npz"     # c_from, c_to, year, uni
CSR_NPZ   = f"{CACHE}/case_csr.npz"       # out_ptr/out_idx (cites), in_ptr/in_idx (cited by)

# metadata.csv columns actually used. `cites` is a reporter citation string ("59 Mass. App.
# Dec. 120"), not a reference list — the references are the edge list.
META_COLS = ["id", "jurisdiction__name", "jurisdiction_id", "court__name_abbreviation",
             "court_id", "reporter__short_name", "reporter_id", "name_abbreviation",
             "decision_date_original"]

NEEDS = {
    "case_metadata":              ["metadata.csv", "Edge_list.parquet"],
    "case_citation":              ["@case_graph.npz"],
    "case_citation_trend":        ["@case_graph.npz"],
    "case_disruption":            ["@case_csr.npz"],
    "case_feg_disruption_trend":  [],      # reads this folder's own output
    "case_hit_probability":       [],      # ditto
    "case_sb":                    ["@case_graph.npz"],
}


def out(name: str) -> str:
    return f"{OUT}/{name}"


def _year_from_date(s: pd.Series) -> np.ndarray:
    """Decision year as int32, -1 where absent.

    The leading four digits are taken rather than a full date parse: `decision_date_original`
    is mostly YYYY-MM-DD, but a partial date (YYYY, YYYY-MM) is still a usable year and a
    strict parse throws it away. Both are reported by case_metadata so the difference is
    visible rather than assumed."""
    y = s.astype(str).str.slice(0, 4)
    y = pd.to_numeric(y, errors="coerce")
    y = y.where((y >= 1600) & (y <= 2030))
    return y.fillna(-1).astype(np.int32).to_numpy()


def read_metadata(usecols=None, verbose: bool = True) -> pd.DataFrame:
    """metadata.csv with `decision_year` derived. 605 MB, read in one pass."""
    t0 = time.time()
    d = pd.read_csv(META, usecols=usecols or META_COLS, dtype=str,
                    on_bad_lines="skip", low_memory=False)
    d["case_id"] = pd.to_numeric(d["id"], errors="coerce").astype("Int64")
    d = d[d["case_id"].notna()].copy()
    d["case_id"] = d["case_id"].astype(np.int64)
    if "decision_date_original" in d.columns:
        d["decision_year"] = _year_from_date(d["decision_date_original"])
    if verbose:
        print(f"[{time.time()-t0:.0f}s] metadata: {len(d):,} cases")
    return d


def build_graph(force: bool = False, verbose: bool = True) -> str:
    """Edge list + decision years in code space -> CACHE/case_graph.npz."""
    if os.path.exists(GRAPH_NPZ) and not force:
        if verbose:
            print(f"graph cache present: {GRAPH_NPZ}")
        return GRAPH_NPZ
    t0 = time.time()
    m = read_metadata(usecols=["id", "decision_date_original"], verbose=verbose)
    uni = np.sort(m["case_id"].to_numpy())
    year = np.full(len(uni), -1, np.int32)
    year[np.searchsorted(uni, m["case_id"].to_numpy())] = m["decision_year"].to_numpy()
    del m

    e = pq.read_table(EDGES, columns=["source", "target"])
    src = e.column("source").to_numpy().astype(np.int64)
    dst = e.column("target").to_numpy().astype(np.int64)
    del e
    # Both endpoints are known to exist; the mask is kept so a future snapshot that breaks
    # that assumption fails loudly in the printout instead of silently mis-indexing.
    cf = np.searchsorted(uni, src); ct = np.searchsorted(uni, dst)
    cf = np.clip(cf, 0, len(uni) - 1); ct = np.clip(ct, 0, len(uni) - 1)
    ok = (uni[cf] == src) & (uni[ct] == dst)
    if verbose and not ok.all():
        print(f"  WARNING: {int((~ok).sum()):,} edges have an endpoint absent from metadata "
              f"and are dropped")
    cf, ct = cf[ok].astype(np.int32), ct[ok].astype(np.int32)
    del src, dst, ok
    np.savez(GRAPH_NPZ, c_from=cf, c_to=ct, year=year, uni=uni)
    if verbose:
        print(f"[{time.time()-t0:.0f}s] graph: {len(uni):,} cases, {len(cf):,} edges "
              f"-> {GRAPH_NPZ}")
    return GRAPH_NPZ


def load_graph():
    build_graph()
    z = np.load(GRAPH_NPZ)
    return z["c_from"], z["c_to"], z["year"].astype(np.int32), z["uni"]


def _csr(src, dst, n):
    order = np.argsort(src, kind="stable")
    s, d = src[order], dst[order]
    ptr = np.zeros(n + 1, np.int64)
    np.add.at(ptr, s.astype(np.int64) + 1, 1)
    np.cumsum(ptr, out=ptr)
    return ptr, d


def build_csr(force: bool = False, verbose: bool = True) -> str:
    """Both directions of the graph as CSR -> CACHE/case_csr.npz."""
    if os.path.exists(CSR_NPZ) and not force:
        if verbose:
            print(f"CSR cache present: {CSR_NPZ}")
        return CSR_NPZ
    t0 = time.time()
    cf, ct, year, uni = load_graph()
    n = len(uni)
    out_ptr, out_idx = _csr(cf, ct, n)      # what each case CITES
    in_ptr,  in_idx  = _csr(ct, cf, n)      # what CITES each case
    np.savez(CSR_NPZ, out_ptr=out_ptr, out_idx=out_idx, in_ptr=in_ptr, in_idx=in_idx,
             year=year, uni=uni)
    if verbose:
        print(f"[{time.time()-t0:.0f}s] CSR: {n:,} cases, {len(out_idx):,} edges "
              f"-> {CSR_NPZ}")
    return CSR_NPZ


def load_csr():
    build_csr()
    z = np.load(CSR_NPZ)
    return (z["out_ptr"], z["out_idx"], z["in_ptr"], z["in_idx"],
            z["year"].astype(np.int32), z["uni"])


def preflight(notebook: str | None = None) -> bool:
    """Report which inputs are present. Returns True if everything needed is there."""
    print(f"case law : {BASE}")
    print(f"output   : {OUT}")
    print(f"cache    : {CACHE}\n")
    ok_all = True
    for nb in ([notebook] if notebook else sorted(NEEDS)):
        rows = []
        for f in NEEDS.get(nb, []):
            cached = f.startswith("@")
            p = f"{CACHE}/{f.lstrip('@')}" if cached else f"{BASE}/{f.lstrip('@')}"
            rows.append((f.lstrip("@"), "OK" if os.path.exists(p) else "MISSING"))
        miss = [f for f, s in rows if s == "MISSING"]
        if miss:
            ok_all = False
        print(f"  {nb:<28}{'OK' if not miss else f'MISSING {len(miss)}'}")
        for f, s in rows:
            if s == "MISSING":
                print(f"      {f}  <- build it (case_metadata builds the cache)")
    return ok_all


def summary() -> None:
    for name, p in (("edges", EDGES), ("metadata", META),
                    ("graph", GRAPH_NPZ), ("csr", CSR_NPZ)):
        state = f"{os.path.getsize(p)/1e9:.2f} GB" if os.path.exists(p) else "MISSING"
        print(f"  {name:<9} {state:>10}  {p}")
