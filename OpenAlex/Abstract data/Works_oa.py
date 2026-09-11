import os
import json
import pandas as pd
from tqdm import tqdm
import pyarrow as pa
import pyarrow.parquet as pq


def reconstruct_abstract(inv_index) -> str | None:
    """Safely reconstruct OpenAlex abstract from inverted index."""
    if inv_index is None or (isinstance(inv_index, float) and pd.isna(inv_index)):
        return None

    if isinstance(inv_index, str):
        inv_index = inv_index.strip()
        if inv_index == "" or inv_index.lower() == "null":
            return None
        try:
            inv_index = json.loads(inv_index)
        except Exception:
            return None

    if not isinstance(inv_index, dict) or len(inv_index) == 0:
        return None

    try:
        max_pos = max(p for positions in inv_index.values() for p in positions)
    except Exception:
        return None

    words = [""] * (max_pos + 1)
    for w, positions in inv_index.items():
        if not isinstance(positions, (list, tuple)):
            continue
        for p in positions:
            if isinstance(p, int) and 0 <= p <= max_pos:
                words[p] = w

    abstract = " ".join(words).strip()
    return abstract if abstract else None


# -----------------------------
# Paths
# -----------------------------
DATA_DIR = "/project/jevans/tip/data/openalex/works.parquet"
OUT_DIR = "/project/jevans/Dawoon/OpenAlex/works_en_1970plus_by_year"  # <-- change if you want

os.makedirs(OUT_DIR, exist_ok=True)

# -----------------------------
# Columns to read and to keep
# -----------------------------
READ_COLS = [
    "abstract_inverted_index",
    "language",
    "publication_year",
    "title",
    "display_name",
    "concepts",
    "concepts_count",
    "authors_count",
    "grants",
    "mesh",
    "open_access",
    "publication_date",
    "referenced_works_count",
    "type",
]

KEEP_COLS = [
    "title",
    "display_name",
    "abstract",
    "concepts",
    "concepts_count",
    "authors_count",
    "grants",
    "mesh",
    "open_access",
    "publication_date",
    "publication_year",
    "referenced_works_count",
    "type",
]

file_list = sorted([f for f in os.listdir(DATA_DIR) if f.endswith(".parquet")])

for file in tqdm(file_list, desc="Shard -> filter -> reconstruct -> write partitioned dataset"):
    path = os.path.join(DATA_DIR, file)

    temp_df = pd.read_parquet(path, columns=READ_COLS)

    # Defensive: year to numeric
    temp_df["publication_year"] = pd.to_numeric(temp_df["publication_year"], errors="coerce")

    # Filter: English & year >= 1970
    temp_df = temp_df[(temp_df["language"] == "en") & (temp_df["publication_year"] >= 1970)]
    if len(temp_df) == 0:
        continue

    # Reconstruct abstract
    temp_df["abstract"] = temp_df["abstract_inverted_index"].apply(reconstruct_abstract)

    # Drop missing abstracts (recommended for LM training)
    temp_df = temp_df[temp_df["abstract"].notna()]
    if len(temp_df) == 0:
        continue

    # Keep only requested cols
    temp_df = temp_df[KEEP_COLS]

    # Write incrementally, partitioned by publication_year
    table = pa.Table.from_pandas(temp_df, preserve_index=False)

    pq.write_to_dataset(
        table,
        root_path=OUT_DIR,
        partition_cols=["publication_year"],
        existing_data_behavior="overwrite_or_ignore",  # safe for repeated writes
        compression="snappy",
    )
