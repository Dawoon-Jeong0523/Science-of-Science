# Science of Science

Metric pipelines for the science of science: forward citations, the CD disruption
index with its F/E/G citer profile, atypicality (Uzzi journal-pair z-scores for
papers, Kim et al. CPC-subclass z-scores for patents), sleeping-beauty
coefficients, cohort hit probability, and yearly citation and disruption
trajectories. The same kernels run over several literatures so results can be
compared document for document.

| Pipeline | Documents | Source | Key | Notebooks |
|---|---|---|---|---|
| `OpenAlex/` | papers | OpenAlex snapshot 2026-01-16 (renli_shared) | `paper_id` = `W` + integer | 12 |
| `Dimensions/` | papers | Dimensions June 2025 dump | `paper_id` = `pub.` + digits | 10 |
| `PatentView/` | US granted utility patents | PatentsView bulk (granted 2026-05-21, pre-grant 2026-08-28) | `patent_id` | 14 |
| `PATSTAT/` | patent applications, worldwide | PATSTAT Global 2023 Autumn | `appln_id` | 10 |
| `Case law/` | US court opinions (CAP) | `Edge_list.parquet` (47.5 M citations) + `metadata.csv` (5.18 M cases) | case id | 8 |
| `pcs/` | patent -> paper citations | Reliance on Science (`pcs_oa_uspto.csv`) | `paper_id` | 3 |
| `PPP/` | patent-paper pairs | `_patent_paper_pairs_plus.csv` | (`paperid`, `patent`) | 1 |
| `validation/` | face-validity checks and the metrics dashboard | all of the above | | 8 |

Every pipeline writes one tidy parquet per metric, keyed on its id, so the
outputs of one pipeline are meant to be merged with each other, not read alone.

The two notebooks at the repository root, `Disruption_Index.ipynb` and
`Atypical_combinations.ipynb`, are the original 2025 Colab implementations on
MAG/SciSciNet. The pipelines below supersede them.

## What is in this repository, and what is not

Tracked: notebooks, the `*_common.py` data layers, SLURM job scripts under
`jobs/`, per-pipeline `Readme.txt` files, validation figures, the metrics
dashboard, and the OpenAlex schema CSVs at the root.

Not tracked (see `.gitignore`): every parquet file, every cache
(`cache/`, `*.npz`), the raw-data mirrors (`PatentView/Granted`,
`PatentView/Pregranted`, `PATSTAT/raw`), the large CSV and GML inputs, SLURM
logs, and the `Atypicality/` analysis folder. The full tree on Midway is about
290 GB of data against roughly 60 MB of code, and most output files are larger
than GitHub's 100 MB limit. All data paths are absolute Midway paths under
`/project/jevans/Dawoon/Science of Science/`.

## Layout

```
OpenAlex/      oa_common.py   notebook/  output/  cache/  Old/  Abstract data/  Readme.txt
Dimensions/    dim_common.py  notebook/  output/  cache/                        Readme.txt
PatentView/    pv_common.py   notebook/  output/  cache/  Old/  Granted/  Pregranted/
PATSTAT/       ps_common.py   notebook/  output/  cache/  raw/                  Readme.txt
Case law/      cl_common.py   notebook/  output/  cache/  Figures/
pcs/           pcs_common.py  notebook/  output/  Old/
PPP/           ppp_common.py  notebook/  output/  Old/
validation/    val_common.py  *.ipynb    Figures/ data/   Old/  metrics_dashboard.html
jobs/<pipeline>/   nb.sbatch, submit_<pipeline>.sh, run_notebook.py, logs/
run_notebook.py    executes a notebook's code cells in order as a plain script
paper_style.py     matplotlib style shared by the figures (fonts/ holds Lato)
```

Each pipeline has a `*_common.py` that holds the absolute paths and the data
layer. Import it instead of hard-coding paths:

```python
import sys; sys.path.insert(0, '/project/jevans/Dawoon/Science of Science/PatentView')
import pv_common as pv
pv.preflight('patent_disruption')      # what is present, what is missing
df = pd.read_parquet(pv.out('patent_disruption.parquet'))
```

`Dimensions/dim_common.py` keeps the public names of `oa_common.py`, and
`PATSTAT/ps_common.py` plays the role of `pv_common.py`, so a notebook written
against one index reads unchanged against its twin.

## Metrics

Notation shared by all pipelines: `P` is the focal document, `y_X` its year
(papers: publication year; PatentsView: grant year; PATSTAT: filing year; case
law: decision year), `W` a citation window of 3 / 5 / 10 / all years, written as
column suffixes `_3`, `_5`, `_10`, `_all`.

| Metric | Output | Definition |
|---|---|---|
| Forward citations | `*_citation` | `C_W = #{c cites P : 0 <= y_c - y_P <= W}`. Patents split by who submitted the reference (`C_examiner`, `C_non_examiner`, `C_unknown`), add application-stage citations `appC`, and `uniqueC` = de-duplicated union of granted and application citations. |
| Disruption | `*_disruption` | `CD_W = (n_i - n_j) / (n_i + n_j + n_k)` with `n_j` = citers of P that also cite a reference of P, `n_i` = citers of P only, `n_k` = citers of P's references only. F/E/G = per-citer Foundation / Extension / Generalization shares, `F + E + G = 1`. |
| Disruption trajectory | `*_disruption_trend` | One row per document x year with cumulative `ni/nj/nk/CD/F/E/G` and per-year `ni_new/nj_new/nk_new`. Prefix sums reproduce the windowed table exactly. `*_summary` holds cohort means. |
| Atypicality, papers | `paper_z_score`, `z_score_pair` | Uzzi et al. (2013): journal-pair co-occurrence z-scores against a cited-year-preserving shuffle null (10 shuffles). Per paper `Z_median`, `Z_10pct`, `Z_min`, `n_pairs`. |
| Atypicality, patents | `patent_z_score`, `patstat_z_score` | Kim et al. (2016): analytic hypergeometric null on CPC-subclass pairs over the cumulative patent set. `z < 0` is atypical. |
| Sleeping beauty | `*_sb` | Ke et al. (2015) beauty coefficient `SB_B` and awakening time `SB_T` from the yearly citation histogram. |
| Hit probability | `*_hit_probability` | Percentile of each count column within its cohort: (field, year) for papers, (WIPO sector, year) for patents. `pctl >= 0.99` is the top 1 %. |
| Citation trajectory | `*_citation_trend` | One row per (document, citing year), with years since publication or grant and the citation channel (paper -> paper, patent -> paper by examiner / applicant, patent -> patent). |
| Team size / authors | `paper_author`, `paper_team_size` | Author lists and team size from OpenAlex `works_au_affs` or Dimensions `authors[]`. |
| FEG trend | `*_feg_disruption_trend` | Per-year means of CD / F / E / G / ni / nj / nk. |

Where the literatures differ in a way that matters (field taxonomy, what counts
as a journal, the time anchor, what "examiner" means, left-censoring of the
citation graph), the per-pipeline `Readme.txt` files spell it out:
[OpenAlex](OpenAlex/Readme.txt), [Dimensions](Dimensions/Readme.txt),
[PATSTAT](PATSTAT/Readme.txt).

## Running

Everything corpus-scale runs on Midway compute nodes, partition `jevans`
(`-A pi-jevans --qos=jevans`). Login nodes cap memory at 8 GiB and kill large
kernels without a traceback.

```bash
cd "/project/jevans/Dawoon/Science of Science/jobs/<pipeline>"
./submit_<pipeline>.sh plan     # print the dependency order and what is blocked
./submit_<pipeline>.sh          # submit the chain with afterok dependencies
sbatch --export=ALL,NB=<notebook_stem> -J <jobname> nb.sbatch   # one notebook
```

Run orders:

- OpenAlex and Dimensions: `references_w_year` first (one pass over the dump),
  then `paper_metadata`, `paper_citation`, `paper_disruption`, `paper_sb`,
  `paper_z_score` (+ `paper_z_score_merge`), `paper_citation_trend`,
  `paper_hit_probability`, `paper_author`, `paper_disruption_trend`.
- PatentView: `patent_metadata`, `patent_reference`, `patent_disruption`,
  `patent_sb`, `patent_citation`, `patent_citation_trend`,
  `patent_disruption_app_add` have no dependency; then `patent_z_score`,
  `patent_feg_disruption_trend`, `patent_hit_probability`,
  `patent_disruption_app_compare`, `patent_disruption_trend`, `patent_uniqueC_trend`.
- PATSTAT: `sbatch load.sbatch` (array of 21 zip parts to `raw/`), then
  `submit_patstat.sh`: `patstat_reference` -> `patstat_metadata` -> counting
  notebooks -> `patstat_citation_trend`, `patstat_hit_probability`,
  `patstat_feg_disruption_trend`.
- Case law: `case_metadata` first (it builds the graph and CSR caches), then
  `case_citation`, `case_citation_trend`, `case_sb`, `case_disruption`; then
  `case_hit_probability` (after citation) and `case_feg_disruption_trend`
  (after disruption). `submit_case_law.sh fast` skips the hours-long disruption step.

Environment: conda env `/project/jevans/Dawoon/env/Curvature`, plus

```bash
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib:$LD_LIBRARY_PATH
```

without which `import pandas` fails on `GLIBCXX_3.4.29`. `nb.sbatch` sets this;
interactive shells do not. Notebooks are executed with `run_notebook.py` rather
than `nbconvert --execute` because the runs emit about a million tqdm updates
that nbconvert would store back into the notebook.

Smoke tests: the Dimensions notebooks honour `NB_DIM_BASE=<scratch>`,
`NB_FILE_LIMIT=12` and `NB_Z_YEARS=a:b`; the PATSTAT ones honour
`NB_DUCKDB_MEM`.

## Validation

`validation/` holds one face-validity notebook per literature
(`paper_validation`, `patent_validation`, `dimension_validation`,
`case_law_validation`, `pcs_validation`, `ppp_validation`) plus
`disruption_crosscheck`. There is no external gold standard for most metrics, so
the checks are internal consistency (`C3 <= C5 <= C10 <= C_all`, `F + E + G = 1`,
`CD` in `[-1, 1]`), expected artefacts (citation truncation in recent years,
left-censoring at the start of a citation record) and, where it exists,
agreement with SciSciNet. Figures go to `validation/Figures/<notebook>_<section>.{jpg,pdf}`.
`dashboard_update.ipynb` and `refresh_dashboard.py` regenerate
`metrics_dashboard.html` from `data/inventory.json`.

## Known caveats

- OpenAlex publication years 2023 to 2025 are incomplete in the 2026-01-16
  snapshot. Trends ending there measure ingestion, not science, and each window
  `w` must stop at `last year - w`.
- Paper atypicality on OpenAlex is computed for selected year ranges only
  (2000-2005, 2007-2011, 1990-2000, single years 2012-2020); there is no
  corpus-wide `paper_z_score.parquet`. Files suffixed `_old` come from a
  superseded null model and are not a baseline.
- PatentsView `citation_category` changed coding in 2001 and 2013, so any
  examiner-share trend crossing those years measures the coding change.
- PatentsView citations are recorded only from patents granted 1976 onwards, so
  `n_k` is undercounted and CD inflated for the earliest grant years. Quote
  patent disruption trends from 1985.
- The Uzzi 2x2 (conventionality x novelty) does not reproduce on the 2000-2005
  paper data; Z agreement with SciSciNet is only moderate while pair counts
  agree almost exactly. Resolve before interpreting.
- PATSTAT uses the filing year at both ends and its own citation-origin codes;
  it is not a drop-in for PatentsView numbers. See `PATSTAT/Readme.txt` §4.
- Dimensions fields are ANZSRC FoR 2020 divisions, not OpenAlex fields, and
  its patent -> paper channel carries no examiner tag. See `Dimensions/Readme.txt` §4.

## Superseded versions

Each pipeline keeps earlier notebook versions in `<pipeline>/Old/`, named
`<notebook>.ipynb.<stage>` where `<stage>` describes the edit that came next
(`.pre-paths`, `.pre-midway/`, `.pre-mag`, `.pre-dedup`, `.pre-uniqueC`,
`.pre-app`, `.pre-zscore`). Data backups keep their own suffix next to the data
(for example `patent_disruption.parquet.pre-dedup`) and are not tracked here.
