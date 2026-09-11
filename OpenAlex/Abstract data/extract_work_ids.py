#!/usr/bin/env python3
"""Re-extract the paper training corpus from the tip dump WITH the OpenAlex work id.

`OpenAlex/Works_oa.py` built `OpenAlex/Data/work_{year}.parquet` (the corpus every paper chain
under Model/ and Model_full/ was trained on) from /project/jevans/tip/data/openalex/works.parquet
but left `id` out of READ_COLS. This script re-runs the SAME source, the SAME filter and the SAME
abstract reconstruction, reading `id` as well, and writes one row per kept work with the columns
needed to (a) prove the row set is identical to the training files and (b) attach the id to each
training row by an exact key.

    python extract_work_ids.py             # all 405 shards, resumable
    python extract_work_ids.py --workers 8
    python extract_work_ids.py --limit 3   # smoke: first 3 shards

Output: OpenAlex/Data/work_id_exact/shards/part_XXXX.parquet, hive-free, columns
    id, title, abstract, publication_date, publication_year, type,
    authors_count, referenced_works_count, concepts_count
then verify_attach_ids.py consolidates per year and does the proof.

Nothing here is new logic. The filter lines and reconstruct_abstract are taken from Works_oa.py:
reconstruct_abstract is loaded from that file's source at run time, so it cannot drift.
"""
from __future__ import annotations

import argparse
import ast
import gc
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

DATA_DIR = "/project/jevans/tip/data/openalex/works.parquet"          # same as Works_oa.py
WORKS_OA = "/project/jevans/Dawoon/OpenAlex/Works_oa.py"               # the original extractor
OUT_DIR = "/project/jevans/Dawoon/OpenAlex/Data/work_id_exact/shards"

# Works_oa.py READ_COLS, minus the nested columns nobody needs for a key, plus `id`.
READ_COLS = ["id", "abstract_inverted_index", "language", "publication_year", "publication_date",
             "title", "type", "authors_count", "referenced_works_count", "concepts_count"]
KEEP_COLS = ["id", "title", "abstract", "publication_date", "publication_year", "type",
             "authors_count", "referenced_works_count", "concepts_count"]


def load_reconstruct_abstract():
    """Take reconstruct_abstract verbatim from Works_oa.py without executing that script."""
    tree = ast.parse(open(WORKS_OA).read())
    fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "reconstruct_abstract"]
    assert len(fn) == 1, "reconstruct_abstract not found in Works_oa.py"
    ns = {"json": json, "pd": pd}
    exec(compile(ast.Module(body=fn, type_ignores=[]), WORKS_OA, "exec"), ns)
    return ns["reconstruct_abstract"], ast.get_source_segment(open(WORKS_OA).read(), fn[0])


def process_shard(i: int, file: str) -> dict:
    out = os.path.join(OUT_DIR, f"part_{i:04d}.parquet")
    if os.path.exists(out):
        return {"i": i, "file": file, "status": "skip"}
    reconstruct_abstract, _ = load_reconstruct_abstract()
    t0 = time.time()
    df = pd.read_parquet(os.path.join(DATA_DIR, file), columns=READ_COLS)
    n_read = len(df)
    # ---- Works_oa.py, verbatim logic ----
    df["publication_year"] = pd.to_numeric(df["publication_year"], errors="coerce")
    df = df[(df["language"] == "en") & (df["publication_year"] >= 1970)]
    n_filt = len(df)
    if len(df):
        df["abstract"] = df["abstract_inverted_index"].apply(reconstruct_abstract)
        df = df[df["abstract"].notna()]
    n_kept = len(df)
    # -------------------------------------
    if len(df):
        df = df[KEEP_COLS].copy()
        df["id"] = df["id"].astype(str).str.rstrip("/").str.rsplit("/", n=1).str[-1]   # W123
        df["publication_year"] = df["publication_year"].astype("int64")
        tbl = pa.Table.from_pandas(df, preserve_index=False)
    else:
        tbl = pa.table({c: pa.array([], type=pa.string()) for c in KEEP_COLS})
    pq.write_table(tbl, out + ".tmp", compression="zstd")
    os.replace(out + ".tmp", out)
    del df; gc.collect()
    return {"i": i, "file": file, "status": "ok", "n_read": n_read, "n_filtered": n_filt,
            "n_kept": n_kept, "sec": round(time.time() - t0, 1)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=int(os.environ.get("SLURM_CPUS_PER_TASK", "8")))
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)

    _, src = load_reconstruct_abstract()
    print("reconstruct_abstract loaded from Works_oa.py:\n" + "\n".join("    " + l for l in src.splitlines()[:3]) + "\n    ...")
    files = sorted(f for f in os.listdir(DATA_DIR) if f.endswith(".parquet"))     # same order as Works_oa.py
    if a.limit:
        files = files[: a.limit]
    print(f"{len(files)} shards, {a.workers} workers -> {OUT_DIR}", flush=True)

    t0 = time.time(); rows = []; done = 0
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(process_shard, i, f): i for i, f in enumerate(files)}
        for fut in as_completed(futs):
            r = fut.result(); rows.append(r); done += 1
            if r["status"] == "ok" and (done % 10 == 0 or done == len(files)):
                kept = sum(x.get("n_kept", 0) for x in rows)
                print(f"  {done}/{len(files)} shards  kept so far {kept:,}  ({time.time()-t0:.0f}s)", flush=True)
    log = pd.DataFrame(rows).sort_values("i")
    log.to_csv(os.path.join(os.path.dirname(OUT_DIR), "extract_log.csv"), index=False)
    ok = log[log.status == "ok"]
    print(f"\ndone: {len(ok)} shards processed, {(log.status == 'skip').sum()} skipped (already present)")
    if len(ok):
        print(f"  rows read {ok.n_read.sum():,}  after en/1970 filter {ok.n_filtered.sum():,}  "
              f"with abstract {ok.n_kept.sum():,}  in {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
