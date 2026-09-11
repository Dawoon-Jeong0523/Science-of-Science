#!/usr/bin/env python3
"""Does the streamed citation count reproduce paper_citation.parquet exactly?

paper_citation.parquet was produced by the graph path: load c_from/c_to/year (21.6 GB),
diff = year[c_from] - year[c_to], bincount. oa.citation_counts() takes the same numbers off
the edge table's own work_year / referenced_work_year columns without materialising the
graph. If the two agree element for element, the streaming path is a drop-in and the graph
load can go; if they do not, the difference localises which edges the two paths disagree
about, which is the thing worth knowing before rewiring seven notebooks.
"""
import gc
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import oa_common as oa

print("streaming the edge table …", flush=True)
uni_mag, year, res = oa.citation_counts(windows=(3, 5, 10))
n = len(uni_mag)
print(f"\nstreamed: {n:,} works")
for k in ("_3", "_5", "_10", "_all"):
    print(f"  C{k}: total {int(res[k].sum()):,}  mean {res[k].mean():.4f}")

print("\nloading paper_citation.parquet …", flush=True)
old = pq.read_table(oa.out_fp if hasattr(oa, "out_fp") else f"{oa.OUT}/paper_citation.parquet",
                    columns=["paper_id", "C_3", "C_5", "C_10", "C_all"]).to_pandas()
print(f"  {len(old):,} rows")

code = oa.id_to_code(old["paper_id"])
i = np.clip(np.searchsorted(uni_mag, code), 0, n - 1)
hit = uni_mag[i] == code
print(f"  ids resolvable in the streamed code space: {hit.sum():,}/{len(old):,} "
      f"({hit.mean()*100:.3f}%)")

ok_all = True
for w, col in ((3, "C_3"), (5, "C_5"), (10, "C_10"), (None, "C_all")):
    key = "_all" if w is None else f"_{w}"
    a = old[col].to_numpy()[hit]
    b = res[key][i[hit]]
    same = int((a == b).sum())
    diff = np.flatnonzero(a != b)
    print(f"  {col:<6} identical {same:,}/{len(a):,} ({same/len(a)*100:.4f}%)"
          + (f"  |  max |delta| {int(np.abs(a[diff]-b[diff]).max())}" if len(diff) else ""))
    ok_all &= (same == len(a))
    del a, b, diff
    gc.collect()

print("\nRESULT:", "IDENTICAL — the streaming path is a drop-in"
      if ok_all else "DIFFERS — do not rewire the notebooks yet")
