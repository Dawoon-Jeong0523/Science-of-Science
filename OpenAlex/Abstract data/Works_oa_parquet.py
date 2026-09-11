#!/usr/bin/env python

import os
import re
from tqdm import tqdm

import pyarrow.dataset as ds
import pyarrow.parquet as pq


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PARQUET_ROOT = "/project/jevans/Dawoon/OpenAlex/works_en_1970plus_by_year"  # input partitioned dir
OUT_DIR = "/project/jevans/Dawoon/OpenAlex/Data"  # output dir (원하면 바꿔)
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# Find year partitions
# ---------------------------------------------------------
pattern = re.compile(r"^publication_year=(\d{4})$")
year_dirs = []

for name in os.listdir(PARQUET_ROOT):
    m = pattern.match(name)
    if m:
        year = int(m.group(1))
        year_dirs.append((year, os.path.join(PARQUET_ROOT, name)))

year_dirs = sorted(year_dirs, key=lambda x: x[0])
if not year_dirs:
    raise RuntimeError(f"No year partitions found under: {PARQUET_ROOT}")

# ---------------------------------------------------------
# Convert each year partition folder -> single yearly parquet
# ---------------------------------------------------------
for year, ydir in tqdm(year_dirs, desc="Consolidating yearly parquet partitions"):
    out_path = os.path.join(OUT_DIR, f"work_{year}.parquet")

    # skip if already exists
    if os.path.exists(out_path):
        continue

    # read whole year as an Arrow Table (no pandas conversion)
    dataset = ds.dataset(ydir, format="parquet")
    table = dataset.to_table()

    # write as a single parquet file
    pq.write_table(table, out_path, compression="snappy")

    # sanity check
    if (not os.path.exists(out_path)) or (os.path.getsize(out_path) == 0):
        raise RuntimeError(f"Parquet write failed or empty: {out_path}")

print("Done.")
