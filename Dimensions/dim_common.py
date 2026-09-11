"""Data layer for the paper-metric notebooks, on the Dimensions June 2025 dump.

This is `OpenAlex/oa_common.py` re-pointed at Dimensions. The metric kernels in the notebooks --
the numba disruption engine, the sleeping-beauty kernel, the Uzzi shuffle, the vectorised
citation counts, the percentile rank -- are the same code, byte for byte; only the data layer
below differs. The public names are kept (`load_graph`, `load_csr`, `build_journal`, `build_fos`,
`stream_edges`, `citation_counts`, `code_to_id`, ...) so a notebook written against `oa` reads
the same against `dim`.

The one idea that makes that possible is the same one as before: a Dimensions publication id is
`pub.` followed by up to ten digits, so `int(id[4:])` round-trips through int64, and the
notebooks' code-space machinery (a sorted `uni_mag`, `searchsorted` to map id -> code, back with
the prefix) keeps working with the Dimensions accession number standing in for the MAG integer.
Journals are `jour.` + digits and go through the same codec.

    import dim_common as dim
    dim.build_graph()      # references_w_year -> edges + years, cached as .npz
    dim.build_csr()        # -> out/in adjacency, cached

Environment knobs (all optional):
    NB_DIM_BASE    where cache/ and output/ live (default: this folder) -- a smoke test points
                   it at a scratch directory so nothing here is touched
    NB_FILE_LIMIT  read only a strided sample of this many publication files -- smoke tests
    NB_WORKERS     processes for the per-file passes (default 8)
"""
from __future__ import annotations

import gc
import glob
import os
import re
import time

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

# ── Where everything lives ────────────────────────────────────────────────────────────────
ROOT    = "/project/jevans/dimensions/dimensions/dimensions_june_2025"      # read-only dump
PUBS    = f"{ROOT}/publications"      # 4,219 extension-less parquet files, one year each
PATENTS = f"{ROOT}/patents"           # 3,580 files; publication_ids = patent -> paper citations
SOURCES = f"{ROOT}/source_titles"     # id (jour.…), type, title, issns -- the sources.csv.gz twin

HERE  = os.path.dirname(os.path.abspath(__file__))
BASE  = os.environ.get("NB_DIM_BASE", HERE)
CACHE = f"{BASE}/cache"               # derived artefacts; the dump is read-only
OUT   = f"{BASE}/output"              # every notebook writes its parquet here
for _d in (CACHE, OUT):
    os.makedirs(_d, exist_ok=True)

GRAPH_NPZ  = f"{CACHE}/paper_graph.npz"        # c_from, c_to, year, uni_mag
CSR_NPZ    = f"{CACHE}/paper_csr.npz"          # out_ptr, out_idx, in_ptr, in_idx, year, uni_mag
JOURNAL_PQ = f"{CACHE}/paper_journal.parquet"  # work_id, source_id, journal, is_journal
FOS_PQ     = f"{CACHE}/paper_fos.parquet"      # work_id, FoS_rep, FoS_0, for_division_codes, for_group_codes
INDEX_PQ   = f"{CACHE}/publications_file_index.parquet"   # footer index: year/type/rows per file

# ── What references_w_year.ipynb writes ───────────────────────────────────────────────────
#   SCALARS  one part per publications file: every document-level scalar the pipeline needs
#            (year, type, class, source, reference count, FoR codes, citation counts, ...).
#            Read ONCE from the 490 GB dump; everything else reads these slim parts.
#   AUTHORS  one part per publications file: author_list / team_size / first / last / countries
#   MAP_NPZ  one row per publication: code, year (int16, -1 unknown), source (int64, -1 none)
#   REF_PQ   one row per reference edge, both endpoints dated and placed -- the same six
#            column names as OpenAlex/output/referenced_works_w_year so oa-derived code reads it
SCALARS = f"{CACHE}/pub_scalars"
AUTHORS = f"{CACHE}/pub_authors"
MAP_NPZ = f"{CACHE}/pub_year_source_map.npz"
REF_PQ  = f"{OUT}/references_w_year"
PAT2PUB = f"{CACHE}/patent2pub_edges.parquet"   # patent_id, jurisdiction, cite_year, paper_id

# Scope. Publication years in the dump run from the 1600s to 2025 with a thin tail of junk;
# these reject impossible values only (1700 also keeps paper_citation_trend's
# `cited * 400 + (year - 1700)` key collision-free). YEAR_RANGE narrows the corpus when the
# graph is built and everything downstream inherits it.
YEAR_MIN, YEAR_MAX = 1700, 2030
YEAR_RANGE = None          # e.g. (1950, 2025); None = no filter beyond YEAR_MIN/MAX

N_WORKERS  = int(os.environ.get("NB_WORKERS", "8"))
FILE_LIMIT = os.environ.get("NB_FILE_LIMIT")          # smoke tests only


# ── Ids ───────────────────────────────────────────────────────────────────────────────────
ID_PREFIX, SRC_PREFIX = "pub.", "jour."
_ID_RE  = re.compile(r"^pub\.(\d+)$")
_SRC_RE = re.compile(r"^jour\.(\d+)$")


def norm_id(s: pd.Series) -> pd.Series:
    """Dimensions ids come in one form only (`pub.1046637280`); this strips whitespace and is
    kept for interface parity with oa_common.norm_id."""
    return s.astype(str).str.strip()


def id_to_code(s) -> np.ndarray:
    """`pub.1046637280` -> 1046637280 as int64. Invalid ids become -1."""
    t = pd.Series(s).astype(str).str.extract(_ID_RE, expand=False)
    return pd.to_numeric(t, errors="coerce").fillna(-1).astype(np.int64).to_numpy()


def code_to_id(a: np.ndarray) -> np.ndarray:
    """1046637280 -> `pub.1046637280`. The notebooks' `np.char.add` idiom, kept."""
    return np.char.add(ID_PREFIX, np.asarray(a).astype(np.int64).astype(str))


def src_to_code(s) -> np.ndarray:
    """`jour.1137841` -> 1137841 as int64; invalid / null -> -1."""
    t = pd.Series(s).astype(str).str.extract(_SRC_RE, expand=False)
    return pd.to_numeric(t, errors="coerce").fillna(-1).astype(np.int64).to_numpy()


def code_to_src(a: np.ndarray) -> np.ndarray:
    return np.char.add(SRC_PREFIX, np.asarray(a).astype(np.int64).astype(str))


# ── Files ─────────────────────────────────────────────────────────────────────────────────
def pub_files() -> list[str]:
    """Every publications file, sorted; a strided sample of NB_FILE_LIMIT of them if set."""
    fs = sorted(glob.glob(f"{PUBS}/publications_*"))
    if FILE_LIMIT:
        k = int(FILE_LIMIT)
        step = max(1, len(fs) // k)
        fs = fs[::step][:k]
    return fs


def patent_files() -> list[str]:
    fs = sorted(glob.glob(f"{PATENTS}/patents_*"))
    if FILE_LIMIT:
        k = int(FILE_LIMIT)
        step = max(1, len(fs) // k)
        fs = fs[::step][:k]
    return fs


def part_name(i: int) -> str:
    return f"part_{i:04d}.parquet"


def scalar_parts() -> list[str]:
    return sorted(glob.glob(f"{SCALARS}/part_*.parquet"))


def author_parts() -> list[str]:
    return sorted(glob.glob(f"{AUTHORS}/part_*.parquet"))


def ref_parts() -> list[str]:
    return sorted(glob.glob(f"{REF_PQ}/part_*.parquet"))


def have_consolidated() -> bool:
    return os.path.exists(MAP_NPZ) and bool(ref_parts()) and bool(scalar_parts())


def load_map():
    """code (sorted int64), year (int16, -1 = unknown), source (int64, -1 = none).

    Built by references_w_year.ipynb. The authoritative per-publication table: every
    publication in the dump, whether or not it has an edge."""
    if not os.path.exists(MAP_NPZ):
        raise SystemExit(
            f"{MAP_NPZ} is missing.\n"
            f"        Run notebook/references_w_year.ipynb first -- it builds the map, the scalar "
            f"parts and the edge table that everything else reads.")
    z = np.load(MAP_NPZ)
    return z["code"], z["year"], z["source"]


def _need_consolidated():
    if not have_consolidated():
        raise SystemExit("run notebook/references_w_year.ipynb first -- it builds the map, the "
                         "scalar parts and the edge table that everything else reads")


# ── The citation graph ────────────────────────────────────────────────────────────────────
def build_graph(force: bool = False, verbose: bool = True) -> str:
    """Years + reference edges, in the code space the notebooks expect.

    Saves c_from / c_to / year / uni_mag with exactly the names the notebooks load. `uni_mag`
    keeps its name deliberately: it is the sorted array of accession numbers, the same role the
    sorted MAG ids played, and the notebooks index it by position. Read off the consolidated
    edge table; there is no slow path over the dump."""
    if os.path.exists(GRAPH_NPZ) and not force:
        if verbose:
            print(f"graph cache present: {GRAPH_NPZ}")
        return GRAPH_NPZ
    _need_consolidated()
    t0 = time.time()
    uni_mag, year_full, _src = load_map()
    keep = year_full >= 0                       # a work with no usable year cannot be dated
    if YEAR_RANGE is not None:
        keep &= (year_full >= YEAR_RANGE[0]) & (year_full <= YEAR_RANGE[1])
    uni_mag, year = uni_mag[keep], year_full[keep].astype(np.int32)
    del year_full, _src, keep
    gc.collect()
    n = len(uni_mag)
    if verbose:
        print(f"[1/2] {n:,} publications with a year, from {os.path.basename(MAP_NPZ)}", flush=True)

    def to_code(a):
        i = np.clip(np.searchsorted(uni_mag, a), 0, n - 1)
        return np.where(uni_mag[i] == a, i, -1).astype(np.int32)

    parts = ref_parts()
    if verbose:
        print(f"[2/2] edges from {len(parts)} partitions of {REF_PQ} ...", flush=True)
    cf, ct = [], []
    for i, f in enumerate(parts):
        d = pq.read_table(f, columns=["work_id", "referenced_work_id"]).to_pandas()
        u = to_code(id_to_code(d["work_id"]))
        v = to_code(id_to_code(d["referenced_work_id"]))
        m = (u >= 0) & (v >= 0)
        if m.any():
            cf.append(u[m]); ct.append(v[m])
        del d, u, v, m
        if verbose and (i + 1) % 500 == 0:
            print(f"      {i+1}/{len(parts)}  {sum(map(len, cf)):,} edges  "
                  f"[{time.time()-t0:.0f}s]", flush=True)
        gc.collect()
    c_from = np.concatenate(cf).astype(np.int32)
    c_to = np.concatenate(ct).astype(np.int32)
    del cf, ct
    gc.collect()
    np.savez(GRAPH_NPZ, c_from=c_from, c_to=c_to, year=year, uni_mag=uni_mag)
    if verbose:
        print(f"[{time.time()-t0:.0f}s] {len(c_from):,} edges, {n:,} publications -> {GRAPH_NPZ}"
              f"  ({os.path.getsize(GRAPH_NPZ)/1e9:.1f} GB)")
    return GRAPH_NPZ


def build_csr(force: bool = False, verbose: bool = True) -> str:
    """out/in adjacency in CSR form -- identical in shape to the OpenAlex cache."""
    if os.path.exists(CSR_NPZ) and not force:
        if verbose:
            print(f"CSR cache present: {CSR_NPZ}")
        return CSR_NPZ
    build_graph(verbose=verbose)
    t0 = time.time()
    z = np.load(GRAPH_NPZ)
    c_from = np.ascontiguousarray(z["c_from"]); c_to = np.ascontiguousarray(z["c_to"])
    year = np.ascontiguousarray(z["year"]).astype(np.int32)
    uni_mag = np.ascontiguousarray(z["uni_mag"])
    del z; gc.collect()
    n = len(year)

    def csr(src, dst):
        order = np.argsort(src, kind="stable")
        idx = dst[order].astype(np.int32); del order; gc.collect()
        ptr = np.zeros(n + 1, np.int64)
        np.add.at(ptr, src.astype(np.int64) + 1, 1)
        np.cumsum(ptr, out=ptr)
        return ptr, idx

    out_ptr, out_idx = csr(c_from, c_to)     # references (out-edges)
    in_ptr, in_idx = csr(c_to, c_from)       # citers (in-edges)
    del c_from, c_to; gc.collect()
    np.savez(CSR_NPZ, out_ptr=out_ptr, out_idx=out_idx, in_ptr=in_ptr, in_idx=in_idx,
             year=year, uni_mag=uni_mag)
    if verbose:
        print(f"[{time.time()-t0:.0f}s] CSR: {n:,} publications, {len(out_idx):,} edges -> {CSR_NPZ}")
    return CSR_NPZ


def load_graph():
    build_graph()
    z = np.load(GRAPH_NPZ)
    return z["c_from"], z["c_to"], z["year"].astype(np.int32), z["uni_mag"]


def load_csr():
    build_csr()
    z = np.load(CSR_NPZ)
    return (z["out_ptr"], z["out_idx"], z["in_ptr"], z["in_idx"],
            z["year"].astype(np.int32), z["uni_mag"])


# ── Reading the consolidated edge table directly ──────────────────────────────────────────
# references_w_year carries the six OpenAlex column names:
#     work_id, work_year, work_id_source_id,
#     referenced_work_id, referenced_work_year, referenced_work_id_source_id
# Parts are keyed on the CITING publication (one input file -> one part), so a paper's
# references are contiguous inside exactly one part and can be streamed; its citers are
# scattered over every part and need the CSR.

def stream_edges(columns, verbose: bool = True, every: int = 500):
    """Yield (part_index, pyarrow.Table) over the consolidated edge table."""
    ps = ref_parts()
    if not ps:
        raise SystemExit(f"{REF_PQ} has no part_*.parquet.\n"
                         f"        Run notebook/references_w_year.ipynb first.")
    t0 = time.time()
    for i, f in enumerate(ps):
        yield i, pq.read_table(f, columns=columns)
        if verbose and (i + 1) % every == 0:
            print(f"      {i+1}/{len(ps)} parts  [{time.time()-t0:.0f}s]", flush=True)


def code_index():
    """(uni_mag, year, to_code) for the publications that have a usable year -- identical to
    what build_graph() puts in the .npz, so a streamed result lands in the same code space."""
    code, year_full, _src = load_map()
    keep = year_full >= 0
    if YEAR_RANGE is not None:
        keep &= (year_full >= YEAR_RANGE[0]) & (year_full <= YEAR_RANGE[1])
    uni_mag = np.ascontiguousarray(code[keep])
    year = np.ascontiguousarray(year_full[keep]).astype(np.int32)
    del code, year_full, _src, keep
    gc.collect()
    n = len(uni_mag)

    def to_code(a):
        i = np.clip(np.searchsorted(uni_mag, a), 0, n - 1)
        return np.where(uni_mag[i] == a, i, -1).astype(np.int32)

    return uni_mag, year, to_code


def citation_counts(windows=(3, 5, 10), verbose: bool = True):
    """Forward-citation counts per window, streamed off the edge table.

    Reproduces paper_citation.ipynb's vectorised bincount exactly -- same code space, same
    `0 <= citer_year - cited_year <= w` rule -- without materialising c_from/c_to.
    Returns (uni_mag, year, {'_all': arr, '_10': arr, '_5': arr, '_3': arr})."""
    uni_mag, year, to_code = code_index()
    n = len(uni_mag)
    if verbose:
        print(f"[1/2] {n:,} publications with a year, from {os.path.basename(MAP_NPZ)}", flush=True)
        print(f"[2/2] streaming {len(ref_parts())} partitions of {REF_PQ} ...", flush=True)
    keys = ["_all"] + [f"_{w}" for w in sorted(windows, reverse=True)]
    res = {k: np.zeros(n, np.int64) for k in keys}
    cols = ["work_year", "referenced_work_id", "referenced_work_year"]
    for _, t in stream_edges(cols, verbose=verbose):
        cited = to_code(id_to_code(t.column("referenced_work_id").to_pandas()))
        cy = t.column("work_year").to_numpy(zero_copy_only=False)
        dy = t.column("referenced_work_year").to_numpy(zero_copy_only=False)
        with np.errstate(invalid="ignore"):
            diff = cy.astype(np.float64) - dy.astype(np.float64)
            ok = (cited >= 0) & np.isfinite(diff) & (diff >= 0)
            if not ok.any():
                continue
            cc = cited[ok].astype(np.int64)
            dd = diff[ok]
            res["_all"] += np.bincount(cc, minlength=n)
            for w in sorted(windows, reverse=True):
                m = dd <= w
                if m.any():
                    res[f"_{w}"] += np.bincount(cc[m], minlength=n)
        del cited, cy, dy, diff, ok
        gc.collect()
    return uni_mag, year, res


def stream_reference_journals(verbose: bool = True):
    """Yield (focal work_id array, focal source_id array, ref source code array, ref year
    array, run boundaries) per part -- the input atypicality needs, without the CSR."""
    cols = ["work_id", "work_id_source_id",
            "referenced_work_id_source_id", "referenced_work_year"]
    for i, t in stream_edges(cols, verbose=verbose):
        wid = t.column("work_id").to_pandas()
        chg = np.flatnonzero(wid.to_numpy()[1:] != wid.to_numpy()[:-1]) + 1
        starts = np.concatenate(([0], chg))
        ends = np.concatenate((chg, [len(wid)]))
        focal_id = wid.to_numpy()[starts]
        focal_src = t.column("work_id_source_id").to_pandas().to_numpy()[starts]
        ref_src = src_to_code(t.column("referenced_work_id_source_id").to_pandas())
        ref_year = t.column("referenced_work_year").to_numpy(zero_copy_only=False)
        yield i, focal_id, focal_src, ref_src, ref_year, starts, ends


# ── Journal and field, the two lookups ────────────────────────────────────────────────────
def read_sources() -> pd.DataFrame:
    """source_titles -> source_id, journal (title), source_type, issns.

    The `sources.csv.gz` twin. `source_type == 'journal'` (163,809 of 195,923 sources; the
    rest are proceedings, book series, seminar series, preprint platforms) is the analogue of
    MAG's `DocType == 'Journal'`, which paper_z_score uses to pick focal papers."""
    fs = sorted(glob.glob(f"{SOURCES}/source_titles_*"))
    d = pd.concat([pq.read_table(f, columns=["id", "type", "title", "issns"]).to_pandas()
                   for f in fs], ignore_index=True)
    d = d.rename(columns={"id": "source_id", "title": "journal", "type": "source_type"})
    d["source_id"] = norm_id(d["source_id"])
    return d[["source_id", "journal", "source_type", "issns"]]


def build_journal(force: bool = False, verbose: bool = True) -> str:
    """publication -> source id, journal title, is_journal, from the map's `source` column and
    source_titles. One row per publication that has a source."""
    if os.path.exists(JOURNAL_PQ) and not force:
        if verbose:
            print(f"journal cache present: {JOURNAL_PQ}")
        return JOURNAL_PQ
    code_, _year, source_ = load_map()
    m = source_ >= 0
    src = read_sources().drop_duplicates("source_id").set_index("source_id")
    out = pd.DataFrame({"work_id": code_to_id(code_[m]), "source_id": code_to_src(source_[m])})
    out["journal"] = out["source_id"].map(src["journal"])
    out["is_journal"] = out["source_id"].map(src["source_type"] == "journal").fillna(False).astype(bool)
    out.to_parquet(JOURNAL_PQ, index=False)
    if verbose:
        print(f"journal map from {os.path.basename(MAP_NPZ)}: {len(out):,} publications with a "
              f"source, {int(out.is_journal.sum()):,} in a journal-type source -> {JOURNAL_PQ}")
    return JOURNAL_PQ


def build_fos(force: bool = False, verbose: bool = True) -> str:
    """publication -> field of study, from `categories.for_2020_v2022` in the scalar parts.

    MAG's level-0 Field of Study has no exact twin here either. The closest is the ANZSRC
    Fields of Research 2020 **division** (2-digit, 23 of them): `FoS_rep` is the first division
    listed on the publication (Dimensions attaches no score, so there is no "highest-scoring"
    one) and `FoS_0` the `;`-joined set of its divisions. The 2- and 4-digit codes ride along."""
    if os.path.exists(FOS_PQ) and not force:
        if verbose:
            print(f"FoS cache present: {FOS_PQ}")
        return FOS_PQ
    _need_consolidated()
    import duckdb
    con = duckdb.connect()
    con.execute("SET preserve_insertion_order=false")
    con.execute(f"""
    COPY (
      SELECT pub_id AS work_id,
             CASE WHEN for1_names IS NULL OR for1_names = '' THEN NULL
                  ELSE str_split(for1_names, ';')[1] END AS FoS_rep,
             nullif(for1_names, '') AS FoS_0,
             nullif(for1_codes, '') AS for_division_codes,
             nullif(for2_codes, '') AS for_group_codes
      FROM read_parquet('{SCALARS}/part_*.parquet')
      WHERE for1_codes IS NOT NULL AND for1_codes <> ''
    ) TO '{FOS_PQ}' (FORMAT PARQUET, COMPRESSION ZSTD)""")
    n = con.execute(f"SELECT count(*) FROM read_parquet('{FOS_PQ}')").fetchone()[0]
    con.close()
    if verbose:
        print(f"FoS map: {n:,} publications with a FoR division -> {FOS_PQ}")
    return FOS_PQ


# ── Stage-0 workers ───────────────────────────────────────────────────────────────────────
# Module-level on purpose: ProcessPoolExecutor pickles the callable by qualified name, and a
# function defined in a notebook cell is not importable when the notebook runs through
# run_notebook.py (cells exec in a private namespace). Here they always are.

def readable(p: str) -> bool:
    """A parquet with a footer -- a name check would accept a half-written file."""
    try:
        return os.path.exists(p) and pq.ParquetFile(p).metadata.num_rows >= 0
    except Exception:
        return False


def footer_stats(path: str) -> dict:
    """year / type / rows of one publications file from its footer statistics -- no data page."""
    md_ = pq.ParquetFile(path).metadata
    y0 = y1 = None; types = set(); n = 0; ok = True
    for g in range(md_.num_row_groups):
        rg = md_.row_group(g); n += rg.num_rows
        cols = {rg.column(i).path_in_schema: rg.column(i).statistics for i in range(rg.num_columns)}
        sy, st = cols.get("year"), cols.get("type")
        if sy is None or not sy.has_min_max or st is None or not st.has_min_max:
            ok = False; continue
        y0 = sy.min if y0 is None else min(y0, sy.min); y1 = sy.max if y1 is None else max(y1, sy.max)
        types.update({st.min, st.max})
    return {"file": os.path.basename(path), "rows": n, "row_groups": md_.num_row_groups,
            "year_min": y0, "year_max": y1, "types": "|".join(sorted(types)), "stats_ok": ok,
            "MB": os.path.getsize(path) / 1e6}


def scalars_part(args, compression: str = "zstd"):
    """One publications file -> SCALARS/part_i and AUTHORS/part_i (DuckDB, one thread).

    The nested columns are unnested here and never again. See references_w_year.ipynb
    section 3 for the column semantics. Returns (i, rows, was_already_done)."""
    import duckdb
    i, src = args
    dst_s = f"{SCALARS}/{part_name(i)}"
    dst_a = f"{AUTHORS}/{part_name(i)}"
    if readable(dst_s) and readable(dst_a):
        return i, 0, True
    con = duckdb.connect()
    con.execute("SET threads=1"); con.execute("SET memory_limit='12GB'")   # x N_WORKERS, under nb.sbatch's 250 GB
    con.execute("SET preserve_insertion_order=false")
    con.execute(f"""
    CREATE TEMP TABLE x AS
    SELECT id AS pub_id, TRY_CAST(substr(id, 5) AS BIGINT) AS pid,
           TRY_CAST(year AS INTEGER) AS year, type,
           document_type.classification AS doc_class, document_type.is_citable AS is_citable,
           source_id, journal.id AS journal_id, journal.title AS journal_title,
           coalesce(len(reference_ids), 0) AS ref_count,
           citations_count, metrics.times_cited AS times_cited,
           array_to_string(list_transform(categories.for_2020_v2022.first_level.full,  f -> f.code), ';') AS for1_codes,
           array_to_string(list_transform(categories.for_2020_v2022.first_level.full,  f -> f.name), ';') AS for1_names,
           array_to_string(list_transform(categories.for_2020_v2022.second_level.full, f -> f.code), ';') AS for2_codes,
           coalesce(len(authors), 0) AS n_authors, doi,
           authors
    FROM read_parquet('{src}')""")
    n = con.execute("SELECT count(*) FROM x").fetchone()[0]
    con.execute(f"""COPY (SELECT * EXCLUDE (authors) FROM x)
                    TO '{dst_s}.tmp' (FORMAT PARQUET, COMPRESSION {compression})""")
    con.execute(f"""
    COPY (
      SELECT pub_id, pid,
             n_authors AS team_size,
             array_to_string(list_transform(list_filter(authors, a -> a.researcher_id IS NOT NULL),
                                            a -> a.researcher_id), ';')          AS author_list,
             len(list_filter(authors, a -> a.researcher_id IS NOT NULL))          AS n_resolved,
             authors[1].researcher_id                                              AS first_author,
             list_extract(authors, len(authors)).researcher_id                     AS last_author,
             list_filter(authors, a -> coalesce(a.corresponding, false))[1].researcher_id AS corresponding_author,
             array_to_string(list_sort(cc), ';')                                   AS countries,
             len(cc)                                                               AS n_countries
      FROM (SELECT *, list_distinct(flatten(list_transform(authors, a -> list_transform(
                        list_filter(coalesce(a.affiliations_address, []), ad -> ad.country_code IS NOT NULL),
                        ad -> ad.country_code)))) AS cc
            FROM x WHERE n_authors > 0)
    ) TO '{dst_a}.tmp' (FORMAT PARQUET, COMPRESSION {compression})""")
    con.close()
    os.replace(dst_s + ".tmp", dst_s)
    os.replace(dst_a + ".tmp", dst_a)
    return i, n, False


_MAP = None          # (code, year, source) -- set by set_map() BEFORE the pool is forked


def set_map(code, year, source):
    global _MAP
    _MAP = (np.ascontiguousarray(code), np.ascontiguousarray(year), np.ascontiguousarray(source))


def lookup(codes):
    """(year float32 with NaN, source id str or None) for each publication code, via the map."""
    CODE, YEAR, SOURCE = _MAP
    i = np.searchsorted(CODE, codes)
    i = np.clip(i, 0, len(CODE) - 1)
    hit = CODE[i] == codes
    yr = np.full(len(codes), np.nan, dtype=np.float32)
    sc = np.full(len(codes), -1, dtype=np.int64)
    yr[hit] = YEAR[i[hit]]
    sc[hit] = SOURCE[i[hit]]
    yr[yr < 0] = np.nan
    src = np.where(sc >= 0, np.char.add(SRC_PREFIX, sc.astype(str)), None)
    return yr, src


EDGE_SCHEMA = None   # built lazily: pyarrow schema of the edge table (OpenAlex column names)


def _edge_schema():
    global EDGE_SCHEMA
    import pyarrow as pa
    if EDGE_SCHEMA is None:
        EDGE_SCHEMA = pa.schema([
            ("work_id", pa.string()), ("work_year", pa.int16()), ("work_id_source_id", pa.string()),
            ("referenced_work_id", pa.string()), ("referenced_work_year", pa.int16()),
            ("referenced_work_id_source_id", pa.string()),
        ])
    return EDGE_SCHEMA


def edges_part(args, compression: str = "zstd"):
    """One publications file -> REF_PQ/part_i: reference_ids exploded, both endpoints dated
    and placed through the map. Requires set_map() in the parent before forking."""
    import pyarrow as pa
    import pyarrow.compute as pc
    assert _MAP is not None, "call dim.set_map(code, year, source) before the pool is created"
    i, src = args
    dst = f"{REF_PQ}/{part_name(i)}"
    if readable(dst):
        return i, 0, True
    schema = _edge_schema()

    def i16(x):
        # NaN -> int16 with safe=False silently becomes 0, not null: values and mask apart.
        m = np.isnan(x)
        return pa.array(np.where(m, 0, x).astype(np.int16), type=pa.int16(), mask=m)

    t = pq.read_table(src, columns=["id", "reference_ids"])
    refs = t.column("reference_ids").combine_chunks()
    flat = pc.list_flatten(refs)
    parent = pc.list_parent_indices(refs)
    citing = pc.take(t.column("id").combine_chunks(), parent)
    n = len(flat)
    if n == 0:
        tbl = schema.empty_table()
    else:
        cu = citing.to_pandas(); cv = flat.to_pandas()
        yu, su = lookup(id_to_code(cu))
        yv, sv = lookup(id_to_code(cv))
        tbl = pa.table({
            "work_id": pa.array(cu.to_numpy(), pa.string()), "work_year": i16(yu),
            "work_id_source_id": pa.array(su, pa.string()),
            "referenced_work_id": pa.array(cv.to_numpy(), pa.string()), "referenced_work_year": i16(yv),
            "referenced_work_id_source_id": pa.array(sv, pa.string()),
        }, schema=schema)
        del cu, cv, yu, su, yv, sv
    pq.write_table(tbl, dst + ".tmp", compression=compression)
    os.replace(dst + ".tmp", dst)
    del t, refs, flat, parent, citing, tbl
    gc.collect()
    return i, n, False


def summary():
    print(f"dump     : {ROOT}")
    print(f"cache    : {CACHE}")
    print(f"output   : {OUT}")
    if FILE_LIMIT:
        print(f"  NB_FILE_LIMIT={FILE_LIMIT}: a strided SAMPLE of the publication files -- smoke test")
    print(f"  consolidated edge table: "
          + ("present" if have_consolidated() else "NOT BUILT "
             "(run notebook/references_w_year.ipynb)"))
    for name, p in (("map", MAP_NPZ), ("graph", GRAPH_NPZ), ("csr", CSR_NPZ),
                    ("journal", JOURNAL_PQ), ("fos", FOS_PQ), ("pat2pub", PAT2PUB)):
        s = f"{os.path.getsize(p)/1e9:.2f} GB" if os.path.exists(p) else "not built"
        print(f"  {name:<9} {s:>12}  {p}")
    for name, d in (("scalars", SCALARS), ("authors", AUTHORS), ("edges", REF_PQ)):
        k = len(glob.glob(f"{d}/part_*.parquet"))
        print(f"  {name:<9} {k:>8} parts  {d}")
