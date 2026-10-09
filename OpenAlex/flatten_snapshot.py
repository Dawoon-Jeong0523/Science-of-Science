"""Flatten OpenAlex's official nested parquet snapshot into the table layout the notebooks read.

The notebooks were built on renli's 2026-01-16 conversion, a set of flat tables under works/<table>/part_XXXX.parquet
plus topics.csv.gz, sources.csv.gz and works_au_affs_fixed.csv.gz at the root. That conversion lost 104M of 477M works
(it named each output part by the input file's basename, so same-numbered files from different updated_date= folders
overwrote one another, and 301 failed files were never retried). This script rebuilds the same layout from the official
parquet export with one rule that prevents a repeat: output part i is input file i of the sorted manifest, for every
table, so names cannot collide and the tables stay partition-aligned (part i of each table holds exactly the works of
input file i).

    python flatten_snapshot.py parts  SHARD NSHARD [PROCS]   # convert this shard's input files
    python flatten_snapshot.py lookups                       # topics.csv.gz, sources.csv.gz
    python flatten_snapshot.py verify                        # counts vs manifest, alignment, id uniqueness

Tables (column names, types and id forms follow renli's tables, so the notebooks run unchanged):
  works/works              id, doi, title, display_name, publication_year, publication_date, type, cited_by_count,
                           is_retracted, is_paratext, cited_by_api_url (null), language, is_xpac
  works/works_semantic     work_id (URL form, as renli's), primary_topic_json, keywords_json, has_abstract
  works/topics             work_id, topic_id, score                    (one row per scored topic)
  works/primary_locations  work_id, source_id, landing_page_url, pdf_url, is_oa, version, license
  works/locations          same columns, one row per location
  works/referenced_works   work_id, referenced_work_id
  works/authorships        replaces works_au_affs_fixed.csv.gz: one row per authorship (work, author slot) with
                           work_id, author_position_int (1-based slot), author_position, author_id, author_display_name,
                           raw_author_name, is_corresponding, institution_ids, countries (';'-joined), orcid
abstract_inverted_index, concepts, mesh, ids, biblio, open_access and related_works are not carried over: no notebook
reads them. Read them from the nested snapshot directly.
"""
from __future__ import annotations

import gc
import glob
import json
import os
import sys
import time
from multiprocessing import get_context

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

SRC = "/project/jevans/OpenAlex_shared/OpenAlex_2026_Sep_23"        # unmodified mirror of s3://openalex/data/parquet/
DST = os.environ.get("FLAT_DST", "/project/jevans/OpenAlex_shared/OpenAlex_2026_Sep_23_flat")   # FLAT_DST: smoke tests
PREFIX = "https://openalex.org/"
TABLES = ("works", "works_semantic", "topics", "primary_locations", "locations", "referenced_works", "authorships")
READ_COLS = ["id", "doi", "title", "display_name", "publication_year", "publication_date", "type", "cited_by_count",
             "is_retracted", "is_paratext", "language", "is_xpac", "primary_topic", "topics", "keywords",
             "primary_location", "locations", "referenced_works", "authorships", "abstract_inverted_index"]


def input_files() -> list[tuple[str, int]]:
    """(local path, record_count) of every works file, sorted by (updated_date, part number)."""
    m = json.load(open(f"{SRC}/works/manifest.json"))
    rows = [(f["url"].replace("s3://openalex/data/parquet/", SRC + "/"), f["meta"]["record_count"],
             f["meta"]["content_length"]) for f in m["files"]]
    rows.sort(key=lambda r: (r[0].split("updated_date=")[1].split("/")[0], int(r[0].rsplit("part_", 1)[1][:4])))
    return rows


def strip(a):
    """'https://openalex.org/W123' -> 'W123' (renli's bare form); nulls stay null."""
    return pc.replace_substring(a, PREFIX, "")


def score32(a):
    """float32 score -> float64 via its shortest decimal form, so 0.0406 stays 0.0406 as in renli's tables
    (a plain cast would give 0.04060000181...)."""
    return pc.cast(pc.cast(a, pa.string()), pa.float64())


def explode(list_arr):
    """(parent row index, flattened values, 0-based slot within the list) of a list column."""
    list_arr = list_arr.combine_chunks() if isinstance(list_arr, pa.ChunkedArray) else list_arr
    parent = pc.list_parent_indices(list_arr).to_numpy()
    values = pc.list_flatten(list_arr)
    slot = np.arange(len(parent)) - np.searchsorted(parent, parent, side="left")
    return parent, values, slot


def join_list(list_arr, sep=";"):
    """list<string> -> 'a;b;c'; null or empty list -> null."""
    s = pc.binary_join(list_arr, sep)
    return pc.if_else(pc.equal(s, ""), pa.scalar(None, pa.string()), s)


def primary_topic_json(pt) -> pa.Array:
    """renli's json.dumps layout: id, display_name, score, subfield, field, domain (null when no primary topic)."""
    pt = pt.combine_chunks() if isinstance(pt, pa.ChunkedArray) else pt
    scores = score32(pc.struct_field(pt, "score")).to_pylist()
    return pa.array([None if d is None else json.dumps({
        "id": d["id"], "display_name": d["display_name"], "score": s,
        "subfield": d["subfield"], "field": d["field"], "domain": d["domain"]})
        for d, s in zip(pt.to_pylist(), scores)], pa.string())


def keywords_json(kw, n) -> pa.Array:
    """renli's layout: a JSON list of {id, display_name, score}; '[]' when a work has none."""
    p, v, _ = explode(kw)
    rows = [[] for _ in range(n)]
    for i, a, b, s in zip(p.tolist(), pc.struct_field(v, "id").to_pylist(),
                          pc.struct_field(v, "display_name").to_pylist(),
                          score32(pc.struct_field(v, "score")).to_pylist()):
        rows[i].append({"id": a, "display_name": b, "score": s})
    return pa.array([json.dumps(r) for r in rows], pa.string())


def location_table(work_ids, parent, loc):
    """Rows of locations (struct array) with the work id of each row's parent."""
    src = pc.struct_field(loc, "source")
    return pa.table({
        "work_id": pc.take(work_ids, pa.array(parent)),
        "source_id": strip(pc.struct_field(src, "id")),
        "landing_page_url": pc.struct_field(loc, "landing_page_url"),
        "pdf_url": pc.struct_field(loc, "pdf_url"),
        "is_oa": pc.struct_field(loc, "is_oa"),
        "version": pc.struct_field(loc, "version"),
        "license": pc.struct_field(loc, "license"),
    })


def convert_batch(t: pa.Table) -> dict[str, pa.Table]:
    n = t.num_rows
    wid = strip(t["id"]).combine_chunks()
    out = {}
    out["works"] = pa.table({
        "id": wid, "doi": t["doi"], "title": t["title"], "display_name": t["display_name"],
        "publication_year": pc.cast(t["publication_year"], pa.int64()),
        "publication_date": pc.cast(t["publication_date"], pa.string()),
        "type": t["type"], "cited_by_count": pc.cast(t["cited_by_count"], pa.int64()),
        "is_retracted": t["is_retracted"], "is_paratext": t["is_paratext"], "cited_by_api_url": pa.nulls(n),
        "language": t["language"], "is_xpac": t["is_xpac"]})
    out["works_semantic"] = pa.table({
        "work_id": t["id"],
        "primary_topic_json": primary_topic_json(t["primary_topic"]),
        "keywords_json": keywords_json(t["keywords"], n),
        "has_abstract": pc.is_valid(t["abstract_inverted_index"])})
    p, v, _ = explode(t["topics"])
    out["topics"] = pa.table({"work_id": pc.take(wid, pa.array(p)), "topic_id": strip(pc.struct_field(v, "id")),
                              "score": score32(pc.struct_field(v, "score"))})
    pl = t["primary_location"].combine_chunks()
    keep = np.flatnonzero(pc.is_valid(pl).to_numpy(zero_copy_only=False))
    out["primary_locations"] = location_table(wid, keep, pc.take(pl, pa.array(keep)))
    p, v, _ = explode(t["locations"])
    out["locations"] = location_table(wid, p, v)
    p, v, _ = explode(t["referenced_works"])
    out["referenced_works"] = pa.table({"work_id": pc.take(wid, pa.array(p)), "referenced_work_id": strip(v)})
    p, v, slot = explode(t["authorships"])
    author = pc.struct_field(v, "author")
    inst = pc.struct_field(v, "institutions")
    lens = pc.fill_null(pc.list_value_length(inst), 0).to_numpy()
    inst_ids = pa.ListArray.from_arrays(pa.array(np.r_[0, np.cumsum(lens)].astype(np.int32)),
                                        pc.struct_field(pc.list_flatten(inst), "id"))
    out["authorships"] = pa.table({
        "work_id": pc.take(wid, pa.array(p)),
        "author_position_int": pa.array(slot + 1, pa.int32()),
        "author_position": pc.struct_field(v, "author_position"),
        "author_id": strip(pc.struct_field(author, "id")),
        "author_display_name": pc.struct_field(author, "display_name"),
        "raw_author_name": pc.struct_field(v, "raw_author_name"),
        "is_corresponding": pc.struct_field(v, "is_corresponding"),
        "institution_ids": join_list(inst_ids),
        "countries": join_list(pc.struct_field(v, "countries")),
        "orcid": pc.struct_field(author, "orcid")})
    return out


def do_file(arg):
    """Convert input file `idx` into part_{idx:04d}.parquet of every table. Idempotent: skips a part whose stats file
    exists (written last, after every table is in place)."""
    idx, path, n_expected = arg
    stats_fp = f"{DST}/_stats/part_{idx:04d}.json"
    if os.path.exists(stats_fp):
        return idx, "skipped"
    t0 = time.time()
    pf = pq.ParquetFile(path)          # a ParquetFile, never pq.read_table: the updated_date= folder would be read as
                                       # a hive partition column and clash with the file's own updated_date column
    writers, counts = {}, dict.fromkeys(TABLES, 0)
    tmp = {tb: f"{DST}/works/{tb}/part_{idx:04d}.parquet.tmp" for tb in TABLES}
    try:
        for g in range(pf.num_row_groups):
            for tb, tab in convert_batch(pf.read_row_group(g, columns=READ_COLS)).items():
                if tb not in writers:
                    writers[tb] = pq.ParquetWriter(tmp[tb], tab.schema, compression="zstd")
                writers[tb].write_table(tab)
                counts[tb] += tab.num_rows
            gc.collect()
        if not writers:                # a file with no row groups still gets (empty) parts, to keep alignment
            for tb, tab in convert_batch(pf.schema_arrow.empty_table().select(READ_COLS)).items():
                writers[tb] = pq.ParquetWriter(tmp[tb], tab.schema, compression="zstd")
        for w in writers.values():
            w.close()
    except Exception:
        for w in writers.values():
            try:
                w.close()
            except Exception:
                pass
        raise
    assert counts["works"] == n_expected, f"{path}: {counts['works']} works, manifest says {n_expected}"
    for tb in TABLES:
        os.replace(tmp[tb], tmp[tb][:-4])
    json.dump({"idx": idx, "source": path, "manifest_records": n_expected, "rows": counts,
               "seconds": round(time.time() - t0, 1)}, open(stats_fp, "w"))
    return idx, f"{counts['works']:,} works in {time.time() - t0:.0f}s"


def shard_of(files, nshard):
    """Largest file first to the lightest shard (by bytes), so the shards finish together."""
    load, owner = [0] * nshard, {}
    for i in sorted(range(len(files)), key=lambda i: -files[i][2]):
        k = load.index(min(load))
        owner[i] = k
        load[k] += files[i][2]
    return owner


def run_parts(shard: int, nshard: int, procs: int):
    files = input_files()
    for tb in TABLES:
        os.makedirs(f"{DST}/works/{tb}", exist_ok=True)
    os.makedirs(f"{DST}/_stats", exist_ok=True)
    owner = shard_of(files, nshard)
    mine = sorted((i for i in range(len(files)) if owner[i] == shard), key=lambda i: -files[i][2])
    if os.environ.get("FLAT_ONLY"):                      # smoke test: only these input indices
        mine = [int(x) for x in os.environ["FLAT_ONLY"].split(",")]
    print(f"shard {shard}/{nshard}: {len(mine)} of {len(files)} files, "
          f"{sum(files[i][2] for i in mine) / 1e9:.1f} GB, {procs} processes", flush=True)
    t0, done = time.time(), 0
    with get_context("fork").Pool(procs, maxtasksperchild=20) as pool:
        for idx, msg in pool.imap_unordered(do_file, [(i, files[i][0], files[i][1]) for i in mine]):
            done += 1
            if done % 25 == 0 or done == len(mine):
                print(f"  {done}/{len(mine)}  part_{idx:04d} {msg}  [{time.time() - t0:.0f}s]", flush=True)


def run_lookups():
    """topics.csv.gz and sources.csv.gz with renli's column names (URL-form ids)."""
    tp = pa.concat_tables(pq.ParquetFile(f).read() for f in sorted(glob.glob(f"{SRC}/topics/*/*.parquet")))
    d = pd.DataFrame({
        "id": tp["id"].to_pandas(), "display_name": tp["display_name"].to_pandas(),
        "subfield_id": pc.struct_field(tp["subfield"], "id").to_pandas(),
        "subfield_display_name": pc.struct_field(tp["subfield"], "display_name").to_pandas(),
        "field_id": pc.struct_field(tp["field"], "id").to_pandas(),
        "field_display_name": pc.struct_field(tp["field"], "display_name").to_pandas(),
        "domain_id": pc.struct_field(tp["domain"], "id").to_pandas(),
        "domain_display_name": pc.struct_field(tp["domain"], "display_name").to_pandas(),
        "description": tp["description"].to_pandas(),
        "keywords": pc.binary_join(tp["keywords"], "; ").to_pandas(),
        "works_count": tp["works_count"].to_pandas(), "cited_by_count": tp["cited_by_count"].to_pandas()})
    assert d["id"].is_unique and d[["id", "display_name", "subfield_id", "field_id", "domain_id"]].notna().all().all()
    d.sort_values("id").to_csv(f"{DST}/topics.csv.gz", index=False, compression="gzip")
    print(f"topics.csv.gz: {len(d):,} topics, {d.subfield_id.nunique()} subfields, {d.field_id.nunique()} fields")
    cols = ["id", "issn_l", "display_name", "host_organization_name", "works_count", "cited_by_count", "type",
            "country_code", "is_oa", "is_in_doaj", "is_core", "first_publication_year", "last_publication_year"]
    so = pd.concat(pq.ParquetFile(f).read(columns=cols).to_pandas()
                   for f in sorted(glob.glob(f"{SRC}/sources/*/*.parquet")))
    assert so["id"].is_unique
    so.sort_values("id").to_csv(f"{DST}/sources.csv.gz", index=False, compression="gzip")
    print(f"sources.csv.gz: {len(so):,} sources ({(so.type == 'journal').sum():,} journals)")


def run_verify():
    files = input_files()
    ok = True
    stats = []
    for i, (path, n, _) in enumerate(files):
        fp = f"{DST}/_stats/part_{i:04d}.json"
        if not os.path.exists(fp):
            print(f"MISSING part_{i:04d} ({path})"); ok = False; continue
        s = json.load(open(fp))
        stats.append(s)
        if s["source"] != path or s["rows"]["works"] != n:
            print(f"BAD part_{i:04d}: {s}"); ok = False
    for tb in TABLES:
        ps = sorted(glob.glob(f"{DST}/works/{tb}/part_*.parquet"))
        rows = sum(pq.ParquetFile(p).metadata.num_rows for p in ps)
        want = sum(s["rows"][tb] for s in stats)
        good = len(ps) == len(files) and rows == want and not glob.glob(f"{DST}/works/{tb}/*.tmp")
        ok &= good
        print(f"{tb:<18} {len(ps):>5} parts  {rows:>15,} rows  {'OK' if good else 'MISMATCH (want ' + str(want) + ')'}")
    n_works = sum(s["rows"]["works"] for s in stats)
    man = json.load(open(f"{SRC}/works/manifest.json"))["record_count"]
    print(f"works {n_works:,} vs manifest {man:,}")
    ok &= n_works == man
    # every work once, and works_semantic row-aligned with works in every part
    codes = []
    for i in range(len(files)):
        a = pq.ParquetFile(f"{DST}/works/works/part_{i:04d}.parquet").read(columns=["id"])["id"]
        b = pq.ParquetFile(f"{DST}/works/works_semantic/part_{i:04d}.parquet").read(columns=["work_id"])["work_id"]
        if not a.equals(strip(b)):
            print(f"works_semantic not aligned in part_{i:04d}"); ok = False
        codes.append(pc.cast(pc.utf8_slice_codeunits(a, 1), pa.int64()).to_numpy())
    c = np.sort(np.concatenate(codes))
    dup = int((c[1:] == c[:-1]).sum())
    print(f"distinct work ids {len(c) - dup:,}, duplicates {dup:,}")
    ok &= dup == 0
    print("VERIFY", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "parts":
        run_parts(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]) if len(sys.argv) > 4 else 8)
    elif cmd == "lookups":
        run_lookups()
    elif cmd == "verify":
        sys.exit(run_verify())
    else:
        raise SystemExit(__doc__)
