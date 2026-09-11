================================================================================
THE PAPER-METRIC PIPELINE ON THE DIMENSIONS JUNE 2025 DUMP
================================================================================
Written 2026-09-07. Modelled cell for cell on ../OpenAlex (read its Readme.txt first;
this file records only what is different here).

The ten notebooks in notebook/ are the OpenAlex ones re-pointed at

    /project/jevans/dimensions/dimensions/dimensions_june_2025/     (832 GB, read-only)

through a new data layer, dim_common.py, that keeps oa_common.py's public names. Every
metric kernel -- the numba disruption engine, the sleeping-beauty kernel, the Uzzi
shuffle and its validation tests, the vectorised citation counts, the percentile rank --
is copied VERBATIM out of the OpenAlex notebooks by the generator that wrote these
(the cells are pulled by index and asserted on a marker string), so the two pipelines
compute the same quantity on two indices and can be compared paper for paper via DOI.


================================================================================
0. THE SHORT VERSION
================================================================================
  * dim_common.py = oa_common.py with the Dimensions paths, the `pub.`/`jour.` id codec,
    and a one-pass extraction of the nested columns. Same function names.
  * A Dimensions id is `pub.` + up to ten digits, so int(id[4:]) round-trips through
    int64 and the notebooks' code space (sorted `uni_mag`, searchsorted) is unchanged.
    Journals are `jour.` + digits and use the same trick.
  * There is no partition alignment to exploit and no second tree to walk: publications
    is ONE table of 155.5M rows with everything nested on the row (references, authors,
    fields, source), so stage 0 reads it once and writes slim per-file parts that every
    other notebook reads. The dump is never opened again after stage 0 (except the
    patents folder, by paper_citation_trend).
  * Three things are NOT equivalent to OpenAlex and are called out in section 4: the
    field taxonomy, what a "journal" is, and the patent->paper channel.


================================================================================
1. INPUT MAPPING
================================================================================
  OpenAlex (renli snapshot)                 Dimensions June 2025
  ----------------------------------------  ------------------------------------------
  works/referenced_works (edges)            publications.reference_ids[]  (exploded)
  works/works  id, publication_year, type   publications.id, year, type,
                                              document_type.classification/is_citable
  primary_locations + sources.csv.gz        publications.source_id (journal.id fills the
    (source, journal name, is_journal)        gap) + source_titles/ (id, type, title)
  works/topics + topics.csv.gz (field)      categories.for_2020_v2022 first_level (2-digit
                                              ANZSRC FoR divisions) / second_level (4-digit)
  works_au_affs_fixed.csv.gz (38 GB gzip)   publications.authors[] -- on the row, in order,
                                              with researcher_id and affiliation countries
  pcs/pcs_oa_uspto.csv + g_patent.tsv.zip   patents/ publication_ids[] + granted_year /
                                              publication_year / jurisdiction
  cited_by_count                            metrics.times_cited, citations_count

  Ids: publications `pub.<digits>`; sources `jour.<digits>`; researchers `ur.<digits>.<dd>`
  (not an integer -- carried as strings); patents `US-5078767-A` style (strings).


================================================================================
2. THE MODULE -- dim_common.py, and what stage 0 writes
================================================================================
  dim.ROOT / PUBS / PATENTS / SOURCES   the dump
  dim.BASE / CACHE / OUT                this folder (NB_DIM_BASE overrides, for smoke tests)

  Stage 0 (notebook/references_w_year.ipynb) writes:
    cache/publications_file_index.parquet   footer index: year/type/rows per file
    cache/pub_scalars/part_NNNN.parquet     one row per publication, all document scalars
    cache/pub_authors/part_NNNN.parquet     author_list, team_size, first/last/corresponding,
                                            countries
    cache/pub_year_source_map.npz           code, year (int16, -1 unknown), source (int64)
    output/references_w_year/part_NNNN      one row per edge, both endpoints dated and
                                            placed -- the SAME six column names as the
                                            OpenAlex edge table (work_id, work_year,
                                            work_id_source_id, referenced_work_id,
                                            referenced_work_year, referenced_work_id_source_id)

  dim.build_graph() / build_csr() / load_graph() / load_csr()   as in oa_common, from the
                                            edge table (no slow path over the dump)
  dim.build_journal()   work_id, source_id, journal (source_titles.title),
                        is_journal (= source_titles.type == 'journal')
  dim.build_fos()       work_id, FoS_rep (first FoR division listed), FoS_0 (all, ;-joined),
                        for_division_codes, for_group_codes
  dim.stream_edges / code_index / citation_counts / stream_reference_journals   as before
  dim.id_to_code / code_to_id / src_to_code / code_to_src   the codec
  dim.pub_files() / patent_files()   honour NB_FILE_LIMIT (strided sample)


================================================================================
3. TRAPS
================================================================================
  * publications files are extension-less parquet named publications_000000000NNN, one
    `year` each but NOT in year order -- pick by footer statistics, never by name.
  * `authors[]` has one entry per author SLOT; only slots Dimensions disambiguated carry a
    researcher_id. author_list lists the resolved ones; team_size counts every slot;
    first_author / last_author are null when that slot is unresolved. Do not read
    len(author_list) as the team size.
  * `citations[]` (forward citations with year) exists on the row but is NOT used: the
    graph is built from reference_ids so that in- and out-edges are the same edge set.
    citations_count / metrics.times_cited are carried into paper_metadata for comparison;
    they count citations from the whole Dimensions index at export time, C_all counts edges
    present in the dump.
  * `publication_ids` on a patent repeats a publication when it is cited more than once;
    the edge table is list_distinct-ed.
  * Years run 1700-2030 by construction (dim.YEAR_MIN/MAX); anything outside is -1 in the
    map and its edges drop out of every window. 1700 also keeps paper_citation_trend's
    `cited * 400 + (year - 1700)` key collision-free.


================================================================================
4. WHERE THE TWO INDICES ARE NOT THE SAME THING
================================================================================
  (a) FIELD OF STUDY. OpenAlex: 26 topic-hierarchy fields, FoS_rep = field of the
      highest-scoring topic. Dimensions: 23 ANZSRC Fields of Research 2020 divisions,
      no score, so FoS_rep = the first division listed and FoS_0 = all of them.
      paper_hit_probability cohorts on (FoS_rep, year): the metric is unchanged, the
      partition is a different taxonomy. `domain` has no Dimensions twin and is not written.
  (b) JOURNAL. OpenAlex: primary-location source with sources.type == 'journal'.
      Dimensions: source_id with source_titles.type == 'journal' (163,809 of 195,923
      sources; the rest are proceedings, book series, seminar series, preprint platforms).
      paper_z_score's focal set and its journal-pair map both rest on this flag.
  (c) PATENT -> PAPER. OpenAlex: PCS (US patents, examiner / applicant split by reftype).
      Dimensions: its own patent index, all jurisdictions, no examiner tag. So
      paper_citation_trend writes pat2p and pat2p_us, not pat2p_examiner / non_examiner,
      dated by granted_year (else publication_year).
  (d) COVERAGE. 155.5M publications against OpenAlex's ~396M works; Dimensions is
      article-heavy (chapters, proceedings, preprints, monographs are typed) and stops in
      2025. `doctype` is Dimensions' `type` vocabulary; `doc_class` (RESEARCH_ARTICLE,
      REVIEW_ARTICLE, CONFERENCE_ABSTRACT, EDITORIAL, ...) is an extra column OpenAlex
      lacks and is what a "research article only" filter should use.
  (e) REFERENCE COUNT. len(reference_ids): references within the Dimensions index, as
      OpenAlex's was references within its snapshot. Different snapshots, do not compare.


================================================================================
5. WHAT WAS NOT TOUCHED
================================================================================
  paper_citation        the vectorised bincount over (citer_year - cited_year)
  paper_disruption      compute_numba(): CD, F/E/G, ni/nj/nk
  paper_sb              _sb_one() and sb_paper()
  paper_z_score         atypicality_mag(): Uzzi shuffle, cell-wide donor pool, per-year
                        seeding -- and its five validation tests
  paper_hit_probability add_percentile(): rank(pct=True, method='min')
  paper_citation_trend  the p2p unique-key trick
  (paper_metadata, paper_author and references_w_year are data-layer notebooks and are new.)


================================================================================
6. RUN ORDER
================================================================================
  cd '/project/jevans/Dawoon/Science of Science/jobs/Dimensions'
  ./submit_dimensions.sh plan     # the order
  ./submit_dimensions.sh          # submit the chain with afterok dependencies

  0. references_w_year       the one pass over the dump          (RUN THIS FIRST, alone)
  1. paper_metadata          journal + FoS caches, per-publication table
  2. paper_author            consolidates cache/pub_authors
  3. paper_citation          builds cache/paper_graph.npz
  4. paper_disruption        builds cache/paper_csr.npz from it
  5. paper_sb                CSR only
  6. paper_z_score           CSR + journal cache  (1990-2000 by default; NB_Z_MODE=extended
                             for 1980-2025, NB_Z_YEARS=a:b for a slice; then
                             paper_z_score_merge promotes the partitions)
  7. paper_citation_trend    graph + patents folder
  8. paper_hit_probability   needs 1 and 3

  Smoke test (everything into a scratch folder, twelve files of the dump):
    NB_DIM_BASE=/some/scratch NB_FILE_LIMIT=12 NB_Z_YEARS=1900:2025 \
      python ../jobs/Dimensions/run_notebook.py notebook/<name>.ipynb


================================================================================
7. RESOURCES -- THIS DOES NOT RUN ON A LOGIN NODE
================================================================================
  ~155M publications; expect ~3B reference edges (articles average ~18 references
  within the index). Graph arrays ~25 GB, CSR ~30 GB, argsort peak ~60 GB. nb.sbatch
  asks for 250 GB on jevans, as the OpenAlex one does. Stage 0 is I/O: 8 processes, one
  DuckDB per file, a few hours.

  Environment: conda env /project/jevans/Dawoon/env/Curvature, and
    export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
