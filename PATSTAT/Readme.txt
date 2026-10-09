================================================================================
THE PATENT-METRIC PIPELINE ON PATSTAT GLOBAL 2023 AUTUMN
================================================================================
Written 2026-09-07. Modelled on ../PatentView (read its notebooks' headers first; this file
records what is different here). Same outputs, same column conventions, same kernels; the
unit is the PATSTAT APPLICATION instead of the US granted utility patent.

    /project/jevans/PATSTAT/unzipped_data/     65 zip parts, one CSV each (read-only)
    /project/jevans/PATSTAT/index_documentation_scripts_PATSTAT_Global_2023_Autumn.zip
                                               DataCatalog_Global_v5.22.pdf, the DDL, RowCount_2023b_result.txt


================================================================================
0. THE SHORT VERSION
================================================================================
  * ps_common.py = pv_common.py's role: paths, the universe predicate, the citation-origin
    buckets, the WIPO sector map, a DuckDB connection with the node's limits, and the
    zip -> parquet loader.
  * Stage 0 (jobs/PATSTAT/load.sbatch, an array of 21 tasks; or notebook/patstat_load.ipynb)
    streams each zip part once to raw/<tls>/partMM.parquet with the DDL's column types.
    ~2 min per part on a jevans node; row counts are asserted against the official counts.
  * Stage 1 (patstat_reference) resolves the 508 M citation rows to application -> application
    edges ONCE; every metric notebook reads that parquet, never tls212 again.
  * Everything is DuckDB SQL except the two numba kernels (disruption, sleeping beauty),
    which are the OpenAlex/Dimensions and PatentView kernels verbatim.
  * Three things are NOT equivalent to PatentView and are called out in section 4:
    the unit and universe, the time anchor, and what "examiner / applicant" means.
  * Three output sets, same notebooks and file names: output/ (applications, filing clock, the
    default), output_grant/ (applications, grant clock; 4b) and output_family/ (DOCDB families,
    earliest priority year; 4h).


================================================================================
1. INPUT MAPPING
================================================================================
  PatentView (granted bulk .tsv.zip)          PATSTAT 2023b (raw/<tls>/*.parquet)
  ------------------------------------------  ------------------------------------------------
  g_patent (patent_id, type, date)            tls201_appln  appln_id, ipr_type, appln_filing_year,
                                                granted, docdb_family_id, earliest_publn_year
  g_application (filing_date)                 tls201_appln  appln_filing_date (the anchor here)
  -- grant year --                            tls211_pat_publn  min publn_date with publn_first_grant='Y'
  g_us_patent_citation + g_us_application_    tls212_citation  pat_publn_id -> cited_pat_publn_id |
    citation + pg_granted_pgpubs_crosswalk      cited_appln_id, routed through tls211 to appln_id
  citation_category (examiner / other)        tls212.citn_origin  APP / SEA ISR SUP PRS EXA FOP CH2 /
                                                OPP '' ; 115 TPO excluded (third party)
  g_cpc_current (cpc_group, sequence)         tls224_appln_cpc (no sequence; IPC 'F' position from
                                                tls209_appln_ipc picks the subclass of cpc_code)
  g_wipo_technology (sector)                  tls230_appln_techn_field  techn_field_nr (1..35, weights)
                                                -> ps.WIPO_SECTOR (Schmoch's five sectors)
  g_inventor_/g_assignee_disambiguated        tls207_pers_appln x tls206_person  person_id,
                                                invt_seq_nr / applt_seq_nr, person_ctry_code, psn_sector
  -- (none) --                                tls202 titles, tls204 priorities, tls228 docdb family
                                                citations: loaded, not read by the metrics


================================================================================
2. THE MODULE -- ps_common.py
================================================================================
  ps.DUMP / RAW / OUT / CACHE          the dump, raw/, output/, cache/
  ps.TABLES                            the registry: DDL types + official row counts
  ps.UNIVERSE_WHERE                    ipr_type='PI' AND appln_id < 900000000 AND filing year 1900-2023
  ps.EDGE_WHERE                        age >= 0 AND NOT replenished  (every counting notebook)
  ps.bucket_sql() / third_party_sql()  citn_origin -> examiner / applicant / other ; 115, TPO
  ps.wipo_sector_sql()                 techn_field_nr -> sector
  ps.raw('tls212')                     "read_parquet('raw/tls212/part*.parquet')" -- raises if a part is missing
  ps.connect()                         duckdb: memory_limit 200GB (NB_DUCKDB_MEM), threads, and a temp folder
                                       per process (cache/duckdb_tmp/<NB>_<pid>): jobs running at once must
                                       never share one
  NB_PS_BASE / NB_PS_SAMPLE            smoke switches: redirect output/ + cache/, keep appln_id % k = 0
  NB_PS_CLOCK (ps.CLOCK)               filing (output/) | grant (output_grant/); ps.YEAR_COL / ps.AGE_COL name
                                       the clock's columns, ps.universe_sql() gives (appln_id, clock year)
  NB_PS_UNIT (ps.UNIT)                 application (default) | family (output_family/, filing clock only);
                                       ps.KEY is the output key (appln_id | docdb_family_id), ps.UNITS the plural
                                       for messages, ps.family_map_sql() gives (appln_id, docdb_family_id, fam_year)
  ps.load_table(tls, zip)              stage 0 for one part (unzip -p | pyarrow.csv -> zstd parquet)
  ps.preflight(nb) / ps.summary()      what is present / loaded row counts vs official


================================================================================
3. THE NOTEBOOKS (notebook/) AND THEIR OUTPUTS (output/)
================================================================================
  patstat_load                 raw/<tls>/*.parquet                    serial fallback + row-count check
  patstat_reference            patstat_reference.parquet              edge list: citing_id, cited_id, both
                                                                      filing years, age, citn_origin, bucket,
                                                                      replenished, resolved, publication ids
  patstat_metadata             patstat_metadata.parquet               one row per application in the universe
  patstat_citation             patstat_citation.parquet               C_{3,5,10,all} + by bucket + uniqueC_*
  patstat_citation_trend       patstat_citation_trend.parquet         per (application, citing year)
  patstat_disruption           patstat_disruption.parquet             CD/F/E/G/ni/nj/nk x windows (numba)
                               cache/patstat_csr.npz
  patstat_sb                   patstat_sb.parquet                     SB_B, SB_T, n_cite
  patstat_hit_probability      patstat_hit_probability.parquet        pctl_<count col> within sector x filing year
  patstat_z_score              patstat_z_score.parquet, z_score_pair.parquet   CPC-subclass-pair atypicality
  patstat_feg_disruption_trend patstat_feg_disruption_trend.parquet   yearly means
  patstat_disruption_trend     patstat_disruption_trend.parquet       per (application, year): new + cumulative
                               (+ _summary.parquet)                   ni/nj/nk, CD, F/E/G (numba, from the CSR cache)
  patstat_uniqueC_trend        patstat_uniqueC_trend.parquet          uniqueC by year since filing (== the uniqueC
                                                                      column of patstat_citation_trend, asserted)
  patstat_inventor             patstat_inventor.parquet               inventor_list (person_id), n_inventors, first/last
  patstat_inventor_country     patstat_inventor_country.parquet       countries, n_countries, country_inventor_counts,
                                                                      first_inventor_country, applicant_countries
  patstat_disruption also appends CD_{3,5,10,all}_pctl / _pctl_cume (filing year x CPC Section), as
  PatentView's patent_disruption section 6 does.

  Order (jobs/PATSTAT/submit_patstat.sh): reference -> metadata -> {citation, disruption, sb,
  z_score, inventor} -> {citation_trend, hit_probability} <- citation ; {feg_disruption_trend,
  disruption_trend} <- disruption ; inventor_country <- inventor ; uniqueC_trend <- citation_trend.
  Run: cd jobs/PATSTAT && sbatch load.sbatch ; then ./submit_patstat.sh  (or `after <arrayjobid>`).
  Smoke test of the whole chain first: sbatch smoke.sbatch (NB_PS_BASE=PATSTAT/cache/smoke,
  NB_PS_SAMPLE=20: every 20th application; raw scans stay full-size).


================================================================================
4. WHAT IS NOT EQUIVALENT TO PATENTVIEW
================================================================================
  a. Unit and universe. PatentView: US granted utility patents (one per invention, all granted,
     all dated by grant). PATSTAT: APPLICATIONS worldwide -- patents of invention only
     (ipr_type PI; utility models and designs out), real applications only (appln_id <
     900,000,000; PATSTAT's 'artificial' applications stand for cited documents it does not
     hold), filing year 1900-2023. About half are never granted; `granted` and `grant_year`
     are in the metadata for a granted-only view. One invention filed in several offices is
     several applications in one docdb family; `docdb_family_id` is carried in the metadata, and the
     whole chain is also run on DOCDB families (4h). tls228 (family -> family citations) is loaded
     but not used: the family edges are built from the application edges, so both units share one
     citation definition.
  b. Time anchor. PatentView: grant year at both ends. Here, by default: FILING year of the application at
     both ends (`age = citing_filing_year - cited_filing_year`), the PATSTAT / OECD convention.
     Search reports can cite documents filed later than the citing application, so `age` can
     be negative; such rows are in the edge list and excluded by ps.EDGE_WHERE. The citing
     publication's year is also in the edge list for a publication-based clock.
     The GRANT clock is available as a second output set (2026-10-01): NB_PS_CLOCK=grant runs the same
     notebooks with grant years (year of the first publication with publn_first_grant = 'Y') at both
     ends and only applications that have one, into output_grant/ (cache/grant/, executed notebooks in
     notebook/grant/); year / age columns become grant_year / yrs_since_grant. Measured on samples:
     53.7 % of applications are granted, 61.5 % of the filing-clock edges have both ends granted, 1.7 %
     of those have a negative grant age (excluded by EDGE_WHERE), WO (PCT) applications drop out (4.8 %
     granted), and grant lags differ by office (mean 2.4 y RU, 3.3 US, 3.5 CN, 4.7 JP, 5.7 EP, 6.8 CA),
     so a grant-year window or cohort mixes filing vintages differently across offices. The CD
     percentile cohort stays filing year x CPC Section in both sets, as in PatentView.
         NB_PS_CLOCK=grant ./submit_patstat.sh        sbatch --export=ALL,NB_PS_CLOCK=grant smoke.sbatch
  c. Provenance. PatentView's `cited by examiner` vs `other` is a US printing convention that
     changed in 2001 and 2013. PATSTAT records the origin of every citation: APP (applicant),
     SEA/ISR/SUP (search reports), PRS/EXA (examination), FOP/CH2, OPP (opposition), 115/TPO
     (third-party observations, excluded here as PatentView excludes `cited by third party`).
     `applicant` is therefore a real category here, not a proxy.
  d. Replenished citations (citn_replenished <> 0) are copies of another family member's
     citations onto a publication that carried none. Kept in the edge list with a flag,
     excluded from every count by default (ps.EDGE_WHERE).
  e. uniqueC. PatentView's uniqueC de-duplicates a citing patent's pre-grant and granted
     records of the same reference. Here the same thing happens between the several
     publications of one application (A1 search report, B1 grant) and the several publications
     of the target, so `C` (rows) exceeds `uniqueC` (distinct citing applications) by more
     than in PatentView. uniqueC is the impact count to use.
  f. Fields. PatentView's WIPO sector comes from g_wipo_technology; here from
     tls230_appln_techn_field (Schmoch concordance, IPC-based, weights across up to a few
     fields; the largest weight wins). The five sector names are identical.
  g. Atypicality. Same Kim et al. (2016) null on CPC subclass pairs; the cumulative set is by
     filing year and the arithmetic is done as DuckDB window sums instead of a Python loop.
     For a subclass with no new application in a year the count is looked up as-of that year
     (ASOF JOIN), which is what the loop's running dictionary holds.
  h. The family unit (2026-10-01). NB_PS_UNIT=family runs the same notebooks with the DOCDB family
     as the document, into output_family/ (cache/family/, executed copies in notebook/family/):
         NB_PS_UNIT=family ./submit_patstat.sh        sbatch --export=ALL,NB_PS_UNIT=family smoke.sbatch
     - Universe: the DOCDB families of the filing-clock universe (84,914,026 applications ->
       52,766,567 families, 1.61 per family; 82.4 % have one universe member). Key docdb_family_id.
     - Year: the family's earliest priority year over its universe members,
       min(coalesce(NULLIF(earliest_filing_year, 9999), appln_filing_year)); column priority_year,
       age column yrs_since_priority. The family unit has no grant clock (asserted in ps_common).
     - Edges: the application edge list mapped to families, one row per distinct (citing family,
       cited family, bucket) with n_appln_edges = the application edges it collapses. Citations
       inside a family are dropped (2,132,856 application edges), replenished rows too (they copy a
       member's citations, which the family already holds). 265,250,641 rows on 238,074,037 distinct
       pairs; a pair cited under two buckets has a row per bucket, so C counts rows and uniqueC
       distinct citing families (the impact count, as before).
     - Metadata, one row per family: priority_year, filing_year and appln_auth / first_appln_id of the
       earliest-filed member (filing year, then appln_id), n_appln, offices, granted (any member),
       n_granted, grant_year (first), docdb_family_size, nb_citing_docdb_fam; IPC / CPC main code and
       WIPO field from the earliest-filed member that has one; cpc_subclass_list = the union over
       members (also the atypicality input). Persons come from ONE representative member,
       inv_appln_id (most located inventors, then most inventors, then earliest filing):
       person_ids differ between offices, so a union over members would count one inventor several
       times. 48,141,257 families have inventors; 38.9 % of those have a located one (CN and JP
       first filings rarely carry an address -- validation/patent_country_validation section 1).
     - Cohorts: hit percentile within WIPO sector x priority year; CD percentile within the earliest
       member's filing year x CPC Section (pctl_year = filing_year).
     - Validation: validation/patstat_validation sections 17-18 (identities against the application
       set, family citations against EPO's nb_citing_docdb_fam, the same invention on both units).


================================================================================
5. HISTORY
================================================================================
  2026-09-08  the first chain stalled 24 h in patstat_reference cell 2 and was cancelled
              (patstat_chain_cancel_20260909.tex): `LEFT JOIN pub pp ON c.cited_pat_publn_id <> 0 AND
              c.cited_pat_publn_id = pp.pat_publn_id` planned as a BLOCKWISE_NL_JOIN because the
              one-sided `<> 0` cannot be a hash-join condition. `pub` has no publn id 0, so the
              predicate was redundant; dropped 2026-10-01 (EXPLAIN now shows two HASH_JOINs).
  2026-10-01  + disruption_trend, uniqueC_trend, inventor, inventor_country; CD cohort percentiles
              in patstat_disruption; per-process DuckDB temp folders; smoke switches.
  2026-10-01  grant clock as a second output set (NB_PS_CLOCK=grant -> output_grant/).
  2026-10-01  DOCDB family unit as a third output set (NB_PS_UNIT=family -> output_family/), 4h.
              Smoke (1/20) passed all 13 notebooks; full chain 59850068-80 ran 16:21-17:06
              (45 min; disruption 28 min, disruption_trend 6 min), every notebook check passes:
              30,785,709 cited families, CSR 37,623,677 nodes / 234,940,931 edges, CD_5 defined for
              64.4 % with mean +0.298 (applications +0.302), disruption_trend and uniqueC_trend
              reproduce every window exactly. 15 files, 10.7 GB.
  2026-10-03  patstat_feg_disruption_trend reads the ni / nj / nk = -1 "nothing in the window" placeholder
              as NULL (NULLIF) before averaging, in all three sets (jobs 59958116-18). The 3-, 5- and 10-year
              ni / nj / nk / njfrac means had averaged it in (ni_3_mean exactly -1 for the 1901+ cohorts,
              njfrac pulled toward 1/3); year, n, CD / F / E / G and every _all mean are unchanged. Previous
              notebook and outputs in Old/pre_sentinel_2026-10-03/.
