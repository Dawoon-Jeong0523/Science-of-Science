# SciSci Dataset — document-level science-of-science metrics for papers, patents and court cases

This item holds the metric tables produced by the *Science of Science* pipeline: one row per
document (paper, US utility patent, or US court case) or per document × year, computed with the
same code on several corpora so that the metrics are comparable across them. Every file is
Apache Parquet (ZSTD or Snappy), readable with pandas, pyarrow, DuckDB, R `arrow`, Spark, etc.

The code that produced every file is in the `Science-of-Science` repository
(github.com/Dawoon-Jeong0523/Science-of-Science). Each parquet file has a notebook of the same
name under `<domain>/notebook/`, whose first cell documents inputs, definitions, and the
verification that was run before the file was written.

Author: Dawoon Jeong, University of Chicago (jdwoon0523@uchicago.edu).

---

## 1. Layout

The pipeline is organised in *domain* folders. Figshare items are flat, so each file is named
`<Domain>__<file>` where `<Domain>` is the folder it came from (space → underscore):

| Figshare file prefix | pipeline folder | corpus | key |
|---|---|---|---|
| `OpenAlex__` | `OpenAlex/output/` | OpenAlex works (snapshot 2026-01-16), ~373M papers | `paper_id` = OpenAlex work id, `W…` |
| `Dimensions__` | `Dimensions/output/` | Dimensions publications (June 2025 dump), ~155M papers | `paper_id` = Dimensions id, `pub.…` |
| `PatentView__` | `PatentView/output/` | US **utility** patents, PatentsView granted bulk (2026-05-21), ~8.5M patents | `patent_id` = USPTO patent number as a string |
| `Case_law__` | `Case law/output/` | US court cases, Caselaw Access Project (CAP), 5.18M cases | `case_id` = CAP case id (int64) |
| `pcs__` | `pcs/output/` | patent→paper citations (Reliance on Science, US patents only), per **paper** | `paper_id` (OpenAlex `W…`) |
| `PPP__` | `PPP/output/` | 548,315 curated patent–paper pairs | `paperid` (OpenAlex `W…`) + `patent` (`US-…`) |

Two outputs are directories of part files rather than single parquet files
(`OpenAlex__referenced_works_w_year`, `Dimensions__references_w_year`). They are delivered as
uncompressed `.tar` bundles (`<Domain>__<dir>.partNN.tar`); each tar extracts to
`<domain>/output/<dir>/part_NNNN.parquet` and the parts can be read as one dataset
(`pd.read_parquet('<dir>/')`, `read_parquet('<dir>/*.parquet')` in DuckDB).

**Availability.** The full set is ~111 GiB, which exceeds the storage attached to this item.
Uploaded so far: every table of Case law, pcs, PPP and PatentView, plus
`OpenAlex__paper_author_country.parquet`. The remaining OpenAlex and Dimensions tables are
documented below so their schemas are on record, but are **not yet uploaded**. The file list on
the item itself is the authoritative statement of what is present.

Ids never carry a URL prefix (`W3002427681`, not `https://openalex.org/W3002427681`).
Sibling files within a domain join on the key column above; `OpenAlex__paper_author.parquet`
calls that column `work_id` (see §3).

---

## 2. Metric families (definitions shared by every domain)

Let *F* be the focal document with year *y* (publication year, grant year, or decision year),
and let a citation from *c* to *F* have age `age = year(c) − y`. Only `age ≥ 0` is counted.

**Citation counts — `*_citation.parquet`.** `C_3, C_5, C_10` count citers with `0 ≤ age ≤ w`;
`C_all` counts every citer with `age ≥ 0`. Uncited documents are present with zeros.

**Citation trend — `*_citation_trend.parquet`.** The same citations kept by year: one row per
(document, citing year) with ≥ 1 citation, `yrs_since_* = cite_year − y`. Sparse: a year with
no citation has no row; a never-cited document is absent.

**Disruption — `*_disruption.parquet`.** Funk & Owen-Smith's CD index with the F/E/G
decomposition, per window `w ∈ {3, 5, 10, all}` (column suffix `_3, _5, _10, _all`):

- `ni` citers of *F* that cite none of *F*'s references; `nj` citers of *F* that also cite ≥ 1 of
  its references; `nk` documents citing ≥ 1 of *F*'s references but not *F*;
- `CD = (ni − nj) / (ni + nj + nk)` in [−1, 1]; +1 disruptive, −1 consolidating;
- `F, E, G` (Foundation / Extension / Generalization) partition *F*'s citers by whether a citer
  leans on *F*'s references (`E`), on *F*'s other citers (`F`), or on neither (`G`); ties split
  ½/½ so `F + E + G = 1`.

A document with no citer in the window has `CD, F, E, G = NaN` (not 0) and `ni, nj, nk` = −1
(OpenAlex/Dimensions) or NaN (PatentView/Case law).

**Disruption trend — `*_disruption_trend.parquet`.** CD and F/E/G as they evolve: one row per
(document, year) in which a new citer or co-citing document appeared, carrying that year's
new arrivals (`ni_new, nj_new, nk_new`), the cumulative `ni, nj, nk`, and `CD, F, E, G` on the
cumulative counts. The row at `yrs_since_* = w` equals the `_w` value of the per-window file,
and the last row equals `_all`. `*_disruption_trend_summary.parquet` averages these by cohort
year × age. `*_feg_disruption_trend.parquet` averages the per-window file by cohort year.

**Sleeping beauty — `*_sb.parquet`.** Ke, Ferrara, Radicchi & Flammini's beauty coefficient
`SB_B` and awakening time `SB_T` from the yearly citation histogram; `n_cite` is the number of
dated citations the curve was built from (filter on it — `B` means little on 2–3 citations).
A document that peaks in year 0 has `B = T = 0` by definition. Uncited documents are omitted.

**Hit probability — `*_hit_probability.parquet`.** Each document's citation percentile in
[0, 1] within a cohort, computed independently for each window (`pctl_c3, pctl_c5, pctl_c10,
pctl_call`, or `pctl_C_*`). Percentile 0.99 = top 1 % of its cohort. Ties share the lowest rank,
so uncited documents sit at the bottom. Cohorts: OpenAlex/Dimensions/pcs = (field, year);
PatentView = (WIPO technology sector, grant year); Case law = (jurisdiction, decision year).

**Atypicality — `*_z_score.parquet` and `z_score_pair*.parquet`.** Per document the median,
10th percentile and minimum z-score over the pairs it combines (`Z_median, Z_10pct, Z_min`),
with `n_pairs` distinct pairs. Negative z = an unusual combination. Papers: Uzzi et al. (2013)
journal pairs among the references, against a year-preserving rewiring null (10 shuffles).
Patents: Kim et al. (2016) CPC-subclass pairs of the patent itself, against an analytic
hypergeometric null on the cumulative patent set. The `z_score_pair*` files hold the pair-level
z per year (`code_1, code_2, year, Z_score`; codes are integer journal/source codes for papers,
CPC subclasses for patents).

---

## 3. OpenAlex (papers) — `OpenAlex__*`

Source: OpenAlex snapshot of 2026-01-16 (works, referenced_works, primary_locations, topics,
authorships). Citation graph: ~1.78 B work→work references with both endpoints dated.

| file | rows | columns | notes |
|---|---|---|---|
| `paper_metadata.parquet` | 372.7M | `paper_id, year, doctype, ref_count, journal, is_journal, author_list, FoS_0, FoS_rep, domain, cited_by_count, is_retracted` | `FoS_rep` = field of the highest-scoring topic (26 OpenAlex fields), `FoS_0` = all fields `;`-joined, `domain` = the 4 OpenAlex domains. `author_list` is **entirely null** here — use `paper_author`. `cited_by_count` is OpenAlex's own count, not the graph's. |
| `paper_author.parquet` | 251.7M | `work_id, author_list, team_size, first_author, last_author` | One row per work with ≥ 1 author. De-duplicated on (work, author): the source is author × affiliation. `author_list` = author ids in author order. Keyed `work_id` (same values as `paper_id`). |
| `paper_author_country.parquet` | 251.7M | `paper_id, team_size, n_located, countries, n_countries, country_author_counts, first_author_country, last_author_country, is_international` | Author countries (ISO2, from the affiliation's institution); same works and `team_size` as `paper_author`. 44.6 % of papers have ≥ 1 located author, 7.2 % are international. `countries` sorted `;`-joined, `country_author_counts` like `US:3;CN:1` (an author with two countries counts in both). Added 2026-09-13. |
| `paper_team_size.parquet` | 251.7M | `paper_id, team_size` | Superseded by `paper_author` (identical team sizes; kept for continuity). |
| `paper_citation.parquet` | 348.9M | `paper_id, C_3, C_5, C_10, C_all` | paper→paper. |
| `paper_citation_trend.parquet` | 584.1M | `paper_id, pub_year, cite_year, yrs_since_pub, p2p, pat2p_examiner, pat2p_non_examiner` | `p2p` paper→paper; `pat2p_*` US patent→paper citations (Reliance on Science) by patent grant year, split by who put the reference on the patent. |
| `paper_disruption.parquet` | 348.9M | `paper_id` + `CD, F, E, G, ni, nj, nk` × `_3, _5, _10, _all` | 28 metric columns. |
| `paper_disruption_trend.parquet` | 1.23 B | `paper_id, pub_year, cite_year, yrs_since_pub, ni_new, nj_new, nk_new, ni, nj, nk, CD, F, E, G` | 13.5 GB. |
| `paper_disruption_trend_summary.parquet` | 34k | `pub_year, yrs_since_pub, n_CD, CD_mean, n_F, F_mean, n_E, E_mean, n_G, G_mean` | cohort × age means. |
| `paper_sb.parquet` | 88.3M | `paper_id, SB_B, SB_T, n_cite` | |
| `paper_hit_probability.parquet` | 262.5M | `paper_id, FoS, year, pctl_c3, pctl_c5, pctl_c10, pctl_call` | cohort = (`FoS`, `year`). |
| `paper_z_score.parquet` | 41.4M | `paper_id, Z_median, Z_10pct, Z_min, n_pairs` | Journal-type papers **1980–2020** (not 1900–2020) with 2–1000 references. Merged from the year partitions below. |
| `paper_z_score_<a>_<b>.parquet` | — | same | Year-range partitions of the above (1980_1984 … 2020_2020). `paper_z_score_2000_2005` and `paper_z_score_old` are an earlier vintage with a wrong journal mapping and are **not** part of the merged file; `*_2001_2006.onepass` is a byte-identical verification copy of `*_2001_2006`. |
| `z_score_pair.parquet`, `z_score_pair_<a>_<b>.parquet` | 430.0M | `code_1, code_2, year, Z_score` | Journal-pair z by focal year; same partitioning and vintage caveats as above. |
| `referenced_works_w_year/` (1,334 parts, tar bundles) | ~1.78 B | `work_id, work_year, work_id_source_id, referenced_work_id, referenced_work_year, referenced_work_id_source_id` | The citation edge list with year and source (journal) of both endpoints. Years are nullable int16. |

## 4. Dimensions (papers) — `Dimensions__*`

Source: Dimensions publications and patents dump, June 2025. Same kernels as OpenAlex; the
differences are in the data layer: ids are `pub.…`, fields are the 23 ANZSRC FoR 2020
divisions, and patent→paper links are Dimensions' own (all jurisdictions), not Reliance on Science.

| file | rows | columns | notes |
|---|---|---|---|
| `paper_metadata.parquet` | 155.5M | `paper_id, year, doctype, doc_class, is_citable, ref_count, journal, is_journal, source_id, author_list, team_size, FoS_0, FoS_rep, for_division_codes, for_group_codes, cited_by_count, citations_count, doi` | `doctype` = article/chapter/proceeding/preprint/monograph/book; `doc_class` = RESEARCH_ARTICLE, REVIEW_ARTICLE, …; `author_list` = resolved researcher ids in author order. |
| `paper_author.parquet` | 142.4M | `paper_id, author_list, team_size, n_resolved, first_author, last_author, corresponding_author, countries, n_countries` | `team_size` counts every author slot, `n_resolved` those with a researcher id; `countries` = sorted distinct ISO2 over the authors' affiliation addresses (17–25 % of articles have any). |
| `paper_citation.parquet` | 155.4M | `paper_id, C_3, C_5, C_10, C_all` | |
| `paper_citation_trend.parquet` | 577.3M | `paper_id, pub_year, cite_year, yrs_since_pub, p2p, pat2p, pat2p_us` | `pat2p` from Dimensions patent `publication_ids`, dated by grant year; `pat2p_us` = US-jurisdiction subset. No examiner split exists in Dimensions. |
| `paper_disruption.parquet` | 155.4M | as OpenAlex | |
| `paper_sb.parquet` | 83.8M | `paper_id, SB_B, SB_T, n_cite` | |
| `paper_hit_probability.parquet` | 119.0M | `paper_id, FoS, year, pctl_c3, pctl_c5, pctl_c10, pctl_call` | `FoS` = FoR division. |
| `paper_z_score_1990_2000.parquet`, `z_score_pair_1990_2000.parquet` | 6.2M / 34.1M | as OpenAlex | Only the 1990–2000 validation range has been run. |
| `references_w_year/` (4,219 parts, tar bundles) | — | same six columns as the OpenAlex edge table | |

## 5. PatentView (US utility patents) — `PatentView__*`

Source: PatentsView granted bulk files (data.uspto.gov, downloaded 2026-05-21) and the
pre-grant publication crosswalk. Universe: **utility** patents; citations are utility↔utility.
Two citation sources appear: **granted** (`g_us_patent_citation`, the references on the issued
patent) and **application** (`g_us_application_citation`, references made at the pre-grant
stage, mapped from the cited publication number to the granted patent). Both are dated by the
citing patent's **grant year**.

Provenance split: `examiner` = the reference was added by the USPTO examiner;
`non_examiner` = applicant and other; `unknown` = no category recorded. **Read with the coding
history in mind:** before 2001 no category exists (everything is `unknown`); 2001–2012 only
examiner citations are flagged; from 2013 a three-way coding exists. Category shares therefore
jump around 2001 and 2013 by construction.

| file | rows | columns | notes |
|---|---|---|---|
| `patent_metadata.parquet` | 8.53M | `patent_id, grant_year, filing_year, ref_count, cpc_code, cpc_code_list, inventor_list, assignee_list` | `cpc_code` = primary CPC group; lists are `;`-joined disambiguated ids in sequence order. `ref_count` = US patent backward references. |
| `patent_inventor_country.parquet` | 8.53M | `patent_id, n_inventors, n_located, countries, n_countries, country_inventor_counts, first_inventor_country, is_international, assignee_countries` | Inventor countries (ISO2) from the address on the grant, 99.3 % of patents located, 6.3 % international; `assignee_countries` likewise for assignees. Added 2026-09-13. |
| `patent_reference.parquet` | 171.5M | `citing_id, cited_id, type, grant_id` | The edge list. `type` = `granted` / `application`; `cited_id` is the identifier as cited (a pgpub number on application rows); **join on `grant_id`**, the granted patent it resolves to. |
| `patent_citation.parquet` | 7.16M | `patent_id`, `C_{w}`, `C_examiner_{w}`, `C_non_examiner_{w}`, `C_unknown_{w}`, `appC_{w}`, `appC_examiner_{w}`, `appC_non_examiner_{w}`, `uniqueC_{w}`, `uniqueC_examiner_{w}`, `uniqueC_non_examiner_{w}`, `uniqueC_unknown_{w}` for `w ∈ {3, 5, 10, all}` | `C` granted citations, `appC` application-stage citations, `uniqueC` distinct citing patents over the union of both. **Cited patents only** (a patent never cited is absent). |
| `patent_citation_trend.parquet` | 50.5M | `patent_id, grant_year, cite_year, yrs_since_grant, C, C_examiner, C_non_examiner, C_unknown, appC, appC_examiner, appC_non_examiner, pat2pat_examiner, pat2pat_non_examiner, app2pat_examiner, app2pat_non_examiner` | The last four columns are the pre-2026-09 names of `C_*` / `appC_*` and are kept for compatibility. |
| `patent_citation_trend_old.parquet` | 50.5M | `patent_id, grant_year, cite_year, yrs_since_grant, pat2pat_examiner, pat2pat_non_examiner, app2pat_examiner, app2pat_non_examiner` | Previous vintage; superseded by the file above. |
| `patent_uniqueC_trend.parquet` | 50.5M | `patent_id, grant_year, cite_year, yrs_since_grant, uniqueC` | Distinct citing patents by the year of their earliest citation; cumulates to `uniqueC_w`. |
| `patent_disruption.parquet` | 8.06M | `patent_id` + `CD, F, E, G, ni, nj, nk` × windows | Granted citation network. |
| `patent_disruption_app.parquet` | 8.46M | same schema | Extended network: granted ∪ application citations, de-duplicated. |
| `patent_disruption_compare.parquet` | 4 | `window, n_base_rows, n_app_rows, n_app_only, n_paired, base_mean, app_mean, delta, pearson, spearman, pct_down, pct_up, pct_same, d_ni, d_nj, d_nk` | Per-window comparison of the two tables above. |
| `patent_disruption_trend.parquet` | 93.7M | `patent_id, grant_year, cite_year, yrs_since_grant, ni_new, nj_new, nk_new, ni, nj, nk, CD, F, E, G` | |
| `patent_disruption_trend_summary.parquet` | 1,275 | `grant_year, yrs_since_grant, n_CD, CD_mean, …, G_mean` | |
| `patent_feg_disruption_trend.parquet` | 49 | `year, n, {CD,F,E,G,ni,nj,nk,njfrac}_{w}_mean` | Means by grant year; `njfrac = nj / (ni + nj)`. |
| `patent_sb.parquet` | 6.80M | `patent_id, SB_B, SB_T, n_cite` | |
| `patent_hit_probability.parquet` | 8.51M | `patent_id, wipo_sector, grant_year`, `pctl_<count>_{w}` for every count column of `patent_citation`, plus `pctl_c3, pctl_c5, pctl_c10, pctl_call` (= `pctl_C_*`) | cohort = (WIPO sector, grant year); 5 sectors. |
| `patent_hit_probability_old.parquet` | 8.51M | `patent_id, wipo_sector, grant_year, pctl_c3, pctl_c5, pctl_c10, pctl_call` | Previous vintage (granted `C_*` only). |
| `patent_z_score.parquet` | 4.16M | `patent_id, Z_median, Z_10pct, Z_min, n_pairs` | Patents with ≥ 2 inventional CPC subclasses. |
| `z_score_pair.parquet` | 0.98M | `code_1, code_2, year, Z_score` | CPC-subclass pair z per grant year (cumulative null). |

## 6. Case law (US court cases) — `Case_law__*`

Source: Caselaw Access Project metadata (5,179,698 cases; jurisdiction, court, reporter,
decision date) and a 47.5M-edge case-to-case citation list. Every case has a decision year, so
no edge is lost to missing dates.

| file | rows | columns | notes |
|---|---|---|---|
| `case_metadata.parquet` | 5.18M | `case_id, decision_year, decision_date, jurisdiction, jurisdiction_id, court, court_id, reporter, reporter_id, name_abbreviation, ref_count` | `ref_count` = cases this case cites. 61 jurisdictions, 3,221 courts, 413 reporters. |
| `case_citation.parquet` | 5.18M | `case_id, C_3, C_5, C_10, C_all` | Includes the 1,391,837 never-cited cases with zeros. |
| `case_citation_trend.parquet` | 25.8M | `case_id, decision_year, cite_year, yrs_since_decision, C` | |
| `case_disruption.parquet` | 5.18M | `case_id` + `CD, F, E, G, ni, nj, nk` × windows | |
| `case_feg_disruption_trend.parquet` | 221 | `year, n, {CD,F,E,G,ni,nj,nk,njfrac}_{w}_mean, n_{w}_defined` | Means by decision year. Right-truncated at the recent end. |
| `case_sb.parquet` | 3.79M | `case_id, SB_B, SB_T, n_cite` | |
| `case_hit_probability.parquet` | 5.18M | `case_id, jurisdiction, decision_year, cohort_n, pctl_C_3, pctl_C_5, pctl_C_10, pctl_C_all` | cohort = (jurisdiction, decision year); `cohort_n` is its size — filter on it. |

## 7. pcs — patent→paper citations per paper — `pcs__*`

Source: Reliance on Science (Marx & Fuegi) patent-to-paper citation links for **US** patents
matched to OpenAlex works (`pcs_oa_uspto`). `paper_id` is the OpenAlex `W…` id; citing patents
are dated by grant year. Provenance: `examiner` vs `non_examiner` (applicant and other).

| file | rows | columns | notes |
|---|---|---|---|
| `pcs_citation.parquet` | 5.11M | `paper_id, C_{w}, C_examiner_{w}, C_non_examiner_{w}` for `w ∈ {3,5,10,all}`, `C_total, C_examiner_total, C_non_examiner_total` | Number of US patents citing the paper. `*_total` ignores the year (includes citing patents without a matched grant year). Cited papers only. |
| `pcs_citation_trend.parquet` | 13.0M | `paper_id, pub_year, cite_year, yrs_since_pub, pcs, pcs_examiner, pcs_non_examiner` | |
| `pcs_hit_probability.parquet` | 4.48M | `paper_id, FoS, year, pctl_c3, pctl_c5, pctl_c10, pctl_call` | Percentile of patent citations within the OpenAlex (field, year) cohort of papers that have ≥ 1 patent citation. |

## 8. PPP — patent–paper pairs — `PPP__*`

Source: 548,315 curated patent–paper pairs (`_patent_paper_pairs_plus`, 335,917 papers ×
309,729 US patents), i.e. a paper and the patent that covers the same invention. Both sides of
each pair get a yearly citation trend.

| file | rows | columns | notes |
|---|---|---|---|
| `ppp_paper_trend.parquet` | 5.79M | `paperid, patent, pub_year, cite_year, yrs_since_pub, p2p, pat2p_examiner, pat2p_non_examiner` | Paper side, anchored at publication year: paper→paper and US patent→paper citations. |
| `ppp_patent_trend.parquet` | 2.91M | `paperid, patent, grant_year, cite_year, yrs_since_grant, pat2pat_examiner, pat2pat_non_examiner` | Patent side, anchored at grant year: US patent→patent citations. |

`patent` is formatted `US-<number>`; strip the prefix to join `PatentView__*` on `patent_id`.

---

## 9. Reading notes

- **Right truncation.** A document from 2018 cannot have a 10-year window. Every fixed-window
  series bends at the recent end for that reason alone; `_all` grows shorter the closer the
  document is to the snapshot. Read windows only where they have closed.
- **NaN is "undefined", not zero.** CD/F/E/G are NaN for documents with no citer in the window;
  SB and hit-probability tables omit or rank-at-the-bottom uncited documents as documented above.
- **Sparse trend tables.** A missing (document, year) row means zero citations in that year;
  a document missing from a trend table was never cited.
- **`_old` and `.onepass` files** are earlier vintages or verification copies kept for
  reproducibility of past analyses; prefer the un-suffixed file.
- **Types.** Ids are strings except `case_id` (int64). `year` in `OpenAlex__paper_metadata`
  is float (nullable); `filing_year` in `PatentView__patent_metadata` likewise.
- **Splitting `inventor_list`.** 36 patents carry a PatentsView inventor id with a `;` of its own
  (an HTML entity, `fl:iv_ln:jadri&cacute;-1`, or a mangled ß, `fl:jo_ln:ha;feld-1`), so a plain
  split on `;` overcounts them. Split where the next id starts instead — an `fl:` id or a
  20-character hash id, e.g. `re.split(r';(?=fl:|[0-9a-z]{20})', s)` — or take `n_inventors` from
  `patent_inventor_country.parquet`, which is computed from the source rows.
- **Country codes** are ISO 3166-1 alpha-2. Namibia is `NA` — do not let a CSV reader turn it
  into a missing value.

## 10. References

- Funk, R. J., & Owen-Smith, J. (2017). A dynamic network measure of technological change. *Management Science*, 63(3), 791–817.
- Ke, Q., Ferrara, E., Radicchi, F., & Flammini, A. (2015). Defining and identifying Sleeping Beauties in science. *PNAS*, 112(24), 7426–7431.
- Uzzi, B., Mukherjee, S., Stringer, M., & Jones, B. (2013). Atypical combinations and scientific impact. *Science*, 342(6157), 468–472.
- Kim, D., Cerigo, D. B., Jeong, H., & Youn, H. (2016). Technological novelty profile and invention's future impact. *EPJ Data Science*, 5, 8.
- Marx, M., & Fuegi, A. (2020). Reliance on science: Worldwide front-page patent citations to scientific articles. *Strategic Management Journal*, 41(9), 1572–1594.
- Priem, J., Piwowar, H., & Orr, R. (2022). OpenAlex: A fully-open index of scholarly works, authors, venues, institutions, and concepts. arXiv:2205.01833.
- PatentsView, USPTO. https://patentsview.org
- Caselaw Access Project, Harvard Law School Library. https://case.law
