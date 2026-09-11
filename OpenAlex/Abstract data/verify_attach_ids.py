#!/usr/bin/env python3
"""Prove the re-extraction is the training corpus, attach exact ids, write the report.

For every year with a training file OpenAlex/Data/work_{year}.parquet:

  1. Consolidate the re-extracted shards for that publication_year.
  2. Same row set?  Compare, as multisets (sorted hash arrays), the abstract column alone and
     the full key (title, abstract, publication_date, type, authors_count,
     referenced_works_count, concepts_count). Row order cannot be reproduced -- Works_oa_parquet.py
     concatenated UUID-named partition files in discovery order -- so the proof is on sets.
  3. Attach the id by exact key join. Keys that occur k>1 times on both sides with the same k are
     duplicate records (identical text and metadata, different ids); an id is assigned within the
     group and the row is flagged id_ambiguous. Nothing is matched by title alone.
  4. Compare with the title+year recovery (work_by_year_with_id): agreement, disagreement, gain.
  5. Write OpenAlex/Data/work_by_year_with_id_exact/work_{year}.parquet = the training file's
     columns in the training file's row order + openalex_id + id_ambiguous.

Outputs (this folder): work_id_exact_verification.csv, work_id_exact_disagreements.csv,
work_id_exact_verification.tex.

    python verify_attach_ids.py                 # all years
    NB_YEARS=1976,1977 python verify_attach_ids.py   # subset (report marked partial)
"""
from __future__ import annotations

import datetime as dt
import gc
import os
import sys
import time

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq

HERE = os.path.dirname(os.path.abspath(__file__))
OLD_DIR = "/project/jevans/Dawoon/OpenAlex/Data"                          # work_{year}.parquet (training input)
TITLE_DIR = "/project/jevans/Dawoon/OpenAlex/Data/work_by_year_with_id"   # title+year recovery
SHARDS = "/project/jevans/Dawoon/OpenAlex/Data/work_id_exact/shards"
KEYS_DIR = "/project/jevans/Dawoon/OpenAlex/Data/work_id_exact/keys"
OUT_DIR = "/project/jevans/Dawoon/OpenAlex/Data/work_by_year_with_id_exact"
TIP = "/project/jevans/tip/data/openalex/works.parquet"
KEY = ["title", "abstract", "publication_date", "type", "authors_count", "referenced_works_count", "concepts_count"]

os.makedirs(KEYS_DIR, exist_ok=True); os.makedirs(OUT_DIR, exist_ok=True)


def years_wanted():
    raw = os.environ.get("NB_YEARS", "").strip()
    have = sorted(int(f[5:9]) for f in os.listdir(OLD_DIR) if f.startswith("work_") and f.endswith(".parquet"))
    if not raw:
        return have, False
    want = set()
    for p in raw.split(","):
        if "-" in p:
            a, b = p.split("-"); want |= set(range(int(a), int(b) + 1))
        else:
            want.add(int(p))
    return [y for y in have if y in want], True


def key_hash(df: pd.DataFrame) -> np.ndarray:
    return pd.util.hash_pandas_object(df[KEY], index=False).to_numpy()


def consolidate_year(y: int) -> pd.DataFrame:
    out = os.path.join(KEYS_DIR, f"keys_{y}.parquet")
    if not os.path.exists(out):
        t = ds.dataset(SHARDS, format="parquet").to_table(filter=ds.field("publication_year") == y)
        pq.write_table(t, out + ".tmp", compression="zstd"); os.replace(out + ".tmp", out)
    return pq.read_table(out).to_pandas()


def attach(old: pd.DataFrame, new: pd.DataFrame):
    """Exact-key join that also resolves duplicate keys positionally within the group."""
    o = pd.DataFrame({"k": key_hash(old)}); n = pd.DataFrame({"k": key_hash(new), "id": new["id"].to_numpy()})
    o["j"] = o.groupby("k").cumcount(); n["j"] = n.groupby("k").cumcount()
    grp = o.groupby("k")["j"].transform("size")
    m = o.merge(n, on=["k", "j"], how="left")
    assert len(m) == len(o)
    ids = m["id"].astype(object).where(m["id"].notna(), None).to_numpy()   # None, not NaN: pa.array(type=string) needs it
    return ids, (grp > 1).to_numpy(), o["k"].to_numpy(), n["k"].to_numpy()


def main() -> int:
    years, partial = years_wanted()
    print(f"{len(years)} years{' (PARTIAL: NB_YEARS set)' if partial else ''}", flush=True)
    rows, dis = [], []
    t0 = time.time()
    for y in years:
        t1 = time.time()
        old_pf = pq.ParquetFile(os.path.join(OLD_DIR, f"work_{y}.parquet"))
        old = old_pf.read(columns=KEY).to_pandas()          # key columns only; the full table is streamed at write time
        new = consolidate_year(y)
        r = {"year": y, "n_train": len(old), "n_reextract": len(new)}

        ha_o = np.sort(pd.util.hash_pandas_object(old["abstract"], index=False).to_numpy())
        ha_n = np.sort(pd.util.hash_pandas_object(new["abstract"], index=False).to_numpy())
        r["abstract_multiset_equal"] = bool(len(ha_o) == len(ha_n) and np.array_equal(ha_o, ha_n))
        ids, amb, ko, kn = attach(old, new)
        r["key_multiset_equal"] = bool(len(ko) == len(kn) and np.array_equal(np.sort(ko), np.sort(kn)))
        r["n_unmatched"] = int(pd.isna(ids).sum())
        r["n_ambiguous"] = int(amb.sum())
        r["n_distinct_abstracts_train"] = int(len(np.unique(ha_o)))
        r["exact_coverage"] = round(1 - r["n_unmatched"] / max(len(old), 1), 6)
        del ha_o, ha_n, ko, kn, new; gc.collect()

        # compare with the title+year recovery
        tp = os.path.join(TITLE_DIR, f"work_{y}.parquet")
        if os.path.exists(tp):
            tid = pq.read_table(tp, columns=["openalex_id"])["openalex_id"].to_pandas().to_numpy()
            assert len(tid) == len(old)
            ex = pd.Series(ids); tt = pd.Series(tid)
            both = ex.notna() & tt.notna()
            r["title_coverage"] = round(float(tt.notna().mean()), 6)
            r["agree"] = int((both & (ex == tt)).sum())
            r["disagree"] = int((both & (ex != tt)).sum())
            r["gain_exact_only"] = int((ex.notna() & tt.isna()).sum())
            r["title_only"] = int((ex.isna() & tt.notna()).sum())
            r["disagree_share_of_title_ids"] = round(r["disagree"] / max(int(tt.notna().sum()), 1), 6)
            bad = np.flatnonzero((both & (ex != tt)).to_numpy())[:5]
            for i in bad:
                dis.append({"year": y, "row": int(i), "exact_id": ids[i], "title_id": tid[i],
                            "title": (old["title"].iloc[i] or "")[:90], "abstract_head": (old["abstract"].iloc[i] or "")[:90]})
        else:
            r.update(title_coverage=np.nan, agree=0, disagree=0, gain_exact_only=0, title_only=0, disagree_share_of_title_ids=np.nan)

        # write the training file + two columns, row group by row group, in the training file's order
        del old; gc.collect()
        out = os.path.join(OUT_DIR, f"work_{y}.parquet")
        writer, off = None, 0
        for rg in range(old_pf.num_row_groups):
            t = old_pf.read_row_group(rg)
            n = t.num_rows
            t = t.append_column("openalex_id", pa.array(ids[off:off + n], type=pa.string())) \
                 .append_column("id_ambiguous", pa.array(amb[off:off + n], type=pa.bool_()))
            if writer is None:
                writer = pq.ParquetWriter(out + ".tmp", t.schema, compression="snappy")
            writer.write_table(t); off += n
            del t
        writer.close(); os.replace(out + ".tmp", out)
        assert off == len(ids)
        r["sec"] = round(time.time() - t1, 1)
        rows.append(r)
        print(f"  {y}: train {r['n_train']:>9,}  re-extract {r['n_reextract']:>9,}  "
              f"abs-set {'=' if r['abstract_multiset_equal'] else '!='}  key-set {'=' if r['key_multiset_equal'] else '!='}  "
              f"unmatched {r['n_unmatched']:,}  ambiguous {r['n_ambiguous']:,}  "
              f"title-agree {r['agree']:,} disagree {r['disagree']:,} gain {r['gain_exact_only']:,}  ({r['sec']}s)", flush=True)
        del old_pf, ids, amb; gc.collect()

    v = pd.DataFrame(rows)
    v.to_csv(os.path.join(HERE, "work_id_exact_verification.csv"), index=False)
    pd.DataFrame(dis).to_csv(os.path.join(HERE, "work_id_exact_disagreements.csv"), index=False)
    write_tex(v, pd.DataFrame(dis), partial)
    print(f"\nall years in {time.time()-t0:.0f}s")
    return 0


def tex_escape(s):
    return str(s).replace("\\", "\\textbackslash{}").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_") \
                 .replace("#", "\\#").replace("$", "\\$").replace("{", "\\{").replace("}", "\\}")


def write_tex(v: pd.DataFrame, dis: pd.DataFrame, partial: bool):
    tot = v[["n_train", "n_reextract", "n_unmatched", "n_ambiguous", "agree", "disagree", "gain_exact_only", "title_only"]].sum()
    all_abs = bool(v.abstract_multiset_equal.all()); all_key = bool(v.key_multiset_equal.all())
    n_years = len(v)
    tip_mtime = dt.datetime.fromtimestamp(os.path.getmtime(TIP)).strftime("%Y-%m-%d")
    n_shards = len([f for f in os.listdir(TIP) if f.endswith(".parquet")])
    ex_log = os.path.join(os.path.dirname(SHARDS), "extract_log.csv")
    ex = pd.read_csv(ex_log) if os.path.exists(ex_log) else None
    today = dt.date.today().isoformat()
    verdict = ("identical" if (all_abs and all_key and tot.n_unmatched == 0) else "NOT identical")
    title_cov = v.title_coverage.mean() if v.title_coverage.notna().any() else float("nan")

    L = []
    A = L.append
    A(r"% work_id_exact_verification.tex -- generated by verify_attach_ids.py; do not edit by hand")
    A(r"\documentclass[11pt,a4paper]{article}")
    A(r"\usepackage[margin=2.2cm]{geometry}\usepackage[T1]{fontenc}\usepackage{booktabs}\usepackage{longtable}")
    A(r"\usepackage{xcolor}\usepackage[colorlinks=true,linkcolor=blue,urlcolor=blue]{hyperref}")
    A(r"\setlength{\parskip}{0.6em}\setlength{\parindent}{0pt}")
    A(r"\newcommand{\pth}[1]{\texttt{\small #1}}")
    A(r"\title{\textbf{The paper training corpus, re-extracted with OpenAlex ids}\\[0.3em]\large Proof that the row set is unchanged, and exact id attachment}")
    A(r"\author{Science of Science / OpenAlex / Abstract data}")
    A(rf"\date{{{today}{'  --- PARTIAL RUN (year subset)' if partial else ''}}}")
    A(r"\begin{document}\maketitle")

    A(r"\section*{Verdict}")
    if verdict == "identical":
        A(rf"Across {n_years} year files ({v.year.min()}--{v.year.max()}), the re-extraction reproduces the training corpus "
          rf"\textbf{{exactly}}: {int(tot.n_train):,} rows on both sides, the multiset of abstracts is identical in every year, "
          rf"the multiset of full row keys is identical in every year, and every training row receives an id by exact key "
          rf"({int(tot.n_unmatched):,} unmatched). {int(tot.n_ambiguous):,} rows "
          rf"({tot.n_ambiguous / max(tot.n_train, 1):.4%}) belong to duplicate-record groups (identical text and metadata under "
          rf"two or more ids) and are flagged \pth{{id\_ambiguous}}; the text they were trained on is not in doubt, only which of "
          rf"the duplicate ids to name.")
        A(r"\textbf{No retraining is implied.} The chains consumed the \pth{abstract} column and nothing else; the id is a label "
          r"attached afterwards to the very same rows. What changes is auditability: which works a checkpoint saw is now a "
          r"document-level fact with 100\,\% coverage instead of a title-matched estimate.")
    else:
        A(rf"\textcolor{{red}}{{\textbf{{The re-extraction does NOT reproduce the training corpus in every year.}}}} "
          rf"Years with a differing abstract multiset: {', '.join(str(y) for y in v.loc[~v.abstract_multiset_equal, 'year'])}; "
          rf"differing key multiset: {', '.join(str(y) for y in v.loc[~v.key_multiset_equal, 'year'])}; "
          rf"unmatched rows in total: {int(tot.n_unmatched):,}. Before drawing any conclusion about retraining, the cause of the "
          rf"difference has to be found (see the per-year table); the ids attached for matched rows remain exact.")

    A(r"\section{Why this was needed}")
    A(r"\pth{OpenAlex/Works\_oa.py} built \pth{OpenAlex/Data/work\_\{year\}.parquet}, the corpus behind every paper chain under "
      r"\pth{Model/} and \pth{Model\_full/}, from the shared dump \pth{" + tex_escape(TIP) + r"} "
      rf"({n_shards} shards, last modified {tip_mtime}). Its \pth{{READ\_COLS}} omitted \pth{{id}}, so the corpus carries no work id. "
      r"\pth{SciTech\_PPP/00\_attach\_openalex\_id\_CPU\_Midway.ipynb} recovered ids afterwards by matching normalised title and "
      rf"publication year against the same dump (\pth{{work\_by\_year\_with\_id/}}), reaching about {title_cov:.1%} coverage and, as the "
      r"PPP abstract audit showed, occasionally linking a row to a different work with the same title (a ChemInform digest and its "
      r"source article; a neural-stem-cell paper linked to a fuel-assembly abstract).")

    A(r"\section{Method}")
    A(r"\textbf{Re-extraction} (\pth{extract\_work\_ids.py}). The same shards in the same sorted order, the same filter "
      r"(\pth{language == 'en'} and \pth{publication\_year >= 1970} after \pth{pd.to\_numeric}), the same "
      r"\pth{reconstruct\_abstract} -- loaded from \pth{Works\_oa.py}'s source at run time so it cannot drift -- and the same "
      r"\pth{abstract.notna()} drop. Only the column list differs: \pth{id} is read, and the nested columns "
      r"(\pth{concepts}, \pth{mesh}, \pth{grants}, \pth{open\_access}) are not, because they play no part in the key.")
    if ex is not None and (ex.status == "ok").any():
        e = ex[ex.status == "ok"]
        A(rf"Shards processed: {len(e)}; rows read {int(e.n_read.sum()):,}; after the language/year filter {int(e.n_filtered.sum()):,}; "
          rf"with a reconstructed abstract {int(e.n_kept.sum()):,}.")
    A(r"\textbf{Why sets and not positions.} \pth{Works\_oa\_parquet.py} produced each \pth{work\_\{year\}.parquet} with "
      r"\pth{pyarrow.dataset(...).to\_table()} over a Hive partition whose part files carry UUID names, so the row order of the training "
      r"file is the discovery order of random file names and cannot be reproduced. The proof therefore compares multisets: for each year, "
      r"the sorted array of 64-bit hashes of the \pth{abstract} column, and the sorted array of hashes of the full key "
      r"(\pth{title, abstract, publication\_date, type, authors\_count, referenced\_works\_count, concepts\_count}). "
      r"Equal length and element-wise equality of the sorted arrays means the two files hold the same rows.")
    A(r"\textbf{Attachment} (\pth{verify\_attach\_ids.py}). Each training row is joined to the re-extraction on the full key. "
      r"When a key occurs $k>1$ times on both sides (duplicate records in OpenAlex: same text, same metadata, different ids) the ids "
      r"are assigned within the group by position and the rows are flagged \pth{id\_ambiguous}. No row is ever matched by title alone. "
      r"The output \pth{OpenAlex/Data/work\_by\_year\_with\_id\_exact/work\_\{year\}.parquet} is the training file, in the training "
      r"file's row order and with all its columns, plus \pth{openalex\_id} and \pth{id\_ambiguous}.")

    A(r"\section{Per-year result}")
    A(r"\small")
    A(r"\begin{longtable}{rrrccrrrrrr}")
    A(r"\toprule year & rows (train) & rows (re-ex.) & abs.\ set & key set & unmatched & ambiguous & title cov. & agree & disagree & gain \\ \midrule \endhead")
    for _, r in v.iterrows():
        tc = f"{r.title_coverage:.1%}" if pd.notna(r.title_coverage) else "--"
        A(rf"{int(r.year)} & {int(r.n_train):,} & {int(r.n_reextract):,} & {'=' if r.abstract_multiset_equal else r'$\neq$'} & "
          rf"{'=' if r.key_multiset_equal else r'$\neq$'} & {int(r.n_unmatched):,} & {int(r.n_ambiguous):,} & {tc} & "
          rf"{int(r.agree):,} & {int(r.disagree):,} & {int(r.gain_exact_only):,} \\")
    A(r"\midrule")
    A(rf"all & {int(tot.n_train):,} & {int(tot.n_reextract):,} & {'=' if all_abs else r'$\neq$'} & {'=' if all_key else r'$\neq$'} & "
      rf"{int(tot.n_unmatched):,} & {int(tot.n_ambiguous):,} & {title_cov:.1%} & {int(tot.agree):,} & {int(tot.disagree):,} & {int(tot.gain_exact_only):,} \\")
    A(r"\bottomrule\end{longtable}\normalsize")
    A(r"\emph{abs.\ set} / \emph{key set}: multiset equality of the abstract column / of the full key between the training file and the "
      r"re-extraction. \emph{unmatched}: training rows that received no id. \emph{ambiguous}: rows in duplicate-record groups. "
      r"\emph{title cov.}: coverage of the title+year recovery. \emph{agree}/\emph{disagree}: rows where both methods give an id and it is the "
      r"same / different. \emph{gain}: rows with an exact id and no title-matched id.")

    A(r"\section{Against the title+year recovery}")
    n_title = int(tot.agree + tot.disagree)
    A(rf"Where both methods assign an id ({n_title:,} rows) they agree on {int(tot.agree):,} and disagree on {int(tot.disagree):,} "
      rf"({tot.disagree / max(n_title, 1):.3%} of title-matched ids). The exact method adds an id to {int(tot.gain_exact_only):,} rows the "
      rf"title match left empty; {int(tot.title_only):,} rows have a title-matched id but no exact id.")
    if len(dis):
        A(r"Examples of disagreement (exact id is the row's own id from the dump; the title-matched id belongs to another work with the same normalised title):")
        A(r"\small\begin{longtable}{rlll}\toprule year & exact id & title id & title (truncated) \\ \midrule \endhead")
        for _, r in dis.head(25).iterrows():
            A(rf"{int(r.year)} & {tex_escape(r.exact_id)} & {tex_escape(r.title_id)} & {tex_escape(r.title)} \\")
        A(r"\bottomrule\end{longtable}\normalsize")

    A(r"\section{Consequences}")
    A(r"\begin{itemize}")
    A(r"\item \pth{work\_by\_year\_with\_id\_exact/} supersedes \pth{work\_by\_year\_with\_id/} for every question of the form "
      r"``was this work in the training set of checkpoint $t$''. The PPP audit (\pth{Atypicality/Data check/abstract\_consistency\_check.ipynb}) "
      r"and the revision build (\pth{Atypicality/build\_ppp\_df\_wabstract\_rev.ipynb}) read it through \pth{OA\_WITH\_ID}.")
    A(r"\item The training files themselves are untouched. The chains under \pth{Model/} and \pth{Model\_full/} remain valid as trained.")
    A(r"\item Retraining would be required only if the corpus \emph{text} changed: a different snapshot (e.g.\ the January 2026 "
      r"\pth{renli\_shared} dump), a different filter, or de-duplication. Attaching ids is not such a change.")
    A(r"\end{itemize}")
    A(r"\section*{Files}")
    A(r"\begin{tabular}{ll}\toprule file & what \\ \midrule")
    A(r"\pth{extract\_work\_ids.py} & re-extraction, resumable, one parquet per shard \\")
    A(r"\pth{verify\_attach\_ids.py} & per-year proof, id attachment, this report \\")
    A(r"\pth{run\_work\_id\_exact.sbatch} & the SLURM job (both stages) \\")
    A(r"\pth{work\_id\_exact\_verification.csv} & the per-year table above \\")
    A(r"\pth{work\_id\_exact\_disagreements.csv} & up to 5 title-vs-exact disagreements per year \\")
    A(r"\pth{OpenAlex/Data/work\_id\_exact/} & shards/ (re-extraction), keys/ (per year), extract\_log.csv \\")
    A(r"\pth{OpenAlex/Data/work\_by\_year\_with\_id\_exact/} & training files + \pth{openalex\_id}, \pth{id\_ambiguous} \\")
    A(r"\bottomrule\end{tabular}")
    A(r"\end{document}")
    p = os.path.join(HERE, "work_id_exact_verification.tex")
    open(p, "w").write("\n".join(L) + "\n")
    print("wrote", p)


if __name__ == "__main__":
    sys.exit(main())
