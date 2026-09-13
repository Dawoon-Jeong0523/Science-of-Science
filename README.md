# Science of Science

Metric pipelines for the science of science: forward citations, the CD disruption
index with its F/E/G citer profile, atypicality (Uzzi journal-pair z-scores for
papers, Kim et al. CPC-subclass z-scores for patents), sleeping-beauty
coefficients, cohort hit probability, author and inventor geography, and yearly
citation and disruption trajectories. The same kernels run over several
literatures so results can be compared document for document.

| Pipeline | Documents | Source | Key | Notebooks |
|---|---|---|---|---|
| `OpenAlex/` | papers | OpenAlex snapshot 2026-01-16 (renli_shared) | `paper_id` = `W` + integer | 13 |
| `Dimensions/` | papers | Dimensions June 2025 dump | `paper_id` = `pub.` + digits | 10 |
| `PatentView/` | US granted utility patents | PatentsView bulk (granted 2026-05-21, pre-grant 2026-08-28) | `patent_id` | 15 |
| `PATSTAT/` | patent applications, worldwide | PATSTAT Global 2023 Autumn | `appln_id` | 10 |
| `Case law/` | US court opinions (CAP) | `Edge_list.parquet` (47.5 M citations) + `metadata.csv` (5.18 M cases) | case id | 8 |
| `pcs/` | patent -> paper citations | Reliance on Science (`pcs_oa_uspto.csv`) | `paper_id` | 3 |
| `PPP/` | patent-paper pairs | `_patent_paper_pairs_plus.csv` | (`paperid`, `patent`) | 1 |
| `validation/` | face-validity checks and the metrics dashboard | all of the above | | 10 |

Every pipeline writes one tidy parquet per metric, keyed on its id, so the
outputs of one pipeline are meant to be merged with each other, not read alone.
There are 45 such tables, about 62 GB.

The three notebooks at the repository root, `Disruption_Index.ipynb`,
`Atypical_combinations.ipynb` and `MAG-Disruption-CD5.ipynb`, are the original
2025 Colab implementations on MAG/SciSciNet. The pipelines below supersede them.

## What is in this repository, and what is not

Tracked: notebooks, the `*_common.py` data layers, SLURM job scripts under
`jobs/`, per-pipeline `Readme.txt` files, validation figures, the metrics
dashboard and its refresh scripts, the country-boundary GeoJSON the map figures
need, and the OpenAlex schema CSVs at the root.

Not tracked (see `.gitignore`): every parquet file, every cache
(`cache/`, `*.npz`), the raw-data mirrors (`PatentView/Granted`,
`PatentView/Pregranted`, `PATSTAT/raw`), the large CSV and GML inputs, SLURM
logs, the Figshare API token and its staging directory, and the `Atypicality/`
analysis folder. The full tree on Midway is about 290 GB of data against roughly
60 MB of code, and most output files are larger than GitHub's 100 MB limit. All
data paths are absolute Midway paths under
`/project/jevans/Dawoon/Science of Science/`.

## Layout

```
Science of Science/
├── README.md                      this file
├── run_notebook.py                exec a notebook's code cells in order, as a plain script
├── paper_style.py, fonts/         shared matplotlib style (Lato)
├── figshare_upload.py             deposit the output parquets on Figshare (resumable, md5-checked)
├── FIGSHARE_README.md             the dataset README that accompanies that deposit
├── openalex_2026_*.csv            schema listings for the OpenAlex snapshot
├── Disruption_Index.ipynb         ┐
├── Atypical_combinations.ipynb    ├ superseded 2025 Colab originals on MAG/SciSciNet
├── MAG-Disruption-CD5.ipynb       ┘
│
├── OpenAlex/                      papers, OpenAlex 2026-01-16
│   ├── oa_common.py               paths + data layer; every notebook imports this
│   ├── notebook/                  13 metric notebooks (see Metrics below)
│   ├── output/                    the parquet tables            (not tracked)
│   ├── cache/                     graph/CSR/journal/FoS caches  (not tracked)
│   ├── Abstract data/, Old/       superseded notebooks and side data
│   └── Readme.txt                 how the MAG-era notebooks were ported to OpenAlex
├── Dimensions/                    the same paper metrics on the Dimensions June 2025 index
│   ├── dim_common.py              keeps the public names of oa_common.py
│   ├── notebook/                  10 notebooks
│   └── Readme.txt                 where Dimensions is NOT equivalent to OpenAlex
├── PatentView/                    US granted utility patents
│   ├── pv_common.py               paths, the granted/pre-grant file resolver, preflight()
│   ├── notebook/                  15 notebooks
│   ├── Granted/, Pregranted/      PatentsView bulk .tsv.zip     (not tracked)
│   └── Old/
├── PATSTAT/                       worldwide applications, PATSTAT Global 2023 Autumn
│   ├── ps_common.py               plays the role of pv_common.py
│   ├── notebook/                  10 notebooks
│   ├── raw/                       zip -> parquet mirror         (not tracked)
│   └── Readme.txt                 filing-year anchor, citation-origin codes
├── Case law/                      US court opinions, Caselaw Access Project
│   ├── cl_common.py
│   ├── notebook/                  7 notebooks + gml_to_edgelist.ipynb
│   └── Figures/
├── pcs/                           patent -> paper citations, Reliance on Science
│   ├── pcs_common.py
│   └── notebook/                  3 notebooks
├── PPP/                           patent-paper pairs
│   ├── ppp_common.py
│   └── notebook/                  ppp_citation_trend.ipynb
│
├── validation/                    face validity, and the public dashboard
│   ├── val_common.py              V.init / V.save / V.paper / V.patent / V.dim / NEEDS
│   ├── *_validation.ipynb         one per literature, plus the two country notebooks
│   ├── disruption_crosscheck.ipynb   an independent transcription of CD_5, scored against ours
│   ├── dashboard_update.ipynb     legacy Case-law injector; its last cell calls the script below
│   ├── refresh_dashboard.py       rebuild metrics_dashboard.html from the figures + inventory
│   ├── dashboard_inventory.py     read row counts and schemas out of the parquet footers
│   ├── metrics_dashboard.html     the dashboard, also published to the SciSci Pages repo
│   ├── Figures/                   <notebook>_<section>.{jpg,pdf} at 600 dpi
│   └── data/
│       ├── world_countries.geojson         Natural Earth 1:50m Admin 0, trimmed (tracked)
│       ├── world_countries.source.json     its provenance
│       ├── inventory.json                  local diagnostic report (not published)
│       └── author_country_base.parquet     cached join, rebuilt on demand (not tracked)
│
└── jobs/<pipeline>/               nb.sbatch, submit_<pipeline>.sh, run_notebook.py, logs/
    └── validation/                also execute_inplace.py and smoke_country.sbatch
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
| Hit probability | `*_hit_probability` | Percentile of each count column within its cohort: (field, year) for papers, (WIPO sector, year) for patents, (jurisdiction, year) for case law. `pctl >= 0.99` is the top 1 %. |
| Citation trajectory | `*_citation_trend` | One row per (document, citing year), with years since publication or grant and the citation channel (paper -> paper, patent -> paper by examiner / applicant, patent -> patent). |
| Team size / authors | `paper_author`, `paper_team_size` | Author lists and team size from OpenAlex `works_au_affs` or Dimensions `authors[]`. |
| Geography | `paper_author_country`, `patent_inventor_country` | ISO2 countries of a document's authors or inventors: the sorted distinct set, the per-country head counts, whether the document is international, and (papers) the first and last author's own countries. Papers take the country of the institution an affiliation resolved to; patents take the address printed on the grant, with the assignee countries beside it. |
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
  `paper_author_country` has no dependency on the others and re-uses
  `paper_author`'s scan of the 40.8 GB affiliation gzip.
- PatentView: `patent_metadata`, `patent_reference`, `patent_disruption`,
  `patent_sb`, `patent_citation`, `patent_citation_trend`,
  `patent_disruption_app_add` have no dependency; then `patent_z_score`,
  `patent_feg_disruption_trend`, `patent_hit_probability`,
  `patent_disruption_app_compare`, `patent_disruption_trend`,
  `patent_uniqueC_trend`, `patent_inventor_country`.
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
interactive shells do not. Pipeline notebooks are executed with
`run_notebook.py` rather than `nbconvert --execute` because the runs emit about
a million tqdm updates that nbconvert would store back into the notebook;
validation notebooks use `jobs/validation/execute_inplace.py` instead, which
runs them on a real kernel and writes the outputs back, so the committed
`.ipynb` is the record of the last real run.

Smoke tests: the Dimensions notebooks honour `NB_DIM_BASE=<scratch>`,
`NB_FILE_LIMIT=12` and `NB_Z_YEARS=a:b`; PATSTAT honours `NB_DUCKDB_MEM`;
`patent_inventor_country` honours `NB_ROW_LIMIT` and `NB_OUT_DIR`;
`paper_author_country` honours `NB_AU_AFFS_SRC`, `NB_OUT_DIR` and
`NB_FORCE_PASS1`; the two country validation notebooks honour `NB_BASE_FP` and
`NB_BASE_LIMIT`, and `jobs/validation/smoke_country.sbatch` runs both against a
sampled base with the figures redirected to scratch, so a test run cannot
overwrite `validation/Figures/`.

## Validation and the dashboard

`validation/` holds one face-validity notebook per literature
(`paper_validation`, `patent_validation`, `dimension_validation`,
`case_law_validation`, `pcs_validation`, `ppp_validation`), two geography
notebooks (`author_country_validation`, `inventor_country_validation`), and
`disruption_crosscheck`. There is no external gold standard for most metrics, so
the checks are internal consistency (`C3 <= C5 <= C10 <= C_all`, `F + E + G = 1`,
`CD` in `[-1, 1]`), expected artefacts (citation truncation in recent years,
left-censoring at the start of a citation record) and, where it exists,
agreement with an independent index — SciSciNet for the paper metrics,
Dimensions for the author countries.

Figures go to `validation/Figures/<notebook>_<section>.{jpg,pdf}` at 600 dpi;
the section is the number of the markdown heading the plot sits under.
`refresh_dashboard.py` discovers every export of a family listed in its
`FAMILIES` table, captions it from `CAPTIONS`, and creates the section,
navigation entry, accent colour and KPI card of a family the page does not have
yet. Adding a validation notebook therefore means one `FAMILIES` entry plus
captions. Two steps, both from `validation/`:

```bash
python refresh_dashboard.py --source . --output ./metrics_dashboard.html
python refresh_dashboard.py --source . --output /project/jevans/Dawoon/SciSci/metrics_dashboard.html
```

The second copies the referenced figures into the public
[SciSci](https://github.com/Dawoon-Jeong0523/SciSci) repository, whose `main`
branch deploys to
[the live dashboard](https://dawoon-jeong0523.github.io/SciSci/metrics_dashboard.html).
Keep `SciSci/scripts/` in sync with the two scripts here after editing them.

The world maps need `validation/data/world_countries.geojson` (Natural Earth
1:50m Admin 0, public domain, trimmed to `iso2`/`name`/`continent` and
simplified; provenance in the `.source.json` beside it). It is checked in
because geopandas 1.0 removed its bundled `naturalearth_lowres` and a compute
node cannot be assumed to reach the internet. The 1:50m cut is deliberate: the
1:110m one omits Singapore, Hong Kong, Malta and Bahrain, and a country missing
from a choropleth reads as a country with no output.

## Data availability

The derived tables are being deposited on Figshare as *SciSci Dataset*
(item 33710572); the deposit is private while it is assembled.
`figshare_upload.py` performs the upload — it is idempotent, resumes a
half-finished file part by part, verifies MD5 on both sides, and refuses to
exceed the account quota:

```bash
python figshare_upload.py --dry-run                          # plan and quota check
python figshare_upload.py --domains "Case law" pcs PPP       # a subset
python figshare_upload.py --readme FIGSHARE_README.md --readme-only --replace
```

`FIGSHARE_README.md` is the dataset-level README that accompanies the deposit:
every file, its columns, the metric definitions and the reading caveats.

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
- Author country coverage is a property of OpenAlex's affiliation matching, not
  of the paper: 17.5 % of 1950 papers have a located author against 59.2 % of
  2020 papers. Take every country share over located documents, or a rising
  coverage curve will read as rising collaboration. Inventor coverage does not
  have this problem (99.3 %, because a US grant must print an address), except
  in the 1970s.
- 36 patents carry a PatentsView inventor id containing a semicolon of its own
  (an HTML entity, `fl:iv_ln:jadri&cacute;-1`, or a mangled sharp s,
  `fl:jo_ln:ha;feld-1`), so splitting `patent_metadata.inventor_list` on a bare
  `;` overcounts them. Split where the next id starts, or take `n_inventors`
  from `patent_inventor_country.parquet`.

## Superseded versions

Each pipeline keeps earlier notebook versions in `<pipeline>/Old/`, named
`<notebook>.ipynb.<stage>` where `<stage>` describes the edit that came next
(`.pre-paths`, `.pre-midway/`, `.pre-mag`, `.pre-dedup`, `.pre-uniqueC`,
`.pre-app`, `.pre-zscore`). Data backups keep their own suffix next to the data
(for example `patent_disruption.parquet.pre-dedup`) and are not tracked here.
