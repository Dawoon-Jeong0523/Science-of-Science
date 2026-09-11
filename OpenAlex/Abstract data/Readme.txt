================================================================================
HOW /project/jevans/Dawoon/OpenAlex/Data WAS BUILT
================================================================================
Copied here 2026-08-28 from /project/jevans/Dawoon/OpenAlex/, unchanged. These
are the scripts that produced the yearly abstract corpus the annual paper BERT
chains train on.

--------------------------------------------------------------------------------
THE PIPELINE
--------------------------------------------------------------------------------
  /project/jevans/tip/data/openalex/works.parquet      <- the OpenAlex snapshot
        │                                                 (shared, not ours)
        │  Works_oa.py            run_Works_oa.sbatch
        │    - read 14 columns per shard
        │    - keep language == 'en' AND publication_year >= 1970
        │    - RECONSTRUCT the abstract from abstract_inverted_index
        │    - drop rows with no abstract
        │    - write partitioned by publication_year, snappy
        ↓
  OpenAlex/works_en_1970plus_by_year/publication_year=YYYY/*.parquet
        │
        ├─ Works_oa_parquet.py    run_Works_oa_parquet.sbatch
        │    consolidate each year partition -> one file per year
        ↓
  OpenAlex/Data/work_YYYY.parquet          56 files, 1970-2025, 132.3 GB
        │                                   <- WHAT THE TRAINING READS
        │
        └─ Works_oa_pkl.py        run_Works_oa_pkl.sbatch
             the same years as pickles -> OpenAlex/Data/work_YYYY.pkl
             (56 more files; the training does not use them. Data/ is 533 GB
              in total, and roughly three quarters of that is these pickles.)

  00_attach_openalex_id_CPU_Midway.ipynb    (from SciTech_PPP/, a later step)
        adds openalex_id by normalised-title + year matching against a
        156,881,663-row map -> OpenAlex/Data/work_by_year_with_id/work_YYYY.parquet
        Same row count as the input, 89.9% id coverage, ambiguous titles dropped.

--------------------------------------------------------------------------------
WHAT THE FILTERS MEAN
--------------------------------------------------------------------------------
Three filters are applied once, in Works_oa.py, and everything downstream
inherits them:

  language == 'en'        Non-English works never enter the corpus. The chains
                          are English-only by construction, not by accident.
  publication_year >= 1970  The 1976 training start sits inside this.
  abstract is not null    The abstract is RECONSTRUCTED from OpenAlex's
                          inverted index (reconstruct_abstract()), and rows
                          where that fails or is empty are dropped. This is why
                          `abstract` has zero nulls in every year file — the
                          nulls were removed upstream, not absent from OpenAlex.

  NOT filtered: `type`. Every work type survives — article, book-chapter,
  dissertation, dataset, and the rest. Measured on the 1976-2025 files:
  91.70% article, 8.30% something else. The scoring notebooks (nb_f_2, nb_f_3)
  then filter to type == 'article', so training and scoring populations differ
  by that 8.30%.

--------------------------------------------------------------------------------
COLUMNS
--------------------------------------------------------------------------------
  title, display_name, abstract, concepts, concepts_count, authors_count,
  grants, mesh, open_access, publication_date, referenced_works_count, type

  `publication_year` is the partition key, so it is NOT a column in the
  consolidated per-year files. train_full.py re-derives the year from
  publication_date and filters year == <file year> rather than trusting the
  filename — a sensible precaution, since the partition and the date could in
  principle disagree.

  There is NO id column. That is what 00_attach_openalex_id exists to fix, and
  why the scoring corpus lives in a different directory from the training one.

--------------------------------------------------------------------------------
RUNNING IT AGAIN
--------------------------------------------------------------------------------
  cd "/project/jevans/Dawoon/Science of Science/OpenAlex/Abstract data"
  sbatch run_Works_oa.sbatch          # shard -> filter -> reconstruct  (48h, 200G)
  sbatch run_Works_oa_parquet.sbatch  # partitions -> one file per year
  sbatch run_Works_oa_pkl.sbatch      # optional, and 400 GB of it

  The sbatch files still cd to /project/jevans/Dawoon/OpenAlex and activate
  env/GSMArena (not env/Curvature, which the rest of this project uses). Both
  are as they were when the corpus was built; change them before rerunning if
  you want the output somewhere else.

  Works_oa_parquet.py skips a year whose output already exists, so a rerun is
  incremental. Works_oa.py is not — it writes with
  existing_data_behavior='overwrite_or_ignore' over the whole snapshot.

--------------------------------------------------------------------------------
ONE THING WORTH CHANGING
--------------------------------------------------------------------------------
The training corpus has no id, and the id-attached copy
(work_by_year_with_id/) has EXACTLY the same rows — verified: 452,068 /
1,370,770 / 4,909,805 for 1980 / 2000 / 2020, identical on both sides, with
openalex_id null for the ~10% that could not be matched rather than dropped.

So pointing the training at work_by_year_with_id/ instead of work_*.parquet
changes not one training document, and makes it possible to say afterwards
which papers a checkpoint saw. The patent side already has this; the paper side
is the only place an id that was available was thrown away.
