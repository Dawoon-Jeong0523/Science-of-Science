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
  ps.connect()                         duckdb: memory_limit 200GB (NB_DUCKDB_MEM), temp in cache/, threads
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

  Order (jobs/PATSTAT/submit_patstat.sh): reference -> metadata -> {citation, disruption, sb,
  z_score} -> {citation_trend, hit_probability} <- citation ; feg_disruption_trend <- disruption.
  Run: cd jobs/PATSTAT && sbatch load.sbatch ; then ./submit_patstat.sh  (or `after <arrayjobid>`).


================================================================================
4. WHAT IS NOT EQUIVALENT TO PATENTVIEW
================================================================================
  a. Unit and universe. PatentView: US granted utility patents (one per invention, all granted,
     all dated by grant). PATSTAT: APPLICATIONS worldwide -- patents of invention only
     (ipr_type PI; utility models and designs out), real applications only (appln_id <
     900,000,000; PATSTAT's 'artificial' applications stand for cited documents it does not
     hold), filing year 1900-2023. About half are never granted; `granted` and `grant_year`
     are in the metadata for a granted-only view. One invention filed in several offices is
     several applications in one docdb family; `docdb_family_id` is carried so family-level
     aggregation is a GROUP BY away, and tls228 (family -> family citations) is loaded.
  b. Time anchor. PatentView: grant year at both ends. Here: FILING year of the application at
     both ends (`age = citing_filing_year - cited_filing_year`), the PATSTAT / OECD convention.
     Search reports can cite documents filed later than the citing application, so `age` can
     be negative; such rows are in the edge list and excluded by ps.EDGE_WHERE. The citing
     publication's year is also in the edge list for a publication-based clock.
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
