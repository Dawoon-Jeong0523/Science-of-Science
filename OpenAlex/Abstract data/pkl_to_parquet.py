#!/usr/bin/env python

import os
import gc
import pickle
import pandas as pd
from typing import Optional
from tqdm import tqdm

def pkl_path_for_year(base_dir: str, year: int) -> str:
    """
    Year-wise PKL path convention.
    """
    return os.path.join(base_dir, f"work_{year}.pkl")


def parquet_path_for_year(base_dir: str, year: int) -> str:
    """
    Year-wise Parquet path convention (same folder).
    """
    return os.path.join(base_dir, f"work_{year}.parquet")


def convert_year_pkl_to_parquet(
    base_dir: str,
    year: int,
    overwrite: bool = False,
) -> bool:
    """
    Convert a single year's PKL file to Parquet.

    Returns
    -------
    bool
        True if converted successfully, False otherwise.
    """
    pkl_path = pkl_path_for_year(base_dir, year)
    parquet_path = parquet_path_for_year(base_dir, year)

    if not os.path.isfile(pkl_path):
        print(f"[Year {year}] PKL not found → skipped.")
        return False

    if os.path.isfile(parquet_path) and not overwrite:
        print(f"[Year {year}] Parquet already exists → skipped.")
        return False

    print(f"[Year {year}] Loading PKL...")
    with open(pkl_path, "rb") as f:
        obj = pickle.load(f)

    # Ensure DataFrame
    if isinstance(obj, pd.DataFrame):
        df = obj
    else:
        df = pd.DataFrame(obj)

    print(f"[Year {year}] Rows: {len(df):,}, Columns: {list(df.columns)}")

    print(f"[Year {year}] Saving Parquet...")
    df.to_parquet(
        parquet_path,
        engine="pyarrow",
        compression="snappy",
        index=False,
    )

    if not os.path.exists(parquet_path):
        raise RuntimeError(f"Parquet file not created: {parquet_path}")
    
    if os.path.getsize(parquet_path) == 0:
        raise RuntimeError(f"Parquet file is empty: {parquet_path}")
        
    # Memory cleanup
    del df, obj
    gc.collect()

    print(f"[Year {year}] Done → {parquet_path}")
    return True


def convert_range_pkl_to_parquet(
    base_dir: str,
    start_year: int,
    end_year: int,
    overwrite: bool = False,
):
    """
    Convert PKL files for a range of years to Parquet.
    """
    print("### PKL → Parquet conversion started ###")

    for year in tqdm(range(start_year, end_year + 1)):
        print(year)
        convert_year_pkl_to_parquet(
            base_dir=base_dir,
            year=year,
            overwrite=overwrite,
        )
    print("### Conversion finished ###")


# ============================================================
# Configuration (edit here)
# ============================================================

DATA_YEAR_DIR = "/project/jevans/Dawoon/OpenAlex/Data"
START_YEAR = 1970
END_YEAR = 2025
OVERWRITE = False


if __name__ == "__main__":
    convert_range_pkl_to_parquet(
        base_dir=DATA_YEAR_DIR,
        start_year=START_YEAR,
        end_year=END_YEAR,
        overwrite=OVERWRITE,
    )
