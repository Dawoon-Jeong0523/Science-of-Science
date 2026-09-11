"""Paths for the PPP (patent-paper pair) citation-trend notebook, on Midway.

Replaces the Windows layout: the `os.chdir('..')` marker hunt,
`Data/Reliance on Science/...`, `E:/Dawoon Jeong/Data/PatentView/Granted/...` and
`E:/Dawoon Jeong/Data/paper_disruption_csr.npz`.

THE PAIR LIST IS A CHOICE, and it changes the result by more than an order of magnitude:

  PAIRS_PLUS      _patent_paper_pairs_plus.csv   548,315 pairs  paperid ('W…'), patent ('US-…'),
                  (this folder -- THE DEFAULT)   335,917 papers ppp_score 1-4, concepts,
                                                 309,729 patents daysdiffcont, sector flags,
                                                                citationbased, reassigned,
                                                                commercialized, prerecommercialized
  PAIRS_ADJUSTED  finalpppsadjusted_260831.csv    42,967 pairs  magid, patent_id,
                  (this folder, dated 2026-08-31)               confidence_level
                                                                high 16,738 / mid 26,229
  PAIRS_FULL      SciTech_PPP/Data/_patent_paper_pairs.csv     548,315 pairs  paperid, patent,
                  (the older copy of the same list,             ppp_score, daysdiffcont
                   without the extra columns)

`load_pairs()` normalises all three into the same four columns, so switching is one variable.
The default is the plus list: it is what the notebook's own header documents, it is the widest
of the three, and it is the only one that carries the sector and commercialisation flags.
Set PAIRS_SOURCE='adjusted' for the 42,967-pair list.

    import ppp_common as P
    pr = P.load_pairs()          # paperid, patent, oaid (int64), patent_id (str)
"""
from __future__ import annotations

import os
import sys

SOS  = "/project/jevans/Dawoon/Science of Science"
BASE = f"{SOS}/PPP"
OUT  = f"{BASE}/output"
os.makedirs(OUT, exist_ok=True)

PAIRS_PLUS     = f"{BASE}/_patent_paper_pairs_plus.csv"
PAIRS_ADJUSTED = f"{BASE}/finalpppsadjusted_260831.csv"
PAIRS_FULL     = "/project/jevans/Dawoon/SciTech_PPP/Data/_patent_paper_pairs.csv"
PAIRS_SOURCE   = os.environ.get("NB_PAIRS_SOURCE", "plus")   # 'plus' | 'adjusted' | 'full'

# Columns of the plus list that are carried through to load_pairs() when present. They are not
# used to build the trends; they are what makes a pair splittable afterwards (by score, by
# sector, by whether the patent was ever commercialised).
PLUS_EXTRAS = ["ppp_score", "concepts", "daysdiffcont", "citationbased",
               "paperuniv", "papergovn", "paperfirm", "paperunk",
               "patentuniv", "patentfirm", "patentgovn", "patentlone",
               "reassigned", "commercialized", "prerecommercialized"]

OA_BASE = f"{SOS}/OpenAlex"
PV_BASE = f"{SOS}/PatentView"
PCS_CSV = f"{SOS}/pcs/pcs_oa_uspto.csv"
CSR_NPZ = f"{OA_BASE}/cache/paper_csr.npz"        # was E:/…/paper_disruption_csr.npz

for _p in (OA_BASE, PV_BASE):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def out(name: str) -> str:
    return f"{OUT}/{name}"


def granted(name: str) -> str:
    import pv_common as pv
    return pv.granted(name)


def pairs_path(source: str | None = None) -> str:
    s = (source or PAIRS_SOURCE).lower()
    try:
        return {"plus": PAIRS_PLUS, "adjusted": PAIRS_ADJUSTED, "full": PAIRS_FULL}[s]
    except KeyError:
        raise ValueError(f"PAIRS_SOURCE must be 'plus', 'adjusted' or 'full', got {s!r}") from None


def load_pairs(source: str | None = None, verbose: bool = True):
    """One row per (paper, patent) pair, with the four columns the notebook uses.

    Returns paperid ('W…'), patent ('US-…'), oaid (int64) and patent_id (str of digits),
    whichever of the two schemas the file is in. The adjusted list already carries numeric
    ids, so its 'W…'/'US-…' forms are reconstructed rather than parsed -- the round trip is
    exact because both are just the number with a prefix."""
    import numpy as np
    import pandas as pd
    s = (source or PAIRS_SOURCE).lower()
    p = pairs_path(s)
    if s == "adjusted":
        pr = pd.read_csv(p, dtype=str).dropna(subset=["magid", "patent_id"])
        pr["oaid"] = pd.to_numeric(pr["magid"], errors="coerce")
        pr = pr.dropna(subset=["oaid"])
        pr["oaid"] = pr["oaid"].astype(np.int64)
        pr["patent_id"] = pr["patent_id"].str.strip().str.lstrip("0")
        pr["paperid"] = "W" + pr["oaid"].astype(str)
        pr["patent"] = "US-" + pr["patent_id"]
        keep = ["paperid", "patent", "oaid", "patent_id"]
        if "confidence_level" in pr.columns:
            keep.append("confidence_level")
        pr = pr[keep]
    else:
        # 'plus' and 'full' share a schema: paperid is already 'W…' and patent already 'US-…'.
        head = pd.read_csv(p, nrows=0)
        extras = [c for c in PLUS_EXTRAS if c in head.columns]
        pr = pd.read_csv(p, usecols=["paperid", "patent"] + extras, dtype=str)
        pr = pr.dropna(subset=["paperid", "patent"])
        pr["oaid"] = pd.to_numeric(pr["paperid"].str.slice(1), errors="coerce")
        # The letters matter: plant patents are 'US-PP34398' and PatentsView keys them 'PP34398'.
        # A digits-only pattern silently dropped all 65 of them.
        pr["patent_id"] = pr["patent"].str.extract(r"[Uu][Ss]-0*([A-Za-z]*[0-9]+)", expand=False)
        pr = pr.dropna(subset=["oaid", "patent_id"])
        pr["oaid"] = pr["oaid"].astype(np.int64)
        for c in extras:
            if c not in ("concepts",):
                pr[c] = pd.to_numeric(pr[c], errors="coerce")
        pr = pr[["paperid", "patent", "oaid", "patent_id"] + extras]
    pr = pr.reset_index(drop=True)
    if verbose:
        print(f"[ppp] pairs '{s}': {os.path.basename(p)} -> {len(pr):,} pairs | "
              f"{pr.oaid.nunique():,} distinct papers | {pr.patent_id.nunique():,} distinct patents")
    return pr


NEEDS = [PCS_CSV, CSR_NPZ, "@g_patent.tsv.zip", "@g_us_patent_citation.tsv.zip"]


def preflight() -> bool:
    print(f"ppp base   : {BASE}")
    print(f"output     : {OUT}")
    print(f"pair source: {PAIRS_SOURCE}  ->  {pairs_path()}\n")
    miss = []
    for f in NEEDS + [pairs_path()]:
        if f.startswith("@"):
            try:
                granted(f[1:])
            except FileNotFoundError:
                miss.append(f[1:])
        elif not os.path.exists(f):
            miss.append(f)
    print(f"  ppp_citation_trend    {'OK' if not miss else f'MISSING {len(miss)}'}")
    for m in miss:
        print(f"      {m}  <- not available")
    return not miss
