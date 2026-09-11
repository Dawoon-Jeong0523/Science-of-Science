"""Paths for the PCS (patent->paper citation) notebooks, on Midway.

The two notebooks in notebook/ were written against a Windows layout: a
`for _ in range(6): os.chdir('..')` hunt for a marker directory, then
`Data/Reliance on Science/...`, `E:/Dawoon Jeong/Data/PatentView/Granted/...` and an
`E:/.../paper_metadata.sqlite`. None of that exists here.

Two substitutions are not just path rewrites and are called out where they happen:

  * the paper_id -> year lookup was a SQLite table (`SELECT paper_id, year FROM papers`).
    Here it comes from oa_common.load_map(), which is the authoritative per-work table for
    this snapshot -- already sorted by id, which is what the searchsorted lookup wants.
  * paper metadata for the hit-probability join is
    Science of Science/OpenAlex/output/paper_metadata.parquet, whose `paper_id` is the
    'W…' string form, matching what pcs_citation writes.

    import pcs_common as pcs
    pcs.preflight()
    df = pd.read_csv(pcs.PCS_CSV, ...)
"""
from __future__ import annotations

import os
import sys

SOS  = "/project/jevans/Dawoon/Science of Science"
BASE = f"{SOS}/pcs"
OUT  = f"{BASE}/output"
os.makedirs(OUT, exist_ok=True)

# Reliance on Science, patent -> paper citations. Was Data/Reliance on Science/pcs_oa_uspto.csv
PCS_CSV = f"{BASE}/pcs_oa_uspto.csv"

# Sibling pipelines
OA_BASE  = f"{SOS}/OpenAlex"
PV_BASE  = f"{SOS}/PatentView"
PAPER_META = f"{OA_BASE}/output/paper_metadata.parquet"   # was notebook/paper/output/…

for _p in (OA_BASE, PV_BASE):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def out(name: str) -> str:
    return f"{OUT}/{name}"


def granted(name: str) -> str:
    """A PatentsView granted bulk file, via pv_common's own local/project fallback."""
    import pv_common as pv
    return pv.granted(name)


def paper_year_map():
    """(sorted int64 work ids, int32 year) -- the replacement for paper_metadata.sqlite.

    oa_common.load_map() returns the per-work table built by referenced_works_w_year.ipynb:
    `code` is already sorted, so it drops straight into the searchsorted lookup the notebook
    uses. Unknown years are -1 there; they are returned as a sentinel the caller can test,
    because a -1 silently used as a year makes every citation lag one year too long."""
    import numpy as np
    import oa_common as oa
    code, year, _src = oa.load_map()
    year = year.astype(np.int32)
    return code, year


NEEDS = {
    "pcs_citation":        [PCS_CSV, "@g_patent.tsv.zip", f"{OA_BASE}/cache/work_year_source_map.npz"],
    "pcs_hit_probability": [out("pcs_citation.parquet"), PAPER_META],
}


def preflight(notebook: str | None = None) -> bool:
    names = [notebook] if notebook else sorted(NEEDS)
    print(f"pcs base   : {BASE}")
    print(f"output     : {OUT}\n")
    ok_all = True
    for nb in names:
        miss = []
        for f in NEEDS.get(nb, []):
            if f.startswith("@"):
                try:
                    granted(f[1:])
                except FileNotFoundError:
                    miss.append(f[1:])
            elif not os.path.exists(f):
                miss.append(f)
        print(f"  {nb:<22}{'OK' if not miss else f'MISSING {len(miss)}'}")
        for m in miss:
            print(f"      {m}  <- not available")
        ok_all &= not miss
    return ok_all
