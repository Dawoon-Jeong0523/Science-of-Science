import os
import re
import pickle
import pandas as pd
from tqdm import tqdm


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PARQUET_ROOT = "/project/jevans/Dawoon/OpenAlex/works_en_1970plus_by_year"  # your output dir
OUT_DIR = "./Data"  # local output dir in your project
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------
# Find year partitions
# ---------------------------------------------------------
# Expected folder name pattern: publication_year=YYYY
year_dirs = []
pattern = re.compile(r"^publication_year=(\d{4})$")

for name in os.listdir(PARQUET_ROOT):
    m = pattern.match(name)
    if m:
        year_dirs.append((int(m.group(1)), os.path.join(PARQUET_ROOT, name)))

year_dirs = sorted(year_dirs, key=lambda x: x[0])

if not year_dirs:
    raise RuntimeError(f"No year partitions found under: {PARQUET_ROOT}")

# ---------------------------------------------------------
# Convert each year partition to a yearly pickle
# ---------------------------------------------------------
for year, ydir in tqdm(year_dirs, desc="Converting yearly parquet -> yearly pkl"):
    # Read the entire year partition (all parquet parts under that folder)
    df_year = pd.read_parquet(ydir)

    out_path = os.path.join(OUT_DIR, f"work_{year}.pkl")
    with open(out_path, "wb") as f:
        pickle.dump(df_year, f, protocol=pickle.HIGHEST_PROTOCOL)
