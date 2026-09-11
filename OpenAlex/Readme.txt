================================================================================
ADAPTING notebook/*.ipynb TO renli's OpenAlex SNAPSHOT
================================================================================
Written 2026-08-28.

The seven notebooks in notebook/ were built against MAG + SciSciNet on a Windows
drive. None of that data exists on Midway. They now read

    /project/jevans/renli_shared/OpenAlex_2026_Jan_16_Renly_parquet/     (627 GB, read-only)

instead. This file records what changed, what deliberately did NOT, and where the
two data sources are not the same thing wearing different names.


================================================================================
0. THE SHORT VERSION
================================================================================
  * A new module, oa_common.py, supplies everything the notebooks used to read off
    E:/ — the citation graph, publication years, journal names, fields of study.
  * Every metric kernel is BYTE-IDENTICAL to what it was. The numba disruption
    engine, the sleeping-beauty kernel, the Uzzi shuffle, the vectorised citation
    counts, the DuckDB percentile logic: untouched. Only the data layer moved.
  * That was possible because an OpenAlex work id is `W` + digits (largest here
    ~7.1e9), so int(id[1:]) round-trips through int64. The notebooks' entire
    code-space design — a sorted `uni_mag`, searchsorted to map id -> code,
    'W' + str(code) to map back — keeps working with the accession number standing
    in for the MAG integer. No algorithm was rewritten to accommodate string ids.
  * Three things are NOT equivalent and are called out in section 4: field of
    study, journal-type, and reference count.


================================================================================
1. INPUT MAPPING
================================================================================
  WAS (MAG / SciSciNet, Windows)              IS NOW (renli OpenAlex)
  ------------------------------------------  -----------------------------------------
  E:/…/MAG/mag/PaperReferences.txt            works/referenced_works/part_*.parquet
    citing <TAB> cited, ~1.8B                   work_id, referenced_work_id
                                                1,334 parts, ~2.2B edges

  E:/…/paper_metadata.sqlite                  works/works/part_*.parquet
    papers(paper_id, year, journal_id,          id, publication_year, type,
           is_journal)                          cited_by_count, is_retracted
                                                + works/primary_locations (source_id)

  E:/…/MAG/mag/Journals.txt                   sources.csv.gz
    JournalId -> DisplayName                    id, display_name, type, issn_l

  Data/SciSciNet_v2/                          works/topics + topics.csv.gz
    sciscinet_papers_fos.parquet                work_id, topic_id, score
    paperid, FoS_0, FoS_rep                     + field_display_name, domain_display_name

  E:/…/PaperAuthorAffiliations.txt            works_au_affs_fixed.csv.gz
    PaperId, AuthorId, seq  (51 GB)             work_id, author_id, author_position_int
                                                (38 GB gzip; off by default, as before)

  Data/Reliance on Science/pcs_oa_uspto.csv   /project/jevans/Dawoon/Drug_Data/Data/
                                              _pcs_oa.csv   (47.8M rows, same schema:
                                                reftype, oaid, patent)

  E:/…/PatentView/Granted/g_patent.tsv.zip    /project/jevans/Dawoon/PatentView/Granted/
                                                g_patent.tsv.zip        (unchanged)

  duckdb (out-of-core join engine)            pyarrow 22 — see section 4(f)

  E:/…/paper_disruption_graph.npz             OpenAlex/cache/paper_graph.npz
  E:/…/paper_disruption_csr.npz               OpenAlex/cache/paper_csr.npz
    (same array names: c_from, c_to, year, uni_mag / out_ptr, out_idx, in_ptr, in_idx)

  notebook/paper/output/                      OpenAlex/output/
                                                (moved 2026-08-28; every notebook takes it
                                                 from oa.OUT, so one definition drives all
                                                 seven)


================================================================================
1b. THE CONSOLIDATED EDGE TABLE (added 2026-08-28)
================================================================================
notebook/referenced_works_w_year.ipynb now sits in front of everything else. It
walks renli's tree ONCE and writes two artefacts that the rest of the pipeline
reads instead:

  cache/work_year_source_map.npz     one row per work
      code   sorted int64 accession (W3002427681 -> 3002427681)
      year   int16, -1 where publication_year is null or impossible
      source int64 source accession, -1 where the work has no location
      -> ~396M works, ~7 GB. primary_locations first, locations only to fill
         its 0.17% gap, so each work has at most one source and the rule is
         deterministic.

  output/referenced_works_w_year/    one row per edge, 1,334 partitions
      work_id, work_year, work_id_source_id,
      referenced_work_id, referenced_work_year, referenced_work_id_source_id
      -> ~1.78B edges. Both endpoints dated AND placed.

WHY. Three separate things used to be rebuilt per notebook: the year lookup, the
journal lookup, and the citation graph. Each walked 1,334 partitions. They are
now one pass, and the result is a table you can filter and join without loading
40 GB of npz.

WHAT CHANGED DOWNSTREAM. Nothing in the notebooks' interfaces:

  oa.load_graph()    reads the edge table (falls back to the old two-pass walk
                     if it has not been built)
  oa.load_csr()      unchanged, built from whatever load_graph returns
  oa.build_journal() reads the map's `source` column instead of re-walking
                     primary_locations/
  paper_metadata     ref_count is a value_counts on the edge table

  The numba disruption engine, the SB kernel and the Uzzi shuffle are still
  untouched. So is the code space: the edge table's ids go through the same
  int(id[1:]) codec on the way in.

ONE THING THE EDGE TABLE MAKES CHEAPER THAN IT WAS. paper_z_score needs the
JOURNAL PAIR of every reference, and used to assemble it from the CSR plus a
separate journal lookup. Both source ids are columns now.

A NOTE ON NULLS. work_year / referenced_work_year are int16 with real nulls, not
zeros. Casting a NaN to int16 with safe=False silently yields 0, which would be
recorded as "published in year zero" and make every citation age wrong by the
publication year; the writer builds the values and the null mask separately to
avoid exactly that.


================================================================================
2. THE NEW MODULE — oa_common.py
================================================================================
Imported by every notebook as `oa`. Paths in one place; nothing else duplicated.

  oa.build_graph()    works/works (years) then works/referenced_works (edges), into
                      cache/paper_graph.npz with the array names the notebooks
                      already load. Replaces the PaperReferences.txt scan AND the
                      sqlite year lookup in one pass.
                      NOTE: it loads EVERY partition's years before touching any
                      edges. An edge survives only if both endpoints are known
                      works, so a partial year pass silently drops most edges.

  oa.build_csr()      out/in adjacency, same shape as the old cache.
  oa.load_graph()     -> c_from, c_to, year, uni_mag        (builds on first call)
  oa.load_csr()       -> out_ptr, out_idx, in_ptr, in_idx, year, uni_mag

  oa.build_journal()  work -> journal name + is_journal, from primary_locations x
                      sources.csv.gz. Replaces Journals.txt + sqlite.
  oa.build_fos()      work -> FoS_rep / FoS_0 / domain, from works/topics x
                      topics.csv.gz. Replaces sciscinet_papers_fos.parquet.

  oa.norm_id(s)       strips the URL prefix — see section 3.
  oa.id_to_code(s)    'W3002427681' -> 3002427681 (int64); invalid -> -1
  oa.code_to_id(a)    the inverse; the notebooks' np.char.add('W', …) idiom kept

  oa.YEAR_RANGE       set this (e.g. (1950, 2026)) BEFORE build_graph() to cut the
                      corpus down. Everything downstream inherits the restriction.

  oa.OUT              OpenAlex/output/ -- the seven notebooks' parquet outputs
  oa.CACHE            OpenAlex/cache/  -- the derived graph/CSR/journal/FoS artefacts


================================================================================
3. A TRAP IN THE SNAPSHOT THAT COST REAL TIME
================================================================================
Work ids come in TWO forms in this snapshot:

    works, ids, topics, referenced_works, primary_locations, …   W3002427681
    works_semantic, works_au_affs_fixed, works_authorships       https://openalex.org/W3002427681

A join across the two returns ZERO ROWS and raises nothing. `oa.norm_id()` is
applied on every read in oa_common.py; if you add a reader, apply it there too.

Also: works names its key `id`; the other thirteen work datasets name it `work_id`.

Also: the 14 work datasets are PARTITION-ALIGNED — part_NNNN holds the same works
everywhere — so a part-by-part join needs no shuffle. paper_metadata exploits this
by zipping works/works with works/referenced_works partition for partition.

(All three established in ../explore_openalex_2026_renli.ipynb.)


================================================================================
4. WHERE THE TWO DATA SOURCES ARE NOT THE SAME THING
================================================================================
These are substantive, not cosmetic. Results will differ from the MAG runs.

  (a) FIELD OF STUDY.
      MAG had a level-0 Field of Study (19 of them). OpenAlex has a topic
      hierarchy: ~4,500 topics -> 252 subfields -> 26 FIELDS -> 4 domains. The
      closest analogue is the FIELD, so:
          FoS_rep = field of the work's highest-scoring topic
          FoS_0   = ';'-joined distinct fields of all its topics
          domain  = the domain of the top topic (new column, no MAG twin)
      The label set differs from MAG's. paper_hit_probability cohorts on
      (FoS_rep, year), so its cohorts are OpenAlex fields now — the metric is
      unchanged, the partition it is computed within is not.

  (b) JOURNAL-TYPE.
      MAG had DocType == 'Journal' and an is_journal flag in sqlite. Here it is
      sources.type == 'journal' (206,115 of 255,250 sources) attached through
      works/primary_locations. paper_z_score selects focal papers with it.
      A work with no primary location gets is_journal = False and is excluded,
      as an unjournalled MAG paper was.

  (c) REFERENCE COUNT.
      SciSciNet shipped reference_count as a column. OpenAlex works does not, so
      paper_metadata COUNTS rows in works/referenced_works per work. This is the
      reference count *within the snapshot* — references to works OpenAlex does
      not have are not counted. SciSciNet's number was also snapshot-bounded, but
      to a different snapshot; do not compare the two directly.

  (d) COVERAGE.
      MAG stopped in 2021. This snapshot runs to 2026 and holds ~396M works
      against MAG's ~250M, including datasets, preprints and dissertations that
      MAG typed differently or not at all. `doctype` is now the OpenAlex `type`
      vocabulary (article, dataset, other, book-chapter, dissertation, …), which
      is NOT MAG's DocType vocabulary.

  (f) NO DUCKDB IN THIS ENVIRONMENT.
      paper_metadata and paper_hit_probability both used duckdb for their
      out-of-core joins. It is not installed in env/Curvature and is not in any
      other env here, and installing into a shared env is not this notebook's
      business. Both were rewritten:
        paper_metadata        joins partition by partition (the datasets are
                              partition-aligned, so this is a local join)
        paper_hit_probability pyarrow Table.join, then percentiles computed one
                              FIELD at a time so peak memory is bounded by the
                              largest field rather than by the corpus
      The percentile itself is untouched: rank(pct=True, method='min') within
      (FoS, year), exactly as before.

  (e) PUBLICATION YEAR is dirty: the snapshot spans 1010–2050 with ~0.6% null.
      oa_common clamps to YEAR_MIN=1800 / YEAR_MAX=2026 when building the graph.


================================================================================
5. WHAT WAS NOT TOUCHED
================================================================================
Every formula and every kernel. Specifically:

  paper_citation        the vectorised bincount over (citer_year - cited_year)
  paper_disruption      compute_numba(): CD, F/E/G, ni/nj/nk — not one character
  paper_sb              _sb_one() and sb_paper(): Ke et al. Beauty coefficient
  paper_z_score         atypicality_from_csr(): Uzzi shuffle, year-preserving null
  paper_hit_probability add_percentile(): rank(pct=True, method='min')
  paper_citation_trend  the p2p unique-key trick and the PCS examiner split

If a number looks wrong, the cause is in the data layer or in section 4, not in
the metric.


================================================================================
6. RUN ORDER
================================================================================
  0. referenced_works_w_year builds cache/work_year_source_map.npz and
                             output/referenced_works_w_year/   (RUN THIS FIRST)
  1. paper_metadata          builds cache/paper_journal.parquet + paper_fos.parquet
  2. paper_citation          builds cache/paper_graph.npz   (now from the edge table)
  3. paper_disruption        builds cache/paper_csr.npz from it
  4. paper_sb                CSR only
  5. paper_z_score           CSR + journal cache
  6. paper_citation_trend    graph + PCS
  7. paper_hit_probability   needs 1 and 2 done

Steps 2 and 3 are the ones that cost; everything after them loads a cache.


================================================================================
7. RESOURCES — THIS DOES NOT RUN ON A LOGIN NODE
================================================================================
Full snapshot, no YEAR_RANGE:

    uni_mag   396M x int64                    ~3.2 GB
    year      396M x int32                    ~1.6 GB
    edges     ~2.2B x 2 x int32              ~17.6 GB
    CSR       idx again + ptr 396M x int64   ~21.0 GB
    peak during the argsort in build_csr()   ~40-50 GB

So: submit it. `amd` (250 GB) or `bigmem` (768 GB) fit comfortably; caslake
(184 GB) fits if you do not hold graph and CSR at once. The Midway3 login-node
watchdog SIGKILLs jobs this size with no traceback — a fast way to lose an hour.

Setting oa.YEAR_RANGE = (1950, 2026) before build_graph() cuts this substantially
and is the right first move if you only need the modern literature.

Environment: conda env /project/jevans/Dawoon/env/Curvature, and
    export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
the ENV's libstdc++, not /software/gcc-12.2.0-el8-x86_64/lib64 — that one stops at
CXXABI_1.3.13 and breaks matplotlib while fixing pandas.


================================================================================
8. STILL OPEN
================================================================================
  * None of the seven has been run to completion on the full snapshot. What IS
    tested: the id codec round-trips both id forms; sources.csv.gz reads and
    types resolve (206,115 journals of 255,250 sources); a 2-partition graph and
    CSR build end to end; and the first cell of all seven notebooks executes.
    End-to-end cost has not been measured.
  * author_list (paper_metadata, RUN_AUTHORS=True) is written but untested — it
    scans a 38 GB gzip that cannot be seeked or parallelised.
  * paper_citation_trend maps PCS `oaid` to a work by assuming it is the MAG/
    OpenAlex integer. Verify that against this snapshot before trusting pat2p.
  * works_authorships.csv.gz is only 47.8 MB against works_au_affs_fixed.csv.gz's
    38 GB. It looks partial; prefer the latter.
