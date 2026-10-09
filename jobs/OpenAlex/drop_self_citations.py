"""Drop self-citation rows from OpenAlex/output/referenced_works_w_year (one-off, 2026-10-03).

813,123 works of the 2026-01-16 snapshot list themselves among their own referenced_works. Since
2026-10-03 referenced_works_w_year.ipynb drops those rows in pass 2; this script applies the same
filter to the table that notebook already wrote, instead of re-walking the snapshot (~7 h). Rows are
only removed, never reordered, and parts are written with the notebook's own settings (zstd,
pq.write_table defaults), so the result is what a fresh run of the patched notebook writes.

Steps, all checked before anything is moved:
  1. every part -> referenced_works_w_year.new/ with `work_id != referenced_work_id`
  2. per part: rows_new == rows_old - self_rows, and no self row left
  3. in total: exactly EXPECTED self rows dropped
  4. swap: the old table and the graph / CSR caches built from it go to
     OpenAlex/Old/pre_selfcite_2026-10-03/, the new table takes the old name.
     The caches are moved, not deleted, so that oa.build_graph() / oa.build_csr() rebuild them.
Copies of the outputs that will be recomputed also go there, for the before/after comparison.

    sbatch drop_self_citations.sbatch
"""
import glob, os, shutil, sys, time
import pyarrow.compute as pc
import pyarrow.parquet as pq

BASE = "/project/jevans/Dawoon/Science of Science"
OA = f"{BASE}/OpenAlex"
SRC = f"{OA}/output/referenced_works_w_year"
NEW = f"{SRC}.new"
OLD = f"{OA}/Old/pre_selfcite_2026-10-03"
EXPECTED = 813_123                  # counted 2026-10-03: work_id == referenced_work_id rows
COMPRESSION = "zstd"                # as in referenced_works_w_year.ipynb
# outputs recomputed after the fix; copied (not moved) so readers keep a file until the rerun replaces it
OUTPUTS = ["paper_metadata.parquet", "paper_citation.parquet", "paper_citation_trend.parquet",
           "paper_disruption.parquet", "paper_disruption_trend.parquet", "paper_disruption_trend_summary.parquet",
           "paper_hit_probability.parquet", "paper_sb.parquet", "paper_fos_coverage_by_year.csv",
           "paper_z_score.parquet", "z_score_pair.parquet", "paper_z_score_provenance.json"]
Z_PARTS = ["1980_1984", "1985_1989", "1990_2000", "2001_2006", "2007_2011"] + [f"{y}_{y}" for y in range(2012, 2021)]
OUTPUTS += [f"paper_z_score_{p}.parquet" for p in Z_PARTS] + [f"z_score_pair_{p}.parquet" for p in Z_PARTS]
PPP = [f"{BASE}/PPP/output/ppp_paper_trend.parquet", f"{BASE}/PPP/output/ppp_patent_trend.parquet"]

parts = sorted(glob.glob(f"{SRC}/part_*.parquet"))
assert len(parts) == 1334, f"expected 1334 parts, found {len(parts)}"
assert not os.path.exists(OLD + "/referenced_works_w_year"), "already swapped once -- nothing to do"
os.makedirs(NEW, exist_ok=True)

t0 = time.time()
rows_old = rows_new = dropped = 0
for i, f in enumerate(parts):
    t = pq.read_table(f)
    self_row = pc.equal(t["work_id"], t["referenced_work_id"])
    n_self = int(pc.sum(self_row).as_py() or 0)
    keep = t.filter(pc.invert(pc.fill_null(self_row, False)))
    assert keep.num_rows == t.num_rows - n_self
    assert not pc.any(pc.equal(keep["work_id"], keep["referenced_work_id"])).as_py()
    dst = f"{NEW}/{os.path.basename(f)}"
    pq.write_table(keep, dst + ".tmp", compression=COMPRESSION)
    os.replace(dst + ".tmp", dst)
    assert pq.ParquetFile(dst).metadata.num_rows == keep.num_rows
    rows_old += t.num_rows; rows_new += keep.num_rows; dropped += n_self
    if (i + 1) % 100 == 0:
        print(f"  {i + 1}/{len(parts)}  {rows_old:,} -> {rows_new:,}  ({dropped:,} self rows)  "
              f"[{time.time() - t0:.0f}s]", flush=True)
print(f"\nall parts: {rows_old:,} -> {rows_new:,} rows, {dropped:,} self-citation rows dropped "
      f"[{time.time() - t0:.0f}s]", flush=True)
assert dropped == EXPECTED, f"dropped {dropped:,}, expected {EXPECTED:,}"
assert rows_new == rows_old - EXPECTED

os.makedirs(f"{OLD}/cache", exist_ok=True)
os.makedirs(f"{OLD}/output", exist_ok=True)
os.makedirs(f"{OLD}/PPP_output", exist_ok=True)
for name in OUTPUTS:
    p = f"{OA}/output/{name}"
    if os.path.exists(p):
        shutil.copy2(p, f"{OLD}/output/{name}")
    else:
        print(f"  [note] no {name} to keep")
for p in PPP:
    shutil.copy2(p, f"{OLD}/PPP_output/{os.path.basename(p)}")
print(f"copied {len(os.listdir(OLD + '/output'))} outputs + {len(PPP)} PPP tables to {OLD}", flush=True)

os.replace(SRC, f"{OLD}/referenced_works_w_year")
os.replace(NEW, SRC)
for name in ("paper_graph.npz", "paper_csr.npz"):
    p = f"{OA}/cache/{name}"
    if os.path.exists(p):
        os.replace(p, f"{OLD}/cache/{name}")
print(f"swapped: {SRC} is the filtered table; the old one and the graph / CSR caches are in {OLD}")
print(f"DONE in {time.time() - t0:.0f}s")
sys.exit(0)
