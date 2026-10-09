"""Column descriptions for the derived-table inventory of the metrics dashboard.

`describe(path, column)` returns the meaning of one column of one inventoried table (`path` relative to the
Science of Science root, as in data/inventory.json); `is_personal(path, column)` says whether its values carry
people's names, in which case the page describes the column but shows no example value. SHARED holds a
description that reads the same in every table with that column; TABLES holds table-specific ones and wins over
SHARED. Backticked spans render as code on the page.

Written 2026-10-03 from the producing notebooks and *_common.py modules. When a pipeline adds or changes a column,
edit it here: refresh_dashboard.py prints every inventoried column that has no description, and the page shows
'Not described yet.' for it.
"""

from __future__ import annotations

SHARED = {
    'appln_kind': ('Application kind code (tls201.appln_kind, trimmed): A = patent application (about '
                   '91 % of rows), W = PCT application in the international phase, T = filing that '
                   'translates or validates an EP / PCT application at some offices; D and the rare '
                   'remaining codes as defined in the PATSTAT Data Catalog.'),
    'appln_nr': ('Application number assigned by the filing office, as stored in tls201.appln_nr (a '
                 "string in DOCDB format, e.g. '515678'); read it together with appln_auth and "
                 'appln_kind.'),
    'C_applicant': ("The 'applicant' part of C in this year (citn_origin APP: references submitted by "
                    'the applicant); C = C_examiner + C_applicant + C_other.'),
    'C_other': ("The 'other' part of C in this year (citn_origin OPP, APL or blank: "
                'opposition-division and appeal citations); C = C_examiner + C_applicant + C_other.'),
    'CD': ('Disruption index (ni - nj) / (ni + nj + nk) on the cumulative counts, i.e. CD with a '
           'window of exactly this age; in [-1, 1], never NaN on a written row.'),
    'cited_publn_id': ('tls211 pat_publn_id of the cited publication (tls212.cited_pat_publn_id); 0 '
                       "exactly when the citation names an application instead (resolved = 'appln')."),
    'citing_publn_id': ('tls211 pat_publn_id of the citing publication on which the citation is '
                        'recorded (e.g. the A1 search-report publication or the B1 grant of the citing'
                        ' application).'),
    'citn_origin': ('PATSTAT citation origin (tls212.citn_origin, trimmed): APP applicant, SEA search '
                    'report, ISR international search report, SUP supplementary search report, PRS '
                    'USPTO pre-search, EXA examination, FOP filed opposition, CH2 PCT chapter II, OPP '
                    'opposition division, APL appeal. Third-party observations (115, TPO) are excluded'
                    ' upstream.'),
    'E': ('Share of the citers arrived by this age classed Extension (up > down, plus half of the '
          'ties); NaN before the first citer. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
    'F': ('Share of the citers that have arrived by this age classed Foundation at this age (down > '
          'up, with down counted among citers of age <= this age; up = down > 0 ties count half). NaN '
          '(a float NaN, not NULL) on rows before the first citer arrives. Decomposition of Fang & '
          'Evans (2025), arXiv:2510.03240.'),
    'filing_date': 'Filing date of the application (tls201.appln_filing_date).',
    'first_inventor': 'person_id (int64) of the inventor at the lowest sequence position.',
    'G': ('Share of the citers arrived by this age classed Generalization (up = down = 0); NaN before '
          'the first citer. F + E + G = 1 when defined. Decomposition of Fang & Evans (2025), '
          'arXiv:2510.03240.'),
    'inpadoc_family_id': ('INPADOC extended-family id (tls201.inpadoc_family_id): applications linked '
                          'directly or indirectly through priorities, PCT routes, technical relations '
                          'or continuations; an integer id passed through from PATSTAT.'),
    'last_inventor': ('person_id (int64) of the inventor at the highest sequence position (equals '
                      'first_inventor for a single inventor).'),
    'nb_applicants': ("PATSTAT's count of applicants on the most recent publication carrying "
                      'Latin-script names (tls201.nb_applicants); 0 when none does, so it can disagree'
                      ' with applicant_list.'),
    'nb_inventors': ("PATSTAT's count of inventors on the most recent publication carrying "
                     'Latin-script names (tls201.nb_inventors); 0 when none does, so it can disagree '
                     'with inventor_list and patstat_inventor.n_inventors.'),
    'nj': ("Cumulative nj from age 0 through this row's age (equals nj_w of patstat_disruption at age "
           'w).'),
    'nk': ("Cumulative nk from age 0 through this row's age (equals nk_w of patstat_disruption at age "
           'w).'),
    'publn_year': ("Year of the application's earliest publication (tls201.earliest_publn_year); NULL "
                   'where PATSTAT has 9999 (no dated publication).'),
    'resolved': ("How the cited end was resolved: 'publn' = via tls212.cited_pat_publn_id -> tls211 ->"
                 " appln_id; 'appln' = via tls212.cited_appln_id directly (about 0.15 % of rows in the"
                 ' filing set).'),
}

TABLES = {
    'OpenAlex/output/paper_author.parquet': {
        'work_id': ("OpenAlex work id ('W' + digits, URL prefix stripped); the same values as paper_id"
                    ' in the sibling tables, under a different column name. One row per work with at '
                    'least one author id in works/authorships (292.4M works).'),
        'author_list': ("';'-joined OpenAlex author ids (opaque 'A' + digits) in byline order "
                        '(author_position_int, ties broken by author id), each author listed once even'
                        ' when the source repeats them per affiliation.'),
        'team_size': 'Number of distinct author ids on the work (= number of entries in author_list).',
        'first_author': ("OpenAlex author id ('A' + digits) at the lowest author position (first entry"
                         ' of author_list).'),
        'last_author': ('OpenAlex author id at the highest author position (last entry of '
                        'author_list); equals first_author for single-author works.'),
    },
    'OpenAlex/output/paper_author_country.parquet': {
        'paper_id': ("OpenAlex work id as a string: 'W' followed by digits (e.g. W3002427681), URL "
                     'prefix stripped; joins every other OpenAlex/output table. Same 292.4M works as '
                     'paper_author (which calls the column work_id).'),
        'team_size': ('Number of distinct authors (author ids) on the work; identical to '
                      'paper_author.team_size on every row.'),
        'n_located': ("Number of the work's authors with at least one country code (OpenAlex's "
                      "per-authorship 'countries', i.e. the countries of the institutions their "
                      'affiliations were matched to). 0 when no author is located.'),
        'countries': ("Sorted, ';'-joined distinct ISO 3166-1 alpha-2 codes over all located authors "
                      "(e.g. 'CN;US'); null when no author is located (53.5% of works). Namibia is 'NA',"
                      ' not a missing value. Coverage rises strongly over time, so take shares over '
                      'located works.'),
        'n_countries': 'Number of distinct codes in countries; 0 when countries is null.',
        'country_author_counts': ("Located authors per country as 'CC:n' items joined by ';', ordered "
                                  "by count descending then code (e.g. 'US:3;CN:1'). An author with "
                                  'two countries counts in both, so the counts can sum to more than '
                                  'n_located; null when no author is located.'),
        'first_author_country': ("';'-joined sorted country codes of the first author (lowest "
                                 'author_position_int, ties by numeric author id); can hold several '
                                 'codes. Null when that author has no country (not replaced by the '
                                 'next located author).'),
        'last_author_country': ("';'-joined sorted country codes of the last author (highest "
                                'author_position_int); null when that author has no country.'),
        'is_international': ("True when the work's authors span more than one country (n_countries > "
                             '1).'),
    },
    'OpenAlex/output/paper_citation.parquet': {
        'paper_id': ("OpenAlex work id as a string: 'W' followed by digits (e.g. W3002427681), URL "
                     'prefix stripped; joins every other OpenAlex/output table. One row per work with '
                     'a usable publication year (460.5M), cited or not.'),
        'C_3': ('Number of citations received within 3 years of publication, publication year counted '
                'as year 0: incoming reference edges from OpenAlex works with 0 <= citing year - cited'
                ' year <= 3 (calendar years), over the OpenAlex works/referenced_works graph '
                '(2026-09-23 release), edges kept when both ends have a publication year in '
                '1000-2030. 0 for uncited documents; cohorts less than 3 years before the snapshot are'
                ' right-truncated.'),
        'C_5': ('Number of citations received within 5 years of publication, publication year counted '
                'as year 0: incoming reference edges from OpenAlex works with 0 <= citing year - cited'
                ' year <= 5 (calendar years), over the OpenAlex works/referenced_works graph '
                '(2026-09-23 release), edges kept when both ends have a publication year in '
                '1000-2030. 0 for uncited documents; cohorts less than 5 years before the snapshot are'
                ' right-truncated.'),
        'C_10': ('Number of citations received within 10 years of publication, publication year '
                 'counted as year 0: incoming reference edges from OpenAlex works with 0 <= citing '
                 'year - cited year <= 10 (calendar years), over the OpenAlex works/referenced_works '
                 'graph (2026-09-23 release), edges kept when both ends have a publication year in '
                 '1000-2030. 0 for uncited documents; cohorts less than 10 years before the snapshot '
                 'are right-truncated.'),
        'C_all': ('Number of citations received from works published in or after the focal year '
                  '(citing year - cited year >= 0, no upper bound), over the OpenAlex '
                  'works/referenced_works graph (2026-09-23 release), edges kept when both ends have '
                  'a publication year in 1000-2030. Citations from works dated earlier than the focal '
                  'document are dropped. 0 for uncited documents.'),
    },
    'OpenAlex/output/paper_citation_trend.parquet': {
        'paper_id': ("OpenAlex work id as a string: 'W' followed by digits (e.g. W3002427681), URL "
                     'prefix stripped; joins every other OpenAlex/output table. Identifies the cited '
                     'paper. Sparse panel: one row per (paper, citing year) with at least one citation'
                     ' of any channel; a missing year means zero, a never-cited paper is absent.'),
        'pub_year': ('Publication year of the cited paper as dated in the citation graph (OpenAlex '
                     'publication_year, kept when within 1000-2030; a few implausible pre-1800 years '
                     'remain).'),
        'cite_year': ("Calendar year of the row's citations: the citing work's publication year for "
                      "p2p, the citing patent's grant year (PatentsView g_patent patent_date) for "
                      'pat2p_*. Rows with cite_year < pub_year are dropped; 2026 is a partial year.'),
        'yrs_since_pub': 'cite_year - pub_year in years (>= 0; 0 = the publication year).',
        'p2p': ('Number of OpenAlex works published in cite_year that cite this paper (incoming '
                'reference edges of the OpenAlex graph); 0 on rows that exist only for a patent '
                'citation.'),
        'pat2p_examiner': ('Number of US patent-to-paper citations (Reliance on Science / PCS links) '
                           "whose reftype is 'exm' (examiner-added), dated by the citing patent's "
                           'grant year. Effectively empty: only a few hundred such citations exist in '
                           'the whole file, so use the sum of the two pat2p columns as total patent '
                           'citations.'),
        'pat2p_non_examiner': ('Number of US patent-to-paper citations (Reliance on Science / PCS '
                               "links) of any other reftype (overwhelmingly applicant 'app'), dated by"
                               ' grant year; only links whose patent number matches a PatentsView '
                               'grant are counted, no confidence-score floor.'),
    },
    'OpenAlex/output/paper_disruption.parquet': {
        'paper_id': ("OpenAlex work id as a string: 'W' followed by digits (e.g. W3002427681), URL "
                     'prefix stripped; joins every other OpenAlex/output table. One row per work with '
                     'a usable publication year (460.5M), same rows as paper_citation.'),
        'CD_3': ("Funk & Owen-Smith CD (disruption) index for window '3': (ni - nj) / (ni + nj + nk), "
                 'counting only papers with 0 <= year(citer) - year(focal) <= 3, publication year '
                 'counted as year 0. Nominal range [-1, 1] (+1 disruptive, -1 consolidating). Null '
                 'when the paper has no citers at all, or when neither a citer nor a paper citing its '
                 'references falls in the window; 0 (not null) when the window has no citer but has '
                 'papers citing the focal references. Self-citation edges are dropped from the graph, so CD stays within [-1, 1].'),
        'F_3': ("Foundation share (0-1) for window '3': fraction of the focal paper's in-window citers"
                " whose own references include more of the focal paper's other in-window citers than "
                'of its references (down > up); ties with up = down > 0 count 1/2 here and 1/2 in E. F'
                ' + E + G = 1. Null when the window has no citer. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'E_3': ("Extension share (0-1) for window '3': fraction of in-window citers that cite more of "
                "the focal paper's references than of its other in-window citers (up > down), plus "
                'half of the ties. Null when the window has no citer. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'G_3': ("Generalization share (0-1) for window '3': fraction of in-window citers that cite "
                "neither any of the focal paper's references nor any of its other in-window citers (up"
                ' = down = 0). Null when the window has no citer. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'ni_3': ("Count of citers in window '3' (0 <= year(citer) - year(focal) <= 3, publication year"
                 " counted as year 0) that cite none of the focal paper's references. -1 is a "
                 'sentinel: the paper has no citers at all, or the window holds neither a citer nor a '
                 'paper citing its references.'),
        'nj_3': ("Count of citers in window '3' that also cite at least one of the focal paper's "
                 'references. -1 sentinel as for ni.'),
        'nk_3': ("Count of papers (other than the focal one) published in window '3' (0 <= year(citer)"
                 ' - year(focal) <= 3, publication year counted as year 0) that cite at least one of '
                 "the focal paper's references but not the focal paper itself. -1 sentinel as for ni. "
                 'Self-citation edges are dropped from the graph, so -1 is only ever the sentinel.'),
        'CD_5': ("Funk & Owen-Smith CD (disruption) index for window '5': (ni - nj) / (ni + nj + nk), "
                 'counting only papers with 0 <= year(citer) - year(focal) <= 5, publication year '
                 'counted as year 0. Nominal range [-1, 1] (+1 disruptive, -1 consolidating). Null '
                 'when the paper has no citers at all, or when neither a citer nor a paper citing its '
                 'references falls in the window; 0 (not null) when the window has no citer but has '
                 'papers citing the focal references. Self-citation edges are dropped from the graph, so CD stays within [-1, 1].'),
        'F_5': ("Foundation share (0-1) for window '5': fraction of the focal paper's in-window citers"
                " whose own references include more of the focal paper's other in-window citers than "
                'of its references (down > up); ties with up = down > 0 count 1/2 here and 1/2 in E. F'
                ' + E + G = 1. Null when the window has no citer. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'E_5': ("Extension share (0-1) for window '5': fraction of in-window citers that cite more of "
                "the focal paper's references than of its other in-window citers (up > down), plus "
                'half of the ties. Null when the window has no citer. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'G_5': ("Generalization share (0-1) for window '5': fraction of in-window citers that cite "
                "neither any of the focal paper's references nor any of its other in-window citers (up"
                ' = down = 0). Null when the window has no citer. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'ni_5': ("Count of citers in window '5' (0 <= year(citer) - year(focal) <= 5, publication year"
                 " counted as year 0) that cite none of the focal paper's references. -1 is a "
                 'sentinel: the paper has no citers at all, or the window holds neither a citer nor a '
                 'paper citing its references.'),
        'nj_5': ("Count of citers in window '5' that also cite at least one of the focal paper's "
                 'references. -1 sentinel as for ni.'),
        'nk_5': ("Count of papers (other than the focal one) published in window '5' (0 <= year(citer)"
                 ' - year(focal) <= 5, publication year counted as year 0) that cite at least one of '
                 "the focal paper's references but not the focal paper itself. -1 sentinel as for ni. "
                 'Self-citation edges are dropped from the graph, so -1 is only ever the sentinel.'),
        'CD_10': ("Funk & Owen-Smith CD (disruption) index for window '10': (ni - nj) / (ni + nj + "
                  'nk), counting only papers with 0 <= year(citer) - year(focal) <= 10, publication '
                  'year counted as year 0. Nominal range [-1, 1] (+1 disruptive, -1 consolidating). '
                  'Null when the paper has no citers at all, or when neither a citer nor a paper '
                  'citing its references falls in the window; 0 (not null) when the window has no '
                  'citer but has papers citing the focal references. Self-citation edges are dropped from the graph, so CD stays within [-1, 1].'),
        'F_10': ("Foundation share (0-1) for window '10': fraction of the focal paper's in-window "
                 "citers whose own references include more of the focal paper's other in-window citers"
                 ' than of its references (down > up); ties with up = down > 0 count 1/2 here and 1/2 '
                 'in E. F + E + G = 1. Null when the window has no citer. Decomposition of Fang & '
                 'Evans (2025), arXiv:2510.03240.'),
        'E_10': ("Extension share (0-1) for window '10': fraction of in-window citers that cite more "
                 "of the focal paper's references than of its other in-window citers (up > down), plus"
                 ' half of the ties. Null when the window has no citer. Decomposition of Fang & Evans '
                 '(2025), arXiv:2510.03240.'),
        'G_10': ("Generalization share (0-1) for window '10': fraction of in-window citers that cite "
                 "neither any of the focal paper's references nor any of its other in-window citers "
                 '(up = down = 0). Null when the window has no citer. Decomposition of Fang & Evans '
                 '(2025), arXiv:2510.03240.'),
        'ni_10': ("Count of citers in window '10' (0 <= year(citer) - year(focal) <= 10, publication "
                  "year counted as year 0) that cite none of the focal paper's references. -1 is a "
                  'sentinel: the paper has no citers at all, or the window holds neither a citer nor a'
                  ' paper citing its references.'),
        'nj_10': ("Count of citers in window '10' that also cite at least one of the focal paper's "
                  'references. -1 sentinel as for ni.'),
        'nk_10': ("Count of papers (other than the focal one) published in window '10' (0 <= "
                  'year(citer) - year(focal) <= 10, publication year counted as year 0) that cite at '
                  "least one of the focal paper's references but not the focal paper itself. -1 "
                  'sentinel as for ni. Self-citation edges are dropped from the graph, so -1 is only ever the sentinel.'),
        'CD_all': ("Funk & Owen-Smith CD (disruption) index for window 'all': (ni - nj) / (ni + nj + "
                   'nk), counting only papers with year(citer) - year(focal) >= 0, no upper bound. '
                   'Nominal range [-1, 1] (+1 disruptive, -1 consolidating). Null when the paper has '
                   'no citers at all, or when neither a citer nor a paper citing its references falls '
                   'in the window; 0 (not null) when the window has no citer but has papers citing the'
                   ' focal references. Self-citation edges are dropped from the graph, so CD stays within [-1, 1].'),
        'F_all': ("Foundation share (0-1) for window 'all': fraction of the focal paper's in-window "
                  "citers whose own references include more of the focal paper's other in-window "
                  'citers than of its references (down > up); ties with up = down > 0 count 1/2 here '
                  'and 1/2 in E. F + E + G = 1. Null when the window has no citer. Decomposition of '
                  'Fang & Evans (2025), arXiv:2510.03240.'),
        'E_all': ("Extension share (0-1) for window 'all': fraction of in-window citers that cite more"
                  " of the focal paper's references than of its other in-window citers (up > down), "
                  'plus half of the ties. Null when the window has no citer. Decomposition of Fang & '
                  'Evans (2025), arXiv:2510.03240.'),
        'G_all': ("Generalization share (0-1) for window 'all': fraction of in-window citers that cite"
                  " neither any of the focal paper's references nor any of its other in-window citers "
                  '(up = down = 0). Null when the window has no citer. Decomposition of Fang & Evans '
                  '(2025), arXiv:2510.03240.'),
        'ni_all': ("Count of citers in window 'all' (year(citer) - year(focal) >= 0, no upper bound) "
                   "that cite none of the focal paper's references. -1 is a sentinel: the paper has no"
                   ' citers at all, or the window holds neither a citer nor a paper citing its '
                   'references.'),
        'nj_all': ("Count of citers in window 'all' that also cite at least one of the focal paper's "
                   'references. -1 sentinel as for ni.'),
        'nk_all': ("Count of papers (other than the focal one) published in window 'all' (year(citer) "
                   "- year(focal) >= 0, no upper bound) that cite at least one of the focal paper's "
                   'references but not the focal paper itself. -1 sentinel as for ni. Self-citation edges are dropped from the graph, so -1 is only ever the sentinel.'),
        'pctl_year': ('Cohort year for the CD percentiles: paper_metadata.year (publication year, '
                      'stored as a double); present on every row.'),
        'pctl_group': ('Cohort field for the CD percentiles: the first field listed in '
                       "paper_metadata.FoS_0, i.e. the OpenAlex field of the work's top-scoring topic "
                       '(= FoS_rep). Null when the work has no topic (about 21%), and then every '
                       'CD_*_pctl is null.'),
        'CD_3_pctl': ('Minimum-rank percentile (0-1] of CD_3 within its (pctl_year, pctl_group) cohort'
                      ' among papers with a non-null CD_3: rank() / n, ties share the lowest rank. '
                      'Null when CD_3 or pctl_group is null. CD has large tie blocks (e.g. CD = 1), so'
                      ' use CD_3_pctl_cume for top-x% thresholds.'),
        'CD_3_pctl_cume': ('Cumulative share (0-1] of the same cohort with CD_3 at or below this '
                           "paper's value (ties inclusive, like cume_dist); always >= CD_3_pctl. The "
                           "column to threshold for 'top x% most disruptive'. Null when CD_3 or "
                           'pctl_group is null.'),
        'CD_5_pctl': ('Minimum-rank percentile (0-1] of CD_5 within its (pctl_year, pctl_group) cohort'
                      ' among papers with a non-null CD_5: rank() / n, ties share the lowest rank. '
                      'Null when CD_5 or pctl_group is null. CD has large tie blocks (e.g. CD = 1), so'
                      ' use CD_5_pctl_cume for top-x% thresholds.'),
        'CD_5_pctl_cume': ('Cumulative share (0-1] of the same cohort with CD_5 at or below this '
                           "paper's value (ties inclusive, like cume_dist); always >= CD_5_pctl. The "
                           "column to threshold for 'top x% most disruptive'. Null when CD_5 or "
                           'pctl_group is null.'),
        'CD_10_pctl': ('Minimum-rank percentile (0-1] of CD_10 within its (pctl_year, pctl_group) '
                       'cohort among papers with a non-null CD_10: rank() / n, ties share the lowest '
                       'rank. Null when CD_10 or pctl_group is null. CD has large tie blocks (e.g. CD '
                       '= 1), so use CD_10_pctl_cume for top-x% thresholds.'),
        'CD_10_pctl_cume': ('Cumulative share (0-1] of the same cohort with CD_10 at or below this '
                            "paper's value (ties inclusive, like cume_dist); always >= CD_10_pctl. The"
                            " column to threshold for 'top x% most disruptive'. Null when CD_10 or "
                            'pctl_group is null.'),
        'CD_all_pctl': ('Minimum-rank percentile (0-1] of CD_all within its (pctl_year, pctl_group) '
                        'cohort among papers with a non-null CD_all: rank() / n, ties share the lowest'
                        ' rank. Null when CD_all or pctl_group is null. CD has large tie blocks (e.g. '
                        'CD = 1), so use CD_all_pctl_cume for top-x% thresholds.'),
        'CD_all_pctl_cume': ('Cumulative share (0-1] of the same cohort with CD_all at or below this '
                             "paper's value (ties inclusive, like cume_dist); always >= CD_all_pctl. "
                             "The column to threshold for 'top x% most disruptive'. Null when CD_all "
                             'or pctl_group is null.'),
    },
    'OpenAlex/output/paper_hit_probability.parquet': {
        'paper_id': ("OpenAlex work id as a string: 'W' followed by digits (e.g. W3002427681), URL "
                     'prefix stripped; joins every other OpenAlex/output table. Only works that have '
                     'both a field (topic) and a publication year (364.3M).'),
        'FoS': ("Cohort field: OpenAlex field name (one of 26, e.g. 'Medicine') of the work's "
                'highest-scoring topic (paper_metadata.FoS_rep, else the first entry of FoS_0). Not '
                'comparable with Dimensions FoR divisions.'),
        'year': ("Cohort year: the work's publication year (paper_metadata.year cast to integer; "
                 '1000-2030 in the file).'),
        'pctl_c3': ("Percentile (0-1] of the document's C_3 (paper_citation) within its (FoS, year) "
                    "cohort: pandas rank(pct=True, method='min') = (number of cohort members with "
                    'strictly fewer citations + 1) / cohort size. Uncited documents share the lowest '
                    'value (1/cohort size); pctl >= 0.99 marks roughly the top 1%.'),
        'pctl_c5': ("Percentile (0-1] of the document's C_5 (paper_citation) within its (FoS, year) "
                    "cohort: pandas rank(pct=True, method='min') = (number of cohort members with "
                    'strictly fewer citations + 1) / cohort size. Uncited documents share the lowest '
                    'value (1/cohort size); pctl >= 0.99 marks roughly the top 1%.'),
        'pctl_c10': ("Percentile (0-1] of the document's C_10 (paper_citation) within its (FoS, year) "
                     "cohort: pandas rank(pct=True, method='min') = (number of cohort members with "
                     'strictly fewer citations + 1) / cohort size. Uncited documents share the lowest '
                     'value (1/cohort size); pctl >= 0.99 marks roughly the top 1%.'),
        'pctl_call': ("Percentile (0-1] of the document's C_all (paper_citation) within its (FoS, "
                      "year) cohort: pandas rank(pct=True, method='min') = (number of cohort members "
                      'with strictly fewer citations + 1) / cohort size. Uncited documents share the '
                      'lowest value (1/cohort size); pctl >= 0.99 marks roughly the top 1%.'),
    },
    'OpenAlex/output/paper_metadata.parquet': {
        'paper_id': ("OpenAlex work id as a string: 'W' followed by digits (e.g. W3002427681), URL "
                     'prefix stripped; joins every other OpenAlex/output table. One row per work of '
                     'works/works in the 2026-09-23 release (476.2M), in partition order.'),
        'year': ('OpenAlex publication_year stored as float64 (null for 3.3% of works). Raw value, not'
                 ' range checked (1007-2050 in the file); the graph-based tables only keep works dated'
                 ' 1000-2030.'),
        'doctype': ('OpenAlex work type (article, other, dataset, book-chapter, dissertation, '
                    'preprint, book, review, paratext, letter, report, editorial, erratum, retraction,'
                    ' ...); not the MAG or Dimensions vocabulary.'),
        'ref_count': ('Number of references the work lists in OpenAlex works/referenced_works (its '
                      'rows in the referenced_works_w_year edge table), i.e. references to other '
                      'OpenAlex works within this snapshot; 0 when none. Not comparable with SciSciNet'
                      ' or Dimensions counts.'),
        'journal': ("Display name (sources.csv.gz) of the work's primary-location source, or of its "
                    "first location's source when there is no primary one. Any source type: journals, "
                    'repositories, conferences, ebook platforms. Null when the work has no source '
                    '(12.8%).'),
        'is_journal': ("True when that source's OpenAlex type is 'journal', False for other source "
                       'types, null when the work has no source.'),
        'author_list': ('Always null (Arrow type null): placeholder kept for schema compatibility; '
                        'author lists are in paper_author.parquet.'),
        'FoS_0': ("';'-joined distinct OpenAlex field names (26 fields) of all the work's scored "
                  'topics (up to 3, works/topics), ordered by topic score, best first; equals '
                  "';'.join(field). Null when the work has no topic (20.6%)."),
        'FoS_rep': ("OpenAlex field name of the work's highest-scoring topic (e.g. 'Materials "
                    "Science'); the cohort key of paper_hit_probability. Null when no topic."),
        'domain': ('OpenAlex domain (Health Sciences, Life Sciences, Physical Sciences or Social '
                   "Sciences) of the work's highest-scoring topic; null when no topic. No Dimensions "
                   'twin.'),
        'primary_topic_field': ("Field name of OpenAlex's own primary topic "
                                '(works_semantic.primary_topic_json); null when the work has none. '
                                'Equal to FoS_rep wherever both exist.'),
        'primary_topic_subfield': ('Subfield name (OpenAlex topic hierarchy, about 250 subfields) of '
                                   'the primary topic; null when none.'),
        'primary_topic_topic': ('Display name of the primary topic (about 4,500 OpenAlex topics), '
                                'looked up in topics.csv.gz by topic id; null when none.'),
        'field': ("List of the distinct field names of all the work's scored topics (1-3), best topic "
                  'score first; null (not an empty list) when the work has no topic.'),
        'subfield': ("List of the distinct subfield names of all the work's topics, best score first; "
                     'de-duplicated by name (8 names are shared by two subfields and collapse to one '
                     'entry); null when no topic.'),
        'topic': ("List of all the work's topic names, one per scored topic (1-3), best score first; "
                  'topic[0] equals primary_topic_topic. Null when no topic. Topic ids and scores are '
                  'in paper_topics.parquet.'),
        'cited_by_count': ("OpenAlex's own cited_by_count at snapshot time (all of OpenAlex); not the "
                           'graph-derived, year-filtered C_all of paper_citation.'),
        'is_retracted': 'OpenAlex is_retracted flag; null for 0.35% of works.',
    },
    'OpenAlex/output/paper_sb.parquet': {
        'paper_id': ("OpenAlex work id as a string: 'W' followed by digits (e.g. W3002427681), URL "
                     'prefix stripped; joins every other OpenAlex/output table. Only documents with at'
                     ' least one dated citation (citing year >= publication year) appear; uncited '
                     'documents are omitted.'),
        'SB_B': ('Ke et al. (2015) beauty coefficient B from the yearly citation histogram C[t] (t = '
                 'citing year - publication year >= 0, all years up to the snapshot): sum over t = '
                 '0..t_m of ((c_m - c_0)/t_m * t + c_0 - C[t]) / max(C[t], 1), where t_m is the age of'
                 ' the first citation peak. 0 when the peak is in the publication year; can be '
                 'negative; higher = longer dormancy before a burst. Unitless; unreliable for small '
                 'n_cite.'),
        'SB_T': ('Awakening time: age in years since publication (not a calendar year), 0..t_m, at '
                 'which the citation curve lies farthest from the straight line joining (0, C[0]) and '
                 'the peak (t_m, C[t_m]). 0 when the paper peaks in its publication year.'),
        'n_cite': ('Number of dated citations the histogram was built from: citations from works '
                   "published in or after the document's publication year, all years (>= 1)."),
    },
    'OpenAlex/output/paper_z_score.parquet': {
        'paper_id': ("OpenAlex work id as a string: 'W' followed by digits (e.g. W3002427681), URL "
                     'prefix stripped; joins every other OpenAlex/output table. Only journal-type '
                     "works (primary-location source of OpenAlex type 'journal') published 1980-2020, "
                     'with 2-1000 dated references in the graph and at least one scorable journal pair'
                     ' (46.4M); merged from the 18 year-range partitions, 1900-1979 never run.'),
        'Z_median': ('Median (numpy linear interpolation) of the Uzzi et al. (2013) z-scores of the '
                     "distinct journal pairs formed by the journals of the paper's references "
                     "(self-pairs included), each z taken from the paper's publication-year cohort "
                     '(z_score_pair). Unitless; low or negative = atypical combinations, high = '
                     'conventional.'),
        'Z_10pct': ('10th percentile (numpy linear interpolation) of the same distinct-pair z-scores: '
                    'the novelty tail (negative = the paper makes some combinations rarer than '
                    'chance).'),
        'Z_min': "Minimum z over the paper's distinct journal pairs (an addition to Uzzi et al.).",
        'n_pairs': ("Number of distinct journal pairs among the paper's references that received a z "
                    '(pairs whose null standard deviation is 0 are dropped); distinct pairs, not pair '
                    'occurrences.'),
    },
    'OpenAlex/output/z_score_pair.parquet': {
        'code_1': ('Integer code of the first journal of the pair: the digits of the OpenAlex source '
                   'id (S146344 -> 146344); only journal-type sources; code_1 <= code_2.'),
        'code_2': ('Integer code of the second journal (the digits of the OpenAlex source id (S146344 '
                   '-> 146344); only journal-type sources); equals code_1 for a self-pair (two '
                   'references in the same journal).'),
        'year': ('Focal cohort year (1980-2020): publication year of the citing papers whose reference'
                 " lists produced the pair; a pair's z is specific to this year."),
        'Z_score': ('z = (observed - null mean) / null SD for the journal pair in that year. Observed '
                    "= co-occurrences of the pair across the reference lists of that year's focal "
                    'papers, counted with multiplicity; null = 10 rewirings that swap cited works '
                    'within each (citing year, cited year) cell; population SD (ddof=0); pairs with '
                    'null SD 0 are omitted. Negative = rarer than chance (atypical).'),
    },
    'Dimensions/output/paper_author.parquet': {
        'paper_id': ("Dimensions publication id: 'pub.' followed by digits (e.g. pub.1000000002); "
                     'joins every other Dimensions/output table. One row per publication with at least'
                     ' one author slot (142.4M).'),
        'author_list': ("';'-joined Dimensions researcher ids (opaque 'ur.' + digits ids) of the "
                        'author slots Dimensions disambiguated, in byline order. Unresolved authors '
                        'are skipped, so it has n_resolved entries, not team_size; null when no slot '
                        'is resolved.'),
        'team_size': ("Number of author slots in the publication's authors[] list, resolved or not. "
                      'Unlike OpenAlex no de-duplication is needed (one entry per slot).'),
        'n_resolved': 'Number of author slots carrying a Dimensions researcher_id (<= team_size).',
        'first_author': ('Researcher id of the first author slot; null when that slot is unresolved '
                         '(not promoted to the next resolved author).'),
        'last_author': 'Researcher id of the last author slot; null when that slot is unresolved.',
        'corresponding_author': ('Researcher id of the first author slot flagged corresponding; null '
                                 'when no slot is flagged or the flagged slot is unresolved (73% '
                                 'null).'),
        'countries': ("Sorted, ';'-joined distinct ISO 3166-1 alpha-2 codes over all authors' "
                      'affiliation addresses (authors[].affiliations_address[].country_code); null '
                      'when none. Identical to paper_author_country.countries.'),
        'n_countries': 'Number of distinct codes in countries; 0 when none.',
    },
    'Dimensions/output/paper_author_country.parquet': {
        'paper_id': ("Dimensions publication id: 'pub.' followed by digits (e.g. pub.1000000002); "
                     'joins every other Dimensions/output table. Same 142.4M publications as '
                     'paper_author (publications with an empty authors[] are absent).'),
        'team_size': ('Number of author slots in authors[], resolved to a researcher id or not; '
                      'identical to paper_author.team_size.'),
        'n_located': ('Number of author slots with at least one country code in their affiliation '
                      'addresses; 0 when none.'),
        'countries': ("Sorted, ';'-joined distinct ISO 3166-1 alpha-2 codes over all author slots' "
                      "affiliations_address[].country_code (the affiliation's address country, whereas"
                      " OpenAlex uses the matched institution's country); null when no slot is "
                      "located. Namibia is 'NA'."),
        'n_countries': 'Number of distinct codes in countries; 0 when countries is null.',
        'country_author_counts': ("Located author slots per country as 'CC:n' items joined by ';', "
                                  "ordered by count descending then code (e.g. 'DE:2;SE:2'); a slot "
                                  'with two countries counts in both, so the sum can exceed n_located;'
                                  ' null when no slot is located.'),
        'first_author_country': ("';'-joined sorted country codes of author slot 1 (can hold several);"
                                 ' null when that slot has no country (not promoted to the next '
                                 'located author).'),
        'last_author_country': ("';'-joined sorted country codes of the final author slot; null when "
                                'that slot has no country.'),
        'is_international': 'True when n_countries > 1.',
    },
    'Dimensions/output/paper_citation.parquet': {
        'paper_id': ("Dimensions publication id: 'pub.' followed by digits (e.g. pub.1000000002); "
                     'joins every other Dimensions/output table. One row per publication with a year '
                     'in 1700-2030 (155.4M), cited or not.'),
        'C_3': ('Number of citations received within 3 years of publication, publication year counted '
                'as year 0: incoming reference edges from Dimensions works with 0 <= citing year - '
                'cited year <= 3 (calendar years), over the Dimensions reference graph (reference_ids '
                'of the June 2025 dump), edges kept when both ends have a year in 1700-2030. 0 for '
                'uncited documents; cohorts less than 3 years before the snapshot are right-truncated.'),
        'C_5': ('Number of citations received within 5 years of publication, publication year counted '
                'as year 0: incoming reference edges from Dimensions works with 0 <= citing year - '
                'cited year <= 5 (calendar years), over the Dimensions reference graph (reference_ids '
                'of the June 2025 dump), edges kept when both ends have a year in 1700-2030. 0 for '
                'uncited documents; cohorts less than 5 years before the snapshot are right-truncated.'),
        'C_10': ('Number of citations received within 10 years of publication, publication year '
                 'counted as year 0: incoming reference edges from Dimensions works with 0 <= citing '
                 'year - cited year <= 10 (calendar years), over the Dimensions reference graph '
                 '(reference_ids of the June 2025 dump), edges kept when both ends have a year in '
                 '1700-2030. 0 for uncited documents; cohorts less than 10 years before the snapshot '
                 'are right-truncated.'),
        'C_all': ('Number of citations received from works published in or after the focal year '
                  '(citing year - cited year >= 0, no upper bound), over the Dimensions reference '
                  'graph (reference_ids of the June 2025 dump), edges kept when both ends have a year '
                  'in 1700-2030. Citations from works dated earlier than the focal document are '
                  'dropped. 0 for uncited documents.'),
    },
    'Dimensions/output/paper_citation_trend.parquet': {
        'paper_id': ("Dimensions publication id: 'pub.' followed by digits (e.g. pub.1000000002); "
                     'joins every other Dimensions/output table. Identifies the cited publication. '
                     'Sparse panel: one row per (publication, citing year) with at least one citation '
                     'of any channel; never-cited publications are absent.'),
        'pub_year': ('Publication year of the cited publication as dated in the graph (dump year, kept'
                     ' when within 1700-2030).'),
        'cite_year': ("Calendar year of the row's citations: the citing publication's year for p2p; "
                      "for pat2p / pat2p_us the citing patent's granted_year, else its "
                      'publication_year. Rows with cite_year < pub_year are dropped.'),
        'yrs_since_pub': 'cite_year - pub_year in years (>= 0; 0 = the publication year).',
        'p2p': ('Number of Dimensions publications from cite_year that cite this one (incoming '
                'reference edges of the Dimensions graph).'),
        'pat2p': ('Number of Dimensions patent records citing this publication '
                  '(patents.publication_ids, de-duplicated per patent), all jurisdictions; grants and '
                  'applications are separate records (publication-level ids such as US-5078767-A), so '
                  'one invention can count more than once. Not PCS and no examiner/applicant split; '
                  'not comparable with the OpenAlex pat2p_* columns.'),
        'pat2p_us': ("The subset of pat2p from patent records with jurisdiction 'US' (mostly US "
                     'grants).'),
    },
    'Dimensions/output/paper_disruption.parquet': {
        'paper_id': ("Dimensions publication id: 'pub.' followed by digits (e.g. pub.1000000002); "
                     'joins every other Dimensions/output table. One row per publication with a year '
                     'in 1700-2030 (155.4M), same rows as paper_citation.'),
        'CD_3': ("Funk & Owen-Smith CD (disruption) index for window '3': (ni - nj) / (ni + nj + nk), "
                 'counting only papers with 0 <= year(citer) - year(focal) <= 3, publication year '
                 'counted as year 0. Nominal range [-1, 1] (+1 disruptive, -1 consolidating). Null '
                 'when the paper has no citers at all, or when neither a citer nor a paper citing its '
                 'references falls in the window; 0 (not null) when the window has no citer but has '
                 'papers citing the focal references.'),
        'F_3': ("Foundation share (0-1) for window '3': fraction of the focal paper's in-window citers"
                " whose own references include more of the focal paper's other in-window citers than "
                'of its references (down > up); ties with up = down > 0 count 1/2 here and 1/2 in E. F'
                ' + E + G = 1. Null when the window has no citer. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'E_3': ("Extension share (0-1) for window '3': fraction of in-window citers that cite more of "
                "the focal paper's references than of its other in-window citers (up > down), plus "
                'half of the ties. Null when the window has no citer. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'G_3': ("Generalization share (0-1) for window '3': fraction of in-window citers that cite "
                "neither any of the focal paper's references nor any of its other in-window citers (up"
                ' = down = 0). Null when the window has no citer. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'ni_3': ("Count of citers in window '3' (0 <= year(citer) - year(focal) <= 3, publication year"
                 " counted as year 0) that cite none of the focal paper's references. -1 is a "
                 'sentinel: the paper has no citers at all, or the window holds neither a citer nor a '
                 'paper citing its references.'),
        'nj_3': ("Count of citers in window '3' that also cite at least one of the focal paper's "
                 'references. -1 sentinel as for ni.'),
        'nk_3': ("Count of papers (other than the focal one) published in window '3' (0 <= year(citer)"
                 ' - year(focal) <= 3, publication year counted as year 0) that cite at least one of '
                 "the focal paper's references but not the focal paper itself. -1 sentinel as for ni."),
        'CD_5': ("Funk & Owen-Smith CD (disruption) index for window '5': (ni - nj) / (ni + nj + nk), "
                 'counting only papers with 0 <= year(citer) - year(focal) <= 5, publication year '
                 'counted as year 0. Nominal range [-1, 1] (+1 disruptive, -1 consolidating). Null '
                 'when the paper has no citers at all, or when neither a citer nor a paper citing its '
                 'references falls in the window; 0 (not null) when the window has no citer but has '
                 'papers citing the focal references.'),
        'F_5': ("Foundation share (0-1) for window '5': fraction of the focal paper's in-window citers"
                " whose own references include more of the focal paper's other in-window citers than "
                'of its references (down > up); ties with up = down > 0 count 1/2 here and 1/2 in E. F'
                ' + E + G = 1. Null when the window has no citer. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'E_5': ("Extension share (0-1) for window '5': fraction of in-window citers that cite more of "
                "the focal paper's references than of its other in-window citers (up > down), plus "
                'half of the ties. Null when the window has no citer. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'G_5': ("Generalization share (0-1) for window '5': fraction of in-window citers that cite "
                "neither any of the focal paper's references nor any of its other in-window citers (up"
                ' = down = 0). Null when the window has no citer. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'ni_5': ("Count of citers in window '5' (0 <= year(citer) - year(focal) <= 5, publication year"
                 " counted as year 0) that cite none of the focal paper's references. -1 is a "
                 'sentinel: the paper has no citers at all, or the window holds neither a citer nor a '
                 'paper citing its references.'),
        'nj_5': ("Count of citers in window '5' that also cite at least one of the focal paper's "
                 'references. -1 sentinel as for ni.'),
        'nk_5': ("Count of papers (other than the focal one) published in window '5' (0 <= year(citer)"
                 ' - year(focal) <= 5, publication year counted as year 0) that cite at least one of '
                 "the focal paper's references but not the focal paper itself. -1 sentinel as for ni."),
        'CD_10': ("Funk & Owen-Smith CD (disruption) index for window '10': (ni - nj) / (ni + nj + "
                  'nk), counting only papers with 0 <= year(citer) - year(focal) <= 10, publication '
                  'year counted as year 0. Nominal range [-1, 1] (+1 disruptive, -1 consolidating). '
                  'Null when the paper has no citers at all, or when neither a citer nor a paper '
                  'citing its references falls in the window; 0 (not null) when the window has no '
                  'citer but has papers citing the focal references.'),
        'F_10': ("Foundation share (0-1) for window '10': fraction of the focal paper's in-window "
                 "citers whose own references include more of the focal paper's other in-window citers"
                 ' than of its references (down > up); ties with up = down > 0 count 1/2 here and 1/2 '
                 'in E. F + E + G = 1. Null when the window has no citer. Decomposition of Fang & '
                 'Evans (2025), arXiv:2510.03240.'),
        'E_10': ("Extension share (0-1) for window '10': fraction of in-window citers that cite more "
                 "of the focal paper's references than of its other in-window citers (up > down), plus"
                 ' half of the ties. Null when the window has no citer. Decomposition of Fang & Evans '
                 '(2025), arXiv:2510.03240.'),
        'G_10': ("Generalization share (0-1) for window '10': fraction of in-window citers that cite "
                 "neither any of the focal paper's references nor any of its other in-window citers "
                 '(up = down = 0). Null when the window has no citer. Decomposition of Fang & Evans '
                 '(2025), arXiv:2510.03240.'),
        'ni_10': ("Count of citers in window '10' (0 <= year(citer) - year(focal) <= 10, publication "
                  "year counted as year 0) that cite none of the focal paper's references. -1 is a "
                  'sentinel: the paper has no citers at all, or the window holds neither a citer nor a'
                  ' paper citing its references.'),
        'nj_10': ("Count of citers in window '10' that also cite at least one of the focal paper's "
                  'references. -1 sentinel as for ni.'),
        'nk_10': ("Count of papers (other than the focal one) published in window '10' (0 <= "
                  'year(citer) - year(focal) <= 10, publication year counted as year 0) that cite at '
                  "least one of the focal paper's references but not the focal paper itself. -1 "
                  'sentinel as for ni.'),
        'CD_all': ("Funk & Owen-Smith CD (disruption) index for window 'all': (ni - nj) / (ni + nj + "
                   'nk), counting only papers with year(citer) - year(focal) >= 0, no upper bound. '
                   'Nominal range [-1, 1] (+1 disruptive, -1 consolidating). Null when the paper has '
                   'no citers at all, or when neither a citer nor a paper citing its references falls '
                   'in the window; 0 (not null) when the window has no citer but has papers citing the'
                   ' focal references.'),
        'F_all': ("Foundation share (0-1) for window 'all': fraction of the focal paper's in-window "
                  "citers whose own references include more of the focal paper's other in-window "
                  'citers than of its references (down > up); ties with up = down > 0 count 1/2 here '
                  'and 1/2 in E. F + E + G = 1. Null when the window has no citer. Decomposition of '
                  'Fang & Evans (2025), arXiv:2510.03240.'),
        'E_all': ("Extension share (0-1) for window 'all': fraction of in-window citers that cite more"
                  " of the focal paper's references than of its other in-window citers (up > down), "
                  'plus half of the ties. Null when the window has no citer. Decomposition of Fang & '
                  'Evans (2025), arXiv:2510.03240.'),
        'G_all': ("Generalization share (0-1) for window 'all': fraction of in-window citers that cite"
                  " neither any of the focal paper's references nor any of its other in-window citers "
                  '(up = down = 0). Null when the window has no citer. Decomposition of Fang & Evans '
                  '(2025), arXiv:2510.03240.'),
        'ni_all': ("Count of citers in window 'all' (year(citer) - year(focal) >= 0, no upper bound) "
                   "that cite none of the focal paper's references. -1 is a sentinel: the paper has no"
                   ' citers at all, or the window holds neither a citer nor a paper citing its '
                   'references.'),
        'nj_all': ("Count of citers in window 'all' that also cite at least one of the focal paper's "
                   'references. -1 sentinel as for ni.'),
        'nk_all': ("Count of papers (other than the focal one) published in window 'all' (year(citer) "
                   "- year(focal) >= 0, no upper bound) that cite at least one of the focal paper's "
                   'references but not the focal paper itself. -1 sentinel as for ni.'),
    },
    'Dimensions/output/paper_hit_probability.parquet': {
        'paper_id': ("Dimensions publication id: 'pub.' followed by digits (e.g. pub.1000000002); "
                     'joins every other Dimensions/output table. Only publications with an FoR '
                     'division and a year (119.0M).'),
        'FoS': ("Cohort field: ANZSRC Fields of Research 2020 division name (e.g. 'Biomedical and "
                "Clinical Sciences'), the first division listed on the publication "
                '(paper_metadata.FoS_rep; Dimensions gives no score). A different taxonomy from '
                'OpenAlex fields.'),
        'year': 'Cohort year: the publication year (paper_metadata.year; 1700-2025 in the file).',
        'pctl_c3': ("Percentile (0-1] of the document's C_3 (paper_citation) within its (FoR division,"
                    " year) cohort: pandas rank(pct=True, method='min') = (number of cohort members "
                    'with strictly fewer citations + 1) / cohort size. Uncited documents share the '
                    'lowest value (1/cohort size); pctl >= 0.99 marks roughly the top 1%.'),
        'pctl_c5': ("Percentile (0-1] of the document's C_5 (paper_citation) within its (FoR division,"
                    " year) cohort: pandas rank(pct=True, method='min') = (number of cohort members "
                    'with strictly fewer citations + 1) / cohort size. Uncited documents share the '
                    'lowest value (1/cohort size); pctl >= 0.99 marks roughly the top 1%.'),
        'pctl_c10': ("Percentile (0-1] of the document's C_10 (paper_citation) within its (FoR "
                     "division, year) cohort: pandas rank(pct=True, method='min') = (number of cohort "
                     'members with strictly fewer citations + 1) / cohort size. Uncited documents '
                     'share the lowest value (1/cohort size); pctl >= 0.99 marks roughly the top 1%.'),
        'pctl_call': ("Percentile (0-1] of the document's C_all (paper_citation) within its (FoR "
                      "division, year) cohort: pandas rank(pct=True, method='min') = (number of cohort"
                      ' members with strictly fewer citations + 1) / cohort size. Uncited documents '
                      'share the lowest value (1/cohort size); pctl >= 0.99 marks roughly the top 1%.'),
    },
    'Dimensions/output/paper_metadata.parquet': {
        'paper_id': ("Dimensions publication id: 'pub.' followed by digits (e.g. pub.1000000002); "
                     'joins every other Dimensions/output table. One row per publication in the dump '
                     '(155.5M), sorted by paper_id.'),
        'year': ("Publication year from the dump's year field (integer, not range checked: 1665-2025, "
                 'about 62k null). Graph-based tables only keep publications dated 1700-2030.'),
        'doctype': ('Dimensions publication type: article, chapter, proceeding, preprint, monograph, '
                    'book or seminar. Not the OpenAlex type vocabulary.'),
        'doc_class': ('Dimensions document_type.classification, e.g. RESEARCH_ARTICLE, REVIEW_ARTICLE,'
                      ' CONFERENCE_PAPER, CONFERENCE_ABSTRACT, EDITORIAL, LETTER_TO_EDITOR, '
                      'BOOK_REVIEW, CORRECTION_ERRATUM, REFERENCE_WORK, RESEARCH_CHAPTER, OTHER_*; '
                      'null for 21%. Use it for a research-article-only filter. No OpenAlex twin.'),
        'is_citable': 'Dimensions document_type.is_citable flag; null when doc_class is null.',
        'ref_count': ("Length of the publication's reference_ids list (Dimensions publication ids it "
                      'cites, including ids absent from the dump); 0 when none. Not comparable with '
                      'OpenAlex ref_count.'),
        'journal': ("Title (source_titles.title) of the publication's source (source_id, else "
                    'journal.id). Any source type: journals, proceedings, book series, preprint '
                    'platforms. Null when there is no source (15%).'),
        'is_journal': ("True when the source's source_titles.type is 'journal'; False for other source"
                       ' types and for publications without a source (never null).'),
        'source_id': ("Dimensions source id from the dump ('jour.' + digits for every source type); "
                      'null when the dump has none.'),
        'author_list': ("';'-joined Dimensions researcher ids ('ur.' + digits) of the resolved author "
                        "slots, in byline order. Empty string '' when the publication has authors but "
                        'none is resolved (23% of rows), null when it has no author slots (8%); '
                        'paper_author.parquet stores the empty case as null.'),
        'team_size': ('Number of author slots in authors[], resolved or not; null when the publication'
                      ' has no author slots.'),
        'FoS_0': ("';'-joined names of all ANZSRC Fields of Research 2020 divisions (2-digit level, "
                  "categories.for_2020_v2022.first_level) assigned to the publication, in the dump's "
                  'order; null when none (23%). Not OpenAlex fields.'),
        'FoS_rep': ('Representative field: the first FoR 2020 division name listed (Dimensions assigns'
                    ' no score, so this is list order, not a best match); null when none. 22 distinct '
                    'values in the file.'),
        'for_division_codes': ("';'-joined 2-digit FoR 2020 division codes (e.g. '30;40'), in the same"
                               ' order as FoS_0; null when none.'),
        'for_group_codes': ("';'-joined 4-digit FoR 2020 group codes (second level, e.g. '3005;4015'),"
                            " in the dump's order; null when none (28%)."),
        'cited_by_count': ("Dimensions' own total citation count (metrics.times_cited) at export time,"
                           ' over the whole Dimensions index; not the graph-derived, year-filtered '
                           'C_all of paper_citation.'),
        'citations_count': ("The dump's citations_count field (Dimensions' own count, like "
                            'cited_by_count). Null rather than 0 for uncited publications (null for '
                            '46% of rows, minimum 1).'),
        'doi': 'DOI as stored in the dump (no https://doi.org/ prefix); null for 5%.',
    },
    'Dimensions/output/paper_sb.parquet': {
        'paper_id': ("Dimensions publication id: 'pub.' followed by digits (e.g. pub.1000000002); "
                     'joins every other Dimensions/output table. Only documents with at least one '
                     'dated citation (citing year >= publication year) appear; uncited documents are '
                     'omitted.'),
        'SB_B': ('Ke et al. (2015) beauty coefficient B from the yearly citation histogram C[t] (t = '
                 'citing year - publication year >= 0, all years up to the snapshot): sum over t = '
                 '0..t_m of ((c_m - c_0)/t_m * t + c_0 - C[t]) / max(C[t], 1), where t_m is the age of'
                 ' the first citation peak. 0 when the peak is in the publication year; can be '
                 'negative; higher = longer dormancy before a burst. Unitless; unreliable for small '
                 'n_cite.'),
        'SB_T': ('Awakening time: age in years since publication (not a calendar year), 0..t_m, at '
                 'which the citation curve lies farthest from the straight line joining (0, C[0]) and '
                 'the peak (t_m, C[t_m]). 0 when the paper peaks in its publication year.'),
        'n_cite': ('Number of dated citations the histogram was built from: citations from works '
                   "published in or after the document's publication year, all years (>= 1)."),
    },
    'Dimensions/output/paper_z_score_1990_2000.parquet': {
        'paper_id': ("Dimensions publication id: 'pub.' followed by digits (e.g. pub.1000000002); "
                     'joins every other Dimensions/output table. Only journal-type publications '
                     "(source_titles.type 'journal') published 1990-2000, with 2-1000 dated references"
                     ' in the graph and at least one scorable journal pair (6.2M). No other year range'
                     ' has been run.'),
        'Z_median': ('Median (numpy linear interpolation) of the Uzzi et al. (2013) z-scores of the '
                     "distinct journal pairs formed by the journals of the paper's references "
                     "(self-pairs included), each z taken from the paper's publication-year cohort "
                     '(z_score_pair). Unitless; low or negative = atypical combinations, high = '
                     'conventional.'),
        'Z_10pct': ('10th percentile (numpy linear interpolation) of the same distinct-pair z-scores: '
                    'the novelty tail (negative = the paper makes some combinations rarer than '
                    'chance).'),
        'Z_min': "Minimum z over the paper's distinct journal pairs (an addition to Uzzi et al.).",
        'n_pairs': ("Number of distinct journal pairs among the paper's references that received a z "
                    '(pairs whose null standard deviation is 0 are dropped); distinct pairs, not pair '
                    'occurrences.'),
    },
    'Dimensions/output/z_score_pair_1990_2000.parquet': {
        'code_1': ('Integer code of the first journal of the pair: the digits of the Dimensions source'
                   ' id (jour.1013101 -> 1013101); only journal-type sources; code_1 <= code_2.'),
        'code_2': ('Integer code of the second journal (the digits of the Dimensions source id '
                   '(jour.1013101 -> 1013101); only journal-type sources); equals code_1 for a '
                   'self-pair (two references in the same journal).'),
        'year': ('Focal cohort year (1990-2000): publication year of the citing papers whose reference'
                 " lists produced the pair; a pair's z is specific to this year."),
        'Z_score': ('z = (observed - null mean) / null SD for the journal pair in that year. Observed '
                    "= co-occurrences of the pair across the reference lists of that year's focal "
                    'papers, counted with multiplicity; null = 10 rewirings that swap cited works '
                    'within each (citing year, cited year) cell; population SD (ddof=0); pairs with '
                    'null SD 0 are omitted. Negative = rarer than chance (atypical).'),
    },
    'PatentView/output/patent_citation.parquet': {
        'patent_id': ("USPTO patent number as a string, without 'US' prefix or kind code (7-8 digits, "
                      "e.g. '10000000'; a few dozen 'RE...' ids that PatentsView types as utility). "
                      'One row per utility patent that received at least one counted forward citation '
                      '(granted or pre-grant-publication, lag >= 0); never-cited patents are absent '
                      'rather than zero.'),
        'C_3': ('Forward citations to P from granted US utility patents (g_us_patent_citation) with 0 '
                '<= y_citing - y_P <= 3 (grant years, inclusive); counts citation rows (~0.16% '
                'duplicate rows count twice), third-party citations dropped; = C_examiner_3 + '
                'C_non_examiner_3 + C_unknown_3.'),
        'C_5': ('Forward citations to P from granted US utility patents (g_us_patent_citation) with 0 '
                '<= y_citing - y_P <= 5 (grant years, inclusive); counts citation rows (~0.16% '
                'duplicate rows count twice), third-party citations dropped; = C_examiner_5 + '
                'C_non_examiner_5 + C_unknown_5.'),
        'C_10': ('Forward citations to P from granted US utility patents (g_us_patent_citation) with 0'
                 ' <= y_citing - y_P <= 10 (grant years, inclusive); counts citation rows (~0.16% '
                 'duplicate rows count twice), third-party citations dropped; = C_examiner_10 + '
                 'C_non_examiner_10 + C_unknown_10.'),
        'C_all': ('Forward citations to P from granted US utility patents (g_us_patent_citation) with '
                  'y_citing >= y_P (grant years, any lag up to the 2025 snapshot end); counts citation'
                  ' rows (~0.16% duplicate rows count twice), third-party citations dropped; = '
                  'C_examiner_all + C_non_examiner_all + C_unknown_all.'),
        'C_examiner_3': ("Part of C_3 whose citation_category is 'cited by examiner'. The flag is "
                         'absent for citing patents granted up to 2001 (all of those fall in '
                         'C_unknown_3), so examiner counts start with ~2002 citers.'),
        'C_non_examiner_3': ('Part of C_3 with a non-empty citation_category other than examiner or '
                             "third party: 'cited by applicant', 'cited by other', 'imported from a "
                             "related application' (mostly applicant references). Per the README the "
                             'applicant/other labelling changed in 2013, but both stay in this bucket;'
                             ' zero for citers granted up to 2001.'),
        'C_unknown_3': ('Part of C_3 with an empty/NULL citation_category, kept separate rather than '
                        'folded into non_examiner. In this snapshot that is every citation made by a '
                        'patent granted 1976-2001 (and ~5% of 2002), so it is nonzero only through '
                        'citers of that era.'),
        'C_examiner_5': ("Part of C_5 whose citation_category is 'cited by examiner'. The flag is "
                         'absent for citing patents granted up to 2001 (all of those fall in '
                         'C_unknown_5), so examiner counts start with ~2002 citers.'),
        'C_non_examiner_5': ('Part of C_5 with a non-empty citation_category other than examiner or '
                             "third party: 'cited by applicant', 'cited by other', 'imported from a "
                             "related application' (mostly applicant references). Per the README the "
                             'applicant/other labelling changed in 2013, but both stay in this bucket;'
                             ' zero for citers granted up to 2001.'),
        'C_unknown_5': ('Part of C_5 with an empty/NULL citation_category, kept separate rather than '
                        'folded into non_examiner. In this snapshot that is every citation made by a '
                        'patent granted 1976-2001 (and ~5% of 2002), so it is nonzero only through '
                        'citers of that era.'),
        'C_examiner_10': ("Part of C_10 whose citation_category is 'cited by examiner'. The flag is "
                          'absent for citing patents granted up to 2001 (all of those fall in '
                          'C_unknown_10), so examiner counts start with ~2002 citers.'),
        'C_non_examiner_10': ('Part of C_10 with a non-empty citation_category other than examiner or '
                              "third party: 'cited by applicant', 'cited by other', 'imported from a "
                              "related application' (mostly applicant references). Per the README the "
                              'applicant/other labelling changed in 2013, but both stay in this '
                              'bucket; zero for citers granted up to 2001.'),
        'C_unknown_10': ('Part of C_10 with an empty/NULL citation_category, kept separate rather than'
                         ' folded into non_examiner. In this snapshot that is every citation made by a'
                         ' patent granted 1976-2001 (and ~5% of 2002), so it is nonzero only through '
                         'citers of that era.'),
        'C_examiner_all': ("Part of C_all whose citation_category is 'cited by examiner'. The flag is "
                           'absent for citing patents granted up to 2001 (all of those fall in '
                           'C_unknown_all), so examiner counts start with ~2002 citers.'),
        'C_non_examiner_all': ('Part of C_all with a non-empty citation_category other than examiner '
                               "or third party: 'cited by applicant', 'cited by other', 'imported from"
                               " a related application' (mostly applicant references). Per the README "
                               'the applicant/other labelling changed in 2013, but both stay in this '
                               'bucket; zero for citers granted up to 2001.'),
        'C_unknown_all': ('Part of C_all with an empty/NULL citation_category, kept separate rather '
                          'than folded into non_examiner. In this snapshot that is every citation made'
                          ' by a patent granted 1976-2001 (and ~5% of 2002), so it is nonzero only '
                          'through citers of that era.'),
        'appC_3': ("Citations by granted US utility patents of P's pre-grant publication "
                   '(g_us_application_citation; pgpub mapped to P via pg_granted_pgpubs_crosswalk) '
                   'with 0 <= y_citing - y_P <= 3 (grant years, inclusive); rows, third party and '
                   'negative-lag citations dropped; = appC_examiner_3 + appC_non_examiner_3.'),
        'appC_5': ("Citations by granted US utility patents of P's pre-grant publication "
                   '(g_us_application_citation; pgpub mapped to P via pg_granted_pgpubs_crosswalk) '
                   'with 0 <= y_citing - y_P <= 5 (grant years, inclusive); rows, third party and '
                   'negative-lag citations dropped; = appC_examiner_5 + appC_non_examiner_5.'),
        'appC_10': ("Citations by granted US utility patents of P's pre-grant publication "
                    '(g_us_application_citation; pgpub mapped to P via pg_granted_pgpubs_crosswalk) '
                    'with 0 <= y_citing - y_P <= 10 (grant years, inclusive); rows, third party and '
                    'negative-lag citations dropped; = appC_examiner_10 + appC_non_examiner_10.'),
        'appC_all': ("Citations by granted US utility patents of P's pre-grant publication "
                     '(g_us_application_citation; pgpub mapped to P via pg_granted_pgpubs_crosswalk) '
                     'with y_citing >= y_P (grant years, any lag up to the 2025 snapshot end); rows, '
                     'third party and negative-lag citations dropped; = appC_examiner_all + '
                     'appC_non_examiner_all.'),
        'appC_examiner_3': "Part of appC_3 whose citation_category is 'cited by examiner'.",
        'appC_non_examiner_3': ("Part of appC_3 with any other category ('cited by applicant', 'cited "
                                "by other', 'imported from a related application'); there is no "
                                'unknown bucket for application citations, so an empty category (none '
                                'observed) would land here.'),
        'appC_examiner_5': "Part of appC_5 whose citation_category is 'cited by examiner'.",
        'appC_non_examiner_5': ("Part of appC_5 with any other category ('cited by applicant', 'cited "
                                "by other', 'imported from a related application'); there is no "
                                'unknown bucket for application citations, so an empty category (none '
                                'observed) would land here.'),
        'appC_examiner_10': "Part of appC_10 whose citation_category is 'cited by examiner'.",
        'appC_non_examiner_10': ("Part of appC_10 with any other category ('cited by applicant', "
                                 "'cited by other', 'imported from a related application'); there is "
                                 'no unknown bucket for application citations, so an empty category '
                                 '(none observed) would land here.'),
        'appC_examiner_all': "Part of appC_all whose citation_category is 'cited by examiner'.",
        'appC_non_examiner_all': ("Part of appC_all with any other category ('cited by applicant', "
                                  "'cited by other', 'imported from a related application'); there is "
                                  'no unknown bucket for application citations, so an empty category '
                                  '(none observed) would land here.'),
        'uniqueC_3': ('Distinct granted US utility patents citing P with 0 <= y_citing - y_P <= 3 '
                      "(grant years, inclusive), each counted once whether it cites P's patent number,"
                      " P's pre-grant publication, or both (C and appC edges de-duplicated); <= C_3 + "
                      'appC_3.'),
        'uniqueC_5': ('Distinct granted US utility patents citing P with 0 <= y_citing - y_P <= 5 '
                      "(grant years, inclusive), each counted once whether it cites P's patent number,"
                      " P's pre-grant publication, or both (C and appC edges de-duplicated); <= C_5 + "
                      'appC_5.'),
        'uniqueC_10': ('Distinct granted US utility patents citing P with 0 <= y_citing - y_P <= 10 '
                       "(grant years, inclusive), each counted once whether it cites P's patent "
                       "number, P's pre-grant publication, or both (C and appC edges de-duplicated); "
                       '<= C_10 + appC_10.'),
        'uniqueC_all': ('Distinct granted US utility patents citing P with y_citing >= y_P (grant '
                        'years, any lag up to the 2025 snapshot end), each counted once whether it '
                        "cites P's patent number, P's pre-grant publication, or both (C and appC edges"
                        ' de-duplicated); <= C_all + appC_all.'),
        'uniqueC_examiner_3': ('Distinct citing patents in window 3 with at least one examiner-flagged'
                               ' citation of P in either source. A citer can count in several '
                               'provenance columns, so the three uniqueC_*_3 splits can sum to more '
                               'than uniqueC_3.'),
        'uniqueC_examiner_5': ('Distinct citing patents in window 5 with at least one examiner-flagged'
                               ' citation of P in either source. A citer can count in several '
                               'provenance columns, so the three uniqueC_*_5 splits can sum to more '
                               'than uniqueC_5.'),
        'uniqueC_examiner_10': ('Distinct citing patents in window 10 with at least one '
                                'examiner-flagged citation of P in either source. A citer can count in'
                                ' several provenance columns, so the three uniqueC_*_10 splits can sum'
                                ' to more than uniqueC_10.'),
        'uniqueC_examiner_all': ('Distinct citing patents in window all with at least one '
                                 'examiner-flagged citation of P in either source. A citer can count '
                                 'in several provenance columns, so the three uniqueC_*_all splits can'
                                 ' sum to more than uniqueC_all.'),
        'uniqueC_non_examiner_3': ('Distinct citing patents in window 3 with at least one non-examiner'
                                   ' (applicant/other/imported) citation of P in either source; '
                                   'overlaps the other splits (see uniqueC_examiner_3).'),
        'uniqueC_non_examiner_5': ('Distinct citing patents in window 5 with at least one non-examiner'
                                   ' (applicant/other/imported) citation of P in either source; '
                                   'overlaps the other splits (see uniqueC_examiner_5).'),
        'uniqueC_non_examiner_10': ('Distinct citing patents in window 10 with at least one '
                                    'non-examiner (applicant/other/imported) citation of P in either '
                                    'source; overlaps the other splits (see uniqueC_examiner_10).'),
        'uniqueC_non_examiner_all': ('Distinct citing patents in window all with at least one '
                                     'non-examiner (applicant/other/imported) citation of P in either '
                                     'source; overlaps the other splits (see uniqueC_examiner_all).'),
        'uniqueC_unknown_3': ('Distinct citing patents in window 3 with at least one empty-category '
                              'granted citation of P (application citations have no unknown bucket), '
                              'i.e. effectively citers granted up to ~2001.'),
        'uniqueC_unknown_5': ('Distinct citing patents in window 5 with at least one empty-category '
                              'granted citation of P (application citations have no unknown bucket), '
                              'i.e. effectively citers granted up to ~2001.'),
        'uniqueC_unknown_10': ('Distinct citing patents in window 10 with at least one empty-category '
                               'granted citation of P (application citations have no unknown bucket), '
                               'i.e. effectively citers granted up to ~2001.'),
        'uniqueC_unknown_all': ('Distinct citing patents in window all with at least one '
                                'empty-category granted citation of P (application citations have no '
                                'unknown bucket), i.e. effectively citers granted up to ~2001.'),
    },
    'PatentView/output/patent_citation_trend.parquet': {
        'patent_id': ("USPTO patent number as a string, without 'US' prefix or kind code (7-8 digits, "
                      "e.g. '10000000'; a few dozen 'RE...' ids that PatentsView types as utility). "
                      'The cited patent; same 7,160,531 patents as patent_citation. Sparse: one row '
                      'per (patent, citing year) with >= 1 citation, so a missing year means zero.'),
        'grant_year': ('Grant year of the cited patent P (calendar year of g_patent.patent_date), '
                       '1976-2025.'),
        'cite_year': ('Grant year of the citing patents, used for both granted and '
                      'pre-grant-publication citations (not the date the reference was made), '
                      '1976-2025.'),
        'yrs_since_grant': ('cite_year - grant_year in years (0-49); citations with a negative lag are'
                            ' dropped. Summing a count over yrs_since_grant <= w reproduces '
                            "patent_citation's _w column."),
        'C': ('Granted citations (g_us_patent_citation rows, third party dropped) received by P from '
              'patents granted in cite_year; per-year, not cumulative; = C_examiner + C_non_examiner +'
              ' C_unknown.'),
        'C_examiner': ("Part of C with citation_category 'cited by examiner' (flag exists only for "
                       'citers granted from ~2002).'),
        'C_non_examiner': ('Part of C with a non-empty category other than examiner/third party '
                           '(applicant, other, imported from a related application).'),
        'C_unknown': ('Part of C with an empty citation_category: 100% of C for cite_year <= 2001, ~5%'
                      ' in 2002, 0 afterwards.'),
        'appC': ("Citations of P's pre-grant publication (pgpub mapped to P via "
                 'pg_granted_pgpubs_crosswalk) made by patents granted in cite_year '
                 '(g_us_application_citation, third party dropped); = appC_examiner + '
                 'appC_non_examiner. Zero for every cite_year before 2005 in this build.'),
        'appC_examiner': "Part of appC with citation_category 'cited by examiner'.",
        'appC_non_examiner': ('Part of appC with any other category (no unknown bucket for application'
                              ' citations).'),
        'pat2pat_examiner': 'Legacy alias kept for older readers: identical to C_examiner.',
        'pat2pat_non_examiner': ("Legacy alias: C_non_examiner + C_unknown (the old folded 'not "
                                 "examiner' definition), NOT equal to C_non_examiner."),
        'app2pat_examiner': 'Legacy alias: identical to appC_examiner.',
        'app2pat_non_examiner': 'Legacy alias: identical to appC_non_examiner.',
    },
    'PatentView/output/patent_disruption.parquet': {
        'patent_id': ("USPTO patent number as a string, without 'US' prefix or kind code (7-8 digits, "
                      "e.g. '10000000'; a few dozen 'RE...' ids that PatentsView types as utility). "
                      'Utility patents granted 1976-2025 that appear in the granted citation graph '
                      '(g_us_patent_citation, third-party rows not excluded) as citing or cited '
                      'patent; never-cited patents have every metric null.'),
        'CD_3': ('CD index (ni_3 - nj_3) / (ni_3 + nj_3 + nk_3) in [-1, 1] (+1 disruptive) on the '
                 'granted utility-to-utility citation network (duplicate pairs and self-citations '
                 'removed), counting citers and nk patents with 0 <= y - y_P <= 3 on grant years. Null'
                 ' if P is never cited or the denominator is 0; 0 with ni = nj = 0 when no citer is in'
                 ' the window but nk > 0. Inflated for early grant years (pre-1976 references '
                 'missing).'),
        'F_3': ("Foundation share: fraction of P's citers in the window (0 <= y - y_P <= 3 on grant "
                "years) that cite more of P's other in-window citers than of P's references (down > "
                'up); a tie with up = down > 0 adds 0.5 to F and E. F + E + G = 1; null when P has no '
                'citer in the window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_3': ("Extension share: fraction of P's in-window citers that cite more of P's references "
                "than of P's other in-window citers (up > down), plus half of the up = down > 0 ties; "
                'null when no in-window citer. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'G_3': ("Generalization share: fraction of P's in-window citers that cite none of P's "
                "references and none of P's other in-window citers; null when no in-window citer. "
                'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_3': ('Number of patents citing P in the window (0 <= y - y_P <= 3 on grant years) that '
                 "cite none of P's references. Stored as float; null where CD_3 is null."),
        'nj_3': ("Number of patents citing P in the window that also cite at least one of P's "
                 'references.'),
        'nk_3': ('Number of patents granted in the window (0 <= y - y_P <= 3 on grant years) that cite'
                 " at least one of P's references but not P."),
        'CD_5': ('CD index (ni_5 - nj_5) / (ni_5 + nj_5 + nk_5) in [-1, 1] (+1 disruptive) on the '
                 'granted utility-to-utility citation network (duplicate pairs and self-citations '
                 'removed), counting citers and nk patents with 0 <= y - y_P <= 5 on grant years. Null'
                 ' if P is never cited or the denominator is 0; 0 with ni = nj = 0 when no citer is in'
                 ' the window but nk > 0. Inflated for early grant years (pre-1976 references '
                 'missing).'),
        'F_5': ("Foundation share: fraction of P's citers in the window (0 <= y - y_P <= 5 on grant "
                "years) that cite more of P's other in-window citers than of P's references (down > "
                'up); a tie with up = down > 0 adds 0.5 to F and E. F + E + G = 1; null when P has no '
                'citer in the window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_5': ("Extension share: fraction of P's in-window citers that cite more of P's references "
                "than of P's other in-window citers (up > down), plus half of the up = down > 0 ties; "
                'null when no in-window citer. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'G_5': ("Generalization share: fraction of P's in-window citers that cite none of P's "
                "references and none of P's other in-window citers; null when no in-window citer. "
                'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_5': ('Number of patents citing P in the window (0 <= y - y_P <= 5 on grant years) that '
                 "cite none of P's references. Stored as float; null where CD_5 is null."),
        'nj_5': ("Number of patents citing P in the window that also cite at least one of P's "
                 'references.'),
        'nk_5': ('Number of patents granted in the window (0 <= y - y_P <= 5 on grant years) that cite'
                 " at least one of P's references but not P."),
        'CD_10': ('CD index (ni_10 - nj_10) / (ni_10 + nj_10 + nk_10) in [-1, 1] (+1 disruptive) on '
                  'the granted utility-to-utility citation network (duplicate pairs and self-citations'
                  ' removed), counting citers and nk patents with 0 <= y - y_P <= 10 on grant years. '
                  'Null if P is never cited or the denominator is 0; 0 with ni = nj = 0 when no citer '
                  'is in the window but nk > 0. Inflated for early grant years (pre-1976 references '
                  'missing).'),
        'F_10': ("Foundation share: fraction of P's citers in the window (0 <= y - y_P <= 10 on grant "
                 "years) that cite more of P's other in-window citers than of P's references (down > "
                 'up); a tie with up = down > 0 adds 0.5 to F and E. F + E + G = 1; null when P has no'
                 ' citer in the window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_10': ("Extension share: fraction of P's in-window citers that cite more of P's references "
                 "than of P's other in-window citers (up > down), plus half of the up = down > 0 ties;"
                 ' null when no in-window citer. Decomposition of Fang & Evans (2025), '
                 'arXiv:2510.03240.'),
        'G_10': ("Generalization share: fraction of P's in-window citers that cite none of P's "
                 "references and none of P's other in-window citers; null when no in-window citer. "
                 'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_10': ('Number of patents citing P in the window (0 <= y - y_P <= 10 on grant years) that '
                  "cite none of P's references. Stored as float; null where CD_10 is null."),
        'nj_10': ("Number of patents citing P in the window that also cite at least one of P's "
                  'references.'),
        'nk_10': ('Number of patents granted in the window (0 <= y - y_P <= 10 on grant years) that '
                  "cite at least one of P's references but not P."),
        'CD_all': ('CD index (ni_all - nj_all) / (ni_all + nj_all + nk_all) in [-1, 1] (+1 disruptive)'
                   ' on the granted utility-to-utility citation network (duplicate pairs and '
                   'self-citations removed), counting citers and nk patents with y - y_P >= 0 on grant'
                   ' years. Null if P is never cited or the denominator is 0; 0 with ni = nj = 0 when '
                   'no citer is in the window but nk > 0. Inflated for early grant years (pre-1976 '
                   'references missing).'),
        'F_all': ("Foundation share: fraction of P's citers in the window (y - y_P >= 0 on grant "
                  "years) that cite more of P's other in-window citers than of P's references (down > "
                  'up); a tie with up = down > 0 adds 0.5 to F and E. F + E + G = 1; null when P has '
                  'no citer in the window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_all': ("Extension share: fraction of P's in-window citers that cite more of P's references "
                  "than of P's other in-window citers (up > down), plus half of the up = down > 0 "
                  'ties; null when no in-window citer. Decomposition of Fang & Evans (2025), '
                  'arXiv:2510.03240.'),
        'G_all': ("Generalization share: fraction of P's in-window citers that cite none of P's "
                  "references and none of P's other in-window citers; null when no in-window citer. "
                  'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_all': ('Number of patents citing P in the window (y - y_P >= 0 on grant years) that cite '
                   "none of P's references. Stored as float; null where CD_all is null."),
        'nj_all': ("Number of patents citing P in the window that also cite at least one of P's "
                   'references.'),
        'nk_all': ('Number of patents granted in the window (y - y_P >= 0 on grant years) that cite at'
                   " least one of P's references but not P."),
        'pctl_year': ("Cohort year of the CD percentile columns: P's filing year "
                      '(patent_metadata.filing_year, earliest g_application filing date), stored as '
                      'double; null for the few patents without one. The CD windows themselves run '
                      'from the grant year.'),
        'pctl_group': ('Cohort group of the CD percentile columns: CPC Section letter A-H (Y allowed, '
                       "none occur) = first character of P's primary CPC group "
                       'patent_metadata.cpc_code; null (~17k patents) when there is no CPC code or no '
                       'filing year.'),
        'CD_3_pctl': ("Minimum-rank percentile of CD_3 within P's filing-year x CPC-Section cohort: (1"
                      ' + # cohort patents with lower CD_3) / # with non-null CD_3, in (0, 1], higher '
                      '= more disruptive; tie blocks (CD = 0, 1) share their lowest value. Null when '
                      'CD_3 or pctl_group is null.'),
        'CD_3_pctl_cume': ('Cumulative percentile of CD_3 in the same cohort: share of cohort patents '
                           "with CD_3 <= P's value (ties inclusive, like cume_dist); range (0, 1], "
                           "always >= CD_3_pctl. The producer recommends this one for 'top x %' "
                           'thresholds.'),
        'CD_5_pctl': ("Minimum-rank percentile of CD_5 within P's filing-year x CPC-Section cohort: (1"
                      ' + # cohort patents with lower CD_5) / # with non-null CD_5, in (0, 1], higher '
                      '= more disruptive; tie blocks (CD = 0, 1) share their lowest value. Null when '
                      'CD_5 or pctl_group is null.'),
        'CD_5_pctl_cume': ('Cumulative percentile of CD_5 in the same cohort: share of cohort patents '
                           "with CD_5 <= P's value (ties inclusive, like cume_dist); range (0, 1], "
                           "always >= CD_5_pctl. The producer recommends this one for 'top x %' "
                           'thresholds.'),
        'CD_10_pctl': ("Minimum-rank percentile of CD_10 within P's filing-year x CPC-Section cohort: "
                       '(1 + # cohort patents with lower CD_10) / # with non-null CD_10, in (0, 1], '
                       'higher = more disruptive; tie blocks (CD = 0, 1) share their lowest value. '
                       'Null when CD_10 or pctl_group is null.'),
        'CD_10_pctl_cume': ('Cumulative percentile of CD_10 in the same cohort: share of cohort '
                            "patents with CD_10 <= P's value (ties inclusive, like cume_dist); range "
                            "(0, 1], always >= CD_10_pctl. The producer recommends this one for 'top x"
                            " %' thresholds."),
        'CD_all_pctl': ("Minimum-rank percentile of CD_all within P's filing-year x CPC-Section "
                        'cohort: (1 + # cohort patents with lower CD_all) / # with non-null CD_all, in'
                        ' (0, 1], higher = more disruptive; tie blocks (CD = 0, 1) share their lowest '
                        'value. Null when CD_all or pctl_group is null.'),
        'CD_all_pctl_cume': ('Cumulative percentile of CD_all in the same cohort: share of cohort '
                             "patents with CD_all <= P's value (ties inclusive, like cume_dist); range"
                             ' (0, 1], always >= CD_all_pctl. The producer recommends this one for '
                             "'top x %' thresholds."),
    },
    'PatentView/output/patent_disruption_app.parquet': {
        'patent_id': ("USPTO patent number as a string, without 'US' prefix or kind code (7-8 digits, "
                      "e.g. '10000000'; a few dozen 'RE...' ids that PatentsView types as utility). "
                      'Utility patents granted 1976-2025 in the extended graph: granted citations plus'
                      ' g_us_application_citation pgpub citations mapped via '
                      'pg_granted_pgpubs_crosswalk (both ends utility, dated by grant years); 398,002 '
                      'more patents than patent_disruption.'),
        'CD_3': ('CD index (ni_3 - nj_3) / (ni_3 + nj_3 + nk_3) in [-1, 1] (+1 disruptive) on the '
                 'extended network (granted citations plus citations of pre-grant publications mapped '
                 'to their granted patent, union de-duplicated), counting citers and nk patents with 0'
                 ' <= y - y_P <= 3 on grant years. Null if P is never cited or the denominator is 0; 0'
                 ' with ni = nj = 0 when no citer is in the window but nk > 0. Equals '
                 'patent_disruption.CD_3 for grant years <= 1997 (verified).'),
        'F_3': ("Foundation share: fraction of P's citers in the window (0 <= y - y_P <= 3 on grant "
                "years) that cite more of P's other in-window citers than of P's references (down > "
                'up); a tie with up = down > 0 adds 0.5 to F and E. F + E + G = 1; null when P has no '
                'citer in the window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_3': ("Extension share: fraction of P's in-window citers that cite more of P's references "
                "than of P's other in-window citers (up > down), plus half of the up = down > 0 ties; "
                'null when no in-window citer. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'G_3': ("Generalization share: fraction of P's in-window citers that cite none of P's "
                "references and none of P's other in-window citers; null when no in-window citer. "
                'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_3': ('Number of patents citing P in the window (0 <= y - y_P <= 3 on grant years) that '
                 "cite none of P's references. Stored as float; null where CD_3 is null."),
        'nj_3': ("Number of patents citing P in the window that also cite at least one of P's "
                 'references.'),
        'nk_3': ('Number of patents granted in the window (0 <= y - y_P <= 3 on grant years) that cite'
                 " at least one of P's references but not P."),
        'CD_5': ('CD index (ni_5 - nj_5) / (ni_5 + nj_5 + nk_5) in [-1, 1] (+1 disruptive) on the '
                 'extended network (granted citations plus citations of pre-grant publications mapped '
                 'to their granted patent, union de-duplicated), counting citers and nk patents with 0'
                 ' <= y - y_P <= 5 on grant years. Null if P is never cited or the denominator is 0; 0'
                 ' with ni = nj = 0 when no citer is in the window but nk > 0. Equals '
                 'patent_disruption.CD_5 for grant years <= 1995 (verified).'),
        'F_5': ("Foundation share: fraction of P's citers in the window (0 <= y - y_P <= 5 on grant "
                "years) that cite more of P's other in-window citers than of P's references (down > "
                'up); a tie with up = down > 0 adds 0.5 to F and E. F + E + G = 1; null when P has no '
                'citer in the window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_5': ("Extension share: fraction of P's in-window citers that cite more of P's references "
                "than of P's other in-window citers (up > down), plus half of the up = down > 0 ties; "
                'null when no in-window citer. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'G_5': ("Generalization share: fraction of P's in-window citers that cite none of P's "
                "references and none of P's other in-window citers; null when no in-window citer. "
                'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_5': ('Number of patents citing P in the window (0 <= y - y_P <= 5 on grant years) that '
                 "cite none of P's references. Stored as float; null where CD_5 is null."),
        'nj_5': ("Number of patents citing P in the window that also cite at least one of P's "
                 'references.'),
        'nk_5': ('Number of patents granted in the window (0 <= y - y_P <= 5 on grant years) that cite'
                 " at least one of P's references but not P."),
        'CD_10': ('CD index (ni_10 - nj_10) / (ni_10 + nj_10 + nk_10) in [-1, 1] (+1 disruptive) on '
                  'the extended network (granted citations plus citations of pre-grant publications '
                  'mapped to their granted patent, union de-duplicated), counting citers and nk '
                  'patents with 0 <= y - y_P <= 10 on grant years. Null if P is never cited or the '
                  'denominator is 0; 0 with ni = nj = 0 when no citer is in the window but nk > 0. '
                  'Equals patent_disruption.CD_10 for grant years <= 1990 (verified).'),
        'F_10': ("Foundation share: fraction of P's citers in the window (0 <= y - y_P <= 10 on grant "
                 "years) that cite more of P's other in-window citers than of P's references (down > "
                 'up); a tie with up = down > 0 adds 0.5 to F and E. F + E + G = 1; null when P has no'
                 ' citer in the window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_10': ("Extension share: fraction of P's in-window citers that cite more of P's references "
                 "than of P's other in-window citers (up > down), plus half of the up = down > 0 ties;"
                 ' null when no in-window citer. Decomposition of Fang & Evans (2025), '
                 'arXiv:2510.03240.'),
        'G_10': ("Generalization share: fraction of P's in-window citers that cite none of P's "
                 "references and none of P's other in-window citers; null when no in-window citer. "
                 'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_10': ('Number of patents citing P in the window (0 <= y - y_P <= 10 on grant years) that '
                  "cite none of P's references. Stored as float; null where CD_10 is null."),
        'nj_10': ("Number of patents citing P in the window that also cite at least one of P's "
                  'references.'),
        'nk_10': ('Number of patents granted in the window (0 <= y - y_P <= 10 on grant years) that '
                  "cite at least one of P's references but not P."),
        'CD_all': ('CD index (ni_all - nj_all) / (ni_all + nj_all + nk_all) in [-1, 1] (+1 disruptive)'
                   ' on the extended network (granted citations plus citations of pre-grant '
                   'publications mapped to their granted patent, union de-duplicated), counting citers'
                   ' and nk patents with y - y_P >= 0 on grant years. Null if P is never cited or the '
                   'denominator is 0; 0 with ni = nj = 0 when no citer is in the window but nk > 0. '
                   'Can differ from patent_disruption at any grant year.'),
        'F_all': ("Foundation share: fraction of P's citers in the window (y - y_P >= 0 on grant "
                  "years) that cite more of P's other in-window citers than of P's references (down > "
                  'up); a tie with up = down > 0 adds 0.5 to F and E. F + E + G = 1; null when P has '
                  'no citer in the window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_all': ("Extension share: fraction of P's in-window citers that cite more of P's references "
                  "than of P's other in-window citers (up > down), plus half of the up = down > 0 "
                  'ties; null when no in-window citer. Decomposition of Fang & Evans (2025), '
                  'arXiv:2510.03240.'),
        'G_all': ("Generalization share: fraction of P's in-window citers that cite none of P's "
                  "references and none of P's other in-window citers; null when no in-window citer. "
                  'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_all': ('Number of patents citing P in the window (y - y_P >= 0 on grant years) that cite '
                   "none of P's references. Stored as float; null where CD_all is null."),
        'nj_all': ("Number of patents citing P in the window that also cite at least one of P's "
                   'references.'),
        'nk_all': ('Number of patents granted in the window (y - y_P >= 0 on grant years) that cite at'
                   " least one of P's references but not P."),
    },
    'PatentView/output/patent_disruption_compare.parquet': {
        'window': ("CD window the row summarises: the string '_3', '_5', '_10' or '_all' (with leading"
                   ' underscore).'),
        'n_base_rows': ('Row count of patent_disruption.parquet (granted network) at run time, '
                        '8,062,166; the same on every row.'),
        'n_app_rows': ('Row count of patent_disruption_app.parquet (extended network), 8,460,168; the '
                       'same on every row.'),
        'n_app_only': ('Patents present only in the extended table (reachable only via '
                       'pre-grant-publication citations), 398,002; no patent is in the granted table '
                       'only.'),
        'n_paired': ('Patents present in both tables with CD for this window non-null in both; every '
                     'statistic below is over this set. Granted side = the pre-de-duplication build of'
                     ' patent_disruption (this ran 2026-09-02 before the dedup rebuild; base_mean '
                     'matches the old file), which differs from the current one by < 1e-4 in mean CD.'),
        'base_mean': ('Mean CD_w of the paired patents in the granted network (patent_disruption). '
                      'Granted side = the pre-de-duplication build of patent_disruption (this ran '
                      '2026-09-02 before the dedup rebuild; base_mean matches the old file), which '
                      'differs from the current one by < 1e-4 in mean CD.'),
        'app_mean': 'Mean CD_w of the paired patents in the extended network (patent_disruption_app).',
        'delta': ('Mean of (extended - granted) CD_w over paired patents = app_mean - base_mean; '
                  'negative means counting pre-grant-publication citations makes patents look more '
                  'consolidating.'),
        'pearson': 'Pearson correlation of CD_w, granted vs extended, over all paired patents.',
        'spearman': ('Spearman rank correlation of CD_w, granted vs extended, estimated on a random '
                     'sample of min(1,000,000, n_paired) paired patents (numpy seed 0).'),
        'pct_down': 'Percent (0-100) of paired patents whose CD_w is lower in the extended network.',
        'pct_up': 'Percent (0-100) of paired patents whose CD_w is higher in the extended network.',
        'pct_same': 'Percent (0-100) of paired patents whose CD_w is exactly equal in both networks.',
        'd_ni': ('Mean over paired patents of (extended - granted) ni_w: added citers that cite none '
                 "of P's references."),
        'd_nj': ('Mean over paired patents of (extended - granted) nj_w: added citers that also cite '
                 "P's references."),
        'd_nk': ("Mean over paired patents of (extended - granted) nk_w: added patents citing P's "
                 'references but not P.'),
    },
    'PatentView/output/patent_feg_disruption_trend.parquet': {
        'year': ('Grant year of the patent cohort (patent_metadata.grant_year), 1976-2024 (2025 '
                 'dropped).'),
        'n': ('Number of utility patents granted in that year with CD_all defined (cited at least once'
              ' in the granted network), i.e. the patents averaged. Built 2026-08-31 from the '
              'pre-de-duplication patent_disruption (values match that file; the current file shifts '
              'yearly CD means by ~1e-4).'),
        'CD_3_mean': ("Mean over the year's patents of patent_disruption.CD_3, the CD disruption index"
                      ' in window 3; nulls are skipped, so it can average fewer than n patents. Recent'
                      ' cohorts are right-truncated. Built 2026-08-31 from the pre-de-duplication '
                      'patent_disruption (values match that file; the current file shifts yearly CD '
                      'means by ~1e-4).'),
        'F_3_mean': ("Mean over the year's patents of patent_disruption.F_3, the Foundation share F in"
                     ' window 3; nulls are skipped, so it can average fewer than n patents. Recent '
                     'cohorts are right-truncated. Decomposition of Fang & Evans (2025), '
                     'arXiv:2510.03240.'),
        'E_3_mean': ("Mean over the year's patents of patent_disruption.E_3, the Extension share E in "
                     'window 3; nulls are skipped, so it can average fewer than n patents. Recent '
                     'cohorts are right-truncated. Decomposition of Fang & Evans (2025), '
                     'arXiv:2510.03240.'),
        'G_3_mean': ("Mean over the year's patents of patent_disruption.G_3, the Generalization share "
                     'G in window 3; nulls are skipped, so it can average fewer than n patents. Recent'
                     ' cohorts are right-truncated. Decomposition of Fang & Evans (2025), '
                     'arXiv:2510.03240.'),
        'ni_3_mean': ("Mean over the year's patents of patent_disruption.ni_3, the ni (citers that "
                      "cite none of the patent's references, a count) in window 3; nulls are skipped, "
                      'so it can average fewer than n patents. Recent cohorts are right-truncated.'),
        'nj_3_mean': ("Mean over the year's patents of patent_disruption.nj_3, the nj (citers that "
                      "also cite the patent's references, a count) in window 3; nulls are skipped, so "
                      'it can average fewer than n patents. Recent cohorts are right-truncated.'),
        'nk_3_mean': ("Mean over the year's patents of patent_disruption.nk_3, the nk (patents citing "
                      'the references but not the patent, a count) in window 3; nulls are skipped, so '
                      'it can average fewer than n patents. Recent cohorts are right-truncated.'),
        'njfrac_3_mean': ("Mean over the year's patents of nj_3 / (ni_3 + nj_3 + nk_3), the nj share "
                          'of the CD denominator (the code divides by ni+nj+nk, not ni+nj as '
                          'FIGSHARE_README says); patents with a zero denominator are skipped.'),
        'CD_5_mean': ("Mean over the year's patents of patent_disruption.CD_5, the CD disruption index"
                      ' in window 5; nulls are skipped, so it can average fewer than n patents. Recent'
                      ' cohorts are right-truncated.'),
        'F_5_mean': ("Mean over the year's patents of patent_disruption.F_5, the Foundation share F in"
                     ' window 5; nulls are skipped, so it can average fewer than n patents. Recent '
                     'cohorts are right-truncated. Decomposition of Fang & Evans (2025), '
                     'arXiv:2510.03240.'),
        'E_5_mean': ("Mean over the year's patents of patent_disruption.E_5, the Extension share E in "
                     'window 5; nulls are skipped, so it can average fewer than n patents. Recent '
                     'cohorts are right-truncated. Decomposition of Fang & Evans (2025), '
                     'arXiv:2510.03240.'),
        'G_5_mean': ("Mean over the year's patents of patent_disruption.G_5, the Generalization share "
                     'G in window 5; nulls are skipped, so it can average fewer than n patents. Recent'
                     ' cohorts are right-truncated. Decomposition of Fang & Evans (2025), '
                     'arXiv:2510.03240.'),
        'ni_5_mean': ("Mean over the year's patents of patent_disruption.ni_5, the ni (citers that "
                      "cite none of the patent's references, a count) in window 5; nulls are skipped, "
                      'so it can average fewer than n patents. Recent cohorts are right-truncated.'),
        'nj_5_mean': ("Mean over the year's patents of patent_disruption.nj_5, the nj (citers that "
                      "also cite the patent's references, a count) in window 5; nulls are skipped, so "
                      'it can average fewer than n patents. Recent cohorts are right-truncated.'),
        'nk_5_mean': ("Mean over the year's patents of patent_disruption.nk_5, the nk (patents citing "
                      'the references but not the patent, a count) in window 5; nulls are skipped, so '
                      'it can average fewer than n patents. Recent cohorts are right-truncated.'),
        'njfrac_5_mean': ("Mean over the year's patents of nj_5 / (ni_5 + nj_5 + nk_5), the nj share "
                          'of the CD denominator (the code divides by ni+nj+nk, not ni+nj as '
                          'FIGSHARE_README says); patents with a zero denominator are skipped.'),
        'CD_10_mean': ("Mean over the year's patents of patent_disruption.CD_10, the CD disruption "
                       'index in window 10; nulls are skipped, so it can average fewer than n patents.'
                       ' Recent cohorts are right-truncated.'),
        'F_10_mean': ("Mean over the year's patents of patent_disruption.F_10, the Foundation share F "
                      'in window 10; nulls are skipped, so it can average fewer than n patents. Recent'
                      ' cohorts are right-truncated. Decomposition of Fang & Evans (2025), '
                      'arXiv:2510.03240.'),
        'E_10_mean': ("Mean over the year's patents of patent_disruption.E_10, the Extension share E "
                      'in window 10; nulls are skipped, so it can average fewer than n patents. Recent'
                      ' cohorts are right-truncated. Decomposition of Fang & Evans (2025), '
                      'arXiv:2510.03240.'),
        'G_10_mean': ("Mean over the year's patents of patent_disruption.G_10, the Generalization "
                      'share G in window 10; nulls are skipped, so it can average fewer than n '
                      'patents. Recent cohorts are right-truncated. Decomposition of Fang & Evans '
                      '(2025), arXiv:2510.03240.'),
        'ni_10_mean': ("Mean over the year's patents of patent_disruption.ni_10, the ni (citers that "
                       "cite none of the patent's references, a count) in window 10; nulls are "
                       'skipped, so it can average fewer than n patents. Recent cohorts are '
                       'right-truncated.'),
        'nj_10_mean': ("Mean over the year's patents of patent_disruption.nj_10, the nj (citers that "
                       "also cite the patent's references, a count) in window 10; nulls are skipped, "
                       'so it can average fewer than n patents. Recent cohorts are right-truncated.'),
        'nk_10_mean': ("Mean over the year's patents of patent_disruption.nk_10, the nk (patents "
                       'citing the references but not the patent, a count) in window 10; nulls are '
                       'skipped, so it can average fewer than n patents. Recent cohorts are '
                       'right-truncated.'),
        'njfrac_10_mean': ("Mean over the year's patents of nj_10 / (ni_10 + nj_10 + nk_10), the nj "
                           'share of the CD denominator (the code divides by ni+nj+nk, not ni+nj as '
                           'FIGSHARE_README says); patents with a zero denominator are skipped.'),
        'CD_all_mean': ("Mean over the year's patents of patent_disruption.CD_all, the CD disruption "
                        'index in window all; nulls are skipped, so it can average fewer than n '
                        'patents. Recent cohorts are right-truncated.'),
        'F_all_mean': ("Mean over the year's patents of patent_disruption.F_all, the Foundation share "
                       'F in window all; nulls are skipped, so it can average fewer than n patents. '
                       'Recent cohorts are right-truncated. Decomposition of Fang & Evans (2025), '
                       'arXiv:2510.03240.'),
        'E_all_mean': ("Mean over the year's patents of patent_disruption.E_all, the Extension share E"
                       ' in window all; nulls are skipped, so it can average fewer than n patents. '
                       'Recent cohorts are right-truncated. Decomposition of Fang & Evans (2025), '
                       'arXiv:2510.03240.'),
        'G_all_mean': ("Mean over the year's patents of patent_disruption.G_all, the Generalization "
                       'share G in window all; nulls are skipped, so it can average fewer than n '
                       'patents. Recent cohorts are right-truncated. Decomposition of Fang & Evans '
                       '(2025), arXiv:2510.03240.'),
        'ni_all_mean': ("Mean over the year's patents of patent_disruption.ni_all, the ni (citers that"
                        " cite none of the patent's references, a count) in window all; nulls are "
                        'skipped, so it can average fewer than n patents. Recent cohorts are '
                        'right-truncated.'),
        'nj_all_mean': ("Mean over the year's patents of patent_disruption.nj_all, the nj (citers that"
                        " also cite the patent's references, a count) in window all; nulls are "
                        'skipped, so it can average fewer than n patents. Recent cohorts are '
                        'right-truncated.'),
        'nk_all_mean': ("Mean over the year's patents of patent_disruption.nk_all, the nk (patents "
                        'citing the references but not the patent, a count) in window all; nulls are '
                        'skipped, so it can average fewer than n patents. Recent cohorts are '
                        'right-truncated.'),
        'njfrac_all_mean': ("Mean over the year's patents of nj_all / (ni_all + nj_all + nk_all), the "
                            'nj share of the CD denominator (the code divides by ni+nj+nk, not ni+nj '
                            'as FIGSHARE_README says); patents with a zero denominator are skipped.'),
    },
    'PatentView/output/patent_hit_probability.parquet': {
        'patent_id': ("USPTO patent number as a string, without 'US' prefix or kind code (7-8 digits, "
                      "e.g. '10000000'). Every utility patent in patent_metadata that has a WIPO "
                      'sector (8,512,715), including never-cited ones.'),
        'wipo_sector': ("WIPO technology sector title of P's primary WIPO field (lowest "
                        "wipo_field_sequence in g_wipo_technology): 'Electrical engineering', "
                        "'Instruments', 'Chemistry', 'Mechanical engineering' or 'Other fields'. "
                        'Cohort key.'),
        'grant_year': "P's grant year (patent_metadata.grant_year), 1976-2025. Cohort key.",
        'pctl_C_3': ("Percentile of granted citations C_3 (patent_citation) within P's (wipo_sector, "
                     "grant_year) cohort, pandas rank(pct=True, method='min') = (1 + # cohort patents "
                     'with a smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero '
                     'counts share 1/cohort size.'),
        'pctl_C_5': ("Percentile of granted citations C_5 (patent_citation) within P's (wipo_sector, "
                     "grant_year) cohort, pandas rank(pct=True, method='min') = (1 + # cohort patents "
                     'with a smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero '
                     'counts share 1/cohort size.'),
        'pctl_C_10': ("Percentile of granted citations C_10 (patent_citation) within P's (wipo_sector,"
                      " grant_year) cohort, pandas rank(pct=True, method='min') = (1 + # cohort "
                      'patents with a smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top '
                      '1%; zero counts share 1/cohort size.'),
        'pctl_C_all': ("Percentile of granted citations C_all (patent_citation) within P's "
                       "(wipo_sector, grant_year) cohort, pandas rank(pct=True, method='min') = (1 + #"
                       ' cohort patents with a smaller count) / cohort size: (0, 1], not 0-100; >= '
                       '0.99 ~ top 1%; zero counts share 1/cohort size.'),
        'pctl_C_examiner_3': ('Percentile of examiner-flagged granted citations C_examiner_3 within '
                              "P's (wipo_sector, grant_year) cohort, pandas rank(pct=True, "
                              "method='min') = (1 + # cohort patents with a smaller count) / cohort "
                              'size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero counts share 1/cohort '
                              'size.'),
        'pctl_C_non_examiner_3': ('Percentile of non-examiner granted citations C_non_examiner_3 '
                                  "within P's (wipo_sector, grant_year) cohort, pandas rank(pct=True, "
                                  "method='min') = (1 + # cohort patents with a smaller count) / "
                                  'cohort size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero counts share'
                                  ' 1/cohort size.'),
        'pctl_C_unknown_3': ('Percentile of unknown-category granted citations C_unknown_3 (all zero '
                             "for cohorts after 2002) within P's (wipo_sector, grant_year) cohort, "
                             "pandas rank(pct=True, method='min') = (1 + # cohort patents with a "
                             'smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero '
                             'counts share 1/cohort size.'),
        'pctl_C_examiner_5': ('Percentile of examiner-flagged granted citations C_examiner_5 within '
                              "P's (wipo_sector, grant_year) cohort, pandas rank(pct=True, "
                              "method='min') = (1 + # cohort patents with a smaller count) / cohort "
                              'size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero counts share 1/cohort '
                              'size.'),
        'pctl_C_non_examiner_5': ('Percentile of non-examiner granted citations C_non_examiner_5 '
                                  "within P's (wipo_sector, grant_year) cohort, pandas rank(pct=True, "
                                  "method='min') = (1 + # cohort patents with a smaller count) / "
                                  'cohort size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero counts share'
                                  ' 1/cohort size.'),
        'pctl_C_unknown_5': ('Percentile of unknown-category granted citations C_unknown_5 (all zero '
                             "for cohorts after 2002) within P's (wipo_sector, grant_year) cohort, "
                             "pandas rank(pct=True, method='min') = (1 + # cohort patents with a "
                             'smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero '
                             'counts share 1/cohort size.'),
        'pctl_C_examiner_10': ('Percentile of examiner-flagged granted citations C_examiner_10 within '
                               "P's (wipo_sector, grant_year) cohort, pandas rank(pct=True, "
                               "method='min') = (1 + # cohort patents with a smaller count) / cohort "
                               'size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero counts share 1/cohort '
                               'size.'),
        'pctl_C_non_examiner_10': ('Percentile of non-examiner granted citations C_non_examiner_10 '
                                   "within P's (wipo_sector, grant_year) cohort, pandas rank(pct=True,"
                                   " method='min') = (1 + # cohort patents with a smaller count) / "
                                   'cohort size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero counts '
                                   'share 1/cohort size.'),
        'pctl_C_unknown_10': ('Percentile of unknown-category granted citations C_unknown_10 (all zero'
                              " for cohorts after 2002) within P's (wipo_sector, grant_year) cohort, "
                              "pandas rank(pct=True, method='min') = (1 + # cohort patents with a "
                              'smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero'
                              ' counts share 1/cohort size.'),
        'pctl_C_examiner_all': ('Percentile of examiner-flagged granted citations C_examiner_all '
                                "within P's (wipo_sector, grant_year) cohort, pandas rank(pct=True, "
                                "method='min') = (1 + # cohort patents with a smaller count) / cohort "
                                'size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero counts share 1/cohort'
                                ' size.'),
        'pctl_C_non_examiner_all': ('Percentile of non-examiner granted citations C_non_examiner_all '
                                    "within P's (wipo_sector, grant_year) cohort, pandas "
                                    "rank(pct=True, method='min') = (1 + # cohort patents with a "
                                    'smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top '
                                    '1%; zero counts share 1/cohort size.'),
        'pctl_C_unknown_all': ('Percentile of unknown-category granted citations C_unknown_all (all '
                               "zero for cohorts after 2002) within P's (wipo_sector, grant_year) "
                               "cohort, pandas rank(pct=True, method='min') = (1 + # cohort patents "
                               'with a smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top '
                               '1%; zero counts share 1/cohort size.'),
        'pctl_appC_3': ('Percentile of pre-grant-publication citations appC_3 (essentially all zero '
                        "for cohorts granted before 2001) within P's (wipo_sector, grant_year) cohort,"
                        " pandas rank(pct=True, method='min') = (1 + # cohort patents with a smaller "
                        'count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero counts share '
                        '1/cohort size.'),
        'pctl_appC_5': ('Percentile of pre-grant-publication citations appC_5 (essentially all zero '
                        "for cohorts granted before 2001) within P's (wipo_sector, grant_year) cohort,"
                        " pandas rank(pct=True, method='min') = (1 + # cohort patents with a smaller "
                        'count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero counts share '
                        '1/cohort size.'),
        'pctl_appC_10': ('Percentile of pre-grant-publication citations appC_10 (essentially all zero '
                         "for cohorts granted before 2001) within P's (wipo_sector, grant_year) "
                         "cohort, pandas rank(pct=True, method='min') = (1 + # cohort patents with a "
                         'smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero '
                         'counts share 1/cohort size.'),
        'pctl_appC_all': ('Percentile of pre-grant-publication citations appC_all (essentially all '
                          "zero for cohorts granted before 2001) within P's (wipo_sector, grant_year) "
                          "cohort, pandas rank(pct=True, method='min') = (1 + # cohort patents with a "
                          'smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero '
                          'counts share 1/cohort size.'),
        'pctl_appC_examiner_3': ('Percentile of examiner-flagged pre-grant-publication citations '
                                 "appC_examiner_3 within P's (wipo_sector, grant_year) cohort, pandas "
                                 "rank(pct=True, method='min') = (1 + # cohort patents with a smaller "
                                 'count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero '
                                 'counts share 1/cohort size.'),
        'pctl_appC_non_examiner_3': ('Percentile of non-examiner pre-grant-publication citations '
                                     "appC_non_examiner_3 within P's (wipo_sector, grant_year) cohort,"
                                     " pandas rank(pct=True, method='min') = (1 + # cohort patents "
                                     'with a smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 '
                                     '~ top 1%; zero counts share 1/cohort size.'),
        'pctl_appC_examiner_5': ('Percentile of examiner-flagged pre-grant-publication citations '
                                 "appC_examiner_5 within P's (wipo_sector, grant_year) cohort, pandas "
                                 "rank(pct=True, method='min') = (1 + # cohort patents with a smaller "
                                 'count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top 1%; zero '
                                 'counts share 1/cohort size.'),
        'pctl_appC_non_examiner_5': ('Percentile of non-examiner pre-grant-publication citations '
                                     "appC_non_examiner_5 within P's (wipo_sector, grant_year) cohort,"
                                     " pandas rank(pct=True, method='min') = (1 + # cohort patents "
                                     'with a smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 '
                                     '~ top 1%; zero counts share 1/cohort size.'),
        'pctl_appC_examiner_10': ('Percentile of examiner-flagged pre-grant-publication citations '
                                  "appC_examiner_10 within P's (wipo_sector, grant_year) cohort, "
                                  "pandas rank(pct=True, method='min') = (1 + # cohort patents with a "
                                  'smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top 1%; '
                                  'zero counts share 1/cohort size.'),
        'pctl_appC_non_examiner_10': ('Percentile of non-examiner pre-grant-publication citations '
                                      "appC_non_examiner_10 within P's (wipo_sector, grant_year) "
                                      "cohort, pandas rank(pct=True, method='min') = (1 + # cohort "
                                      'patents with a smaller count) / cohort size: (0, 1], not 0-100;'
                                      ' >= 0.99 ~ top 1%; zero counts share 1/cohort size.'),
        'pctl_appC_examiner_all': ('Percentile of examiner-flagged pre-grant-publication citations '
                                   "appC_examiner_all within P's (wipo_sector, grant_year) cohort, "
                                   "pandas rank(pct=True, method='min') = (1 + # cohort patents with a"
                                   ' smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top '
                                   '1%; zero counts share 1/cohort size.'),
        'pctl_appC_non_examiner_all': ('Percentile of non-examiner pre-grant-publication citations '
                                       "appC_non_examiner_all within P's (wipo_sector, grant_year) "
                                       "cohort, pandas rank(pct=True, method='min') = (1 + # cohort "
                                       'patents with a smaller count) / cohort size: (0, 1], not '
                                       '0-100; >= 0.99 ~ top 1%; zero counts share 1/cohort size.'),
        'pctl_uniqueC_3': ("Percentile of distinct citing patents uniqueC_3 within P's (wipo_sector, "
                           "grant_year) cohort, pandas rank(pct=True, method='min') = (1 + # cohort "
                           'patents with a smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ '
                           'top 1%; zero counts share 1/cohort size.'),
        'pctl_uniqueC_5': ("Percentile of distinct citing patents uniqueC_5 within P's (wipo_sector, "
                           "grant_year) cohort, pandas rank(pct=True, method='min') = (1 + # cohort "
                           'patents with a smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ '
                           'top 1%; zero counts share 1/cohort size.'),
        'pctl_uniqueC_10': ("Percentile of distinct citing patents uniqueC_10 within P's (wipo_sector,"
                            " grant_year) cohort, pandas rank(pct=True, method='min') = (1 + # cohort "
                            'patents with a smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~'
                            ' top 1%; zero counts share 1/cohort size.'),
        'pctl_uniqueC_all': ("Percentile of distinct citing patents uniqueC_all within P's "
                             "(wipo_sector, grant_year) cohort, pandas rank(pct=True, method='min') = "
                             '(1 + # cohort patents with a smaller count) / cohort size: (0, 1], not '
                             '0-100; >= 0.99 ~ top 1%; zero counts share 1/cohort size.'),
        'pctl_uniqueC_examiner_3': ('Percentile of distinct examiner-citing patents uniqueC_examiner_3'
                                    " within P's (wipo_sector, grant_year) cohort, pandas "
                                    "rank(pct=True, method='min') = (1 + # cohort patents with a "
                                    'smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top '
                                    '1%; zero counts share 1/cohort size.'),
        'pctl_uniqueC_examiner_5': ('Percentile of distinct examiner-citing patents uniqueC_examiner_5'
                                    " within P's (wipo_sector, grant_year) cohort, pandas "
                                    "rank(pct=True, method='min') = (1 + # cohort patents with a "
                                    'smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top '
                                    '1%; zero counts share 1/cohort size.'),
        'pctl_uniqueC_examiner_10': ('Percentile of distinct examiner-citing patents '
                                     "uniqueC_examiner_10 within P's (wipo_sector, grant_year) cohort,"
                                     " pandas rank(pct=True, method='min') = (1 + # cohort patents "
                                     'with a smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 '
                                     '~ top 1%; zero counts share 1/cohort size.'),
        'pctl_uniqueC_examiner_all': ('Percentile of distinct examiner-citing patents '
                                      "uniqueC_examiner_all within P's (wipo_sector, grant_year) "
                                      "cohort, pandas rank(pct=True, method='min') = (1 + # cohort "
                                      'patents with a smaller count) / cohort size: (0, 1], not 0-100;'
                                      ' >= 0.99 ~ top 1%; zero counts share 1/cohort size.'),
        'pctl_uniqueC_non_examiner_3': ('Percentile of distinct non-examiner citing patents '
                                        "uniqueC_non_examiner_3 within P's (wipo_sector, grant_year) "
                                        "cohort, pandas rank(pct=True, method='min') = (1 + # cohort "
                                        'patents with a smaller count) / cohort size: (0, 1], not '
                                        '0-100; >= 0.99 ~ top 1%; zero counts share 1/cohort size.'),
        'pctl_uniqueC_non_examiner_5': ('Percentile of distinct non-examiner citing patents '
                                        "uniqueC_non_examiner_5 within P's (wipo_sector, grant_year) "
                                        "cohort, pandas rank(pct=True, method='min') = (1 + # cohort "
                                        'patents with a smaller count) / cohort size: (0, 1], not '
                                        '0-100; >= 0.99 ~ top 1%; zero counts share 1/cohort size.'),
        'pctl_uniqueC_non_examiner_10': ('Percentile of distinct non-examiner citing patents '
                                         "uniqueC_non_examiner_10 within P's (wipo_sector, grant_year)"
                                         " cohort, pandas rank(pct=True, method='min') = (1 + # cohort"
                                         ' patents with a smaller count) / cohort size: (0, 1], not '
                                         '0-100; >= 0.99 ~ top 1%; zero counts share 1/cohort size.'),
        'pctl_uniqueC_non_examiner_all': ('Percentile of distinct non-examiner citing patents '
                                          "uniqueC_non_examiner_all within P's (wipo_sector, "
                                          "grant_year) cohort, pandas rank(pct=True, method='min') = "
                                          '(1 + # cohort patents with a smaller count) / cohort size: '
                                          '(0, 1], not 0-100; >= 0.99 ~ top 1%; zero counts share '
                                          '1/cohort size.'),
        'pctl_uniqueC_unknown_3': ('Percentile of distinct unknown-category citing patents '
                                   "uniqueC_unknown_3 within P's (wipo_sector, grant_year) cohort, "
                                   "pandas rank(pct=True, method='min') = (1 + # cohort patents with a"
                                   ' smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top '
                                   '1%; zero counts share 1/cohort size.'),
        'pctl_uniqueC_unknown_5': ('Percentile of distinct unknown-category citing patents '
                                   "uniqueC_unknown_5 within P's (wipo_sector, grant_year) cohort, "
                                   "pandas rank(pct=True, method='min') = (1 + # cohort patents with a"
                                   ' smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top '
                                   '1%; zero counts share 1/cohort size.'),
        'pctl_uniqueC_unknown_10': ('Percentile of distinct unknown-category citing patents '
                                    "uniqueC_unknown_10 within P's (wipo_sector, grant_year) cohort, "
                                    "pandas rank(pct=True, method='min') = (1 + # cohort patents with "
                                    'a smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 ~ top '
                                    '1%; zero counts share 1/cohort size.'),
        'pctl_uniqueC_unknown_all': ('Percentile of distinct unknown-category citing patents '
                                     "uniqueC_unknown_all within P's (wipo_sector, grant_year) cohort,"
                                     " pandas rank(pct=True, method='min') = (1 + # cohort patents "
                                     'with a smaller count) / cohort size: (0, 1], not 0-100; >= 0.99 '
                                     '~ top 1%; zero counts share 1/cohort size.'),
        'pctl_c3': ('Legacy alias: an exact copy of pctl_C_3 (percentile of granted citations C_3 '
                    'within WIPO sector x grant year, same 0-1 min-rank scale), kept under the short '
                    'name of the older file and downstream code.'),
        'pctl_c5': ('Legacy alias: an exact copy of pctl_C_5 (percentile of granted citations C_5 '
                    'within WIPO sector x grant year, same 0-1 min-rank scale), kept under the short '
                    'name of the older file and downstream code.'),
        'pctl_c10': ('Legacy alias: an exact copy of pctl_C_10 (percentile of granted citations C_10 '
                     'within WIPO sector x grant year, same 0-1 min-rank scale), kept under the short '
                     'name of the older file and downstream code.'),
        'pctl_call': ('Legacy alias: an exact copy of pctl_C_all (percentile of granted citations '
                      'C_all within WIPO sector x grant year, same 0-1 min-rank scale), kept under the'
                      ' short name of the older file and downstream code.'),
    },
    'PatentView/output/patent_inventor_country.parquet': {
        'patent_id': ("USPTO patent number as a string, without 'US' prefix or kind code (7-8 digits, "
                      "e.g. '10000000'; a few dozen 'RE...' ids that PatentsView types as utility). "
                      'Utility patents with >= 1 disambiguated inventor row (8,531,216 of 8,531,961).'),
        'n_inventors': ('Distinct PatentsView-disambiguated inventors on the patent (de-duplicated on '
                        'inventor_id, lowest sequence kept); equals the number of ids in '
                        'patent_metadata.inventor_list.'),
        'n_located': ('Inventors whose location_id on this patent resolves to a country in '
                      'g_location_disambiguated (<= n_inventors).'),
        'countries': ('Distinct ISO 3166-1 alpha-2 codes of the located inventors, sorted and '
                      "';'-joined (e.g. 'DE;US'); the address printed on this grant, not the "
                      "inventor's usual location. Null when no inventor is located. Namibia is 'NA'."),
        'n_countries': 'Number of codes in countries; 0 when countries is null.',
        'country_inventor_counts': ("Located inventors per country as 'CC:n' pairs, ';'-joined, "
                                    "ordered by count descending then code (e.g. 'US:3;JP:1'); counts "
                                    'sum to n_located; null when none is located.'),
        'first_inventor_country': ('ISO2 country of the first-listed (lowest inventor_sequence) '
                                   'inventor; null when that inventor is unlocated (the next located '
                                   'inventor is not substituted).'),
        'is_international': ('True when n_countries > 1 (located inventors in two or more countries); '
                             'False for 0 or 1.'),
        'assignee_countries': ("Distinct ISO2 codes of the patent's disambiguated assignees' locations"
                               " on this grant, sorted and ';'-joined; null when the patent has no "
                               'assignee or none is located.'),
    },
    'PatentView/output/patent_metadata.parquet': {
        'patent_id': ("USPTO patent number as a string, without 'US' prefix or kind code (7-8 digits, "
                      "e.g. '10000000'; a few dozen 'RE...' ids that PatentsView types as utility). "
                      "Universe: g_patent rows with patent_type 'utility' and a parseable grant date "
                      '(8,531,961).'),
        'grant_year': 'Calendar year of the grant (issue) date g_patent.patent_date, 1976-2025.',
        'filing_year': ('Year of the earliest filing_date in g_application for the patent; double '
                        'because nullable (null for 34 patents). A few source dates are implausible '
                        '(11 before 1900, 46 after the grant year).'),
        'ref_count': ('Backward references to US patents printed on the grant: number of '
                      'g_us_patent_citation rows with this patent as citing patent and a non-null '
                      'cited number, counting cited patents of any type, duplicate rows and '
                      'third-party citations; 0 if none. Larger than the utility-only reference sets '
                      'used by the citation/disruption tables.'),
        'cpc_code': ('Primary CPC classification: the cpc_group symbol (subclass + group/subgroup, '
                     "e.g. 'G01S7/4863') of the lowest cpc_sequence row in g_cpc_current, i.e. the "
                     'current CPC of the snapshot, not the CPC at grant; null for ~0.2% without CPC.'),
        'cpc_code_list': ('All distinct cpc_group symbols of the patent (inventive and additional), '
                          "ordered by cpc_sequence and ';'-joined; the first element is cpc_code."),
        'inventor_list': ('PatentsView disambiguated inventor_ids (g_inventor_disambiguated), '
                          "distinct, in inventor_sequence order, ';'-joined. Most ids embed name "
                          "fragments ('fl:jo_ln:marron-5'); others are 25-character hashes or UUIDs. A"
                          " few dozen ids contain ';' themselves, so split only where the next id "
                          'starts, or use n_inventors from patent_inventor_country.'),
        'assignee_list': ('PatentsView disambiguated assignee_ids (UUIDs, e.g. '
                          "'a45783ae-9cec-49bc-bc2e-7b064aaa5907'), distinct, in assignee_sequence "
                          "order, ';'-joined; null for ~9% of patents with no assignee. Opaque ids; an"
                          ' assignee can be an organisation or an individual person.'),
    },
    'PatentView/output/patent_reference.parquet': {
        'citing_id': ('Patent number (string, no prefix) of the granted US utility patent making the '
                      'reference. Rows are distinct (citing_id, cited_id, type); third-party citations'
                      ' dropped, both ends utility, and no grant-year lag filter (rows where the cited'
                      ' patent was granted after the citing one are kept).'),
        'cited_id': ('The cited document as cited: a granted utility patent number when type = '
                     "'granted'; an 11-digit pre-grant publication number (e.g. '20150201176' = "
                     "publication year + 7-digit serial) when type = 'application'. Join on grant_id, "
                     'not on this.'),
        'type': ("'granted' = reference to a granted patent (g_us_patent_citation); 'application' = "
                 'reference to a pre-grant publication (g_us_application_citation) that later issued '
                 "as grant_id. A patent citing both P and P's publication has two rows sharing "
                 'grant_id.'),
        'grant_id': ('Granted utility patent the cited document is (granted rows: = cited_id) or '
                     'became (application rows: via pg_granted_pgpubs_crosswalk); the join key to the '
                     'other patent tables. Never null in this build, because citations of publications'
                     ' that never issued (~25M) were dropped.'),
    },
    'PatentView/output/patent_sb.parquet': {
        'patent_id': ('USPTO patent number of a granted patent of ANY type: utility (digits), design '
                      "'D...', plant 'PP...', reissue 'RE...', SIR 'H...', defensive publication "
                      "'T...'; unlike the other tables not limited to utility. Only patents with >= 1 "
                      'dated citation.'),
        'SB_B': ("Ke et al. (2015) beauty coefficient from P's yearly citation counts c_t (t = citing "
                 "grant year - P's grant year >= 0): B = sum_{t=0..t_m} [((c_tm - c_0)/t_m) t + c_0 - "
                 'c_t] / max(1, c_t), t_m = first year of the maximum. 0 when the peak is in year 0; '
                 'can be negative; unitless.'),
        'SB_T': ('Awakening time in years since grant: the t <= t_m with the largest distance from the'
                 ' line through (0, c_0) and (t_m, c_tm); 0 when the peak is in year 0. Integer, 0-48.'),
        'n_cite': ('Citations the histogram was built from: g_us_patent_citation rows citing P from a '
                   'granted patent of any type with a non-negative grant-year lag (duplicates and '
                   'third-party rows included); >= 1.'),
    },
    'PatentView/output/patent_z_score.parquet': {
        'patent_id': ("USPTO patent number as a string, without 'US' prefix or kind code (7-8 digits, "
                      "e.g. '10000000'). Utility patents (patent_metadata) with >= 2 distinct "
                      "inventional CPC subclasses (g_cpc_current, cpc_type = 'inventional')."),
        'Z_median': ("Median over P's CPC-subclass pairs of the pair z-score at P's grant year. Kim et"
                     ' al. (2016) z = (o - mu) / sigma, mu = n_a n_b / N, sigma^2 = mu (1 - n_a/N) (N '
                     '- n_b)/(N - 1), with N, n_a, n_b, o counted over all patents with >= 2 '
                     'inventional subclasses granted up to and including the grant year; z < 0 = '
                     'atypical, z set to 0 when sigma = 0; in standard deviations.'),
        'Z_10pct': ("10th percentile (numpy, linear interpolation) of P's pair z-scores; same z "
                    'definition as Z_median.'),
        'Z_min': "Minimum of P's pair z-scores: its most atypical subclass pairing.",
        'n_pairs': ('Number of subclass pairs scored, k(k-1)/2 for k distinct inventional subclasses '
                    '(1-820).'),
    },
    'PatentView/output/z_score_pair.parquet': {
        'code_1': ("First CPC subclass of the pair (4-character inventional subclass, e.g. 'A43B'); "
                   'alphabetically before code_2.'),
        'code_2': 'Second CPC subclass of the pair, alphabetically after code_1.',
        'year': ('Grant year t at which the pair is scored (1976-2025); a row exists only if the pair '
                 'occurs on at least one patent granted in t.'),
        'Z_score': ('Pair z-score on the cumulative set through year t. Kim et al. (2016) z = (o - mu)'
                    ' / sigma, mu = n_a n_b / N, sigma^2 = mu (1 - n_a/N) (N - n_b)/(N - 1), with N, '
                    'n_a, n_b, o counted over all patents with >= 2 inventional subclasses granted up '
                    'to and including the grant year; z < 0 = atypical, z set to 0 when sigma = 0; in '
                    'standard deviations.'),
    },
    'PATSTAT/output/patstat_citation.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000); the cited '
                     'application. Only applications with at least one counted citation are rows; an '
                     'absent application received none (patstat_hit_probability fills the zeros).'),
        'C_3': ('Citation rows received from citing applications whose filing year is 0 to 3 years '
                "after this application's filing year (0 <= age <= 3, inclusive at both ends): every "
                'patstat_reference row with age >= 0 that is not replenished (third-party observations'
                ' removed upstream). One citing application can add several rows (several of its '
                'publications, several publications of the target, several origins), so C >= uniqueC.'),
        'C_examiner_3': ("The 'examiner' part of C_3 (citn_origin SEA, ISR, SUP, PRS, EXA, FOP or CH2:"
                         ' search-report, examination, opposition-filing and PCT chapter II '
                         'citations): citation rows within the same window whose bucket is examiner; '
                         'C_3 = C_examiner_3 + C_applicant_3 + C_other_3.'),
        'C_applicant_3': ("The 'applicant' part of C_3 (citn_origin APP: references submitted by the "
                          'applicant): citation rows within the same window whose bucket is applicant;'
                          ' C_3 = C_examiner_3 + C_applicant_3 + C_other_3.'),
        'C_other_3': ("The 'other' part of C_3 (citn_origin OPP, APL or blank: opposition-division and"
                      ' appeal citations): citation rows within the same window whose bucket is other;'
                      ' C_3 = C_examiner_3 + C_applicant_3 + C_other_3.'),
        'C_5': ('Citation rows received from citing applications whose filing year is 0 to 5 years '
                "after this application's filing year (0 <= age <= 5, inclusive at both ends): every "
                'patstat_reference row with age >= 0 that is not replenished (third-party observations'
                ' removed upstream). One citing application can add several rows (several of its '
                'publications, several publications of the target, several origins), so C >= uniqueC.'),
        'C_examiner_5': ("The 'examiner' part of C_5 (citn_origin SEA, ISR, SUP, PRS, EXA, FOP or CH2:"
                         ' search-report, examination, opposition-filing and PCT chapter II '
                         'citations): citation rows within the same window whose bucket is examiner; '
                         'C_5 = C_examiner_5 + C_applicant_5 + C_other_5.'),
        'C_applicant_5': ("The 'applicant' part of C_5 (citn_origin APP: references submitted by the "
                          'applicant): citation rows within the same window whose bucket is applicant;'
                          ' C_5 = C_examiner_5 + C_applicant_5 + C_other_5.'),
        'C_other_5': ("The 'other' part of C_5 (citn_origin OPP, APL or blank: opposition-division and"
                      ' appeal citations): citation rows within the same window whose bucket is other;'
                      ' C_5 = C_examiner_5 + C_applicant_5 + C_other_5.'),
        'C_10': ('Citation rows received from citing applications whose filing year is 0 to 10 years '
                 "after this application's filing year (0 <= age <= 10, inclusive at both ends): every"
                 ' patstat_reference row with age >= 0 that is not replenished (third-party '
                 'observations removed upstream). One citing application can add several rows (several'
                 ' of its publications, several publications of the target, several origins), so C >= '
                 'uniqueC.'),
        'C_examiner_10': ("The 'examiner' part of C_10 (citn_origin SEA, ISR, SUP, PRS, EXA, FOP or "
                          'CH2: search-report, examination, opposition-filing and PCT chapter II '
                          'citations): citation rows within the same window whose bucket is examiner; '
                          'C_10 = C_examiner_10 + C_applicant_10 + C_other_10.'),
        'C_applicant_10': ("The 'applicant' part of C_10 (citn_origin APP: references submitted by the"
                           ' applicant): citation rows within the same window whose bucket is '
                           'applicant; C_10 = C_examiner_10 + C_applicant_10 + C_other_10.'),
        'C_other_10': ("The 'other' part of C_10 (citn_origin OPP, APL or blank: opposition-division "
                       'and appeal citations): citation rows within the same window whose bucket is '
                       'other; C_10 = C_examiner_10 + C_applicant_10 + C_other_10.'),
        'C_all': ('Citation rows received from citing applications whose filing year is the same as or'
                  " later than this application's filing year (age >= 0, no upper bound: every year up"
                  ' to the 2023 snapshot): every patstat_reference row with age >= 0 that is not '
                  'replenished (third-party observations removed upstream). One citing application can'
                  ' add several rows (several of its publications, several publications of the target,'
                  ' several origins), so C >= uniqueC.'),
        'C_examiner_all': ("The 'examiner' part of C_all (citn_origin SEA, ISR, SUP, PRS, EXA, FOP or "
                           'CH2: search-report, examination, opposition-filing and PCT chapter II '
                           'citations): citation rows within the same window whose bucket is examiner;'
                           ' C_all = C_examiner_all + C_applicant_all + C_other_all.'),
        'C_applicant_all': ("The 'applicant' part of C_all (citn_origin APP: references submitted by "
                            'the applicant): citation rows within the same window whose bucket is '
                            'applicant; C_all = C_examiner_all + C_applicant_all + C_other_all.'),
        'C_other_all': ("The 'other' part of C_all (citn_origin OPP, APL or blank: opposition-division"
                        ' and appeal citations): citation rows within the same window whose bucket is '
                        'other; C_all = C_examiner_all + C_applicant_all + C_other_all.'),
        'uniqueC_3': ('Distinct citing applications whose filing year is 0 to 3 years after this '
                      "application's filing year (0 <= age <= 3, inclusive at both ends), each counted"
                      ' once however many rows it contributes; the de-duplicated impact count to use.'),
        'uniqueC_examiner_3': ('Distinct citing applications within the same window that cite this '
                               "application through at least one 'examiner'-bucket row (citn_origin "
                               'SEA, ISR, SUP, PRS, EXA, FOP or CH2: search-report, examination, '
                               'opposition-filing and PCT chapter II citations). A citer using several'
                               ' buckets counts in each, so the three bucket counts can sum to more '
                               'than uniqueC_3.'),
        'uniqueC_applicant_3': ('Distinct citing applications within the same window that cite this '
                                "application through at least one 'applicant'-bucket row (citn_origin "
                                'APP: references submitted by the applicant). A citer using several '
                                'buckets counts in each, so the three bucket counts can sum to more '
                                'than uniqueC_3.'),
        'uniqueC_other_3': ('Distinct citing applications within the same window that cite this '
                            "application through at least one 'other'-bucket row (citn_origin OPP, APL"
                            ' or blank: opposition-division and appeal citations). A citer using '
                            'several buckets counts in each, so the three bucket counts can sum to '
                            'more than uniqueC_3.'),
        'uniqueC_5': ('Distinct citing applications whose filing year is 0 to 5 years after this '
                      "application's filing year (0 <= age <= 5, inclusive at both ends), each counted"
                      ' once however many rows it contributes; the de-duplicated impact count to use.'),
        'uniqueC_examiner_5': ('Distinct citing applications within the same window that cite this '
                               "application through at least one 'examiner'-bucket row (citn_origin "
                               'SEA, ISR, SUP, PRS, EXA, FOP or CH2: search-report, examination, '
                               'opposition-filing and PCT chapter II citations). A citer using several'
                               ' buckets counts in each, so the three bucket counts can sum to more '
                               'than uniqueC_5.'),
        'uniqueC_applicant_5': ('Distinct citing applications within the same window that cite this '
                                "application through at least one 'applicant'-bucket row (citn_origin "
                                'APP: references submitted by the applicant). A citer using several '
                                'buckets counts in each, so the three bucket counts can sum to more '
                                'than uniqueC_5.'),
        'uniqueC_other_5': ('Distinct citing applications within the same window that cite this '
                            "application through at least one 'other'-bucket row (citn_origin OPP, APL"
                            ' or blank: opposition-division and appeal citations). A citer using '
                            'several buckets counts in each, so the three bucket counts can sum to '
                            'more than uniqueC_5.'),
        'uniqueC_10': ('Distinct citing applications whose filing year is 0 to 10 years after this '
                       "application's filing year (0 <= age <= 10, inclusive at both ends), each "
                       'counted once however many rows it contributes; the de-duplicated impact count '
                       'to use.'),
        'uniqueC_examiner_10': ('Distinct citing applications within the same window that cite this '
                                "application through at least one 'examiner'-bucket row (citn_origin "
                                'SEA, ISR, SUP, PRS, EXA, FOP or CH2: search-report, examination, '
                                'opposition-filing and PCT chapter II citations). A citer using '
                                'several buckets counts in each, so the three bucket counts can sum to'
                                ' more than uniqueC_10.'),
        'uniqueC_applicant_10': ('Distinct citing applications within the same window that cite this '
                                 "application through at least one 'applicant'-bucket row (citn_origin"
                                 ' APP: references submitted by the applicant). A citer using several '
                                 'buckets counts in each, so the three bucket counts can sum to more '
                                 'than uniqueC_10.'),
        'uniqueC_other_10': ('Distinct citing applications within the same window that cite this '
                             "application through at least one 'other'-bucket row (citn_origin OPP, "
                             'APL or blank: opposition-division and appeal citations). A citer using '
                             'several buckets counts in each, so the three bucket counts can sum to '
                             'more than uniqueC_10.'),
        'uniqueC_all': ('Distinct citing applications whose filing year is the same as or later than '
                        "this application's filing year (age >= 0, no upper bound: every year up to "
                        'the 2023 snapshot), each counted once however many rows it contributes; the '
                        'de-duplicated impact count to use.'),
        'uniqueC_examiner_all': ('Distinct citing applications within the same window that cite this '
                                 "application through at least one 'examiner'-bucket row (citn_origin "
                                 'SEA, ISR, SUP, PRS, EXA, FOP or CH2: search-report, examination, '
                                 'opposition-filing and PCT chapter II citations). A citer using '
                                 'several buckets counts in each, so the three bucket counts can sum '
                                 'to more than uniqueC_all.'),
        'uniqueC_applicant_all': ('Distinct citing applications within the same window that cite this '
                                  "application through at least one 'applicant'-bucket row "
                                  '(citn_origin APP: references submitted by the applicant). A citer '
                                  'using several buckets counts in each, so the three bucket counts '
                                  'can sum to more than uniqueC_all.'),
        'uniqueC_other_all': ('Distinct citing applications within the same window that cite this '
                              "application through at least one 'other'-bucket row (citn_origin OPP, "
                              'APL or blank: opposition-division and appeal citations). A citer using '
                              'several buckets counts in each, so the three bucket counts can sum to '
                              'more than uniqueC_all.'),
    },
    'PATSTAT/output/patstat_citation_trend.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000); the cited '
                     'application. One row per (application, citing year) with at least one counted '
                     'citation.'),
        'filing_year': ("Clock year of the cited application: the application's filing year "
                        '(tls201.appln_filing_year, 1900-2023).'),
        'cite_year': ('Filing year of the citing applications counted in this row (the citing '
                      "application's clock year, not the publication year of the citation)."),
        'yrs_since_filing': ("Years since the cited application's filing year: cite_year - filing_year"
                             ' (integer, >= 0; ps.EDGE_WHERE drops negative ages).'),
        'C': ('Citation rows (patstat_reference rows, not replenished) received from applications of '
              'this citing year; one citing application can add several rows. Summing over years gives'
              ' C_all of patstat_citation.'),
        'C_examiner': ("The 'examiner' part of C in this year (citn_origin SEA, ISR, SUP, PRS, EXA, "
                       'FOP or CH2: search-report, examination, opposition-filing and PCT chapter II '
                       'citations); C = C_examiner + C_applicant + C_other.'),
        'uniqueC': ('Distinct citing applications in this citing year. A citer has one clock year, so '
                    'the yearly values sum exactly to uniqueC_all of patstat_citation.'),
    },
    'PATSTAT/output/patstat_disruption.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000); every node of '
                     'the de-duplicated application citation graph (distinct citing -> cited pairs '
                     'from patstat_reference with age >= 0, not replenished), as citer or cited. Nodes'
                     ' that are never cited have NULL CD/F/E/G and -1 in ni/nj/nk.'),
        'CD_3': ('CD disruption index (ni_3 - nj_3) / (ni_3 + nj_3 + nk_3) over applications dated 0 '
                 "to 3 years after the focal application's filing year (0 <= age <= 3); in [-1, 1]. "
                 'NULL when the window holds neither a citer nor a citer of a reference (then ni/nj/nk'
                 ' = -1); 0 when it has no citer but its references do (ni = nj = 0, nk > 0).'),
        'F_3': ('Foundation share: fraction of the citers dated 0 to 3 years after the focal '
                "application's filing year (0 <= age <= 3) for which down > up, where up = how many of"
                ' its references (the applications it cites with age >= 0) the citer also cites and '
                "down = how many of the focal's other citers in the same window it cites; ties with up"
                ' = down > 0 count half F, half E. NULL when there is no citer in the window. F + E + '
                'G = 1. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_3': ('Extension share: fraction of the citers dated 0 to 3 years after the focal '
                "application's filing year (0 <= age <= 3) with up > down (citer cites more of the "
                "focal's references than of its other in-window citers), plus half of the up = down > "
                '0 ties. NULL when there is no citer in the window. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'G_3': ('Generalization share: fraction of the citers dated 0 to 3 years after the focal '
                "application's filing year (0 <= age <= 3) with up = down = 0 (cite neither the "
                "focal's references nor its other in-window citers). NULL when there is no citer in "
                'the window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_3': ("Citers dated 0 to 3 years after the focal application's filing year (0 <= age <= 3) "
                 'that cite none of its references (the applications it cites with age >= 0) (count); '
                 "-1 is the sentinel for 'nothing in the window' (CD_3 NULL), not a count."),
        'nj_3': ("Citers dated 0 to 3 years after the focal application's filing year (0 <= age <= 3) "
                 'that also cite at least one of its references (the applications it cites with age >='
                 ' 0) (count); -1 sentinel when nothing is in the window.'),
        'nk_3': ("Applications dated 0 to 3 years after the focal application's filing year (0 <= age "
                 "<= 3) that cite at least one of the focal's references but not the focal itself "
                 '(distinct citers of the references minus nj, focal excluded); -1 sentinel when '
                 'nothing is in the window.'),
        'CD_5': ('CD disruption index (ni_5 - nj_5) / (ni_5 + nj_5 + nk_5) over applications dated 0 '
                 "to 5 years after the focal application's filing year (0 <= age <= 5); in [-1, 1]. "
                 'NULL when the window holds neither a citer nor a citer of a reference (then ni/nj/nk'
                 ' = -1); 0 when it has no citer but its references do (ni = nj = 0, nk > 0).'),
        'F_5': ('Foundation share: fraction of the citers dated 0 to 5 years after the focal '
                "application's filing year (0 <= age <= 5) for which down > up, where up = how many of"
                ' its references (the applications it cites with age >= 0) the citer also cites and '
                "down = how many of the focal's other citers in the same window it cites; ties with up"
                ' = down > 0 count half F, half E. NULL when there is no citer in the window. F + E + '
                'G = 1. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_5': ('Extension share: fraction of the citers dated 0 to 5 years after the focal '
                "application's filing year (0 <= age <= 5) with up > down (citer cites more of the "
                "focal's references than of its other in-window citers), plus half of the up = down > "
                '0 ties. NULL when there is no citer in the window. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'G_5': ('Generalization share: fraction of the citers dated 0 to 5 years after the focal '
                "application's filing year (0 <= age <= 5) with up = down = 0 (cite neither the "
                "focal's references nor its other in-window citers). NULL when there is no citer in "
                'the window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_5': ("Citers dated 0 to 5 years after the focal application's filing year (0 <= age <= 5) "
                 'that cite none of its references (the applications it cites with age >= 0) (count); '
                 "-1 is the sentinel for 'nothing in the window' (CD_5 NULL), not a count."),
        'nj_5': ("Citers dated 0 to 5 years after the focal application's filing year (0 <= age <= 5) "
                 'that also cite at least one of its references (the applications it cites with age >='
                 ' 0) (count); -1 sentinel when nothing is in the window.'),
        'nk_5': ("Applications dated 0 to 5 years after the focal application's filing year (0 <= age "
                 "<= 5) that cite at least one of the focal's references but not the focal itself "
                 '(distinct citers of the references minus nj, focal excluded); -1 sentinel when '
                 'nothing is in the window.'),
        'CD_10': ('CD disruption index (ni_10 - nj_10) / (ni_10 + nj_10 + nk_10) over applications '
                  "dated 0 to 10 years after the focal application's filing year (0 <= age <= 10); in "
                  '[-1, 1]. NULL when the window holds neither a citer nor a citer of a reference '
                  '(then ni/nj/nk = -1); 0 when it has no citer but its references do (ni = nj = 0, nk'
                  ' > 0).'),
        'F_10': ('Foundation share: fraction of the citers dated 0 to 10 years after the focal '
                 "application's filing year (0 <= age <= 10) for which down > up, where up = how many "
                 'of its references (the applications it cites with age >= 0) the citer also cites and'
                 " down = how many of the focal's other citers in the same window it cites; ties with "
                 'up = down > 0 count half F, half E. NULL when there is no citer in the window. F + E'
                 ' + G = 1. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_10': ('Extension share: fraction of the citers dated 0 to 10 years after the focal '
                 "application's filing year (0 <= age <= 10) with up > down (citer cites more of the "
                 "focal's references than of its other in-window citers), plus half of the up = down >"
                 ' 0 ties. NULL when there is no citer in the window. Decomposition of Fang & Evans '
                 '(2025), arXiv:2510.03240.'),
        'G_10': ('Generalization share: fraction of the citers dated 0 to 10 years after the focal '
                 "application's filing year (0 <= age <= 10) with up = down = 0 (cite neither the "
                 "focal's references nor its other in-window citers). NULL when there is no citer in "
                 'the window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_10': ("Citers dated 0 to 10 years after the focal application's filing year (0 <= age <= "
                  '10) that cite none of its references (the applications it cites with age >= 0) '
                  "(count); -1 is the sentinel for 'nothing in the window' (CD_10 NULL), not a count."),
        'nj_10': ("Citers dated 0 to 10 years after the focal application's filing year (0 <= age <= "
                  '10) that also cite at least one of its references (the applications it cites with '
                  'age >= 0) (count); -1 sentinel when nothing is in the window.'),
        'nk_10': ("Applications dated 0 to 10 years after the focal application's filing year (0 <= "
                  "age <= 10) that cite at least one of the focal's references but not the focal "
                  'itself (distinct citers of the references minus nj, focal excluded); -1 sentinel '
                  'when nothing is in the window.'),
        'CD_all': ('CD disruption index (ni_all - nj_all) / (ni_all + nj_all + nk_all) over '
                   "applications dated at any time from the focal application's filing year on (age >="
                   ' 0); in [-1, 1]. NULL when the window holds neither a citer nor a citer of a '
                   'reference (then ni/nj/nk = -1); 0 when it has no citer but its references do (ni ='
                   ' nj = 0, nk > 0).'),
        'F_all': ('Foundation share: fraction of the citers dated at any time from the focal '
                  "application's filing year on (age >= 0) for which down > up, where up = how many of"
                  ' its references (the applications it cites with age >= 0) the citer also cites and '
                  "down = how many of the focal's other citers in the same window it cites; ties with "
                  'up = down > 0 count half F, half E. NULL when there is no citer in the window. F + '
                  'E + G = 1. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_all': ('Extension share: fraction of the citers dated at any time from the focal '
                  "application's filing year on (age >= 0) with up > down (citer cites more of the "
                  "focal's references than of its other in-window citers), plus half of the up = down "
                  '> 0 ties. NULL when there is no citer in the window. Decomposition of Fang & Evans '
                  '(2025), arXiv:2510.03240.'),
        'G_all': ('Generalization share: fraction of the citers dated at any time from the focal '
                  "application's filing year on (age >= 0) with up = down = 0 (cite neither the "
                  "focal's references nor its other in-window citers). NULL when there is no citer in "
                  'the window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_all': ("Citers dated at any time from the focal application's filing year on (age >= 0) "
                   'that cite none of its references (the applications it cites with age >= 0) '
                   "(count); -1 is the sentinel for 'nothing in the window' (CD_all NULL), not a "
                   'count.'),
        'nj_all': ("Citers dated at any time from the focal application's filing year on (age >= 0) "
                   'that also cite at least one of its references (the applications it cites with age '
                   '>= 0) (count); -1 sentinel when nothing is in the window.'),
        'nk_all': ("Applications dated at any time from the focal application's filing year on (age >="
                   " 0) that cite at least one of the focal's references but not the focal itself "
                   '(distinct citers of the references minus nj, focal excluded); -1 sentinel when '
                   'nothing is in the window.'),
        'pctl_year': ("CD-percentile cohort year: the application's filing year "
                      '(patstat_metadata.filing_year).'),
        'pctl_group': ('CD-percentile cohort group: the CPC Section letter (A-H or Y) of '
                       'patstat_metadata.cpc_code; NULL when there is no CPC code, and then every '
                       'CD_*_pctl column is NULL.'),
        'CD_3_pctl': ('Minimum-rank percentile of CD_3 within its pctl_year x pctl_group cohort, among'
                      ' applications with a non-NULL CD_3: rank() / n on ascending CD, ties share the '
                      'lowest rank; in (0, 1], higher = more disruptive. NULL when CD_3 or pctl_group '
                      'is NULL.'),
        'CD_3_pctl_cume': ("Cumulative percentile of CD_3 in the same cohort: share of the cohort's "
                           'non-NULL CD_3 values <= this value (ties inclusive); in (0, 1], always >= '
                           "CD_3_pctl, and differs from it inside CD's large tie blocks (e.g. many CD "
                           '= 1 or 0). NULL when CD_3 or pctl_group is NULL.'),
        'CD_5_pctl': ('Minimum-rank percentile of CD_5 within its pctl_year x pctl_group cohort, among'
                      ' applications with a non-NULL CD_5: rank() / n on ascending CD, ties share the '
                      'lowest rank; in (0, 1], higher = more disruptive. NULL when CD_5 or pctl_group '
                      'is NULL.'),
        'CD_5_pctl_cume': ("Cumulative percentile of CD_5 in the same cohort: share of the cohort's "
                           'non-NULL CD_5 values <= this value (ties inclusive); in (0, 1], always >= '
                           "CD_5_pctl, and differs from it inside CD's large tie blocks (e.g. many CD "
                           '= 1 or 0). NULL when CD_5 or pctl_group is NULL.'),
        'CD_10_pctl': ('Minimum-rank percentile of CD_10 within its pctl_year x pctl_group cohort, '
                       'among applications with a non-NULL CD_10: rank() / n on ascending CD, ties '
                       'share the lowest rank; in (0, 1], higher = more disruptive. NULL when CD_10 or'
                       ' pctl_group is NULL.'),
        'CD_10_pctl_cume': ("Cumulative percentile of CD_10 in the same cohort: share of the cohort's "
                            'non-NULL CD_10 values <= this value (ties inclusive); in (0, 1], always '
                            ">= CD_10_pctl, and differs from it inside CD's large tie blocks (e.g. "
                            'many CD = 1 or 0). NULL when CD_10 or pctl_group is NULL.'),
        'CD_all_pctl': ('Minimum-rank percentile of CD_all within its pctl_year x pctl_group cohort, '
                        'among applications with a non-NULL CD_all: rank() / n on ascending CD, ties '
                        'share the lowest rank; in (0, 1], higher = more disruptive. NULL when CD_all '
                        'or pctl_group is NULL.'),
        'CD_all_pctl_cume': ('Cumulative percentile of CD_all in the same cohort: share of the '
                             "cohort's non-NULL CD_all values <= this value (ties inclusive); in (0, "
                             "1], always >= CD_all_pctl, and differs from it inside CD's large tie "
                             'blocks (e.g. many CD = 1 or 0). NULL when CD_all or pctl_group is NULL.'),
    },
    'PATSTAT/output/patstat_disruption_trend.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000); a focal '
                     'application with at least one citer in the de-duplicated graph. One row per '
                     '(application, year) in which ni_new, nj_new or nk_new is non-zero; years without'
                     ' a change have no row.'),
        'filing_year': ("Clock year of the focal application: the application's filing year "
                        '(tls201.appln_filing_year, 1900-2023).'),
        'cite_year': ('Calendar filing year of this row = filing_year + yrs_since_filing; the year in '
                      'which the new citers / co-citers counted in *_new appeared (up to 2023).'),
        'yrs_since_filing': ("Years since the focal application's filing year (>= 0); the row at age w"
                             ' (or the last row before it) carries the window-w values of '
                             'patstat_disruption.'),
        'ni_new': ('Citers of the focal whose filing year is exactly this year and that cite none of '
                   'its references.'),
        'nj_new': ('Citers of the focal whose filing year is exactly this year and that also cite at '
                   'least one of its references.'),
        'nk_new': ("Applications of exactly this year that cite at least one of the focal's references"
                   ' but not the focal (focal excluded).'),
        'ni': ("Cumulative ni from age 0 through this row's age; at age w it equals ni_w of "
               'patstat_disruption and the last row equals ni_all (checked on every focal '
               'application).'),
    },
    'PATSTAT/output/patstat_disruption_trend_summary.parquet': {
        'filing_year': ("Cohort year of the focal documents: the application's filing year "
                        '(tls201.appln_filing_year, 1900-2023).'),
        'yrs_since_filing': "Years since the cohort's filing year (>= 0).",
        'n_CD': ('Number of patstat_disruption_trend rows in this (filing_year, yrs_since_filing) cell'
                 ' with a finite CD. Trend rows exist only for years in which a focal application '
                 'gained a new citer or co-citer, so this counts those applications, not every cohort '
                 'member.'),
        'CD_mean': ('Mean cumulative CD over the n_CD trend rows of this (filing_year, '
                    'yrs_since_filing) cell (only applications with a change in exactly this year; '
                    'values are not carried forward for the others).'),
        'n_F': ('Number of patstat_disruption_trend rows in this (filing_year, yrs_since_filing) cell '
                'with a finite F. Trend rows exist only for years in which a focal application gained '
                'a new citer or co-citer, so this counts those applications, not every cohort member.'),
        'F_mean': ('Mean cumulative F (Foundation share) over the n_F trend rows of this (filing_year,'
                   ' yrs_since_filing) cell (only applications with a change in exactly this year; '
                   'values are not carried forward for the others). NULL when n_F = 0. Decomposition '
                   'of Fang & Evans (2025), arXiv:2510.03240.'),
        'n_E': ('Number of patstat_disruption_trend rows in this (filing_year, yrs_since_filing) cell '
                'with a finite E. Trend rows exist only for years in which a focal application gained '
                'a new citer or co-citer, so this counts those applications, not every cohort member.'),
        'E_mean': ('Mean cumulative E (Extension share) over the n_E trend rows of this (filing_year, '
                   'yrs_since_filing) cell (only applications with a change in exactly this year; '
                   'values are not carried forward for the others). NULL when n_E = 0. Decomposition '
                   'of Fang & Evans (2025), arXiv:2510.03240.'),
        'n_G': ('Number of patstat_disruption_trend rows in this (filing_year, yrs_since_filing) cell '
                'with a finite G. Trend rows exist only for years in which a focal application gained '
                'a new citer or co-citer, so this counts those applications, not every cohort member.'),
        'G_mean': ('Mean cumulative G (Generalization share) over the n_G trend rows of this '
                   '(filing_year, yrs_since_filing) cell (only applications with a change in exactly '
                   'this year; values are not carried forward for the others). NULL when n_G = 0. '
                   'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
    },
    'PATSTAT/output/patstat_feg_disruption_trend.parquet': {
        'year': "Cohort year: the application's filing year, 1900-2023.",
        'n': ('Number of applications of this cohort in patstat_disruption with a non-NULL CD_all, '
              'i.e. with at least one citer: the denominator of the `_all` means. The 3-, 5- and '
              '10-year ni / nj / nk / njfrac means are taken over the subset with something in that '
              'window.'),
        'CD_3_mean': ("Mean of CD_3 (window 3) over the cohort's applications with a non-NULL CD_3 "
                      '(NULLs ignored); NULL if none.'),
        'F_3_mean': ("Mean Foundation share F_3 over the cohort's applications with at least one citer"
                     ' in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans '
                     '(2025), arXiv:2510.03240.'),
        'E_3_mean': ("Mean Extension share E_3 over the cohort's applications with at least one citer "
                     'in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans '
                     '(2025), arXiv:2510.03240.'),
        'G_3_mean': ("Mean Generalization share G_3 over the cohort's applications with at least one "
                     'citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans'
                     ' (2025), arXiv:2510.03240.'),
        'ni_3_mean': ("Mean of ni_3 (citers that cite none of its references) over the cohort's "
                      'applications with something in the 3-year window: the -1 placeholder of a '
                      'application with nothing in it (no citer and nothing citing its references) is '
                      'read as NULL. NULL when no application of the cohort has anything in the window'
                      ' (the earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which '
                      'made this negative for early cohorts.'),
        'nj_3_mean': ('Mean of nj_3 (citers that also cite at least one of its references) over the '
                      "cohort's applications with something in the 3-year window: the -1 placeholder "
                      'of a application with nothing in it (no citer and nothing citing its '
                      'references) is read as NULL. NULL when no application of the cohort has '
                      'anything in the window (the earliest cohorts). Before 2026-10-03 the -1 rows '
                      'were averaged in, which made this negative for early cohorts.'),
        'nk_3_mean': ("Mean of nk_3 (documents citing its references but not it) over the cohort's "
                      'applications with something in the 3-year window: the -1 placeholder of a '
                      'application with nothing in it (no citer and nothing citing its references) is '
                      'read as NULL. NULL when no application of the cohort has anything in the window'
                      ' (the earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which '
                      'made this negative for early cohorts.'),
        'njfrac_3_mean': ('Mean of the per-application nj_3 / (ni_3 + nj_3 + nk_3), the share of the '
                          '3-year neighbourhood that cites both the application and its references, '
                          'over the applications with something in the window (the -1 placeholder is '
                          'read as NULL); NULL when there are none. Before 2026-10-03 the -1 rows '
                          'entered as (-1)/(-3) = 1/3 and pulled the mean toward 0.333.'),
        'CD_5_mean': ("Mean of CD_5 (window 5) over the cohort's applications with a non-NULL CD_5 "
                      '(NULLs ignored); NULL if none.'),
        'F_5_mean': ("Mean Foundation share F_5 over the cohort's applications with at least one citer"
                     ' in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans '
                     '(2025), arXiv:2510.03240.'),
        'E_5_mean': ("Mean Extension share E_5 over the cohort's applications with at least one citer "
                     'in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans '
                     '(2025), arXiv:2510.03240.'),
        'G_5_mean': ("Mean Generalization share G_5 over the cohort's applications with at least one "
                     'citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans'
                     ' (2025), arXiv:2510.03240.'),
        'ni_5_mean': ("Mean of ni_5 (citers that cite none of its references) over the cohort's "
                      'applications with something in the 5-year window: the -1 placeholder of a '
                      'application with nothing in it (no citer and nothing citing its references) is '
                      'read as NULL. NULL when no application of the cohort has anything in the window'
                      ' (the earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which '
                      'made this negative for early cohorts.'),
        'nj_5_mean': ('Mean of nj_5 (citers that also cite at least one of its references) over the '
                      "cohort's applications with something in the 5-year window: the -1 placeholder "
                      'of a application with nothing in it (no citer and nothing citing its '
                      'references) is read as NULL. NULL when no application of the cohort has '
                      'anything in the window (the earliest cohorts). Before 2026-10-03 the -1 rows '
                      'were averaged in, which made this negative for early cohorts.'),
        'nk_5_mean': ("Mean of nk_5 (documents citing its references but not it) over the cohort's "
                      'applications with something in the 5-year window: the -1 placeholder of a '
                      'application with nothing in it (no citer and nothing citing its references) is '
                      'read as NULL. NULL when no application of the cohort has anything in the window'
                      ' (the earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which '
                      'made this negative for early cohorts.'),
        'njfrac_5_mean': ('Mean of the per-application nj_5 / (ni_5 + nj_5 + nk_5), the share of the '
                          '5-year neighbourhood that cites both the application and its references, '
                          'over the applications with something in the window (the -1 placeholder is '
                          'read as NULL); NULL when there are none. Before 2026-10-03 the -1 rows '
                          'entered as (-1)/(-3) = 1/3 and pulled the mean toward 0.333.'),
        'CD_10_mean': ("Mean of CD_10 (window 10) over the cohort's applications with a non-NULL CD_10"
                       ' (NULLs ignored); NULL if none.'),
        'F_10_mean': ("Mean Foundation share F_10 over the cohort's applications with at least one "
                      'citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & '
                      'Evans (2025), arXiv:2510.03240.'),
        'E_10_mean': ("Mean Extension share E_10 over the cohort's applications with at least one "
                      'citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & '
                      'Evans (2025), arXiv:2510.03240.'),
        'G_10_mean': ("Mean Generalization share G_10 over the cohort's applications with at least one"
                      ' citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & '
                      'Evans (2025), arXiv:2510.03240.'),
        'ni_10_mean': ("Mean of ni_10 (citers that cite none of its references) over the cohort's "
                       'applications with something in the 10-year window: the -1 placeholder of a '
                       'application with nothing in it (no citer and nothing citing its references) is'
                       ' read as NULL. NULL when no application of the cohort has anything in the '
                       'window (the earliest cohorts). Before 2026-10-03 the -1 rows were averaged in,'
                       ' which made this negative for early cohorts.'),
        'nj_10_mean': ('Mean of nj_10 (citers that also cite at least one of its references) over the '
                       "cohort's applications with something in the 10-year window: the -1 placeholder"
                       ' of a application with nothing in it (no citer and nothing citing its '
                       'references) is read as NULL. NULL when no application of the cohort has '
                       'anything in the window (the earliest cohorts). Before 2026-10-03 the -1 rows '
                       'were averaged in, which made this negative for early cohorts.'),
        'nk_10_mean': ("Mean of nk_10 (documents citing its references but not it) over the cohort's "
                       'applications with something in the 10-year window: the -1 placeholder of a '
                       'application with nothing in it (no citer and nothing citing its references) is'
                       ' read as NULL. NULL when no application of the cohort has anything in the '
                       'window (the earliest cohorts). Before 2026-10-03 the -1 rows were averaged in,'
                       ' which made this negative for early cohorts.'),
        'njfrac_10_mean': ('Mean of the per-application nj_10 / (ni_10 + nj_10 + nk_10), the share of '
                           'the 10-year neighbourhood that cites both the application and its '
                           'references, over the applications with something in the window (the -1 '
                           'placeholder is read as NULL); NULL when there are none. Before 2026-10-03 '
                           'the -1 rows entered as (-1)/(-3) = 1/3 and pulled the mean toward 0.333.'),
        'CD_all_mean': ("Mean of CD_all (any age) over the cohort's applications with a non-NULL "
                        'CD_all (NULLs ignored); NULL if none.'),
        'F_all_mean': ("Mean Foundation share F_all over the cohort's applications with at least one "
                       'citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & '
                       'Evans (2025), arXiv:2510.03240.'),
        'E_all_mean': ("Mean Extension share E_all over the cohort's applications with at least one "
                       'citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & '
                       'Evans (2025), arXiv:2510.03240.'),
        'G_all_mean': ("Mean Generalization share G_all over the cohort's applications with at least "
                       'one citer in the window (NULLs ignored); NULL if none. Decomposition of Fang &'
                       ' Evans (2025), arXiv:2510.03240.'),
        'ni_all_mean': ('Mean of ni_all over the n applications of the cohort (all have ni/nj/nk_all '
                        '>= 0).'),
        'nj_all_mean': ('Mean of nj_all over the n applications of the cohort (all have ni/nj/nk_all '
                        '>= 0).'),
        'nk_all_mean': ('Mean of nk_all over the n applications of the cohort (all have ni/nj/nk_all '
                        '>= 0).'),
        'njfrac_all_mean': ('Mean over the n applications of nj_all / (ni_all + nj_all + nk_all), the '
                            'share of type-j (co-citing) documents.'),
    },
    'PATSTAT/output/patstat_hit_probability.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000); every '
                     'application of patstat_metadata with a non-NULL wipo_sector, cited or not.'),
        'wipo_sector': 'Cohort sector: patstat_metadata.wipo_sector (one of the five WIPO sectors).',
        'filing_year': ("Cohort year: the application's filing year (tls201.appln_filing_year, "
                        '1900-2023).'),
        'pctl_C_3': ('Percentile of C_3 (citation rows within 3 years) within the wipo_sector x '
                     'filing_year cohort: rank() / n with ties at the minimum rank (pandas rank method'
                     " 'min'), ascending, applications absent from patstat_citation counted as 0; in "
                     '(0, 1], higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_examiner_3': ('Percentile of C_examiner_3 (examiner-bucket citation rows within 3 '
                              'years) within the wipo_sector x filing_year cohort: rank() / n with '
                              "ties at the minimum rank (pandas rank method 'min'), ascending, "
                              'applications absent from patstat_citation counted as 0; in (0, 1], '
                              'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_applicant_3': ('Percentile of C_applicant_3 (applicant-bucket citation rows within 3 '
                               'years) within the wipo_sector x filing_year cohort: rank() / n with '
                               "ties at the minimum rank (pandas rank method 'min'), ascending, "
                               'applications absent from patstat_citation counted as 0; in (0, 1], '
                               'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_other_3': ('Percentile of C_other_3 (other-bucket citation rows within 3 years) within'
                           ' the wipo_sector x filing_year cohort: rank() / n with ties at the minimum'
                           " rank (pandas rank method 'min'), ascending, applications absent from "
                           'patstat_citation counted as 0; in (0, 1], higher = more cited, top 1 % <=>'
                           ' >= 0.99 (float32).'),
        'pctl_C_5': ('Percentile of C_5 (citation rows within 5 years) within the wipo_sector x '
                     'filing_year cohort: rank() / n with ties at the minimum rank (pandas rank method'
                     " 'min'), ascending, applications absent from patstat_citation counted as 0; in "
                     '(0, 1], higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_examiner_5': ('Percentile of C_examiner_5 (examiner-bucket citation rows within 5 '
                              'years) within the wipo_sector x filing_year cohort: rank() / n with '
                              "ties at the minimum rank (pandas rank method 'min'), ascending, "
                              'applications absent from patstat_citation counted as 0; in (0, 1], '
                              'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_applicant_5': ('Percentile of C_applicant_5 (applicant-bucket citation rows within 5 '
                               'years) within the wipo_sector x filing_year cohort: rank() / n with '
                               "ties at the minimum rank (pandas rank method 'min'), ascending, "
                               'applications absent from patstat_citation counted as 0; in (0, 1], '
                               'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_other_5': ('Percentile of C_other_5 (other-bucket citation rows within 5 years) within'
                           ' the wipo_sector x filing_year cohort: rank() / n with ties at the minimum'
                           " rank (pandas rank method 'min'), ascending, applications absent from "
                           'patstat_citation counted as 0; in (0, 1], higher = more cited, top 1 % <=>'
                           ' >= 0.99 (float32).'),
        'pctl_C_10': ('Percentile of C_10 (citation rows within 10 years) within the wipo_sector x '
                      'filing_year cohort: rank() / n with ties at the minimum rank (pandas rank '
                      "method 'min'), ascending, applications absent from patstat_citation counted as "
                      '0; in (0, 1], higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_examiner_10': ('Percentile of C_examiner_10 (examiner-bucket citation rows within 10 '
                               'years) within the wipo_sector x filing_year cohort: rank() / n with '
                               "ties at the minimum rank (pandas rank method 'min'), ascending, "
                               'applications absent from patstat_citation counted as 0; in (0, 1], '
                               'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_applicant_10': ('Percentile of C_applicant_10 (applicant-bucket citation rows within '
                                '10 years) within the wipo_sector x filing_year cohort: rank() / n '
                                "with ties at the minimum rank (pandas rank method 'min'), ascending, "
                                'applications absent from patstat_citation counted as 0; in (0, 1], '
                                'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_other_10': ('Percentile of C_other_10 (other-bucket citation rows within 10 years) '
                            'within the wipo_sector x filing_year cohort: rank() / n with ties at the '
                            "minimum rank (pandas rank method 'min'), ascending, applications absent "
                            'from patstat_citation counted as 0; in (0, 1], higher = more cited, top 1'
                            ' % <=> >= 0.99 (float32).'),
        'pctl_C_all': ('Percentile of C_all (citation rows at any age) within the wipo_sector x '
                       'filing_year cohort: rank() / n with ties at the minimum rank (pandas rank '
                       "method 'min'), ascending, applications absent from patstat_citation counted as"
                       ' 0; in (0, 1], higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_examiner_all': ('Percentile of C_examiner_all (examiner-bucket citation rows at any '
                                'age) within the wipo_sector x filing_year cohort: rank() / n with '
                                "ties at the minimum rank (pandas rank method 'min'), ascending, "
                                'applications absent from patstat_citation counted as 0; in (0, 1], '
                                'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_applicant_all': ('Percentile of C_applicant_all (applicant-bucket citation rows at any'
                                 ' age) within the wipo_sector x filing_year cohort: rank() / n with '
                                 "ties at the minimum rank (pandas rank method 'min'), ascending, "
                                 'applications absent from patstat_citation counted as 0; in (0, 1], '
                                 'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_other_all': ('Percentile of C_other_all (other-bucket citation rows at any age) within'
                             ' the wipo_sector x filing_year cohort: rank() / n with ties at the '
                             "minimum rank (pandas rank method 'min'), ascending, applications absent "
                             'from patstat_citation counted as 0; in (0, 1], higher = more cited, top '
                             '1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_3': ('Percentile of uniqueC_3 (distinct citing applications within 3 years) '
                           'within the wipo_sector x filing_year cohort: rank() / n with ties at the '
                           "minimum rank (pandas rank method 'min'), ascending, applications absent "
                           'from patstat_citation counted as 0; in (0, 1], higher = more cited, top 1 '
                           '% <=> >= 0.99 (float32).'),
        'pctl_uniqueC_examiner_3': ('Percentile of uniqueC_examiner_3 (distinct citing applications '
                                    'citing through the examiner bucket within 3 years) within the '
                                    'wipo_sector x filing_year cohort: rank() / n with ties at the '
                                    "minimum rank (pandas rank method 'min'), ascending, applications "
                                    'absent from patstat_citation counted as 0; in (0, 1], higher = '
                                    'more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_applicant_3': ('Percentile of uniqueC_applicant_3 (distinct citing applications '
                                     'citing through the applicant bucket within 3 years) within the '
                                     'wipo_sector x filing_year cohort: rank() / n with ties at the '
                                     "minimum rank (pandas rank method 'min'), ascending, applications"
                                     ' absent from patstat_citation counted as 0; in (0, 1], higher = '
                                     'more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_other_3': ('Percentile of uniqueC_other_3 (distinct citing applications citing '
                                 'through the other bucket within 3 years) within the wipo_sector x '
                                 'filing_year cohort: rank() / n with ties at the minimum rank (pandas'
                                 " rank method 'min'), ascending, applications absent from "
                                 'patstat_citation counted as 0; in (0, 1], higher = more cited, top 1'
                                 ' % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_5': ('Percentile of uniqueC_5 (distinct citing applications within 5 years) '
                           'within the wipo_sector x filing_year cohort: rank() / n with ties at the '
                           "minimum rank (pandas rank method 'min'), ascending, applications absent "
                           'from patstat_citation counted as 0; in (0, 1], higher = more cited, top 1 '
                           '% <=> >= 0.99 (float32).'),
        'pctl_uniqueC_examiner_5': ('Percentile of uniqueC_examiner_5 (distinct citing applications '
                                    'citing through the examiner bucket within 5 years) within the '
                                    'wipo_sector x filing_year cohort: rank() / n with ties at the '
                                    "minimum rank (pandas rank method 'min'), ascending, applications "
                                    'absent from patstat_citation counted as 0; in (0, 1], higher = '
                                    'more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_applicant_5': ('Percentile of uniqueC_applicant_5 (distinct citing applications '
                                     'citing through the applicant bucket within 5 years) within the '
                                     'wipo_sector x filing_year cohort: rank() / n with ties at the '
                                     "minimum rank (pandas rank method 'min'), ascending, applications"
                                     ' absent from patstat_citation counted as 0; in (0, 1], higher = '
                                     'more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_other_5': ('Percentile of uniqueC_other_5 (distinct citing applications citing '
                                 'through the other bucket within 5 years) within the wipo_sector x '
                                 'filing_year cohort: rank() / n with ties at the minimum rank (pandas'
                                 " rank method 'min'), ascending, applications absent from "
                                 'patstat_citation counted as 0; in (0, 1], higher = more cited, top 1'
                                 ' % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_10': ('Percentile of uniqueC_10 (distinct citing applications within 10 years) '
                            'within the wipo_sector x filing_year cohort: rank() / n with ties at the '
                            "minimum rank (pandas rank method 'min'), ascending, applications absent "
                            'from patstat_citation counted as 0; in (0, 1], higher = more cited, top 1'
                            ' % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_examiner_10': ('Percentile of uniqueC_examiner_10 (distinct citing applications '
                                     'citing through the examiner bucket within 10 years) within the '
                                     'wipo_sector x filing_year cohort: rank() / n with ties at the '
                                     "minimum rank (pandas rank method 'min'), ascending, applications"
                                     ' absent from patstat_citation counted as 0; in (0, 1], higher = '
                                     'more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_applicant_10': ('Percentile of uniqueC_applicant_10 (distinct citing '
                                      'applications citing through the applicant bucket within 10 '
                                      'years) within the wipo_sector x filing_year cohort: rank() / n '
                                      "with ties at the minimum rank (pandas rank method 'min'), "
                                      'ascending, applications absent from patstat_citation counted as'
                                      ' 0; in (0, 1], higher = more cited, top 1 % <=> >= 0.99 '
                                      '(float32).'),
        'pctl_uniqueC_other_10': ('Percentile of uniqueC_other_10 (distinct citing applications citing'
                                  ' through the other bucket within 10 years) within the wipo_sector x'
                                  ' filing_year cohort: rank() / n with ties at the minimum rank '
                                  "(pandas rank method 'min'), ascending, applications absent from "
                                  'patstat_citation counted as 0; in (0, 1], higher = more cited, top '
                                  '1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_all': ('Percentile of uniqueC_all (distinct citing applications at any age) '
                             'within the wipo_sector x filing_year cohort: rank() / n with ties at the'
                             " minimum rank (pandas rank method 'min'), ascending, applications absent"
                             ' from patstat_citation counted as 0; in (0, 1], higher = more cited, top'
                             ' 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_examiner_all': ('Percentile of uniqueC_examiner_all (distinct citing '
                                      'applications citing through the examiner bucket at any age) '
                                      'within the wipo_sector x filing_year cohort: rank() / n with '
                                      "ties at the minimum rank (pandas rank method 'min'), ascending,"
                                      ' applications absent from patstat_citation counted as 0; in (0,'
                                      ' 1], higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_applicant_all': ('Percentile of uniqueC_applicant_all (distinct citing '
                                       'applications citing through the applicant bucket at any age) '
                                       'within the wipo_sector x filing_year cohort: rank() / n with '
                                       "ties at the minimum rank (pandas rank method 'min'), "
                                       'ascending, applications absent from patstat_citation counted '
                                       'as 0; in (0, 1], higher = more cited, top 1 % <=> >= 0.99 '
                                       '(float32).'),
        'pctl_uniqueC_other_all': ('Percentile of uniqueC_other_all (distinct citing applications '
                                   'citing through the other bucket at any age) within the wipo_sector'
                                   ' x filing_year cohort: rank() / n with ties at the minimum rank '
                                   "(pandas rank method 'min'), ascending, applications absent from "
                                   'patstat_citation counted as 0; in (0, 1], higher = more cited, top'
                                   ' 1 % <=> >= 0.99 (float32).'),
        'pctl_c3': ('Legacy alias, identical to pctl_C_3 (percentile of citation rows C_3, not of '
                    'uniqueC), kept for readers using the PatentView short names.'),
        'pctl_c5': ('Legacy alias, identical to pctl_C_5 (percentile of citation rows C_5, not of '
                    'uniqueC), kept for readers using the PatentView short names.'),
        'pctl_c10': ('Legacy alias, identical to pctl_C_10 (percentile of citation rows C_10, not of '
                     'uniqueC), kept for readers using the PatentView short names.'),
        'pctl_call': ('Legacy alias, identical to pctl_C_all (percentile of citation rows C_all, not '
                      'of uniqueC), kept for readers using the PatentView short names.'),
    },
    'PATSTAT/output/patstat_inventor.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000); one row per '
                     'application with at least one inventor row in tls207.'),
        'inventor_list': ("Inventor PATSTAT person_ids as a ';'-joined string in invt_seq_nr order "
                          '(ties by person_id): a named person once at its lowest sequence, an unnamed'
                          ' placeholder record (empty tls206.person_name, e.g. person_id 263) once per'
                          ' slot, so its id can repeat. Person records, not disambiguated inventors; '
                          'identical to patstat_metadata.inventor_list.'),
        'n_inventors': ('Number of inventor slots = length of inventor_list (distinct named persons '
                        'plus each slot of an unnamed placeholder); team size under its PatentView '
                        'name. Not tls201.nb_inventors.'),
    },
    'PATSTAT/output/patstat_inventor_country.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000); one row per '
                     'application with at least one inventor row (same rows as patstat_inventor).'),
        'n_inventors': ('Inventor slots under the once-per-named-person / once-per-placeholder-slot '
                        'rule; identical to patstat_inventor.n_inventors.'),
        'n_located': ('Inventor slots whose person record has a two-letter country code '
                      '(tls206.person_ctry_code matching [A-Z]{2}; malformed codes read as unknown); '
                      '<= n_inventors.'),
        'countries': ("Distinct inventor country codes, sorted alphabetically, ';'-joined (e.g. "
                      "'AU;GB;US'); NULL if no inventor is located. Codes are the address country "
                      "recorded on that application's person record."),
        'n_countries': 'Number of codes in countries; 0 when countries is NULL.',
        'country_inventor_counts': ("Inventors per country as 'CC:n' pairs joined by ';', ordered by "
                                    "count descending then code (e.g. 'GB:4;AU:1;US:1'); counts sum to"
                                    ' n_located; NULL if none located.'),
        'first_inventor_country': ('Country of the lowest-sequence inventor; NULL when that inventor '
                                   'has no country (not replaced by the next located inventor).'),
        'is_international': 'TRUE when n_countries > 1 (inventors in at least two countries).',
        'applicant_countries': ('Distinct two-letter country codes of the applicants (all tls207 rows '
                                "with applt_seq_nr > 0), sorted, ';'-joined; NULL if no applicant is "
                                'located; identical to patstat_metadata.applicant_ctry_list.'),
    },
    'PATSTAT/output/patstat_metadata.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000); primary key '
                     'shared with every other table in this set.'),
        'appln_auth': ('Two-letter code of the office the application was filed at '
                       '(tls201.appln_auth), e.g. EP, US, CN, JP, or WO for a PCT international '
                       'application.'),
        'filing_year': ('Filing year of the application (tls201.appln_filing_year, 1900-2023). The '
                        'clock year of every metric in this set.'),
        'priority_year': ("Year of the application's earliest filing date "
                          '(tls201.earliest_filing_year: earliest of its own filing, its PCT '
                          'application, its Paris-convention priorities, technical relations and '
                          "continuations, direct links only); NULL replaces PATSTAT's 9999 default. "
                          'Equals filing_year when no earlier linked filing exists; can precede 1900 '
                          '(min 1819) because the 1900 floor applies to filing years only.'),
        'grant_year': ("Year of the application's first grant publication (min year of tls211 "
                       "publications flagged publn_first_grant = 'Y'); NULL when there is none, "
                       'including about 0.76 M applications flagged granted only through a legal '
                       'event.'),
        'granted': ("PATSTAT's granted flag (tls201.granted = 'Y'): a first-grant publication or an "
                    'IP-right-grant legal event exists; for WO applications, granted in at least one '
                    'designated state. TRUE for about 54 %.'),
        'docdb_family_id': ('DOCDB simple-family id (tls201.docdb_family_id): applications sharing '
                            'exactly the same priorities; the key of the family set '
                            '(PATSTAT/output_family/).'),
        'docdb_family_size': ("PATSTAT's count of applications in the DOCDB simple family "
                              '(tls201.docdb_family_size), all members including those outside this '
                              'universe; 1 = the only member.'),
        'nb_citing_docdb_fam': ("PATSTAT's own family-level forward-citation count "
                                '(tls201.nb_citing_docdb_fam): distinct DOCDB families citing any '
                                "publication or application of this application's family, taken as-is "
                                'from PATSTAT (this pipeline applies no window, universe or provenance'
                                ' filter to it); not the same as C / uniqueC.'),
        'ref_count': ('Number of distinct cited applications for which this application is the citer '
                      "in this set's patstat_reference (both ends in the universe, third-party and "
                      'replenished rows excluded, self-citations dropped, NO age filter so later-filed'
                      ' references count); 0 if none.'),
        'npl_ref_count': ('Number of distinct non-patent-literature documents '
                          "(tls212.cited_npl_publn_id <> '0') cited by any publication of the "
                          'application, replenished rows excluded (third-party NPL not removed); 0 if '
                          'none.'),
        'ipc_main': ("Main IPC symbol (tls209 row with ipc_position = 'F', whitespace removed, e.g. "
                     "'C07D499/06'; alphabetically first if several); NULL if none."),
        'cpc_code': ("One representative CPC symbol (tls224, whitespace removed, e.g. 'G06K7/0013'): "
                     'the alphabetically first symbol in the same 4-character subclass as ipc_main, '
                     'else the alphabetically first symbol; NULL if no CPC. Its first letter is the '
                     'CD-percentile group.'),
        'cpc_code_list': ('All distinct CPC symbols of the application (whitespace removed), sorted, '
                          "';'-joined; NULL if no CPC."),
        'cpc_subclass_list': ("Distinct 4-character CPC subclasses (e.g. 'A61P;C07D'), sorted, "
                              "';'-joined; the atypicality input; NULL if no CPC."),
        'techn_field_nr': ('WIPO technology field 1-35 (Schmoch 2008 concordance, '
                           'tls230_appln_techn_field) with the largest weight, ties to the lowest '
                           'number; NULL if PATSTAT assigns none. Field names in ps_common.WIPO_FIELD.'),
        'wipo_sector': ('WIPO sector of techn_field_nr: Electrical engineering (fields 1-8), '
                        'Instruments (9-13), Chemistry (14-24), Mechanical engineering (25-32), Other '
                        'fields (33-35); NULL when techn_field_nr is NULL. The hit-probability cohort '
                        'sector.'),
        'inventor_list': ('Inventor PATSTAT person_ids (tls207 rows with invt_seq_nr > 0) as a '
                          "';'-joined string in invt_seq_nr order (ties by person_id): a named person "
                          'once at its lowest sequence, an unnamed placeholder record (empty '
                          'tls206.person_name) once per slot, so its id can repeat. person_ids are '
                          'per-record, not disambiguated inventors; NULL if no inventor.'),
        'applicant_list': ('Applicant PATSTAT person_ids (tls207 rows with applt_seq_nr > 0), '
                           "';'-joined in applt_seq_nr order with the same once-per-named-person rule;"
                           ' person and company records, not disambiguated; NULL if no applicant.'),
        'inventor_ctry_list': ('Distinct two-letter country codes of the inventors '
                               '(tls206.person_ctry_code of each person record; only [A-Z]{2} codes '
                               "count, malformed ones are read as unknown), sorted, ';'-joined; NULL "
                               'if no inventor has one (common for CN and JP filings).'),
        'applicant_ctry_list': ('Distinct two-letter country codes of the applicants '
                                "(tls206.person_ctry_code, [A-Z]{2} only), sorted, ';'-joined; NULL if"
                                ' none.'),
        'applicant_sector': ('PATSTAT standardised-name sector (tls206.psn_sector) of the applicant at'
                             ' sequence number 1: COMPANY, INDIVIDUAL, UNIVERSITY, GOV NON-PROFIT, '
                             "HOSPITAL, UNKNOWN or a space-joined combination (e.g. 'GOV NON-PROFIT "
                             "UNIVERSITY'); NULL if missing or blank."),
    },
    'PATSTAT/output/patstat_reference.parquet': {
        'citing_id': 'appln_id of the citing application (in the universe).',
        'cited_id': ('appln_id of the cited application (in the universe); never equal to citing_id '
                     '(self-citations through another publication are dropped).'),
        'citing_year': 'Filing year of the citing application (tls201.appln_filing_year).',
        'cited_year': 'Filing year of the cited application.',
        'age': ('citing_year - cited_year in years. Can be negative (a search report citing a '
                'later-filed document); such rows are kept here, and every metric requires age >= 0 '
                '(ps.EDGE_WHERE).'),
        'citing_publn_year': ("Year of the citing publication's date (tls211.publn_date), a "
                              'publication-based alternative clock; 9999 = date unknown in PATSTAT (a '
                              'few hundred rows).'),
        'bucket': ("Provenance bucket of citn_origin (ps.bucket_sql): 'applicant' = APP; 'examiner' = "
                   "SEA, ISR, SUP, PRS, EXA, FOP, CH2; 'other' = anything else (OPP, APL, blank)."),
        'replenished': ('TRUE when PATSTAT copied the citation onto the citing publication from '
                        'another publication (tls212.citn_replenished <> 0: Euro-PCT EP publications '
                        'filled with the citations of their WO international publication). Kept for '
                        'completeness; excluded from every count by ps.EDGE_WHERE.'),
    },
    'PATSTAT/output/patstat_sb.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000); a cited '
                     'application with at least one counted citation (same rows as patstat_citation).'),
        'SB_B': ('Ke et al. (2015) beauty coefficient from the yearly histogram of citation rows (not '
                 'distinct citing applications) by age 0 .. last cited age (age >= 0, not '
                 'replenished): sum over t <= t_m of (line from (0, c_0) to the peak (t_m, c_m) minus '
                 'c_t) / max(c_t, 1). 0 when the first maximum is at age 0 (also the value for a '
                 'single-year histogram); can be negative (min about -5); float32.'),
        'SB_T': ("Awakening time: the age t <= t_m (years since the application's filing year) at "
                 'which the histogram lies farthest from the line joining (0, c_0) and the peak; 0 '
                 'when the peak is at age 0.'),
        'n_cite': ('Total citation rows (not distinct citing applications) in the histogram, i.e. '
                   'C_all of patstat_citation.'),
    },
    'PATSTAT/output/patstat_uniqueC_trend.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000); the cited '
                     'application. One row per (application, year) with at least one new citing '
                     'application.'),
        'filing_year': ("Clock year of the cited application: the application's filing year "
                        '(tls201.appln_filing_year, 1900-2023).'),
        'cite_year': ('filing_year + yrs_since_filing: the filing year of the citing applications '
                      'counted in this row.'),
        'yrs_since_filing': ("Lag in years from the cited application's filing year to the citer's "
                             "(the minimum over the pair's edges, which is the only lag because both "
                             'ends have one clock year each); >= 0.'),
        'uniqueC': ('Number of distinct citing applications whose citation of this application falls '
                    'at this lag. Cumulative sums over lags <= 3/5/10/all reproduce uniqueC_3/5/10/all'
                    ' of patstat_citation, and the column equals patstat_citation_trend.uniqueC row '
                    'for row (both asserted in the notebook).'),
    },
    'PATSTAT/output/patstat_z_score.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000); a application '
                     'with at least two distinct CPC subclasses (its distinct 4-character CPC '
                     'subclasses (tls224, whitespace removed)).'),
        'Z_median': ("Median over the application's subclass pairs of the pair z-score (Kim et al. "
                     "(2016) hypergeometric z of a CPC-subclass pair in the application's filing year,"
                     ' with counts cumulative over all applications with >= 2 subclasses up to and '
                     'including that year; z < 0 = atypical pair).'),
        'Z_10pct': ("10th percentile (linear interpolation, DuckDB quantile_cont) of the application's"
                    ' pair z-scores; low values flag atypical combinations.'),
        'Z_min': 'Minimum pair z-score of the application (its most atypical subclass pair).',
        'n_pairs': ('Number of distinct CPC-subclass pairs scored = k(k-1)/2 for k distinct '
                    'subclasses.'),
    },
    'PATSTAT/output/z_score_pair.parquet': {
        'code_1': ("First CPC subclass of the pair (4 characters, e.g. 'A01B'); always alphabetically "
                   'lower than code_2.'),
        'code_2': 'Second CPC subclass of the pair (4 characters); alphabetically higher than code_1.',
        'year': ('Year in which at least one application with >= 2 subclasses carries this pair, on '
                 "this set's clock: the application's filing year (tls201.appln_filing_year, "
                 '1900-2023).'),
        'Z_score': ('Hypergeometric z = (o - mu) / sqrt(var) with mu = n_a n_b / N and var = mu (1 - '
                    'n_a / N) (N - n_b) / (N - 1), where N, n_a, n_b and o (co-occurrences) count '
                    'applications with >= 2 subclasses cumulatively through this year inclusive; 0 '
                    'when var <= 0. z < 0 = rarer than chance (atypical).'),
    },
    'PATSTAT/output_grant/patstat_citation.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000) of a granted '
                     'application (grant year 1900-2023); the cited application. Only applications '
                     'with at least one counted citation from another granted application are rows; an'
                     ' absent application received none (patstat_hit_probability fills the zeros).'),
        'C_3': ('Citation rows received from citing applications whose grant year is 0 to 3 years '
                "after this application's grant year (0 <= age <= 3, inclusive at both ends): every "
                'patstat_reference row with age >= 0 that is not replenished (third-party observations'
                ' removed upstream). One citing application can add several rows (several of its '
                'publications, several publications of the target, several origins), so C >= uniqueC.'),
        'C_examiner_3': ("The 'examiner' part of C_3 (citn_origin SEA, ISR, SUP, PRS, EXA, FOP or CH2:"
                         ' search-report, examination, opposition-filing and PCT chapter II '
                         'citations): citation rows within the same window whose bucket is examiner; '
                         'C_3 = C_examiner_3 + C_applicant_3 + C_other_3.'),
        'C_applicant_3': ("The 'applicant' part of C_3 (citn_origin APP: references submitted by the "
                          'applicant): citation rows within the same window whose bucket is applicant;'
                          ' C_3 = C_examiner_3 + C_applicant_3 + C_other_3.'),
        'C_other_3': ("The 'other' part of C_3 (citn_origin OPP, APL or blank: opposition-division and"
                      ' appeal citations): citation rows within the same window whose bucket is other;'
                      ' C_3 = C_examiner_3 + C_applicant_3 + C_other_3.'),
        'C_5': ('Citation rows received from citing applications whose grant year is 0 to 5 years '
                "after this application's grant year (0 <= age <= 5, inclusive at both ends): every "
                'patstat_reference row with age >= 0 that is not replenished (third-party observations'
                ' removed upstream). One citing application can add several rows (several of its '
                'publications, several publications of the target, several origins), so C >= uniqueC.'),
        'C_examiner_5': ("The 'examiner' part of C_5 (citn_origin SEA, ISR, SUP, PRS, EXA, FOP or CH2:"
                         ' search-report, examination, opposition-filing and PCT chapter II '
                         'citations): citation rows within the same window whose bucket is examiner; '
                         'C_5 = C_examiner_5 + C_applicant_5 + C_other_5.'),
        'C_applicant_5': ("The 'applicant' part of C_5 (citn_origin APP: references submitted by the "
                          'applicant): citation rows within the same window whose bucket is applicant;'
                          ' C_5 = C_examiner_5 + C_applicant_5 + C_other_5.'),
        'C_other_5': ("The 'other' part of C_5 (citn_origin OPP, APL or blank: opposition-division and"
                      ' appeal citations): citation rows within the same window whose bucket is other;'
                      ' C_5 = C_examiner_5 + C_applicant_5 + C_other_5.'),
        'C_10': ('Citation rows received from citing applications whose grant year is 0 to 10 years '
                 "after this application's grant year (0 <= age <= 10, inclusive at both ends): every "
                 'patstat_reference row with age >= 0 that is not replenished (third-party '
                 'observations removed upstream). One citing application can add several rows (several'
                 ' of its publications, several publications of the target, several origins), so C >= '
                 'uniqueC.'),
        'C_examiner_10': ("The 'examiner' part of C_10 (citn_origin SEA, ISR, SUP, PRS, EXA, FOP or "
                          'CH2: search-report, examination, opposition-filing and PCT chapter II '
                          'citations): citation rows within the same window whose bucket is examiner; '
                          'C_10 = C_examiner_10 + C_applicant_10 + C_other_10.'),
        'C_applicant_10': ("The 'applicant' part of C_10 (citn_origin APP: references submitted by the"
                           ' applicant): citation rows within the same window whose bucket is '
                           'applicant; C_10 = C_examiner_10 + C_applicant_10 + C_other_10.'),
        'C_other_10': ("The 'other' part of C_10 (citn_origin OPP, APL or blank: opposition-division "
                       'and appeal citations): citation rows within the same window whose bucket is '
                       'other; C_10 = C_examiner_10 + C_applicant_10 + C_other_10.'),
        'C_all': ('Citation rows received from citing applications whose grant year is the same as or '
                  "later than this application's grant year (age >= 0, no upper bound: every year up "
                  'to the 2023 snapshot): every patstat_reference row with age >= 0 that is not '
                  'replenished (third-party observations removed upstream). One citing application can'
                  ' add several rows (several of its publications, several publications of the target,'
                  ' several origins), so C >= uniqueC.'),
        'C_examiner_all': ("The 'examiner' part of C_all (citn_origin SEA, ISR, SUP, PRS, EXA, FOP or "
                           'CH2: search-report, examination, opposition-filing and PCT chapter II '
                           'citations): citation rows within the same window whose bucket is examiner;'
                           ' C_all = C_examiner_all + C_applicant_all + C_other_all.'),
        'C_applicant_all': ("The 'applicant' part of C_all (citn_origin APP: references submitted by "
                            'the applicant): citation rows within the same window whose bucket is '
                            'applicant; C_all = C_examiner_all + C_applicant_all + C_other_all.'),
        'C_other_all': ("The 'other' part of C_all (citn_origin OPP, APL or blank: opposition-division"
                        ' and appeal citations): citation rows within the same window whose bucket is '
                        'other; C_all = C_examiner_all + C_applicant_all + C_other_all.'),
        'uniqueC_3': ('Distinct citing applications whose grant year is 0 to 3 years after this '
                      "application's grant year (0 <= age <= 3, inclusive at both ends), each counted "
                      'once however many rows it contributes; the de-duplicated impact count to use.'),
        'uniqueC_examiner_3': ('Distinct citing applications within the same window that cite this '
                               "application through at least one 'examiner'-bucket row (citn_origin "
                               'SEA, ISR, SUP, PRS, EXA, FOP or CH2: search-report, examination, '
                               'opposition-filing and PCT chapter II citations). A citer using several'
                               ' buckets counts in each, so the three bucket counts can sum to more '
                               'than uniqueC_3.'),
        'uniqueC_applicant_3': ('Distinct citing applications within the same window that cite this '
                                "application through at least one 'applicant'-bucket row (citn_origin "
                                'APP: references submitted by the applicant). A citer using several '
                                'buckets counts in each, so the three bucket counts can sum to more '
                                'than uniqueC_3.'),
        'uniqueC_other_3': ('Distinct citing applications within the same window that cite this '
                            "application through at least one 'other'-bucket row (citn_origin OPP, APL"
                            ' or blank: opposition-division and appeal citations). A citer using '
                            'several buckets counts in each, so the three bucket counts can sum to '
                            'more than uniqueC_3.'),
        'uniqueC_5': ('Distinct citing applications whose grant year is 0 to 5 years after this '
                      "application's grant year (0 <= age <= 5, inclusive at both ends), each counted "
                      'once however many rows it contributes; the de-duplicated impact count to use.'),
        'uniqueC_examiner_5': ('Distinct citing applications within the same window that cite this '
                               "application through at least one 'examiner'-bucket row (citn_origin "
                               'SEA, ISR, SUP, PRS, EXA, FOP or CH2: search-report, examination, '
                               'opposition-filing and PCT chapter II citations). A citer using several'
                               ' buckets counts in each, so the three bucket counts can sum to more '
                               'than uniqueC_5.'),
        'uniqueC_applicant_5': ('Distinct citing applications within the same window that cite this '
                                "application through at least one 'applicant'-bucket row (citn_origin "
                                'APP: references submitted by the applicant). A citer using several '
                                'buckets counts in each, so the three bucket counts can sum to more '
                                'than uniqueC_5.'),
        'uniqueC_other_5': ('Distinct citing applications within the same window that cite this '
                            "application through at least one 'other'-bucket row (citn_origin OPP, APL"
                            ' or blank: opposition-division and appeal citations). A citer using '
                            'several buckets counts in each, so the three bucket counts can sum to '
                            'more than uniqueC_5.'),
        'uniqueC_10': ('Distinct citing applications whose grant year is 0 to 10 years after this '
                       "application's grant year (0 <= age <= 10, inclusive at both ends), each "
                       'counted once however many rows it contributes; the de-duplicated impact count '
                       'to use.'),
        'uniqueC_examiner_10': ('Distinct citing applications within the same window that cite this '
                                "application through at least one 'examiner'-bucket row (citn_origin "
                                'SEA, ISR, SUP, PRS, EXA, FOP or CH2: search-report, examination, '
                                'opposition-filing and PCT chapter II citations). A citer using '
                                'several buckets counts in each, so the three bucket counts can sum to'
                                ' more than uniqueC_10.'),
        'uniqueC_applicant_10': ('Distinct citing applications within the same window that cite this '
                                 "application through at least one 'applicant'-bucket row (citn_origin"
                                 ' APP: references submitted by the applicant). A citer using several '
                                 'buckets counts in each, so the three bucket counts can sum to more '
                                 'than uniqueC_10.'),
        'uniqueC_other_10': ('Distinct citing applications within the same window that cite this '
                             "application through at least one 'other'-bucket row (citn_origin OPP, "
                             'APL or blank: opposition-division and appeal citations). A citer using '
                             'several buckets counts in each, so the three bucket counts can sum to '
                             'more than uniqueC_10.'),
        'uniqueC_all': ('Distinct citing applications whose grant year is the same as or later than '
                        "this application's grant year (age >= 0, no upper bound: every year up to the"
                        ' 2023 snapshot), each counted once however many rows it contributes; the '
                        'de-duplicated impact count to use.'),
        'uniqueC_examiner_all': ('Distinct citing applications within the same window that cite this '
                                 "application through at least one 'examiner'-bucket row (citn_origin "
                                 'SEA, ISR, SUP, PRS, EXA, FOP or CH2: search-report, examination, '
                                 'opposition-filing and PCT chapter II citations). A citer using '
                                 'several buckets counts in each, so the three bucket counts can sum '
                                 'to more than uniqueC_all.'),
        'uniqueC_applicant_all': ('Distinct citing applications within the same window that cite this '
                                  "application through at least one 'applicant'-bucket row "
                                  '(citn_origin APP: references submitted by the applicant). A citer '
                                  'using several buckets counts in each, so the three bucket counts '
                                  'can sum to more than uniqueC_all.'),
        'uniqueC_other_all': ('Distinct citing applications within the same window that cite this '
                              "application through at least one 'other'-bucket row (citn_origin OPP, "
                              'APL or blank: opposition-division and appeal citations). A citer using '
                              'several buckets counts in each, so the three bucket counts can sum to '
                              'more than uniqueC_all.'),
    },
    'PATSTAT/output_grant/patstat_citation_trend.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000) of a granted '
                     'application (grant year 1900-2023); the cited application. One row per '
                     '(application, citing year) with at least one counted citation.'),
        'grant_year': ('Clock year of the cited application: the grant year, i.e. the year of the '
                       "application's first publication flagged publn_first_grant = 'Y' (1900-2023)."),
        'cite_year': ('Grant year of the citing applications counted in this row (the citing '
                      "application's clock year, not the publication year of the citation)."),
        'yrs_since_grant': ("Years since the cited application's grant year: cite_year - grant_year "
                            '(integer, >= 0; ps.EDGE_WHERE drops negative ages).'),
        'C': ('Citation rows (patstat_reference rows, not replenished) received from applications of '
              'this citing year; one citing application can add several rows. Summing over years gives'
              ' C_all of patstat_citation.'),
        'C_examiner': ("The 'examiner' part of C in this year (citn_origin SEA, ISR, SUP, PRS, EXA, "
                       'FOP or CH2: search-report, examination, opposition-filing and PCT chapter II '
                       'citations); C = C_examiner + C_applicant + C_other.'),
        'uniqueC': ('Distinct citing applications in this citing year. A citer has one clock year, so '
                    'the yearly values sum exactly to uniqueC_all of patstat_citation.'),
    },
    'PATSTAT/output_grant/patstat_disruption.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000) of a granted '
                     'application (grant year 1900-2023); every node of the de-duplicated application '
                     'citation graph (distinct citing -> cited pairs from patstat_reference with age '
                     '>= 0, not replenished), as citer or cited. Nodes that are never cited have NULL '
                     'CD/F/E/G and -1 in ni/nj/nk.'),
        'CD_3': ('CD disruption index (ni_3 - nj_3) / (ni_3 + nj_3 + nk_3) over applications dated 0 '
                 "to 3 years after the focal application's grant year (0 <= age <= 3); in [-1, 1]. "
                 'NULL when the window holds neither a citer nor a citer of a reference (then ni/nj/nk'
                 ' = -1); 0 when it has no citer but its references do (ni = nj = 0, nk > 0).'),
        'F_3': ('Foundation share: fraction of the citers dated 0 to 3 years after the focal '
                "application's grant year (0 <= age <= 3) for which down > up, where up = how many of "
                'its references (the applications it cites with age >= 0) the citer also cites and '
                "down = how many of the focal's other citers in the same window it cites; ties with up"
                ' = down > 0 count half F, half E. NULL when there is no citer in the window. F + E + '
                'G = 1. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_3': ('Extension share: fraction of the citers dated 0 to 3 years after the focal '
                "application's grant year (0 <= age <= 3) with up > down (citer cites more of the "
                "focal's references than of its other in-window citers), plus half of the up = down > "
                '0 ties. NULL when there is no citer in the window. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'G_3': ('Generalization share: fraction of the citers dated 0 to 3 years after the focal '
                "application's grant year (0 <= age <= 3) with up = down = 0 (cite neither the focal's"
                ' references nor its other in-window citers). NULL when there is no citer in the '
                'window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_3': ("Citers dated 0 to 3 years after the focal application's grant year (0 <= age <= 3) "
                 'that cite none of its references (the applications it cites with age >= 0) (count); '
                 "-1 is the sentinel for 'nothing in the window' (CD_3 NULL), not a count."),
        'nj_3': ("Citers dated 0 to 3 years after the focal application's grant year (0 <= age <= 3) "
                 'that also cite at least one of its references (the applications it cites with age >='
                 ' 0) (count); -1 sentinel when nothing is in the window.'),
        'nk_3': ("Applications dated 0 to 3 years after the focal application's grant year (0 <= age "
                 "<= 3) that cite at least one of the focal's references but not the focal itself "
                 '(distinct citers of the references minus nj, focal excluded); -1 sentinel when '
                 'nothing is in the window.'),
        'CD_5': ('CD disruption index (ni_5 - nj_5) / (ni_5 + nj_5 + nk_5) over applications dated 0 '
                 "to 5 years after the focal application's grant year (0 <= age <= 5); in [-1, 1]. "
                 'NULL when the window holds neither a citer nor a citer of a reference (then ni/nj/nk'
                 ' = -1); 0 when it has no citer but its references do (ni = nj = 0, nk > 0).'),
        'F_5': ('Foundation share: fraction of the citers dated 0 to 5 years after the focal '
                "application's grant year (0 <= age <= 5) for which down > up, where up = how many of "
                'its references (the applications it cites with age >= 0) the citer also cites and '
                "down = how many of the focal's other citers in the same window it cites; ties with up"
                ' = down > 0 count half F, half E. NULL when there is no citer in the window. F + E + '
                'G = 1. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_5': ('Extension share: fraction of the citers dated 0 to 5 years after the focal '
                "application's grant year (0 <= age <= 5) with up > down (citer cites more of the "
                "focal's references than of its other in-window citers), plus half of the up = down > "
                '0 ties. NULL when there is no citer in the window. Decomposition of Fang & Evans '
                '(2025), arXiv:2510.03240.'),
        'G_5': ('Generalization share: fraction of the citers dated 0 to 5 years after the focal '
                "application's grant year (0 <= age <= 5) with up = down = 0 (cite neither the focal's"
                ' references nor its other in-window citers). NULL when there is no citer in the '
                'window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_5': ("Citers dated 0 to 5 years after the focal application's grant year (0 <= age <= 5) "
                 'that cite none of its references (the applications it cites with age >= 0) (count); '
                 "-1 is the sentinel for 'nothing in the window' (CD_5 NULL), not a count."),
        'nj_5': ("Citers dated 0 to 5 years after the focal application's grant year (0 <= age <= 5) "
                 'that also cite at least one of its references (the applications it cites with age >='
                 ' 0) (count); -1 sentinel when nothing is in the window.'),
        'nk_5': ("Applications dated 0 to 5 years after the focal application's grant year (0 <= age "
                 "<= 5) that cite at least one of the focal's references but not the focal itself "
                 '(distinct citers of the references minus nj, focal excluded); -1 sentinel when '
                 'nothing is in the window.'),
        'CD_10': ('CD disruption index (ni_10 - nj_10) / (ni_10 + nj_10 + nk_10) over applications '
                  "dated 0 to 10 years after the focal application's grant year (0 <= age <= 10); in "
                  '[-1, 1]. NULL when the window holds neither a citer nor a citer of a reference '
                  '(then ni/nj/nk = -1); 0 when it has no citer but its references do (ni = nj = 0, nk'
                  ' > 0).'),
        'F_10': ('Foundation share: fraction of the citers dated 0 to 10 years after the focal '
                 "application's grant year (0 <= age <= 10) for which down > up, where up = how many "
                 'of its references (the applications it cites with age >= 0) the citer also cites and'
                 " down = how many of the focal's other citers in the same window it cites; ties with "
                 'up = down > 0 count half F, half E. NULL when there is no citer in the window. F + E'
                 ' + G = 1. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_10': ('Extension share: fraction of the citers dated 0 to 10 years after the focal '
                 "application's grant year (0 <= age <= 10) with up > down (citer cites more of the "
                 "focal's references than of its other in-window citers), plus half of the up = down >"
                 ' 0 ties. NULL when there is no citer in the window. Decomposition of Fang & Evans '
                 '(2025), arXiv:2510.03240.'),
        'G_10': ('Generalization share: fraction of the citers dated 0 to 10 years after the focal '
                 "application's grant year (0 <= age <= 10) with up = down = 0 (cite neither the "
                 "focal's references nor its other in-window citers). NULL when there is no citer in "
                 'the window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_10': ("Citers dated 0 to 10 years after the focal application's grant year (0 <= age <= "
                  '10) that cite none of its references (the applications it cites with age >= 0) '
                  "(count); -1 is the sentinel for 'nothing in the window' (CD_10 NULL), not a count."),
        'nj_10': ("Citers dated 0 to 10 years after the focal application's grant year (0 <= age <= "
                  '10) that also cite at least one of its references (the applications it cites with '
                  'age >= 0) (count); -1 sentinel when nothing is in the window.'),
        'nk_10': ("Applications dated 0 to 10 years after the focal application's grant year (0 <= age"
                  " <= 10) that cite at least one of the focal's references but not the focal itself "
                  '(distinct citers of the references minus nj, focal excluded); -1 sentinel when '
                  'nothing is in the window.'),
        'CD_all': ('CD disruption index (ni_all - nj_all) / (ni_all + nj_all + nk_all) over '
                   "applications dated at any time from the focal application's grant year on (age >= "
                   '0); in [-1, 1]. NULL when the window holds neither a citer nor a citer of a '
                   'reference (then ni/nj/nk = -1); 0 when it has no citer but its references do (ni ='
                   ' nj = 0, nk > 0).'),
        'F_all': ('Foundation share: fraction of the citers dated at any time from the focal '
                  "application's grant year on (age >= 0) for which down > up, where up = how many of "
                  'its references (the applications it cites with age >= 0) the citer also cites and '
                  "down = how many of the focal's other citers in the same window it cites; ties with "
                  'up = down > 0 count half F, half E. NULL when there is no citer in the window. F + '
                  'E + G = 1. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_all': ('Extension share: fraction of the citers dated at any time from the focal '
                  "application's grant year on (age >= 0) with up > down (citer cites more of the "
                  "focal's references than of its other in-window citers), plus half of the up = down "
                  '> 0 ties. NULL when there is no citer in the window. Decomposition of Fang & Evans '
                  '(2025), arXiv:2510.03240.'),
        'G_all': ('Generalization share: fraction of the citers dated at any time from the focal '
                  "application's grant year on (age >= 0) with up = down = 0 (cite neither the focal's"
                  ' references nor its other in-window citers). NULL when there is no citer in the '
                  'window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_all': ("Citers dated at any time from the focal application's grant year on (age >= 0) "
                   'that cite none of its references (the applications it cites with age >= 0) '
                   "(count); -1 is the sentinel for 'nothing in the window' (CD_all NULL), not a "
                   'count.'),
        'nj_all': ("Citers dated at any time from the focal application's grant year on (age >= 0) "
                   'that also cite at least one of its references (the applications it cites with age '
                   '>= 0) (count); -1 sentinel when nothing is in the window.'),
        'nk_all': ("Applications dated at any time from the focal application's grant year on (age >= "
                   "0) that cite at least one of the focal's references but not the focal itself "
                   '(distinct citers of the references minus nj, focal excluded); -1 sentinel when '
                   'nothing is in the window.'),
        'pctl_year': ("CD-percentile cohort year: the application's FILING year "
                      '(patstat_metadata.filing_year), not its grant year; the cohort stays filing '
                      'year x CPC Section in the grant set, as in PatentView.'),
        'pctl_group': ('CD-percentile cohort group: the CPC Section letter (A-H or Y) of '
                       'patstat_metadata.cpc_code; NULL when there is no CPC code, and then every '
                       'CD_*_pctl column is NULL.'),
        'CD_3_pctl': ('Minimum-rank percentile of CD_3 within its pctl_year x pctl_group cohort, among'
                      ' applications with a non-NULL CD_3: rank() / n on ascending CD, ties share the '
                      'lowest rank; in (0, 1], higher = more disruptive. NULL when CD_3 or pctl_group '
                      'is NULL.'),
        'CD_3_pctl_cume': ("Cumulative percentile of CD_3 in the same cohort: share of the cohort's "
                           'non-NULL CD_3 values <= this value (ties inclusive); in (0, 1], always >= '
                           "CD_3_pctl, and differs from it inside CD's large tie blocks (e.g. many CD "
                           '= 1 or 0). NULL when CD_3 or pctl_group is NULL.'),
        'CD_5_pctl': ('Minimum-rank percentile of CD_5 within its pctl_year x pctl_group cohort, among'
                      ' applications with a non-NULL CD_5: rank() / n on ascending CD, ties share the '
                      'lowest rank; in (0, 1], higher = more disruptive. NULL when CD_5 or pctl_group '
                      'is NULL.'),
        'CD_5_pctl_cume': ("Cumulative percentile of CD_5 in the same cohort: share of the cohort's "
                           'non-NULL CD_5 values <= this value (ties inclusive); in (0, 1], always >= '
                           "CD_5_pctl, and differs from it inside CD's large tie blocks (e.g. many CD "
                           '= 1 or 0). NULL when CD_5 or pctl_group is NULL.'),
        'CD_10_pctl': ('Minimum-rank percentile of CD_10 within its pctl_year x pctl_group cohort, '
                       'among applications with a non-NULL CD_10: rank() / n on ascending CD, ties '
                       'share the lowest rank; in (0, 1], higher = more disruptive. NULL when CD_10 or'
                       ' pctl_group is NULL.'),
        'CD_10_pctl_cume': ("Cumulative percentile of CD_10 in the same cohort: share of the cohort's "
                            'non-NULL CD_10 values <= this value (ties inclusive); in (0, 1], always '
                            ">= CD_10_pctl, and differs from it inside CD's large tie blocks (e.g. "
                            'many CD = 1 or 0). NULL when CD_10 or pctl_group is NULL.'),
        'CD_all_pctl': ('Minimum-rank percentile of CD_all within its pctl_year x pctl_group cohort, '
                        'among applications with a non-NULL CD_all: rank() / n on ascending CD, ties '
                        'share the lowest rank; in (0, 1], higher = more disruptive. NULL when CD_all '
                        'or pctl_group is NULL.'),
        'CD_all_pctl_cume': ('Cumulative percentile of CD_all in the same cohort: share of the '
                             "cohort's non-NULL CD_all values <= this value (ties inclusive); in (0, "
                             "1], always >= CD_all_pctl, and differs from it inside CD's large tie "
                             'blocks (e.g. many CD = 1 or 0). NULL when CD_all or pctl_group is NULL.'),
    },
    'PATSTAT/output_grant/patstat_disruption_trend.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000) of a granted '
                     'application (grant year 1900-2023); a focal application with at least one citer '
                     'in the de-duplicated graph. One row per (application, year) in which ni_new, '
                     'nj_new or nk_new is non-zero; years without a change have no row.'),
        'grant_year': ('Clock year of the focal application: the grant year, i.e. the year of the '
                       "application's first publication flagged publn_first_grant = 'Y' (1900-2023)."),
        'cite_year': ('Calendar grant year of this row = grant_year + yrs_since_grant; the year in '
                      'which the new citers / co-citers counted in *_new appeared (up to 2023).'),
        'yrs_since_grant': ("Years since the focal application's grant year (>= 0); the row at age w "
                            '(or the last row before it) carries the window-w values of '
                            'patstat_disruption.'),
        'ni_new': ('Citers of the focal whose grant year is exactly this year and that cite none of '
                   'its references.'),
        'nj_new': ('Citers of the focal whose grant year is exactly this year and that also cite at '
                   'least one of its references.'),
        'nk_new': ("Applications of exactly this year that cite at least one of the focal's references"
                   ' but not the focal (focal excluded).'),
        'ni': ("Cumulative ni from age 0 through this row's age; at age w it equals ni_w of "
               'patstat_disruption and the last row equals ni_all (checked on every focal '
               'application).'),
    },
    'PATSTAT/output_grant/patstat_disruption_trend_summary.parquet': {
        'grant_year': ('Cohort year of the focal documents: the grant year, i.e. the year of the '
                       "application's first publication flagged publn_first_grant = 'Y' (1900-2023)."),
        'yrs_since_grant': "Years since the cohort's grant year (>= 0).",
        'n_CD': ('Number of patstat_disruption_trend rows in this (grant_year, yrs_since_grant) cell '
                 'with a finite CD. Trend rows exist only for years in which a focal application '
                 'gained a new citer or co-citer, so this counts those applications, not every cohort '
                 'member.'),
        'CD_mean': ('Mean cumulative CD over the n_CD trend rows of this (grant_year, yrs_since_grant)'
                    ' cell (only applications with a change in exactly this year; values are not '
                    'carried forward for the others).'),
        'n_F': ('Number of patstat_disruption_trend rows in this (grant_year, yrs_since_grant) cell '
                'with a finite F. Trend rows exist only for years in which a focal application gained '
                'a new citer or co-citer, so this counts those applications, not every cohort member.'),
        'F_mean': ('Mean cumulative F (Foundation share) over the n_F trend rows of this (grant_year, '
                   'yrs_since_grant) cell (only applications with a change in exactly this year; '
                   'values are not carried forward for the others). NULL when n_F = 0. Decomposition '
                   'of Fang & Evans (2025), arXiv:2510.03240.'),
        'n_E': ('Number of patstat_disruption_trend rows in this (grant_year, yrs_since_grant) cell '
                'with a finite E. Trend rows exist only for years in which a focal application gained '
                'a new citer or co-citer, so this counts those applications, not every cohort member.'),
        'E_mean': ('Mean cumulative E (Extension share) over the n_E trend rows of this (grant_year, '
                   'yrs_since_grant) cell (only applications with a change in exactly this year; '
                   'values are not carried forward for the others). NULL when n_E = 0. Decomposition '
                   'of Fang & Evans (2025), arXiv:2510.03240.'),
        'n_G': ('Number of patstat_disruption_trend rows in this (grant_year, yrs_since_grant) cell '
                'with a finite G. Trend rows exist only for years in which a focal application gained '
                'a new citer or co-citer, so this counts those applications, not every cohort member.'),
        'G_mean': ('Mean cumulative G (Generalization share) over the n_G trend rows of this '
                   '(grant_year, yrs_since_grant) cell (only applications with a change in exactly '
                   'this year; values are not carried forward for the others). NULL when n_G = 0. '
                   'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
    },
    'PATSTAT/output_grant/patstat_feg_disruption_trend.parquet': {
        'year': ("Cohort year: the grant year (first publication flagged publn_first_grant = 'Y'), "
                 '1900-2023.'),
        'n': ('Number of applications of this cohort in patstat_disruption with a non-NULL CD_all, '
              'i.e. with at least one citer: the denominator of the `_all` means. The 3-, 5- and '
              '10-year ni / nj / nk / njfrac means are taken over the subset with something in that '
              'window.'),
        'CD_3_mean': ("Mean of CD_3 (window 3) over the cohort's applications with a non-NULL CD_3 "
                      '(NULLs ignored); NULL if none.'),
        'F_3_mean': ("Mean Foundation share F_3 over the cohort's applications with at least one citer"
                     ' in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans '
                     '(2025), arXiv:2510.03240.'),
        'E_3_mean': ("Mean Extension share E_3 over the cohort's applications with at least one citer "
                     'in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans '
                     '(2025), arXiv:2510.03240.'),
        'G_3_mean': ("Mean Generalization share G_3 over the cohort's applications with at least one "
                     'citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans'
                     ' (2025), arXiv:2510.03240.'),
        'ni_3_mean': ("Mean of ni_3 (citers that cite none of its references) over the cohort's "
                      'applications with something in the 3-year window: the -1 placeholder of a '
                      'application with nothing in it (no citer and nothing citing its references) is '
                      'read as NULL. NULL when no application of the cohort has anything in the window'
                      ' (the earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which '
                      'made this negative for early cohorts.'),
        'nj_3_mean': ('Mean of nj_3 (citers that also cite at least one of its references) over the '
                      "cohort's applications with something in the 3-year window: the -1 placeholder "
                      'of a application with nothing in it (no citer and nothing citing its '
                      'references) is read as NULL. NULL when no application of the cohort has '
                      'anything in the window (the earliest cohorts). Before 2026-10-03 the -1 rows '
                      'were averaged in, which made this negative for early cohorts.'),
        'nk_3_mean': ("Mean of nk_3 (documents citing its references but not it) over the cohort's "
                      'applications with something in the 3-year window: the -1 placeholder of a '
                      'application with nothing in it (no citer and nothing citing its references) is '
                      'read as NULL. NULL when no application of the cohort has anything in the window'
                      ' (the earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which '
                      'made this negative for early cohorts.'),
        'njfrac_3_mean': ('Mean of the per-application nj_3 / (ni_3 + nj_3 + nk_3), the share of the '
                          '3-year neighbourhood that cites both the application and its references, '
                          'over the applications with something in the window (the -1 placeholder is '
                          'read as NULL); NULL when there are none. Before 2026-10-03 the -1 rows '
                          'entered as (-1)/(-3) = 1/3 and pulled the mean toward 0.333.'),
        'CD_5_mean': ("Mean of CD_5 (window 5) over the cohort's applications with a non-NULL CD_5 "
                      '(NULLs ignored); NULL if none.'),
        'F_5_mean': ("Mean Foundation share F_5 over the cohort's applications with at least one citer"
                     ' in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans '
                     '(2025), arXiv:2510.03240.'),
        'E_5_mean': ("Mean Extension share E_5 over the cohort's applications with at least one citer "
                     'in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans '
                     '(2025), arXiv:2510.03240.'),
        'G_5_mean': ("Mean Generalization share G_5 over the cohort's applications with at least one "
                     'citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans'
                     ' (2025), arXiv:2510.03240.'),
        'ni_5_mean': ("Mean of ni_5 (citers that cite none of its references) over the cohort's "
                      'applications with something in the 5-year window: the -1 placeholder of a '
                      'application with nothing in it (no citer and nothing citing its references) is '
                      'read as NULL. NULL when no application of the cohort has anything in the window'
                      ' (the earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which '
                      'made this negative for early cohorts.'),
        'nj_5_mean': ('Mean of nj_5 (citers that also cite at least one of its references) over the '
                      "cohort's applications with something in the 5-year window: the -1 placeholder "
                      'of a application with nothing in it (no citer and nothing citing its '
                      'references) is read as NULL. NULL when no application of the cohort has '
                      'anything in the window (the earliest cohorts). Before 2026-10-03 the -1 rows '
                      'were averaged in, which made this negative for early cohorts.'),
        'nk_5_mean': ("Mean of nk_5 (documents citing its references but not it) over the cohort's "
                      'applications with something in the 5-year window: the -1 placeholder of a '
                      'application with nothing in it (no citer and nothing citing its references) is '
                      'read as NULL. NULL when no application of the cohort has anything in the window'
                      ' (the earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which '
                      'made this negative for early cohorts.'),
        'njfrac_5_mean': ('Mean of the per-application nj_5 / (ni_5 + nj_5 + nk_5), the share of the '
                          '5-year neighbourhood that cites both the application and its references, '
                          'over the applications with something in the window (the -1 placeholder is '
                          'read as NULL); NULL when there are none. Before 2026-10-03 the -1 rows '
                          'entered as (-1)/(-3) = 1/3 and pulled the mean toward 0.333.'),
        'CD_10_mean': ("Mean of CD_10 (window 10) over the cohort's applications with a non-NULL CD_10"
                       ' (NULLs ignored); NULL if none.'),
        'F_10_mean': ("Mean Foundation share F_10 over the cohort's applications with at least one "
                      'citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & '
                      'Evans (2025), arXiv:2510.03240.'),
        'E_10_mean': ("Mean Extension share E_10 over the cohort's applications with at least one "
                      'citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & '
                      'Evans (2025), arXiv:2510.03240.'),
        'G_10_mean': ("Mean Generalization share G_10 over the cohort's applications with at least one"
                      ' citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & '
                      'Evans (2025), arXiv:2510.03240.'),
        'ni_10_mean': ("Mean of ni_10 (citers that cite none of its references) over the cohort's "
                       'applications with something in the 10-year window: the -1 placeholder of a '
                       'application with nothing in it (no citer and nothing citing its references) is'
                       ' read as NULL. NULL when no application of the cohort has anything in the '
                       'window (the earliest cohorts). Before 2026-10-03 the -1 rows were averaged in,'
                       ' which made this negative for early cohorts.'),
        'nj_10_mean': ('Mean of nj_10 (citers that also cite at least one of its references) over the '
                       "cohort's applications with something in the 10-year window: the -1 placeholder"
                       ' of a application with nothing in it (no citer and nothing citing its '
                       'references) is read as NULL. NULL when no application of the cohort has '
                       'anything in the window (the earliest cohorts). Before 2026-10-03 the -1 rows '
                       'were averaged in, which made this negative for early cohorts.'),
        'nk_10_mean': ("Mean of nk_10 (documents citing its references but not it) over the cohort's "
                       'applications with something in the 10-year window: the -1 placeholder of a '
                       'application with nothing in it (no citer and nothing citing its references) is'
                       ' read as NULL. NULL when no application of the cohort has anything in the '
                       'window (the earliest cohorts). Before 2026-10-03 the -1 rows were averaged in,'
                       ' which made this negative for early cohorts.'),
        'njfrac_10_mean': ('Mean of the per-application nj_10 / (ni_10 + nj_10 + nk_10), the share of '
                           'the 10-year neighbourhood that cites both the application and its '
                           'references, over the applications with something in the window (the -1 '
                           'placeholder is read as NULL); NULL when there are none. Before 2026-10-03 '
                           'the -1 rows entered as (-1)/(-3) = 1/3 and pulled the mean toward 0.333.'),
        'CD_all_mean': ("Mean of CD_all (any age) over the cohort's applications with a non-NULL "
                        'CD_all (NULLs ignored); NULL if none.'),
        'F_all_mean': ("Mean Foundation share F_all over the cohort's applications with at least one "
                       'citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & '
                       'Evans (2025), arXiv:2510.03240.'),
        'E_all_mean': ("Mean Extension share E_all over the cohort's applications with at least one "
                       'citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & '
                       'Evans (2025), arXiv:2510.03240.'),
        'G_all_mean': ("Mean Generalization share G_all over the cohort's applications with at least "
                       'one citer in the window (NULLs ignored); NULL if none. Decomposition of Fang &'
                       ' Evans (2025), arXiv:2510.03240.'),
        'ni_all_mean': ('Mean of ni_all over the n applications of the cohort (all have ni/nj/nk_all '
                        '>= 0).'),
        'nj_all_mean': ('Mean of nj_all over the n applications of the cohort (all have ni/nj/nk_all '
                        '>= 0).'),
        'nk_all_mean': ('Mean of nk_all over the n applications of the cohort (all have ni/nj/nk_all '
                        '>= 0).'),
        'njfrac_all_mean': ('Mean over the n applications of nj_all / (ni_all + nj_all + nk_all), the '
                            'share of type-j (co-citing) documents.'),
    },
    'PATSTAT/output_grant/patstat_hit_probability.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000) of a granted '
                     'application (grant year 1900-2023); every application of patstat_metadata with a'
                     ' non-NULL wipo_sector, cited or not.'),
        'wipo_sector': 'Cohort sector: patstat_metadata.wipo_sector (one of the five WIPO sectors).',
        'grant_year': ("Cohort year: the grant year, i.e. the year of the application's first "
                       "publication flagged publn_first_grant = 'Y' (1900-2023)."),
        'pctl_C_3': ('Percentile of C_3 (citation rows within 3 years) within the wipo_sector x '
                     'grant_year cohort: rank() / n with ties at the minimum rank (pandas rank method '
                     "'min'), ascending, applications absent from patstat_citation counted as 0; in "
                     '(0, 1], higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_examiner_3': ('Percentile of C_examiner_3 (examiner-bucket citation rows within 3 '
                              'years) within the wipo_sector x grant_year cohort: rank() / n with ties'
                              " at the minimum rank (pandas rank method 'min'), ascending, "
                              'applications absent from patstat_citation counted as 0; in (0, 1], '
                              'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_applicant_3': ('Percentile of C_applicant_3 (applicant-bucket citation rows within 3 '
                               'years) within the wipo_sector x grant_year cohort: rank() / n with '
                               "ties at the minimum rank (pandas rank method 'min'), ascending, "
                               'applications absent from patstat_citation counted as 0; in (0, 1], '
                               'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_other_3': ('Percentile of C_other_3 (other-bucket citation rows within 3 years) within'
                           ' the wipo_sector x grant_year cohort: rank() / n with ties at the minimum '
                           "rank (pandas rank method 'min'), ascending, applications absent from "
                           'patstat_citation counted as 0; in (0, 1], higher = more cited, top 1 % <=>'
                           ' >= 0.99 (float32).'),
        'pctl_C_5': ('Percentile of C_5 (citation rows within 5 years) within the wipo_sector x '
                     'grant_year cohort: rank() / n with ties at the minimum rank (pandas rank method '
                     "'min'), ascending, applications absent from patstat_citation counted as 0; in "
                     '(0, 1], higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_examiner_5': ('Percentile of C_examiner_5 (examiner-bucket citation rows within 5 '
                              'years) within the wipo_sector x grant_year cohort: rank() / n with ties'
                              " at the minimum rank (pandas rank method 'min'), ascending, "
                              'applications absent from patstat_citation counted as 0; in (0, 1], '
                              'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_applicant_5': ('Percentile of C_applicant_5 (applicant-bucket citation rows within 5 '
                               'years) within the wipo_sector x grant_year cohort: rank() / n with '
                               "ties at the minimum rank (pandas rank method 'min'), ascending, "
                               'applications absent from patstat_citation counted as 0; in (0, 1], '
                               'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_other_5': ('Percentile of C_other_5 (other-bucket citation rows within 5 years) within'
                           ' the wipo_sector x grant_year cohort: rank() / n with ties at the minimum '
                           "rank (pandas rank method 'min'), ascending, applications absent from "
                           'patstat_citation counted as 0; in (0, 1], higher = more cited, top 1 % <=>'
                           ' >= 0.99 (float32).'),
        'pctl_C_10': ('Percentile of C_10 (citation rows within 10 years) within the wipo_sector x '
                      'grant_year cohort: rank() / n with ties at the minimum rank (pandas rank method'
                      " 'min'), ascending, applications absent from patstat_citation counted as 0; in "
                      '(0, 1], higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_examiner_10': ('Percentile of C_examiner_10 (examiner-bucket citation rows within 10 '
                               'years) within the wipo_sector x grant_year cohort: rank() / n with '
                               "ties at the minimum rank (pandas rank method 'min'), ascending, "
                               'applications absent from patstat_citation counted as 0; in (0, 1], '
                               'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_applicant_10': ('Percentile of C_applicant_10 (applicant-bucket citation rows within '
                                '10 years) within the wipo_sector x grant_year cohort: rank() / n with'
                                " ties at the minimum rank (pandas rank method 'min'), ascending, "
                                'applications absent from patstat_citation counted as 0; in (0, 1], '
                                'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_other_10': ('Percentile of C_other_10 (other-bucket citation rows within 10 years) '
                            'within the wipo_sector x grant_year cohort: rank() / n with ties at the '
                            "minimum rank (pandas rank method 'min'), ascending, applications absent "
                            'from patstat_citation counted as 0; in (0, 1], higher = more cited, top 1'
                            ' % <=> >= 0.99 (float32).'),
        'pctl_C_all': ('Percentile of C_all (citation rows at any age) within the wipo_sector x '
                       'grant_year cohort: rank() / n with ties at the minimum rank (pandas rank '
                       "method 'min'), ascending, applications absent from patstat_citation counted as"
                       ' 0; in (0, 1], higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_examiner_all': ('Percentile of C_examiner_all (examiner-bucket citation rows at any '
                                'age) within the wipo_sector x grant_year cohort: rank() / n with ties'
                                " at the minimum rank (pandas rank method 'min'), ascending, "
                                'applications absent from patstat_citation counted as 0; in (0, 1], '
                                'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_applicant_all': ('Percentile of C_applicant_all (applicant-bucket citation rows at any'
                                 ' age) within the wipo_sector x grant_year cohort: rank() / n with '
                                 "ties at the minimum rank (pandas rank method 'min'), ascending, "
                                 'applications absent from patstat_citation counted as 0; in (0, 1], '
                                 'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_other_all': ('Percentile of C_other_all (other-bucket citation rows at any age) within'
                             ' the wipo_sector x grant_year cohort: rank() / n with ties at the '
                             "minimum rank (pandas rank method 'min'), ascending, applications absent "
                             'from patstat_citation counted as 0; in (0, 1], higher = more cited, top '
                             '1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_3': ('Percentile of uniqueC_3 (distinct citing applications within 3 years) '
                           'within the wipo_sector x grant_year cohort: rank() / n with ties at the '
                           "minimum rank (pandas rank method 'min'), ascending, applications absent "
                           'from patstat_citation counted as 0; in (0, 1], higher = more cited, top 1 '
                           '% <=> >= 0.99 (float32).'),
        'pctl_uniqueC_examiner_3': ('Percentile of uniqueC_examiner_3 (distinct citing applications '
                                    'citing through the examiner bucket within 3 years) within the '
                                    'wipo_sector x grant_year cohort: rank() / n with ties at the '
                                    "minimum rank (pandas rank method 'min'), ascending, applications "
                                    'absent from patstat_citation counted as 0; in (0, 1], higher = '
                                    'more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_applicant_3': ('Percentile of uniqueC_applicant_3 (distinct citing applications '
                                     'citing through the applicant bucket within 3 years) within the '
                                     'wipo_sector x grant_year cohort: rank() / n with ties at the '
                                     "minimum rank (pandas rank method 'min'), ascending, applications"
                                     ' absent from patstat_citation counted as 0; in (0, 1], higher = '
                                     'more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_other_3': ('Percentile of uniqueC_other_3 (distinct citing applications citing '
                                 'through the other bucket within 3 years) within the wipo_sector x '
                                 'grant_year cohort: rank() / n with ties at the minimum rank (pandas '
                                 "rank method 'min'), ascending, applications absent from "
                                 'patstat_citation counted as 0; in (0, 1], higher = more cited, top 1'
                                 ' % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_5': ('Percentile of uniqueC_5 (distinct citing applications within 5 years) '
                           'within the wipo_sector x grant_year cohort: rank() / n with ties at the '
                           "minimum rank (pandas rank method 'min'), ascending, applications absent "
                           'from patstat_citation counted as 0; in (0, 1], higher = more cited, top 1 '
                           '% <=> >= 0.99 (float32).'),
        'pctl_uniqueC_examiner_5': ('Percentile of uniqueC_examiner_5 (distinct citing applications '
                                    'citing through the examiner bucket within 5 years) within the '
                                    'wipo_sector x grant_year cohort: rank() / n with ties at the '
                                    "minimum rank (pandas rank method 'min'), ascending, applications "
                                    'absent from patstat_citation counted as 0; in (0, 1], higher = '
                                    'more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_applicant_5': ('Percentile of uniqueC_applicant_5 (distinct citing applications '
                                     'citing through the applicant bucket within 5 years) within the '
                                     'wipo_sector x grant_year cohort: rank() / n with ties at the '
                                     "minimum rank (pandas rank method 'min'), ascending, applications"
                                     ' absent from patstat_citation counted as 0; in (0, 1], higher = '
                                     'more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_other_5': ('Percentile of uniqueC_other_5 (distinct citing applications citing '
                                 'through the other bucket within 5 years) within the wipo_sector x '
                                 'grant_year cohort: rank() / n with ties at the minimum rank (pandas '
                                 "rank method 'min'), ascending, applications absent from "
                                 'patstat_citation counted as 0; in (0, 1], higher = more cited, top 1'
                                 ' % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_10': ('Percentile of uniqueC_10 (distinct citing applications within 10 years) '
                            'within the wipo_sector x grant_year cohort: rank() / n with ties at the '
                            "minimum rank (pandas rank method 'min'), ascending, applications absent "
                            'from patstat_citation counted as 0; in (0, 1], higher = more cited, top 1'
                            ' % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_examiner_10': ('Percentile of uniqueC_examiner_10 (distinct citing applications '
                                     'citing through the examiner bucket within 10 years) within the '
                                     'wipo_sector x grant_year cohort: rank() / n with ties at the '
                                     "minimum rank (pandas rank method 'min'), ascending, applications"
                                     ' absent from patstat_citation counted as 0; in (0, 1], higher = '
                                     'more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_applicant_10': ('Percentile of uniqueC_applicant_10 (distinct citing '
                                      'applications citing through the applicant bucket within 10 '
                                      'years) within the wipo_sector x grant_year cohort: rank() / n '
                                      "with ties at the minimum rank (pandas rank method 'min'), "
                                      'ascending, applications absent from patstat_citation counted as'
                                      ' 0; in (0, 1], higher = more cited, top 1 % <=> >= 0.99 '
                                      '(float32).'),
        'pctl_uniqueC_other_10': ('Percentile of uniqueC_other_10 (distinct citing applications citing'
                                  ' through the other bucket within 10 years) within the wipo_sector x'
                                  ' grant_year cohort: rank() / n with ties at the minimum rank '
                                  "(pandas rank method 'min'), ascending, applications absent from "
                                  'patstat_citation counted as 0; in (0, 1], higher = more cited, top '
                                  '1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_all': ('Percentile of uniqueC_all (distinct citing applications at any age) '
                             'within the wipo_sector x grant_year cohort: rank() / n with ties at the '
                             "minimum rank (pandas rank method 'min'), ascending, applications absent "
                             'from patstat_citation counted as 0; in (0, 1], higher = more cited, top '
                             '1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_examiner_all': ('Percentile of uniqueC_examiner_all (distinct citing '
                                      'applications citing through the examiner bucket at any age) '
                                      'within the wipo_sector x grant_year cohort: rank() / n with '
                                      "ties at the minimum rank (pandas rank method 'min'), ascending,"
                                      ' applications absent from patstat_citation counted as 0; in (0,'
                                      ' 1], higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_applicant_all': ('Percentile of uniqueC_applicant_all (distinct citing '
                                       'applications citing through the applicant bucket at any age) '
                                       'within the wipo_sector x grant_year cohort: rank() / n with '
                                       "ties at the minimum rank (pandas rank method 'min'), "
                                       'ascending, applications absent from patstat_citation counted '
                                       'as 0; in (0, 1], higher = more cited, top 1 % <=> >= 0.99 '
                                       '(float32).'),
        'pctl_uniqueC_other_all': ('Percentile of uniqueC_other_all (distinct citing applications '
                                   'citing through the other bucket at any age) within the wipo_sector'
                                   ' x grant_year cohort: rank() / n with ties at the minimum rank '
                                   "(pandas rank method 'min'), ascending, applications absent from "
                                   'patstat_citation counted as 0; in (0, 1], higher = more cited, top'
                                   ' 1 % <=> >= 0.99 (float32).'),
        'pctl_c3': ('Legacy alias, identical to pctl_C_3 (percentile of citation rows C_3, not of '
                    'uniqueC), kept for readers using the PatentView short names.'),
        'pctl_c5': ('Legacy alias, identical to pctl_C_5 (percentile of citation rows C_5, not of '
                    'uniqueC), kept for readers using the PatentView short names.'),
        'pctl_c10': ('Legacy alias, identical to pctl_C_10 (percentile of citation rows C_10, not of '
                     'uniqueC), kept for readers using the PatentView short names.'),
        'pctl_call': ('Legacy alias, identical to pctl_C_all (percentile of citation rows C_all, not '
                      'of uniqueC), kept for readers using the PatentView short names.'),
    },
    'PATSTAT/output_grant/patstat_inventor.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000) of a granted '
                     'application (grant year 1900-2023); one row per application with at least one '
                     'inventor row in tls207.'),
        'inventor_list': ("Inventor PATSTAT person_ids as a ';'-joined string in invt_seq_nr order "
                          '(ties by person_id): a named person once at its lowest sequence, an unnamed'
                          ' placeholder record (empty tls206.person_name, e.g. person_id 263) once per'
                          ' slot, so its id can repeat. Person records, not disambiguated inventors; '
                          'identical to patstat_metadata.inventor_list.'),
        'n_inventors': ('Number of inventor slots = length of inventor_list (distinct named persons '
                        'plus each slot of an unnamed placeholder); team size under its PatentView '
                        'name. Not tls201.nb_inventors.'),
    },
    'PATSTAT/output_grant/patstat_inventor_country.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000) of a granted '
                     'application (grant year 1900-2023); one row per application with at least one '
                     'inventor row (same rows as patstat_inventor).'),
        'n_inventors': ('Inventor slots under the once-per-named-person / once-per-placeholder-slot '
                        'rule; identical to patstat_inventor.n_inventors.'),
        'n_located': ('Inventor slots whose person record has a two-letter country code '
                      '(tls206.person_ctry_code matching [A-Z]{2}; malformed codes read as unknown); '
                      '<= n_inventors.'),
        'countries': ("Distinct inventor country codes, sorted alphabetically, ';'-joined (e.g. "
                      "'AU;GB;US'); NULL if no inventor is located. Codes are the address country "
                      "recorded on that application's person record."),
        'n_countries': 'Number of codes in countries; 0 when countries is NULL.',
        'country_inventor_counts': ("Inventors per country as 'CC:n' pairs joined by ';', ordered by "
                                    "count descending then code (e.g. 'GB:4;AU:1;US:1'); counts sum to"
                                    ' n_located; NULL if none located.'),
        'first_inventor_country': ('Country of the lowest-sequence inventor; NULL when that inventor '
                                   'has no country (not replaced by the next located inventor).'),
        'is_international': 'TRUE when n_countries > 1 (inventors in at least two countries).',
        'applicant_countries': ('Distinct two-letter country codes of the applicants (all tls207 rows '
                                "with applt_seq_nr > 0), sorted, ';'-joined; NULL if no applicant is "
                                'located; identical to patstat_metadata.applicant_ctry_list.'),
    },
    'PATSTAT/output_grant/patstat_metadata.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000) of a granted '
                     'application (grant year 1900-2023); primary key shared with every other table in'
                     ' this set (the grant-clock universe).'),
        'appln_auth': ('Two-letter code of the office the application was filed at '
                       '(tls201.appln_auth), e.g. EP, US, CN, JP, or WO for a PCT international '
                       'application.'),
        'filing_year': ('Filing year of the application (tls201.appln_filing_year, 1900-2023). Not the'
                        ' clock here (this set dates by grant_year), but it is the CD-percentile '
                        'cohort year (pctl_year) of patstat_disruption.'),
        'priority_year': ("Year of the application's earliest filing date "
                          '(tls201.earliest_filing_year: earliest of its own filing, its PCT '
                          'application, its Paris-convention priorities, technical relations and '
                          "continuations, direct links only); NULL replaces PATSTAT's 9999 default. "
                          'Equals filing_year when no earlier linked filing exists; can precede 1900 '
                          '(min 1819) because the 1900 floor applies to filing years only.'),
        'grant_year': ("Year of the application's first grant publication (min year of tls211 "
                       "publications flagged publn_first_grant = 'Y'); the clock year of every metric "
                       'in this set, 1900-2023, never NULL here.'),
        'granted': ("PATSTAT's granted flag (tls201.granted = 'Y'); always TRUE in this set, which "
                    'holds only applications with a grant publication.'),
        'docdb_family_id': ('DOCDB simple-family id (tls201.docdb_family_id): applications sharing '
                            'exactly the same priorities; the key of the family set '
                            '(PATSTAT/output_family/).'),
        'docdb_family_size': ("PATSTAT's count of applications in the DOCDB simple family "
                              '(tls201.docdb_family_size), all members including those outside this '
                              'universe; 1 = the only member.'),
        'nb_citing_docdb_fam': ("PATSTAT's own family-level forward-citation count "
                                '(tls201.nb_citing_docdb_fam): distinct DOCDB families citing any '
                                "publication or application of this application's family, taken as-is "
                                'from PATSTAT (this pipeline applies no window, universe or provenance'
                                ' filter to it); not the same as C / uniqueC.'),
        'ref_count': ('Number of distinct cited applications for which this application is the citer '
                      "in this set's patstat_reference (both ends in the grant-clock universe, "
                      'third-party and replenished rows excluded, self-citations dropped, NO age '
                      'filter so later-granted references count); 0 if none.'),
        'npl_ref_count': ('Number of distinct non-patent-literature documents '
                          "(tls212.cited_npl_publn_id <> '0') cited by any publication of the "
                          'application, replenished rows excluded (third-party NPL not removed); 0 if '
                          'none.'),
        'ipc_main': ("Main IPC symbol (tls209 row with ipc_position = 'F', whitespace removed, e.g. "
                     "'C07D499/06'; alphabetically first if several); NULL if none."),
        'cpc_code': ("One representative CPC symbol (tls224, whitespace removed, e.g. 'G06K7/0013'): "
                     'the alphabetically first symbol in the same 4-character subclass as ipc_main, '
                     'else the alphabetically first symbol; NULL if no CPC. Its first letter is the '
                     'CD-percentile group.'),
        'cpc_code_list': ('All distinct CPC symbols of the application (whitespace removed), sorted, '
                          "';'-joined; NULL if no CPC."),
        'cpc_subclass_list': ("Distinct 4-character CPC subclasses (e.g. 'A61P;C07D'), sorted, "
                              "';'-joined; the atypicality input; NULL if no CPC."),
        'techn_field_nr': ('WIPO technology field 1-35 (Schmoch 2008 concordance, '
                           'tls230_appln_techn_field) with the largest weight, ties to the lowest '
                           'number; NULL if PATSTAT assigns none. Field names in ps_common.WIPO_FIELD.'),
        'wipo_sector': ('WIPO sector of techn_field_nr: Electrical engineering (fields 1-8), '
                        'Instruments (9-13), Chemistry (14-24), Mechanical engineering (25-32), Other '
                        'fields (33-35); NULL when techn_field_nr is NULL. The hit-probability cohort '
                        'sector.'),
        'inventor_list': ('Inventor PATSTAT person_ids (tls207 rows with invt_seq_nr > 0) as a '
                          "';'-joined string in invt_seq_nr order (ties by person_id): a named person "
                          'once at its lowest sequence, an unnamed placeholder record (empty '
                          'tls206.person_name) once per slot, so its id can repeat. person_ids are '
                          'per-record, not disambiguated inventors; NULL if no inventor.'),
        'applicant_list': ('Applicant PATSTAT person_ids (tls207 rows with applt_seq_nr > 0), '
                           "';'-joined in applt_seq_nr order with the same once-per-named-person rule;"
                           ' person and company records, not disambiguated; NULL if no applicant.'),
        'inventor_ctry_list': ('Distinct two-letter country codes of the inventors '
                               '(tls206.person_ctry_code of each person record; only [A-Z]{2} codes '
                               "count, malformed ones are read as unknown), sorted, ';'-joined; NULL "
                               'if no inventor has one (common for CN and JP filings).'),
        'applicant_ctry_list': ('Distinct two-letter country codes of the applicants '
                                "(tls206.person_ctry_code, [A-Z]{2} only), sorted, ';'-joined; NULL if"
                                ' none.'),
        'applicant_sector': ('PATSTAT standardised-name sector (tls206.psn_sector) of the applicant at'
                             ' sequence number 1: COMPANY, INDIVIDUAL, UNIVERSITY, GOV NON-PROFIT, '
                             "HOSPITAL, UNKNOWN or a space-joined combination (e.g. 'GOV NON-PROFIT "
                             "UNIVERSITY'); NULL if missing or blank."),
    },
    'PATSTAT/output_grant/patstat_reference.parquet': {
        'citing_id': ('appln_id of the citing application (in the grant-clock universe (granted, grant'
                      ' year 1900-2023)).'),
        'cited_id': ('appln_id of the cited application (in the grant-clock universe (granted, grant '
                     'year 1900-2023)); never equal to citing_id (self-citations through another '
                     'publication are dropped).'),
        'citing_year': ('Grant year of the citing application (year of its first publication flagged '
                        "publn_first_grant = 'Y')."),
        'cited_year': 'Grant year of the cited application.',
        'age': ('citing_year - cited_year in years. Can be negative (a search report citing a '
                'later-granted document); such rows are kept here, and every metric requires age >= 0 '
                '(ps.EDGE_WHERE).'),
        'citing_publn_year': ("Year of the citing publication's date (tls211.publn_date), a "
                              'publication-based alternative clock; 9999 = date unknown in PATSTAT (a '
                              'few hundred rows).'),
        'bucket': ("Provenance bucket of citn_origin (ps.bucket_sql): 'applicant' = APP; 'examiner' = "
                   "SEA, ISR, SUP, PRS, EXA, FOP, CH2; 'other' = anything else (OPP, APL, blank)."),
        'replenished': ('TRUE when PATSTAT copied the citation onto the citing publication from '
                        'another publication (tls212.citn_replenished <> 0: Euro-PCT EP publications '
                        'filled with the citations of their WO international publication). Kept for '
                        'completeness; excluded from every count by ps.EDGE_WHERE.'),
    },
    'PATSTAT/output_grant/patstat_sb.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000) of a granted '
                     'application (grant year 1900-2023); a cited application with at least one '
                     'counted citation (same rows as patstat_citation).'),
        'SB_B': ('Ke et al. (2015) beauty coefficient from the yearly histogram of citation rows (not '
                 'distinct citing applications) by age 0 .. last cited age (age >= 0, not '
                 'replenished): sum over t <= t_m of (line from (0, c_0) to the peak (t_m, c_m) minus '
                 'c_t) / max(c_t, 1). 0 when the first maximum is at age 0 (also the value for a '
                 'single-year histogram); can be negative (min about -5); float32.'),
        'SB_T': ("Awakening time: the age t <= t_m (years since the application's grant year) at which"
                 ' the histogram lies farthest from the line joining (0, c_0) and the peak; 0 when the'
                 ' peak is at age 0.'),
        'n_cite': ('Total citation rows (not distinct citing applications) in the histogram, i.e. '
                   'C_all of patstat_citation.'),
    },
    'PATSTAT/output_grant/patstat_uniqueC_trend.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000) of a granted '
                     'application (grant year 1900-2023); the cited application. One row per '
                     '(application, year) with at least one new citing application.'),
        'grant_year': ('Clock year of the cited application: the grant year, i.e. the year of the '
                       "application's first publication flagged publn_first_grant = 'Y' (1900-2023)."),
        'cite_year': ('grant_year + yrs_since_grant: the grant year of the citing applications counted'
                      ' in this row.'),
        'yrs_since_grant': ("Lag in years from the cited application's grant year to the citer's (the "
                            "minimum over the pair's edges, which is the only lag because both ends "
                            'have one clock year each); >= 0.'),
        'uniqueC': ('Number of distinct citing applications whose citation of this application falls '
                    'at this lag. Cumulative sums over lags <= 3/5/10/all reproduce uniqueC_3/5/10/all'
                    ' of patstat_citation, and the column equals patstat_citation_trend.uniqueC row '
                    'for row (both asserted in the notebook).'),
    },
    'PATSTAT/output_grant/patstat_z_score.parquet': {
        'appln_id': ('PATSTAT application id (tls201.appln_id, integer < 900,000,000) of a granted '
                     'application (grant year 1900-2023); a application with at least two distinct CPC'
                     ' subclasses (its distinct 4-character CPC subclasses (tls224, whitespace '
                     'removed)).'),
        'Z_median': ("Median over the application's subclass pairs of the pair z-score (Kim et al. "
                     "(2016) hypergeometric z of a CPC-subclass pair in the application's grant year, "
                     'with counts cumulative over all applications with >= 2 subclasses up to and '
                     'including that year; z < 0 = atypical pair).'),
        'Z_10pct': ("10th percentile (linear interpolation, DuckDB quantile_cont) of the application's"
                    ' pair z-scores; low values flag atypical combinations.'),
        'Z_min': 'Minimum pair z-score of the application (its most atypical subclass pair).',
        'n_pairs': ('Number of distinct CPC-subclass pairs scored = k(k-1)/2 for k distinct '
                    'subclasses.'),
    },
    'PATSTAT/output_grant/z_score_pair.parquet': {
        'code_1': ("First CPC subclass of the pair (4 characters, e.g. 'A01B'); always alphabetically "
                   'lower than code_2.'),
        'code_2': 'Second CPC subclass of the pair (4 characters); alphabetically higher than code_1.',
        'year': ('Year in which at least one application with >= 2 subclasses carries this pair, on '
                 "this set's clock: the grant year, i.e. the year of the application's first "
                 "publication flagged publn_first_grant = 'Y' (1900-2023)."),
        'Z_score': ('Hypergeometric z = (o - mu) / sqrt(var) with mu = n_a n_b / N and var = mu (1 - '
                    'n_a / N) (N - n_b) / (N - 1), where N, n_a, n_b and o (co-occurrences) count '
                    'applications with >= 2 subclasses cumulatively through this year inclusive; 0 '
                    'when var <= 0. z < 0 = rarer than chance (atypical).'),
    },
    'PATSTAT/output_family/patstat_citation.parquet': {
        'docdb_family_id': ('DOCDB simple-family id (tls201.docdb_family_id, integer); the cited '
                            'family. Only families with at least one counted family citation are rows;'
                            ' an absent family received none (patstat_hit_probability fills the '
                            'zeros).'),
        'C_3': ('Family citation rows received from citing families whose priority year is 0 to 3 '
                "years after this family's priority year (0 <= age <= 3, inclusive at both ends). The "
                'family edge list has one row per (citing family, cited family, provenance bucket), so'
                ' a family citing under two buckets counts twice; within-family and replenished '
                'citations are excluded. Use uniqueC_3 for distinct citing families.'),
        'C_examiner_3': ("The 'examiner' part of C_3 (citn_origin SEA, ISR, SUP, PRS, EXA, FOP or CH2:"
                         ' search-report, examination, opposition-filing and PCT chapter II '
                         'citations): citing families with at least one examiner-bucket application '
                         'citation within the window. One row per family and bucket, so it equals '
                         'uniqueC_examiner_3 in this set; C_3 = C_examiner_3 + C_applicant_3 + '
                         'C_other_3.'),
        'C_applicant_3': ("The 'applicant' part of C_3 (citn_origin APP: references submitted by the "
                          'applicant): citing families with at least one applicant-bucket application '
                          'citation within the window. One row per family and bucket, so it equals '
                          'uniqueC_applicant_3 in this set; C_3 = C_examiner_3 + C_applicant_3 + '
                          'C_other_3.'),
        'C_other_3': ("The 'other' part of C_3 (citn_origin OPP, APL or blank: opposition-division and"
                      ' appeal citations): citing families with at least one other-bucket application '
                      'citation within the window. One row per family and bucket, so it equals '
                      'uniqueC_other_3 in this set; C_3 = C_examiner_3 + C_applicant_3 + C_other_3.'),
        'C_5': ('Family citation rows received from citing families whose priority year is 0 to 5 '
                "years after this family's priority year (0 <= age <= 5, inclusive at both ends). The "
                'family edge list has one row per (citing family, cited family, provenance bucket), so'
                ' a family citing under two buckets counts twice; within-family and replenished '
                'citations are excluded. Use uniqueC_5 for distinct citing families.'),
        'C_examiner_5': ("The 'examiner' part of C_5 (citn_origin SEA, ISR, SUP, PRS, EXA, FOP or CH2:"
                         ' search-report, examination, opposition-filing and PCT chapter II '
                         'citations): citing families with at least one examiner-bucket application '
                         'citation within the window. One row per family and bucket, so it equals '
                         'uniqueC_examiner_5 in this set; C_5 = C_examiner_5 + C_applicant_5 + '
                         'C_other_5.'),
        'C_applicant_5': ("The 'applicant' part of C_5 (citn_origin APP: references submitted by the "
                          'applicant): citing families with at least one applicant-bucket application '
                          'citation within the window. One row per family and bucket, so it equals '
                          'uniqueC_applicant_5 in this set; C_5 = C_examiner_5 + C_applicant_5 + '
                          'C_other_5.'),
        'C_other_5': ("The 'other' part of C_5 (citn_origin OPP, APL or blank: opposition-division and"
                      ' appeal citations): citing families with at least one other-bucket application '
                      'citation within the window. One row per family and bucket, so it equals '
                      'uniqueC_other_5 in this set; C_5 = C_examiner_5 + C_applicant_5 + C_other_5.'),
        'C_10': ('Family citation rows received from citing families whose priority year is 0 to 10 '
                 "years after this family's priority year (0 <= age <= 10, inclusive at both ends). "
                 'The family edge list has one row per (citing family, cited family, provenance '
                 'bucket), so a family citing under two buckets counts twice; within-family and '
                 'replenished citations are excluded. Use uniqueC_10 for distinct citing families.'),
        'C_examiner_10': ("The 'examiner' part of C_10 (citn_origin SEA, ISR, SUP, PRS, EXA, FOP or "
                          'CH2: search-report, examination, opposition-filing and PCT chapter II '
                          'citations): citing families with at least one examiner-bucket application '
                          'citation within the window. One row per family and bucket, so it equals '
                          'uniqueC_examiner_10 in this set; C_10 = C_examiner_10 + C_applicant_10 + '
                          'C_other_10.'),
        'C_applicant_10': ("The 'applicant' part of C_10 (citn_origin APP: references submitted by the"
                           ' applicant): citing families with at least one applicant-bucket '
                           'application citation within the window. One row per family and bucket, so '
                           'it equals uniqueC_applicant_10 in this set; C_10 = C_examiner_10 + '
                           'C_applicant_10 + C_other_10.'),
        'C_other_10': ("The 'other' part of C_10 (citn_origin OPP, APL or blank: opposition-division "
                       'and appeal citations): citing families with at least one other-bucket '
                       'application citation within the window. One row per family and bucket, so it '
                       'equals uniqueC_other_10 in this set; C_10 = C_examiner_10 + C_applicant_10 + '
                       'C_other_10.'),
        'C_all': ('Family citation rows received from citing families whose priority year is the same '
                  "as or later than this family's priority year (age >= 0, no upper bound: every year "
                  'up to the 2023 snapshot). The family edge list has one row per (citing family, '
                  'cited family, provenance bucket), so a family citing under two buckets counts '
                  'twice; within-family and replenished citations are excluded. Use uniqueC_all for '
                  'distinct citing families.'),
        'C_examiner_all': ("The 'examiner' part of C_all (citn_origin SEA, ISR, SUP, PRS, EXA, FOP or "
                           'CH2: search-report, examination, opposition-filing and PCT chapter II '
                           'citations): citing families with at least one examiner-bucket application '
                           'citation within the window. One row per family and bucket, so it equals '
                           'uniqueC_examiner_all in this set; C_all = C_examiner_all + C_applicant_all'
                           ' + C_other_all.'),
        'C_applicant_all': ("The 'applicant' part of C_all (citn_origin APP: references submitted by "
                            'the applicant): citing families with at least one applicant-bucket '
                            'application citation within the window. One row per family and bucket, so'
                            ' it equals uniqueC_applicant_all in this set; C_all = C_examiner_all + '
                            'C_applicant_all + C_other_all.'),
        'C_other_all': ("The 'other' part of C_all (citn_origin OPP, APL or blank: opposition-division"
                        ' and appeal citations): citing families with at least one other-bucket '
                        'application citation within the window. One row per family and bucket, so it '
                        'equals uniqueC_other_all in this set; C_all = C_examiner_all + '
                        'C_applicant_all + C_other_all.'),
        'uniqueC_3': ('Distinct citing DOCDB families whose priority year is 0 to 3 years after this '
                      "family's priority year (0 <= age <= 3, inclusive at both ends), each counted "
                      'once however many rows it contributes; the de-duplicated impact count to use.'),
        'uniqueC_examiner_3': ('Distinct citing DOCDB families within the same window that cite this '
                               "family through at least one 'examiner'-bucket row (citn_origin SEA, "
                               'ISR, SUP, PRS, EXA, FOP or CH2: search-report, examination, '
                               'opposition-filing and PCT chapter II citations). A citer using several'
                               ' buckets counts in each, so the three bucket counts can sum to more '
                               'than uniqueC_3.'),
        'uniqueC_applicant_3': ('Distinct citing DOCDB families within the same window that cite this '
                                "family through at least one 'applicant'-bucket row (citn_origin APP: "
                                'references submitted by the applicant). A citer using several buckets'
                                ' counts in each, so the three bucket counts can sum to more than '
                                'uniqueC_3.'),
        'uniqueC_other_3': ('Distinct citing DOCDB families within the same window that cite this '
                            "family through at least one 'other'-bucket row (citn_origin OPP, APL or "
                            'blank: opposition-division and appeal citations). A citer using several '
                            'buckets counts in each, so the three bucket counts can sum to more than '
                            'uniqueC_3.'),
        'uniqueC_5': ('Distinct citing DOCDB families whose priority year is 0 to 5 years after this '
                      "family's priority year (0 <= age <= 5, inclusive at both ends), each counted "
                      'once however many rows it contributes; the de-duplicated impact count to use.'),
        'uniqueC_examiner_5': ('Distinct citing DOCDB families within the same window that cite this '
                               "family through at least one 'examiner'-bucket row (citn_origin SEA, "
                               'ISR, SUP, PRS, EXA, FOP or CH2: search-report, examination, '
                               'opposition-filing and PCT chapter II citations). A citer using several'
                               ' buckets counts in each, so the three bucket counts can sum to more '
                               'than uniqueC_5.'),
        'uniqueC_applicant_5': ('Distinct citing DOCDB families within the same window that cite this '
                                "family through at least one 'applicant'-bucket row (citn_origin APP: "
                                'references submitted by the applicant). A citer using several buckets'
                                ' counts in each, so the three bucket counts can sum to more than '
                                'uniqueC_5.'),
        'uniqueC_other_5': ('Distinct citing DOCDB families within the same window that cite this '
                            "family through at least one 'other'-bucket row (citn_origin OPP, APL or "
                            'blank: opposition-division and appeal citations). A citer using several '
                            'buckets counts in each, so the three bucket counts can sum to more than '
                            'uniqueC_5.'),
        'uniqueC_10': ('Distinct citing DOCDB families whose priority year is 0 to 10 years after this'
                       " family's priority year (0 <= age <= 10, inclusive at both ends), each counted"
                       ' once however many rows it contributes; the de-duplicated impact count to use.'),
        'uniqueC_examiner_10': ('Distinct citing DOCDB families within the same window that cite this '
                                "family through at least one 'examiner'-bucket row (citn_origin SEA, "
                                'ISR, SUP, PRS, EXA, FOP or CH2: search-report, examination, '
                                'opposition-filing and PCT chapter II citations). A citer using '
                                'several buckets counts in each, so the three bucket counts can sum to'
                                ' more than uniqueC_10.'),
        'uniqueC_applicant_10': ('Distinct citing DOCDB families within the same window that cite this'
                                 " family through at least one 'applicant'-bucket row (citn_origin "
                                 'APP: references submitted by the applicant). A citer using several '
                                 'buckets counts in each, so the three bucket counts can sum to more '
                                 'than uniqueC_10.'),
        'uniqueC_other_10': ('Distinct citing DOCDB families within the same window that cite this '
                             "family through at least one 'other'-bucket row (citn_origin OPP, APL or "
                             'blank: opposition-division and appeal citations). A citer using several '
                             'buckets counts in each, so the three bucket counts can sum to more than '
                             'uniqueC_10.'),
        'uniqueC_all': ('Distinct citing DOCDB families whose priority year is the same as or later '
                        "than this family's priority year (age >= 0, no upper bound: every year up to "
                        'the 2023 snapshot), each counted once however many rows it contributes; the '
                        'de-duplicated impact count to use.'),
        'uniqueC_examiner_all': ('Distinct citing DOCDB families within the same window that cite this'
                                 " family through at least one 'examiner'-bucket row (citn_origin SEA,"
                                 ' ISR, SUP, PRS, EXA, FOP or CH2: search-report, examination, '
                                 'opposition-filing and PCT chapter II citations). A citer using '
                                 'several buckets counts in each, so the three bucket counts can sum '
                                 'to more than uniqueC_all.'),
        'uniqueC_applicant_all': ('Distinct citing DOCDB families within the same window that cite '
                                  "this family through at least one 'applicant'-bucket row "
                                  '(citn_origin APP: references submitted by the applicant). A citer '
                                  'using several buckets counts in each, so the three bucket counts '
                                  'can sum to more than uniqueC_all.'),
        'uniqueC_other_all': ('Distinct citing DOCDB families within the same window that cite this '
                              "family through at least one 'other'-bucket row (citn_origin OPP, APL or"
                              ' blank: opposition-division and appeal citations). A citer using '
                              'several buckets counts in each, so the three bucket counts can sum to '
                              'more than uniqueC_all.'),
    },
    'PATSTAT/output_family/patstat_citation_trend.parquet': {
        'docdb_family_id': ('DOCDB simple-family id (tls201.docdb_family_id, integer); the cited '
                            'family. One row per (family, citing year) with at least one counted '
                            'citation.'),
        'priority_year': ("Clock year of the cited family: the family's earliest priority year (min "
                          'over its universe members of tls201.earliest_filing_year, the filing year '
                          'where that is 9999). A few precede 1900 (min 1819) because the 1900 floor '
                          'applies to filing years only.'),
        'cite_year': ('Priority year of the citing DOCDB families counted in this row (the citing '
                      "family's clock year, not the publication year of the citation)."),
        'yrs_since_priority': ("Years since the cited family's priority year: cite_year - "
                               'priority_year (integer, >= 0; ps.EDGE_WHERE drops negative ages).'),
        'C': ('Family citation rows received in this citing year: one row per (citing family, '
              'provenance bucket), so a family citing under two buckets counts twice; within-family '
              'and replenished citations excluded. Summing over years gives C_all of patstat_citation.'),
        'C_examiner': ("The 'examiner' part of C in this year (citn_origin SEA, ISR, SUP, PRS, EXA, "
                       'FOP or CH2: search-report, examination, opposition-filing and PCT chapter II '
                       'citations); C = C_examiner + C_applicant + C_other.'),
        'uniqueC': ('Distinct citing DOCDB families in this citing year. A citer has one clock year, '
                    'so the yearly values sum exactly to uniqueC_all of patstat_citation.'),
    },
    'PATSTAT/output_family/patstat_disruption.parquet': {
        'docdb_family_id': ('DOCDB simple-family id (tls201.docdb_family_id, integer); every node of '
                            'the de-duplicated family citation graph (distinct citing family -> cited '
                            'family pairs with age >= 0), as citer or cited. Nodes that are never '
                            'cited have NULL CD/F/E/G and -1 in ni/nj/nk.'),
        'CD_3': ('CD disruption index (ni_3 - nj_3) / (ni_3 + nj_3 + nk_3) over families dated 0 to 3 '
                 "years after the focal family's priority year (0 <= age <= 3); in [-1, 1]. NULL when "
                 'the window holds neither a citer nor a citer of a reference (then ni/nj/nk = -1); 0 '
                 'when it has no citer but its references do (ni = nj = 0, nk > 0).'),
        'F_3': ("Foundation share: fraction of the citers dated 0 to 3 years after the focal family's "
                'priority year (0 <= age <= 3) for which down > up, where up = how many of its '
                'references (the families it cites with age >= 0) the citer also cites and down = how '
                "many of the focal's other citers in the same window it cites; ties with up = down > 0"
                ' count half F, half E. NULL when there is no citer in the window. F + E + G = 1. '
                'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_3': ("Extension share: fraction of the citers dated 0 to 3 years after the focal family's "
                "priority year (0 <= age <= 3) with up > down (citer cites more of the focal's "
                'references than of its other in-window citers), plus half of the up = down > 0 ties. '
                'NULL when there is no citer in the window. Decomposition of Fang & Evans (2025), '
                'arXiv:2510.03240.'),
        'G_3': ('Generalization share: fraction of the citers dated 0 to 3 years after the focal '
                "family's priority year (0 <= age <= 3) with up = down = 0 (cite neither the focal's "
                'references nor its other in-window citers). NULL when there is no citer in the '
                'window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_3': ("Citers dated 0 to 3 years after the focal family's priority year (0 <= age <= 3) "
                 'that cite none of its references (the families it cites with age >= 0) (count); -1 '
                 "is the sentinel for 'nothing in the window' (CD_3 NULL), not a count."),
        'nj_3': ("Citers dated 0 to 3 years after the focal family's priority year (0 <= age <= 3) "
                 'that also cite at least one of its references (the families it cites with age >= 0) '
                 '(count); -1 sentinel when nothing is in the window.'),
        'nk_3': ("Families dated 0 to 3 years after the focal family's priority year (0 <= age <= 3) "
                 "that cite at least one of the focal's references but not the focal itself (distinct "
                 'citers of the references minus nj, focal excluded); -1 sentinel when nothing is in '
                 'the window.'),
        'CD_5': ('CD disruption index (ni_5 - nj_5) / (ni_5 + nj_5 + nk_5) over families dated 0 to 5 '
                 "years after the focal family's priority year (0 <= age <= 5); in [-1, 1]. NULL when "
                 'the window holds neither a citer nor a citer of a reference (then ni/nj/nk = -1); 0 '
                 'when it has no citer but its references do (ni = nj = 0, nk > 0).'),
        'F_5': ("Foundation share: fraction of the citers dated 0 to 5 years after the focal family's "
                'priority year (0 <= age <= 5) for which down > up, where up = how many of its '
                'references (the families it cites with age >= 0) the citer also cites and down = how '
                "many of the focal's other citers in the same window it cites; ties with up = down > 0"
                ' count half F, half E. NULL when there is no citer in the window. F + E + G = 1. '
                'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_5': ("Extension share: fraction of the citers dated 0 to 5 years after the focal family's "
                "priority year (0 <= age <= 5) with up > down (citer cites more of the focal's "
                'references than of its other in-window citers), plus half of the up = down > 0 ties. '
                'NULL when there is no citer in the window. Decomposition of Fang & Evans (2025), '
                'arXiv:2510.03240.'),
        'G_5': ('Generalization share: fraction of the citers dated 0 to 5 years after the focal '
                "family's priority year (0 <= age <= 5) with up = down = 0 (cite neither the focal's "
                'references nor its other in-window citers). NULL when there is no citer in the '
                'window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_5': ("Citers dated 0 to 5 years after the focal family's priority year (0 <= age <= 5) "
                 'that cite none of its references (the families it cites with age >= 0) (count); -1 '
                 "is the sentinel for 'nothing in the window' (CD_5 NULL), not a count."),
        'nj_5': ("Citers dated 0 to 5 years after the focal family's priority year (0 <= age <= 5) "
                 'that also cite at least one of its references (the families it cites with age >= 0) '
                 '(count); -1 sentinel when nothing is in the window.'),
        'nk_5': ("Families dated 0 to 5 years after the focal family's priority year (0 <= age <= 5) "
                 "that cite at least one of the focal's references but not the focal itself (distinct "
                 'citers of the references minus nj, focal excluded); -1 sentinel when nothing is in '
                 'the window.'),
        'CD_10': ('CD disruption index (ni_10 - nj_10) / (ni_10 + nj_10 + nk_10) over families dated 0'
                  " to 10 years after the focal family's priority year (0 <= age <= 10); in [-1, 1]. "
                  'NULL when the window holds neither a citer nor a citer of a reference (then '
                  'ni/nj/nk = -1); 0 when it has no citer but its references do (ni = nj = 0, nk > 0).'),
        'F_10': ('Foundation share: fraction of the citers dated 0 to 10 years after the focal '
                 "family's priority year (0 <= age <= 10) for which down > up, where up = how many of "
                 'its references (the families it cites with age >= 0) the citer also cites and down ='
                 " how many of the focal's other citers in the same window it cites; ties with up = "
                 'down > 0 count half F, half E. NULL when there is no citer in the window. F + E + G '
                 '= 1. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_10': ("Extension share: fraction of the citers dated 0 to 10 years after the focal family's"
                 " priority year (0 <= age <= 10) with up > down (citer cites more of the focal's "
                 'references than of its other in-window citers), plus half of the up = down > 0 ties.'
                 ' NULL when there is no citer in the window. Decomposition of Fang & Evans (2025), '
                 'arXiv:2510.03240.'),
        'G_10': ('Generalization share: fraction of the citers dated 0 to 10 years after the focal '
                 "family's priority year (0 <= age <= 10) with up = down = 0 (cite neither the focal's"
                 ' references nor its other in-window citers). NULL when there is no citer in the '
                 'window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_10': ("Citers dated 0 to 10 years after the focal family's priority year (0 <= age <= 10) "
                  'that cite none of its references (the families it cites with age >= 0) (count); -1 '
                  "is the sentinel for 'nothing in the window' (CD_10 NULL), not a count."),
        'nj_10': ("Citers dated 0 to 10 years after the focal family's priority year (0 <= age <= 10) "
                  'that also cite at least one of its references (the families it cites with age >= 0)'
                  ' (count); -1 sentinel when nothing is in the window.'),
        'nk_10': ("Families dated 0 to 10 years after the focal family's priority year (0 <= age <= "
                  "10) that cite at least one of the focal's references but not the focal itself "
                  '(distinct citers of the references minus nj, focal excluded); -1 sentinel when '
                  'nothing is in the window.'),
        'CD_all': ('CD disruption index (ni_all - nj_all) / (ni_all + nj_all + nk_all) over families '
                   "dated at any time from the focal family's priority year on (age >= 0); in [-1, 1]."
                   ' NULL when the window holds neither a citer nor a citer of a reference (then '
                   'ni/nj/nk = -1); 0 when it has no citer but its references do (ni = nj = 0, nk > '
                   '0).'),
        'F_all': ("Foundation share: fraction of the citers dated at any time from the focal family's "
                  'priority year on (age >= 0) for which down > up, where up = how many of its '
                  'references (the families it cites with age >= 0) the citer also cites and down = '
                  "how many of the focal's other citers in the same window it cites; ties with up = "
                  'down > 0 count half F, half E. NULL when there is no citer in the window. F + E + G'
                  ' = 1. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'E_all': ("Extension share: fraction of the citers dated at any time from the focal family's "
                  "priority year on (age >= 0) with up > down (citer cites more of the focal's "
                  'references than of its other in-window citers), plus half of the up = down > 0 '
                  'ties. NULL when there is no citer in the window. Decomposition of Fang & Evans '
                  '(2025), arXiv:2510.03240.'),
        'G_all': ('Generalization share: fraction of the citers dated at any time from the focal '
                  "family's priority year on (age >= 0) with up = down = 0 (cite neither the focal's "
                  'references nor its other in-window citers). NULL when there is no citer in the '
                  'window. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_all': ("Citers dated at any time from the focal family's priority year on (age >= 0) that "
                   'cite none of its references (the families it cites with age >= 0) (count); -1 is '
                   "the sentinel for 'nothing in the window' (CD_all NULL), not a count."),
        'nj_all': ("Citers dated at any time from the focal family's priority year on (age >= 0) that "
                   'also cite at least one of its references (the families it cites with age >= 0) '
                   '(count); -1 sentinel when nothing is in the window.'),
        'nk_all': ("Families dated at any time from the focal family's priority year on (age >= 0) "
                   "that cite at least one of the focal's references but not the focal itself "
                   '(distinct citers of the references minus nj, focal excluded); -1 sentinel when '
                   'nothing is in the window.'),
        'pctl_year': ("CD-percentile cohort year: the filing year of the family's earliest-filed "
                      'universe member (patstat_metadata.filing_year in this set), not the priority '
                      'year.'),
        'pctl_group': ('CD-percentile cohort group: the CPC Section letter (A-H or Y) of '
                       'patstat_metadata.cpc_code (from the earliest-filed member with a CPC code); '
                       'NULL when there is no CPC code, and then every CD_*_pctl column is NULL.'),
        'CD_3_pctl': ('Minimum-rank percentile of CD_3 within its pctl_year x pctl_group cohort, among'
                      ' families with a non-NULL CD_3: rank() / n on ascending CD, ties share the '
                      'lowest rank; in (0, 1], higher = more disruptive. NULL when CD_3 or pctl_group '
                      'is NULL.'),
        'CD_3_pctl_cume': ("Cumulative percentile of CD_3 in the same cohort: share of the cohort's "
                           'non-NULL CD_3 values <= this value (ties inclusive); in (0, 1], always >= '
                           "CD_3_pctl, and differs from it inside CD's large tie blocks (e.g. many CD "
                           '= 1 or 0). NULL when CD_3 or pctl_group is NULL.'),
        'CD_5_pctl': ('Minimum-rank percentile of CD_5 within its pctl_year x pctl_group cohort, among'
                      ' families with a non-NULL CD_5: rank() / n on ascending CD, ties share the '
                      'lowest rank; in (0, 1], higher = more disruptive. NULL when CD_5 or pctl_group '
                      'is NULL.'),
        'CD_5_pctl_cume': ("Cumulative percentile of CD_5 in the same cohort: share of the cohort's "
                           'non-NULL CD_5 values <= this value (ties inclusive); in (0, 1], always >= '
                           "CD_5_pctl, and differs from it inside CD's large tie blocks (e.g. many CD "
                           '= 1 or 0). NULL when CD_5 or pctl_group is NULL.'),
        'CD_10_pctl': ('Minimum-rank percentile of CD_10 within its pctl_year x pctl_group cohort, '
                       'among families with a non-NULL CD_10: rank() / n on ascending CD, ties share '
                       'the lowest rank; in (0, 1], higher = more disruptive. NULL when CD_10 or '
                       'pctl_group is NULL.'),
        'CD_10_pctl_cume': ("Cumulative percentile of CD_10 in the same cohort: share of the cohort's "
                            'non-NULL CD_10 values <= this value (ties inclusive); in (0, 1], always '
                            ">= CD_10_pctl, and differs from it inside CD's large tie blocks (e.g. "
                            'many CD = 1 or 0). NULL when CD_10 or pctl_group is NULL.'),
        'CD_all_pctl': ('Minimum-rank percentile of CD_all within its pctl_year x pctl_group cohort, '
                        'among families with a non-NULL CD_all: rank() / n on ascending CD, ties share'
                        ' the lowest rank; in (0, 1], higher = more disruptive. NULL when CD_all or '
                        'pctl_group is NULL.'),
        'CD_all_pctl_cume': ('Cumulative percentile of CD_all in the same cohort: share of the '
                             "cohort's non-NULL CD_all values <= this value (ties inclusive); in (0, "
                             "1], always >= CD_all_pctl, and differs from it inside CD's large tie "
                             'blocks (e.g. many CD = 1 or 0). NULL when CD_all or pctl_group is NULL.'),
    },
    'PATSTAT/output_family/patstat_disruption_trend.parquet': {
        'docdb_family_id': ('DOCDB simple-family id (tls201.docdb_family_id, integer); a focal family '
                            'with at least one citer in the de-duplicated graph. One row per (family, '
                            'year) in which ni_new, nj_new or nk_new is non-zero; years without a '
                            'change have no row.'),
        'priority_year': ("Clock year of the focal family: the family's earliest priority year (min "
                          'over its universe members of tls201.earliest_filing_year, the filing year '
                          'where that is 9999). A few precede 1900 (min 1819) because the 1900 floor '
                          'applies to filing years only.'),
        'cite_year': ('Calendar priority year of this row = priority_year + yrs_since_priority; the '
                      'year in which the new citers / co-citers counted in *_new appeared (up to '
                      '2023).'),
        'yrs_since_priority': ("Years since the focal family's priority year (>= 0); the row at age w "
                               '(or the last row before it) carries the window-w values of '
                               'patstat_disruption.'),
        'ni_new': ('Citers of the focal whose priority year is exactly this year and that cite none of'
                   ' its references.'),
        'nj_new': ('Citers of the focal whose priority year is exactly this year and that also cite at'
                   ' least one of its references.'),
        'nk_new': ("Families of exactly this year that cite at least one of the focal's references but"
                   ' not the focal (focal excluded).'),
        'ni': ("Cumulative ni from age 0 through this row's age; at age w it equals ni_w of "
               'patstat_disruption and the last row equals ni_all (checked on every focal family).'),
    },
    'PATSTAT/output_family/patstat_disruption_trend_summary.parquet': {
        'priority_year': ("Cohort year of the focal documents: the family's earliest priority year "
                          '(min over its universe members of tls201.earliest_filing_year, the filing '
                          'year where that is 9999). A few precede 1900 (min 1819) because the 1900 '
                          'floor applies to filing years only.'),
        'yrs_since_priority': "Years since the cohort's priority year (>= 0).",
        'n_CD': ('Number of patstat_disruption_trend rows in this (priority_year, yrs_since_priority) '
                 'cell with a finite CD. Trend rows exist only for years in which a focal family '
                 'gained a new citer or co-citer, so this counts those families, not every cohort '
                 'member.'),
        'CD_mean': ('Mean cumulative CD over the n_CD trend rows of this (priority_year, '
                    'yrs_since_priority) cell (only families with a change in exactly this year; '
                    'values are not carried forward for the others).'),
        'n_F': ('Number of patstat_disruption_trend rows in this (priority_year, yrs_since_priority) '
                'cell with a finite F. Trend rows exist only for years in which a focal family gained '
                'a new citer or co-citer, so this counts those families, not every cohort member.'),
        'F_mean': ('Mean cumulative F (Foundation share) over the n_F trend rows of this '
                   '(priority_year, yrs_since_priority) cell (only families with a change in exactly '
                   'this year; values are not carried forward for the others). NULL when n_F = 0. '
                   'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'n_E': ('Number of patstat_disruption_trend rows in this (priority_year, yrs_since_priority) '
                'cell with a finite E. Trend rows exist only for years in which a focal family gained '
                'a new citer or co-citer, so this counts those families, not every cohort member.'),
        'E_mean': ('Mean cumulative E (Extension share) over the n_E trend rows of this '
                   '(priority_year, yrs_since_priority) cell (only families with a change in exactly '
                   'this year; values are not carried forward for the others). NULL when n_E = 0. '
                   'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'n_G': ('Number of patstat_disruption_trend rows in this (priority_year, yrs_since_priority) '
                'cell with a finite G. Trend rows exist only for years in which a focal family gained '
                'a new citer or co-citer, so this counts those families, not every cohort member.'),
        'G_mean': ('Mean cumulative G (Generalization share) over the n_G trend rows of this '
                   '(priority_year, yrs_since_priority) cell (only families with a change in exactly '
                   'this year; values are not carried forward for the others). NULL when n_G = 0. '
                   'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
    },
    'PATSTAT/output_family/patstat_feg_disruption_trend.parquet': {
        'year': ("Cohort year: the family's earliest priority year, restricted to 1900-2023 (pre-1900 "
                 'priority cohorts are left out).'),
        'n': ('Number of families of this cohort in patstat_disruption with a non-NULL CD_all, i.e. '
              'with at least one citer: the denominator of the `_all` means. The 3-, 5- and 10-year ni'
              ' / nj / nk / njfrac means are taken over the subset with something in that window.'),
        'CD_3_mean': ("Mean of CD_3 (window 3) over the cohort's families with a non-NULL CD_3 (NULLs "
                      'ignored); NULL if none.'),
        'F_3_mean': ("Mean Foundation share F_3 over the cohort's families with at least one citer in "
                     'the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans (2025), '
                     'arXiv:2510.03240.'),
        'E_3_mean': ("Mean Extension share E_3 over the cohort's families with at least one citer in "
                     'the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans (2025), '
                     'arXiv:2510.03240.'),
        'G_3_mean': ("Mean Generalization share G_3 over the cohort's families with at least one citer"
                     ' in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans '
                     '(2025), arXiv:2510.03240.'),
        'ni_3_mean': ("Mean of ni_3 (citers that cite none of its references) over the cohort's "
                      'families with something in the 3-year window: the -1 placeholder of a family '
                      'with nothing in it (no citer and nothing citing its references) is read as '
                      'NULL. NULL when no family of the cohort has anything in the window (the '
                      'earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which made '
                      'this negative for early cohorts.'),
        'nj_3_mean': ('Mean of nj_3 (citers that also cite at least one of its references) over the '
                      "cohort's families with something in the 3-year window: the -1 placeholder of a "
                      'family with nothing in it (no citer and nothing citing its references) is read '
                      'as NULL. NULL when no family of the cohort has anything in the window (the '
                      'earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which made '
                      'this negative for early cohorts.'),
        'nk_3_mean': ("Mean of nk_3 (documents citing its references but not it) over the cohort's "
                      'families with something in the 3-year window: the -1 placeholder of a family '
                      'with nothing in it (no citer and nothing citing its references) is read as '
                      'NULL. NULL when no family of the cohort has anything in the window (the '
                      'earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which made '
                      'this negative for early cohorts.'),
        'njfrac_3_mean': ('Mean of the per-family nj_3 / (ni_3 + nj_3 + nk_3), the share of the 3-year'
                          ' neighbourhood that cites both the family and its references, over the '
                          'families with something in the window (the -1 placeholder is read as NULL);'
                          ' NULL when there are none. Before 2026-10-03 the -1 rows entered as '
                          '(-1)/(-3) = 1/3 and pulled the mean toward 0.333.'),
        'CD_5_mean': ("Mean of CD_5 (window 5) over the cohort's families with a non-NULL CD_5 (NULLs "
                      'ignored); NULL if none.'),
        'F_5_mean': ("Mean Foundation share F_5 over the cohort's families with at least one citer in "
                     'the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans (2025), '
                     'arXiv:2510.03240.'),
        'E_5_mean': ("Mean Extension share E_5 over the cohort's families with at least one citer in "
                     'the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans (2025), '
                     'arXiv:2510.03240.'),
        'G_5_mean': ("Mean Generalization share G_5 over the cohort's families with at least one citer"
                     ' in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans '
                     '(2025), arXiv:2510.03240.'),
        'ni_5_mean': ("Mean of ni_5 (citers that cite none of its references) over the cohort's "
                      'families with something in the 5-year window: the -1 placeholder of a family '
                      'with nothing in it (no citer and nothing citing its references) is read as '
                      'NULL. NULL when no family of the cohort has anything in the window (the '
                      'earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which made '
                      'this negative for early cohorts.'),
        'nj_5_mean': ('Mean of nj_5 (citers that also cite at least one of its references) over the '
                      "cohort's families with something in the 5-year window: the -1 placeholder of a "
                      'family with nothing in it (no citer and nothing citing its references) is read '
                      'as NULL. NULL when no family of the cohort has anything in the window (the '
                      'earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which made '
                      'this negative for early cohorts.'),
        'nk_5_mean': ("Mean of nk_5 (documents citing its references but not it) over the cohort's "
                      'families with something in the 5-year window: the -1 placeholder of a family '
                      'with nothing in it (no citer and nothing citing its references) is read as '
                      'NULL. NULL when no family of the cohort has anything in the window (the '
                      'earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which made '
                      'this negative for early cohorts.'),
        'njfrac_5_mean': ('Mean of the per-family nj_5 / (ni_5 + nj_5 + nk_5), the share of the 5-year'
                          ' neighbourhood that cites both the family and its references, over the '
                          'families with something in the window (the -1 placeholder is read as NULL);'
                          ' NULL when there are none. Before 2026-10-03 the -1 rows entered as '
                          '(-1)/(-3) = 1/3 and pulled the mean toward 0.333.'),
        'CD_10_mean': ("Mean of CD_10 (window 10) over the cohort's families with a non-NULL CD_10 "
                       '(NULLs ignored); NULL if none.'),
        'F_10_mean': ("Mean Foundation share F_10 over the cohort's families with at least one citer "
                      'in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans '
                      '(2025), arXiv:2510.03240.'),
        'E_10_mean': ("Mean Extension share E_10 over the cohort's families with at least one citer in"
                      ' the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans '
                      '(2025), arXiv:2510.03240.'),
        'G_10_mean': ("Mean Generalization share G_10 over the cohort's families with at least one "
                      'citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & '
                      'Evans (2025), arXiv:2510.03240.'),
        'ni_10_mean': ("Mean of ni_10 (citers that cite none of its references) over the cohort's "
                       'families with something in the 10-year window: the -1 placeholder of a family '
                       'with nothing in it (no citer and nothing citing its references) is read as '
                       'NULL. NULL when no family of the cohort has anything in the window (the '
                       'earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which made '
                       'this negative for early cohorts.'),
        'nj_10_mean': ('Mean of nj_10 (citers that also cite at least one of its references) over the '
                       "cohort's families with something in the 10-year window: the -1 placeholder of "
                       'a family with nothing in it (no citer and nothing citing its references) is '
                       'read as NULL. NULL when no family of the cohort has anything in the window '
                       '(the earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which '
                       'made this negative for early cohorts.'),
        'nk_10_mean': ("Mean of nk_10 (documents citing its references but not it) over the cohort's "
                       'families with something in the 10-year window: the -1 placeholder of a family '
                       'with nothing in it (no citer and nothing citing its references) is read as '
                       'NULL. NULL when no family of the cohort has anything in the window (the '
                       'earliest cohorts). Before 2026-10-03 the -1 rows were averaged in, which made '
                       'this negative for early cohorts.'),
        'njfrac_10_mean': ('Mean of the per-family nj_10 / (ni_10 + nj_10 + nk_10), the share of the '
                           '10-year neighbourhood that cites both the family and its references, over '
                           'the families with something in the window (the -1 placeholder is read as '
                           'NULL); NULL when there are none. Before 2026-10-03 the -1 rows entered as '
                           '(-1)/(-3) = 1/3 and pulled the mean toward 0.333.'),
        'CD_all_mean': ("Mean of CD_all (any age) over the cohort's families with a non-NULL CD_all "
                        '(NULLs ignored); NULL if none.'),
        'F_all_mean': ("Mean Foundation share F_all over the cohort's families with at least one citer"
                       ' in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans '
                       '(2025), arXiv:2510.03240.'),
        'E_all_mean': ("Mean Extension share E_all over the cohort's families with at least one citer "
                       'in the window (NULLs ignored); NULL if none. Decomposition of Fang & Evans '
                       '(2025), arXiv:2510.03240.'),
        'G_all_mean': ("Mean Generalization share G_all over the cohort's families with at least one "
                       'citer in the window (NULLs ignored); NULL if none. Decomposition of Fang & '
                       'Evans (2025), arXiv:2510.03240.'),
        'ni_all_mean': ('Mean of ni_all over the n families of the cohort (all have ni/nj/nk_all >= '
                        '0).'),
        'nj_all_mean': ('Mean of nj_all over the n families of the cohort (all have ni/nj/nk_all >= '
                        '0).'),
        'nk_all_mean': ('Mean of nk_all over the n families of the cohort (all have ni/nj/nk_all >= '
                        '0).'),
        'njfrac_all_mean': ('Mean over the n families of nj_all / (ni_all + nj_all + nk_all), the '
                            'share of type-j (co-citing) documents.'),
    },
    'PATSTAT/output_family/patstat_hit_probability.parquet': {
        'docdb_family_id': ('DOCDB simple-family id (tls201.docdb_family_id, integer); every family of'
                            ' patstat_metadata with a non-NULL wipo_sector, cited or not.'),
        'wipo_sector': ('Cohort sector: patstat_metadata.wipo_sector (one of the five WIPO sectors, '
                        'taken from the earliest-filed member with a technology field).'),
        'priority_year': ("Cohort year: the family's earliest priority year (min over its universe "
                          'members of tls201.earliest_filing_year, the filing year where that is '
                          '9999). A few precede 1900 (min 1819) because the 1900 floor applies to '
                          'filing years only.'),
        'pctl_C_3': ('Percentile of C_3 (citation rows within 3 years) within the wipo_sector x '
                     'priority_year cohort: rank() / n with ties at the minimum rank (pandas rank '
                     "method 'min'), ascending, families absent from patstat_citation counted as 0; in"
                     ' (0, 1], higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_examiner_3': ('Percentile of C_examiner_3 (examiner-bucket citation rows within 3 '
                              'years) within the wipo_sector x priority_year cohort: rank() / n with '
                              "ties at the minimum rank (pandas rank method 'min'), ascending, "
                              'families absent from patstat_citation counted as 0; in (0, 1], higher ='
                              ' more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_applicant_3': ('Percentile of C_applicant_3 (applicant-bucket citation rows within 3 '
                               'years) within the wipo_sector x priority_year cohort: rank() / n with '
                               "ties at the minimum rank (pandas rank method 'min'), ascending, "
                               'families absent from patstat_citation counted as 0; in (0, 1], higher '
                               '= more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_other_3': ('Percentile of C_other_3 (other-bucket citation rows within 3 years) within'
                           ' the wipo_sector x priority_year cohort: rank() / n with ties at the '
                           "minimum rank (pandas rank method 'min'), ascending, families absent from "
                           'patstat_citation counted as 0; in (0, 1], higher = more cited, top 1 % <=>'
                           ' >= 0.99 (float32).'),
        'pctl_C_5': ('Percentile of C_5 (citation rows within 5 years) within the wipo_sector x '
                     'priority_year cohort: rank() / n with ties at the minimum rank (pandas rank '
                     "method 'min'), ascending, families absent from patstat_citation counted as 0; in"
                     ' (0, 1], higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_examiner_5': ('Percentile of C_examiner_5 (examiner-bucket citation rows within 5 '
                              'years) within the wipo_sector x priority_year cohort: rank() / n with '
                              "ties at the minimum rank (pandas rank method 'min'), ascending, "
                              'families absent from patstat_citation counted as 0; in (0, 1], higher ='
                              ' more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_applicant_5': ('Percentile of C_applicant_5 (applicant-bucket citation rows within 5 '
                               'years) within the wipo_sector x priority_year cohort: rank() / n with '
                               "ties at the minimum rank (pandas rank method 'min'), ascending, "
                               'families absent from patstat_citation counted as 0; in (0, 1], higher '
                               '= more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_other_5': ('Percentile of C_other_5 (other-bucket citation rows within 5 years) within'
                           ' the wipo_sector x priority_year cohort: rank() / n with ties at the '
                           "minimum rank (pandas rank method 'min'), ascending, families absent from "
                           'patstat_citation counted as 0; in (0, 1], higher = more cited, top 1 % <=>'
                           ' >= 0.99 (float32).'),
        'pctl_C_10': ('Percentile of C_10 (citation rows within 10 years) within the wipo_sector x '
                      'priority_year cohort: rank() / n with ties at the minimum rank (pandas rank '
                      "method 'min'), ascending, families absent from patstat_citation counted as 0; "
                      'in (0, 1], higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_examiner_10': ('Percentile of C_examiner_10 (examiner-bucket citation rows within 10 '
                               'years) within the wipo_sector x priority_year cohort: rank() / n with '
                               "ties at the minimum rank (pandas rank method 'min'), ascending, "
                               'families absent from patstat_citation counted as 0; in (0, 1], higher '
                               '= more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_applicant_10': ('Percentile of C_applicant_10 (applicant-bucket citation rows within '
                                '10 years) within the wipo_sector x priority_year cohort: rank() / n '
                                "with ties at the minimum rank (pandas rank method 'min'), ascending, "
                                'families absent from patstat_citation counted as 0; in (0, 1], higher'
                                ' = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_other_10': ('Percentile of C_other_10 (other-bucket citation rows within 10 years) '
                            'within the wipo_sector x priority_year cohort: rank() / n with ties at '
                            "the minimum rank (pandas rank method 'min'), ascending, families absent "
                            'from patstat_citation counted as 0; in (0, 1], higher = more cited, top 1'
                            ' % <=> >= 0.99 (float32).'),
        'pctl_C_all': ('Percentile of C_all (citation rows at any age) within the wipo_sector x '
                       'priority_year cohort: rank() / n with ties at the minimum rank (pandas rank '
                       "method 'min'), ascending, families absent from patstat_citation counted as 0; "
                       'in (0, 1], higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_examiner_all': ('Percentile of C_examiner_all (examiner-bucket citation rows at any '
                                'age) within the wipo_sector x priority_year cohort: rank() / n with '
                                "ties at the minimum rank (pandas rank method 'min'), ascending, "
                                'families absent from patstat_citation counted as 0; in (0, 1], higher'
                                ' = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_applicant_all': ('Percentile of C_applicant_all (applicant-bucket citation rows at any'
                                 ' age) within the wipo_sector x priority_year cohort: rank() / n with'
                                 " ties at the minimum rank (pandas rank method 'min'), ascending, "
                                 'families absent from patstat_citation counted as 0; in (0, 1], '
                                 'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_C_other_all': ('Percentile of C_other_all (other-bucket citation rows at any age) within'
                             ' the wipo_sector x priority_year cohort: rank() / n with ties at the '
                             "minimum rank (pandas rank method 'min'), ascending, families absent from"
                             ' patstat_citation counted as 0; in (0, 1], higher = more cited, top 1 % '
                             '<=> >= 0.99 (float32).'),
        'pctl_uniqueC_3': ('Percentile of uniqueC_3 (distinct citing DOCDB families within 3 years) '
                           'within the wipo_sector x priority_year cohort: rank() / n with ties at the'
                           " minimum rank (pandas rank method 'min'), ascending, families absent from "
                           'patstat_citation counted as 0; in (0, 1], higher = more cited, top 1 % <=>'
                           ' >= 0.99 (float32).'),
        'pctl_uniqueC_examiner_3': ('Percentile of uniqueC_examiner_3 (distinct citing DOCDB families '
                                    'citing through the examiner bucket within 3 years) within the '
                                    'wipo_sector x priority_year cohort: rank() / n with ties at the '
                                    "minimum rank (pandas rank method 'min'), ascending, families "
                                    'absent from patstat_citation counted as 0; in (0, 1], higher = '
                                    'more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_applicant_3': ('Percentile of uniqueC_applicant_3 (distinct citing DOCDB '
                                     'families citing through the applicant bucket within 3 years) '
                                     'within the wipo_sector x priority_year cohort: rank() / n with '
                                     "ties at the minimum rank (pandas rank method 'min'), ascending, "
                                     'families absent from patstat_citation counted as 0; in (0, 1], '
                                     'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_other_3': ('Percentile of uniqueC_other_3 (distinct citing DOCDB families citing'
                                 ' through the other bucket within 3 years) within the wipo_sector x '
                                 'priority_year cohort: rank() / n with ties at the minimum rank '
                                 "(pandas rank method 'min'), ascending, families absent from "
                                 'patstat_citation counted as 0; in (0, 1], higher = more cited, top 1'
                                 ' % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_5': ('Percentile of uniqueC_5 (distinct citing DOCDB families within 5 years) '
                           'within the wipo_sector x priority_year cohort: rank() / n with ties at the'
                           " minimum rank (pandas rank method 'min'), ascending, families absent from "
                           'patstat_citation counted as 0; in (0, 1], higher = more cited, top 1 % <=>'
                           ' >= 0.99 (float32).'),
        'pctl_uniqueC_examiner_5': ('Percentile of uniqueC_examiner_5 (distinct citing DOCDB families '
                                    'citing through the examiner bucket within 5 years) within the '
                                    'wipo_sector x priority_year cohort: rank() / n with ties at the '
                                    "minimum rank (pandas rank method 'min'), ascending, families "
                                    'absent from patstat_citation counted as 0; in (0, 1], higher = '
                                    'more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_applicant_5': ('Percentile of uniqueC_applicant_5 (distinct citing DOCDB '
                                     'families citing through the applicant bucket within 5 years) '
                                     'within the wipo_sector x priority_year cohort: rank() / n with '
                                     "ties at the minimum rank (pandas rank method 'min'), ascending, "
                                     'families absent from patstat_citation counted as 0; in (0, 1], '
                                     'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_other_5': ('Percentile of uniqueC_other_5 (distinct citing DOCDB families citing'
                                 ' through the other bucket within 5 years) within the wipo_sector x '
                                 'priority_year cohort: rank() / n with ties at the minimum rank '
                                 "(pandas rank method 'min'), ascending, families absent from "
                                 'patstat_citation counted as 0; in (0, 1], higher = more cited, top 1'
                                 ' % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_10': ('Percentile of uniqueC_10 (distinct citing DOCDB families within 10 years)'
                            ' within the wipo_sector x priority_year cohort: rank() / n with ties at '
                            "the minimum rank (pandas rank method 'min'), ascending, families absent "
                            'from patstat_citation counted as 0; in (0, 1], higher = more cited, top 1'
                            ' % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_examiner_10': ('Percentile of uniqueC_examiner_10 (distinct citing DOCDB '
                                     'families citing through the examiner bucket within 10 years) '
                                     'within the wipo_sector x priority_year cohort: rank() / n with '
                                     "ties at the minimum rank (pandas rank method 'min'), ascending, "
                                     'families absent from patstat_citation counted as 0; in (0, 1], '
                                     'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_applicant_10': ('Percentile of uniqueC_applicant_10 (distinct citing DOCDB '
                                      'families citing through the applicant bucket within 10 years) '
                                      'within the wipo_sector x priority_year cohort: rank() / n with '
                                      "ties at the minimum rank (pandas rank method 'min'), ascending,"
                                      ' families absent from patstat_citation counted as 0; in (0, 1],'
                                      ' higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_other_10': ('Percentile of uniqueC_other_10 (distinct citing DOCDB families '
                                  'citing through the other bucket within 10 years) within the '
                                  'wipo_sector x priority_year cohort: rank() / n with ties at the '
                                  "minimum rank (pandas rank method 'min'), ascending, families absent"
                                  ' from patstat_citation counted as 0; in (0, 1], higher = more '
                                  'cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_all': ('Percentile of uniqueC_all (distinct citing DOCDB families at any age) '
                             'within the wipo_sector x priority_year cohort: rank() / n with ties at '
                             "the minimum rank (pandas rank method 'min'), ascending, families absent "
                             'from patstat_citation counted as 0; in (0, 1], higher = more cited, top '
                             '1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_examiner_all': ('Percentile of uniqueC_examiner_all (distinct citing DOCDB '
                                      'families citing through the examiner bucket at any age) within '
                                      'the wipo_sector x priority_year cohort: rank() / n with ties at'
                                      " the minimum rank (pandas rank method 'min'), ascending, "
                                      'families absent from patstat_citation counted as 0; in (0, 1], '
                                      'higher = more cited, top 1 % <=> >= 0.99 (float32).'),
        'pctl_uniqueC_applicant_all': ('Percentile of uniqueC_applicant_all (distinct citing DOCDB '
                                       'families citing through the applicant bucket at any age) '
                                       'within the wipo_sector x priority_year cohort: rank() / n with'
                                       " ties at the minimum rank (pandas rank method 'min'), "
                                       'ascending, families absent from patstat_citation counted as 0;'
                                       ' in (0, 1], higher = more cited, top 1 % <=> >= 0.99 '
                                       '(float32).'),
        'pctl_uniqueC_other_all': ('Percentile of uniqueC_other_all (distinct citing DOCDB families '
                                   'citing through the other bucket at any age) within the wipo_sector'
                                   ' x priority_year cohort: rank() / n with ties at the minimum rank '
                                   "(pandas rank method 'min'), ascending, families absent from "
                                   'patstat_citation counted as 0; in (0, 1], higher = more cited, top'
                                   ' 1 % <=> >= 0.99 (float32).'),
        'pctl_c3': ('Legacy alias, identical to pctl_C_3 (percentile of citation rows C_3, not of '
                    'uniqueC), kept for readers using the PatentView short names.'),
        'pctl_c5': ('Legacy alias, identical to pctl_C_5 (percentile of citation rows C_5, not of '
                    'uniqueC), kept for readers using the PatentView short names.'),
        'pctl_c10': ('Legacy alias, identical to pctl_C_10 (percentile of citation rows C_10, not of '
                     'uniqueC), kept for readers using the PatentView short names.'),
        'pctl_call': ('Legacy alias, identical to pctl_C_all (percentile of citation rows C_all, not '
                      'of uniqueC), kept for readers using the PatentView short names.'),
    },
    'PATSTAT/output_family/patstat_inventor.parquet': {
        'docdb_family_id': ('DOCDB simple-family id (tls201.docdb_family_id, integer); one row per '
                            "family with at least one inventor row in tls207. Read from the family's "
                            'representative member (patstat_metadata.inv_appln_id), not unioned over '
                            'members.'),
        'inventor_list': ("Inventor PATSTAT person_ids as a ';'-joined string in invt_seq_nr order "
                          '(ties by person_id): a named person once at its lowest sequence, an unnamed'
                          ' placeholder record (empty tls206.person_name, e.g. person_id 263) once per'
                          ' slot, so its id can repeat. Person records, not disambiguated inventors; '
                          "identical to patstat_metadata.inventor_list. Read from the family's "
                          'representative member (patstat_metadata.inv_appln_id), not unioned over '
                          'members.'),
        'n_inventors': ('Number of inventor slots = length of inventor_list (distinct named persons '
                        'plus each slot of an unnamed placeholder); team size under its PatentView '
                        'name. Not tls201.nb_inventors.'),
    },
    'PATSTAT/output_family/patstat_inventor_country.parquet': {
        'docdb_family_id': ('DOCDB simple-family id (tls201.docdb_family_id, integer); one row per '
                            'family with at least one inventor row (same rows as patstat_inventor). '
                            'Persons of the representative member inv_appln_id only.'),
        'n_inventors': ('Inventor slots under the once-per-named-person / once-per-placeholder-slot '
                        'rule; identical to patstat_inventor.n_inventors.'),
        'n_located': ('Inventor slots whose person record has a two-letter country code '
                      '(tls206.person_ctry_code matching [A-Z]{2}; malformed codes read as unknown); '
                      '<= n_inventors.'),
        'countries': ("Distinct inventor country codes, sorted alphabetically, ';'-joined (e.g. "
                      "'AU;GB;US'); NULL if no inventor is located. Codes are the address country "
                      "recorded on that application's person record."),
        'n_countries': 'Number of codes in countries; 0 when countries is NULL.',
        'country_inventor_counts': ("Inventors per country as 'CC:n' pairs joined by ';', ordered by "
                                    "count descending then code (e.g. 'GB:4;AU:1;US:1'); counts sum to"
                                    ' n_located; NULL if none located.'),
        'first_inventor_country': ('Country of the lowest-sequence inventor; NULL when that inventor '
                                   'has no country (not replaced by the next located inventor).'),
        'is_international': 'TRUE when n_countries > 1 (inventors in at least two countries).',
        'applicant_countries': ('Distinct two-letter country codes of the applicants (all tls207 rows '
                                "with applt_seq_nr > 0), sorted, ';'-joined; NULL if no applicant is "
                                'located; identical to patstat_metadata.applicant_ctry_list. Persons '
                                'of the representative member inv_appln_id only.'),
    },
    'PATSTAT/output_family/patstat_metadata.parquet': {
        'docdb_family_id': ('DOCDB simple-family id (tls201.docdb_family_id; applications sharing '
                            'exactly the same priorities). One row per family with at least one '
                            'application in the filing-clock universe; the key of every table in this '
                            'set.'),
        'priority_year': ("Family's earliest priority year: min over its universe members of "
                          'tls201.earliest_filing_year (the filing year where that is 9999); the clock'
                          ' year of every metric in this set. Can precede 1900 (min 1819) because the '
                          '1900 floor applies to filing years only.'),
        'filing_year': ('Filing year of the earliest-filed universe member (min '
                        'tls201.appln_filing_year, 1900-2023); used as pctl_year for the CD '
                        'percentiles.'),
        'n_appln': ("Number of the family's applications inside the universe (patents of invention, "
                    'real applications, filed 1900-2023); at most docdb_family_size.'),
        'offices': ('Distinct filing offices (appln_auth, two-letter codes such as EP, US, WO) of the '
                    "universe members, sorted, ';'-joined."),
        'first_appln_id': ('appln_id of the earliest-filed universe member (earliest filing year, then'
                           ' lowest appln_id).'),
        'appln_auth': 'Filing office (two-letter appln_auth) of first_appln_id.',
        'granted': ("TRUE if any universe member carries PATSTAT's granted flag (tls201.granted = 'Y':"
                    ' a first-grant publication or an IP-right-grant legal event).'),
        'n_granted': "Number of universe members with PATSTAT's granted flag.",
        'grant_year': ("Earliest grant year among the universe members (year of a member's first "
                       "publication flagged publn_first_grant = 'Y'); NULL when no member has one, "
                       'which can happen while granted is TRUE (grant known only from a legal event).'),
        'docdb_family_size': ("PATSTAT's size of the DOCDB family (tls201.docdb_family_size; max over "
                              'members of this family-level value), counting all members, including '
                              'those outside this universe.'),
        'nb_citing_docdb_fam': ("PATSTAT's own family-level forward-citation count "
                                '(tls201.nb_citing_docdb_fam, max over members): distinct DOCDB '
                                'families citing any publication or application of the family, taken '
                                'as-is from PATSTAT (no window, universe or provenance filter from '
                                'this pipeline); not the same as C / uniqueC here.'),
        'ipc_main': ("Main IPC symbol (tls209 ipc_position = 'F', whitespace removed, e.g. "
                     "'C07D499/06') of the earliest-filed universe member that has one (filing year, "
                     'then appln_id; chosen per column); NULL if no member has one.'),
        'cpc_code': ('Representative CPC symbol (whitespace removed) of the earliest-filed universe '
                     'member that has one (filing year, then appln_id; chosen per column); per member '
                     'it is the alphabetically first symbol in the IPC-main subclass, else the '
                     'alphabetically first symbol. NULL if no member has CPC.'),
        'techn_field_nr': ('WIPO technology field 1-35 (Schmoch concordance, tls230 field with the '
                           'largest weight, ties to the lowest number) of the earliest-filed universe '
                           'member that has one (filing year, then appln_id; chosen per column); NULL '
                           'if none. Field names in ps_common.WIPO_FIELD.'),
        'wipo_sector': ('WIPO sector of techn_field_nr (same member): Electrical engineering (fields '
                        '1-8), Instruments (9-13), Chemistry (14-24), Mechanical engineering (25-32), '
                        'Other fields (33-35); NULL with techn_field_nr. The hit-probability cohort '
                        'sector.'),
        'inv_appln_id': ('appln_id of the representative member whose persons fill inventor_list, '
                         'applicant_list, both country lists and applicant_sector here and in '
                         'patstat_inventor / patstat_inventor_country: most located inventors, then '
                         'most inventors, then earliest filing year, then lowest appln_id. Never NULL.'),
        'ref_count': ("Number of distinct cited families among this family's rows of the family "
                      'patstat_reference (within-family citations excluded, any age, so later-priority'
                      ' references count too); 0 if none.'),
        'npl_ref_count': ("Distinct non-patent-literature documents (tls212.cited_npl_publn_id <> '0')"
                          ' cited by any publication of any universe member, replenished rows excluded'
                          ' (third-party NPL not removed); 0 if none.'),
        'cpc_subclass_list': ("Union of the members' distinct 4-character CPC subclasses, sorted, "
                              "';'-joined (e.g. 'B60G;F16C'); the atypicality input; NULL if no member"
                              ' has CPC.'),
        'inventor_list': ('Inventor PATSTAT person_ids (tls207 rows with invt_seq_nr > 0) as a '
                          "';'-joined string in invt_seq_nr order (ties by person_id): a named person "
                          'once at its lowest sequence, an unnamed placeholder record (empty '
                          'tls206.person_name) once per slot, so its id can repeat. person_ids are '
                          'per-record, not disambiguated inventors; NULL if no inventor. Taken from '
                          'the representative member inv_appln_id only (person_ids differ between '
                          'offices, so members are not unioned).'),
        'applicant_list': ('Applicant PATSTAT person_ids (tls207 rows with applt_seq_nr > 0), '
                           "';'-joined in applt_seq_nr order with the same once-per-named-person rule;"
                           ' person and company records, not disambiguated; NULL if no applicant. '
                           'Taken from the representative member inv_appln_id only (person_ids differ '
                           'between offices, so members are not unioned).'),
        'inventor_ctry_list': ('Distinct two-letter country codes of the inventors '
                               '(tls206.person_ctry_code of each person record; only [A-Z]{2} codes '
                               "count, malformed ones are read as unknown), sorted, ';'-joined; NULL "
                               'if no inventor has one (common for CN and JP filings). Taken from the '
                               'representative member inv_appln_id only (person_ids differ between '
                               'offices, so members are not unioned).'),
        'applicant_ctry_list': ('Distinct two-letter country codes of the applicants '
                                "(tls206.person_ctry_code, [A-Z]{2} only), sorted, ';'-joined; NULL if"
                                ' none. Taken from the representative member inv_appln_id only '
                                '(person_ids differ between offices, so members are not unioned).'),
        'applicant_sector': ('PATSTAT standardised-name sector (tls206.psn_sector) of the applicant at'
                             ' sequence number 1: COMPANY, INDIVIDUAL, UNIVERSITY, GOV NON-PROFIT, '
                             "HOSPITAL, UNKNOWN or a space-joined combination (e.g. 'GOV NON-PROFIT "
                             "UNIVERSITY'); NULL if missing or blank. Taken from the representative "
                             'member inv_appln_id only (person_ids differ between offices, so members '
                             'are not unioned).'),
    },
    'PATSTAT/output_family/patstat_reference.parquet': {
        'citing_id': 'docdb_family_id of the citing family.',
        'cited_id': ('docdb_family_id of the cited family; never equal to citing_id (citations inside '
                     'a family are dropped).'),
        'citing_year': 'Earliest priority year of the citing family.',
        'cited_year': 'Earliest priority year of the cited family.',
        'age': ('citing_year - cited_year in years; negative for about 1.3 % of rows. Kept here; every'
                ' metric requires age >= 0 (ps.EDGE_WHERE).'),
        'citing_publn_year': ('Earliest publication year among the citing publications of the '
                              'application-level rows collapsed into this row (a publication-based '
                              'alternative clock); 9999 = date unknown in PATSTAT.'),
        'bucket': ("Provenance bucket shared by the collapsed application rows: 'examiner' "
                   "(citn_origin SEA, ISR, SUP, PRS, EXA, FOP, CH2), 'applicant' (APP) or 'other' "
                   '(OPP, APL, blank). A family pair cited under several buckets has one row per '
                   'bucket.'),
        'replenished': ('Always FALSE: replenished application rows are dropped before the family '
                        'edges are built; kept so ps.EDGE_WHERE works unchanged.'),
        'n_appln_edges': ('Number of application-level citation rows (non-replenished rows of '
                          'PATSTAT/output/patstat_reference, any application-level age) collapsed into'
                          ' this (citing family, cited family, bucket) row.'),
    },
    'PATSTAT/output_family/patstat_sb.parquet': {
        'docdb_family_id': ('DOCDB simple-family id (tls201.docdb_family_id, integer); a cited family '
                            'with at least one counted citation (same rows as patstat_citation).'),
        'SB_B': ('Ke et al. (2015) beauty coefficient from the yearly histogram of family citation '
                 'rows (one per citing family and bucket) by age 0 .. last cited age (age >= 0, not '
                 'replenished): sum over t <= t_m of (line from (0, c_0) to the peak (t_m, c_m) minus '
                 'c_t) / max(c_t, 1). 0 when the first maximum is at age 0 (also the value for a '
                 'single-year histogram); can be negative (min about -5); float32.'),
        'SB_T': ("Awakening time: the age t <= t_m (years since the family's priority year) at which "
                 'the histogram lies farthest from the line joining (0, c_0) and the peak; 0 when the '
                 'peak is at age 0.'),
        'n_cite': ('Total family citation rows (one per citing family and bucket) in the histogram, '
                   'i.e. C_all of patstat_citation.'),
    },
    'PATSTAT/output_family/patstat_uniqueC_trend.parquet': {
        'docdb_family_id': ('DOCDB simple-family id (tls201.docdb_family_id, integer); the cited '
                            'family. One row per (family, year) with at least one new citing family.'),
        'priority_year': ("Clock year of the cited family: the family's earliest priority year (min "
                          'over its universe members of tls201.earliest_filing_year, the filing year '
                          'where that is 9999). A few precede 1900 (min 1819) because the 1900 floor '
                          'applies to filing years only.'),
        'cite_year': ('priority_year + yrs_since_priority: the priority year of the citing DOCDB '
                      'families counted in this row.'),
        'yrs_since_priority': ("Lag in years from the cited family's priority year to the citer's (the"
                               " minimum over the pair's edges, which is the only lag because both "
                               'ends have one clock year each); >= 0.'),
        'uniqueC': ('Number of distinct citing DOCDB families whose citation of this family falls at '
                    'this lag. Cumulative sums over lags <= 3/5/10/all reproduce uniqueC_3/5/10/all of'
                    ' patstat_citation, and the column equals patstat_citation_trend.uniqueC row for '
                    'row (both asserted in the notebook).'),
    },
    'PATSTAT/output_family/patstat_z_score.parquet': {
        'docdb_family_id': ('DOCDB simple-family id (tls201.docdb_family_id, integer); a family with '
                            "at least two distinct CPC subclasses (the union of its universe members' "
                            'CPC subclasses).'),
        'Z_median': ("Median over the family's subclass pairs of the pair z-score (Kim et al. (2016) "
                     "hypergeometric z of a CPC-subclass pair in the family's priority year, with "
                     'counts cumulative over all families with >= 2 subclasses up to and including '
                     'that year; z < 0 = atypical pair).'),
        'Z_10pct': ("10th percentile (linear interpolation, DuckDB quantile_cont) of the family's pair"
                    ' z-scores; low values flag atypical combinations.'),
        'Z_min': 'Minimum pair z-score of the family (its most atypical subclass pair).',
        'n_pairs': ('Number of distinct CPC-subclass pairs scored = k(k-1)/2 for k distinct '
                    'subclasses.'),
    },
    'PATSTAT/output_family/z_score_pair.parquet': {
        'code_1': ("First CPC subclass of the pair (4 characters, e.g. 'A01B'); always alphabetically "
                   'lower than code_2.'),
        'code_2': 'Second CPC subclass of the pair (4 characters); alphabetically higher than code_1.',
        'year': ('Year in which at least one family with >= 2 subclasses carries this pair, on this '
                 "set's clock: the family's earliest priority year (min over its universe members of "
                 'tls201.earliest_filing_year, the filing year where that is 9999). A few precede 1900'
                 ' (min 1819) because the 1900 floor applies to filing years only.'),
        'Z_score': ('Hypergeometric z = (o - mu) / sqrt(var) with mu = n_a n_b / N and var = mu (1 - '
                    'n_a / N) (N - n_b) / (N - 1), where N, n_a, n_b and o (co-occurrences) count '
                    'families with >= 2 subclasses cumulatively through this year inclusive; 0 when '
                    'var <= 0. z < 0 = rarer than chance (atypical).'),
    },
    'pcs/output/pcs_citation.parquet': {
        'paper_id': ("OpenAlex work id of the cited paper, 'W' + the integer `oaid` of Reliance on "
                     'Science (pcs_oa_uspto.csv). One row per paper with at least one US-patent '
                     'citation in that file (C_total >= 1); papers never cited by a patent are absent,'
                     ' not zero.'),
        'C_3': ('Number of US patents citing the paper (Reliance on Science rows, any confidence '
                'score, front-page or in-text) whose PatentsView grant year y_q is 0 to 3 years after '
                "the paper's publication year (0 <= y_q - y_P <= 3, same year included), y_P = "
                'OpenAlex publication year. Citing documents without a PatentsView grant year '
                '(pre-grant publications, reissue/design/plant numbers) and papers without a year '
                'contribute 0; equals C_examiner_3 + C_non_examiner_3.'),
        'C_5': ('Number of US patents citing the paper (Reliance on Science rows, any confidence '
                'score, front-page or in-text) whose PatentsView grant year y_q is 0 to 5 years after '
                "the paper's publication year (0 <= y_q - y_P <= 5, same year included), y_P = "
                'OpenAlex publication year. Citing documents without a PatentsView grant year '
                '(pre-grant publications, reissue/design/plant numbers) and papers without a year '
                'contribute 0; equals C_examiner_5 + C_non_examiner_5.'),
        'C_10': ('Number of US patents citing the paper (Reliance on Science rows, any confidence '
                 'score, front-page or in-text) whose PatentsView grant year y_q is 0 to 10 years '
                 "after the paper's publication year (0 <= y_q - y_P <= 10, same year included), y_P ="
                 ' OpenAlex publication year. Citing documents without a PatentsView grant year '
                 '(pre-grant publications, reissue/design/plant numbers) and papers without a year '
                 'contribute 0; equals C_examiner_10 + C_non_examiner_10.'),
        'C_all': ('Number of US patents citing the paper (Reliance on Science rows, any confidence '
                  'score, front-page or in-text) whose PatentsView grant year y_q is at or after the '
                  "paper's publication year (0 <= y_q - y_P, no upper bound), y_P = OpenAlex "
                  'publication year. Citing documents without a PatentsView grant year (pre-grant '
                  'publications, reissue/design/plant numbers) and papers without a year contribute 0;'
                  ' equals C_examiner_all + C_non_examiner_all.'),
        'C_examiner_3': ("Part of C_3 whose Reliance on Science reftype is 'exm' (examiner-added "
                         'reference). Near-empty by construction: only 846 of the 34.8M US rows are '
                         "'exm', so treat it as unusable for analysis."),
        'C_non_examiner_3': ("Part of C_3 whose reftype is anything other than 'exm' (in this file "
                             "always 'app', applicant/other); in practice equal to C_3."),
        'C_examiner_5': ("Part of C_5 whose Reliance on Science reftype is 'exm' (examiner-added "
                         'reference). Near-empty by construction: only 846 of the 34.8M US rows are '
                         "'exm', so treat it as unusable for analysis."),
        'C_non_examiner_5': ("Part of C_5 whose reftype is anything other than 'exm' (in this file "
                             "always 'app', applicant/other); in practice equal to C_5."),
        'C_examiner_10': ("Part of C_10 whose Reliance on Science reftype is 'exm' (examiner-added "
                          'reference). Near-empty by construction: only 846 of the 34.8M US rows are '
                          "'exm', so treat it as unusable for analysis."),
        'C_non_examiner_10': ("Part of C_10 whose reftype is anything other than 'exm' (in this file "
                              "always 'app', applicant/other); in practice equal to C_10."),
        'C_examiner_all': ("Part of C_all whose Reliance on Science reftype is 'exm' (examiner-added "
                           'reference). Near-empty by construction: only 846 of the 34.8M US rows are '
                           "'exm', so treat it as unusable for analysis."),
        'C_non_examiner_all': ("Part of C_all whose reftype is anything other than 'exm' (in this file"
                               " always 'app', applicant/other); in practice equal to C_all."),
        'C_total': ('All Reliance on Science citation rows to the paper with no time window and no '
                    "date requirement: includes patents granted before the paper's publication year, "
                    'pre-grant application publications and other documents not matched to a '
                    'PatentsView grant year, and papers with unknown year. Always >= C_all and >= 1; '
                    'pre-grant publications are counted alongside granted patents, so one invention '
                    'can be counted twice.'),
        'C_examiner_total': ("Part of C_total with reftype 'exm' (examiner), no time window. "
                             'Near-empty (846 rows in the whole file, max 44 per paper).'),
        'C_non_examiner_total': ("Part of C_total with reftype other than 'exm' (applicant 'app'), no "
                                 'time window; in practice equal to C_total.'),
    },
    'pcs/output/pcs_citation_trend.parquet': {
        'paper_id': ("OpenAlex work id of the cited paper ('W' + Reliance on Science oaid). Only "
                     'papers with at least one dated patent citation at a non-negative lag appear '
                     '(4.87M papers).'),
        'pub_year': ('Publication year of the cited paper from the OpenAlex 2026-09-23 release '
                     '(oa_common.load_map, works publication_year); papers with unknown year are '
                     'excluded.'),
        'cite_year': ('Grant year of the citing US patents (year of PatentsView g_patent patent_date),'
                      ' 1976-2025.'),
        'yrs_since_pub': ('cite_year - pub_year in years, always >= 0 (citations from patents granted '
                          "before the paper's publication year are dropped, not clamped)."),
        'pcs': ('Number of US patents granted in cite_year that cite the paper (pcs_examiner + '
                'pcs_non_examiner); stored as float64 but integer-valued, rows exist only where >= 1. '
                'Summing over all rows of a paper reproduces pcs_citation.C_all, and over '
                'yrs_since_pub <= w reproduces C_w.'),
        'pcs_examiner': ("Part of pcs whose Reliance on Science reftype is 'exm' (examiner); float64, "
                         'may print as -0.0. Near-empty (423 citations in the whole table), kept only '
                         'for schema parity with patent_citation_trend.'),
        'pcs_non_examiner': ("Part of pcs whose reftype is not 'exm' (applicant 'app'); float64, in "
                             'practice equal to pcs.'),
    },
    'pcs/output/pcs_hit_probability.parquet': {
        'paper_id': ("OpenAlex work id ('W' + integer). Rows are papers present in "
                     'pcs_citation.parquet (i.e. cited by >= 1 US patent at any date) that also have a'
                     ' field and year in OpenAlex paper_metadata (5.02M); never-patent-cited papers '
                     'are not in the cohorts.'),
        'FoS': ("Cohort field: the OpenAlex topic-hierarchy field (one of 26, e.g. 'Medicine', "
                "'Engineering') of the paper's highest-scoring topic (FoS_rep), else the first field "
                'of FoS_0; taken from OpenAlex paper_metadata at build time (2026-10-08).'),
        'year': ("Cohort year: the paper's publication year from "
                 'OpenAlex/output/paper_metadata.parquet (as of 2026-10-08).'),
        'pctl_c3': ("Percentile of the paper's patent-citation count C_3 (pcs_citation) within its "
                    "(FoS, year) cohort, on a 0-1 scale: pandas rank(method='min', pct=True) = (1 + "
                    'number of cohort papers with a strictly lower C_3) / cohort size, so values lie '
                    'in (0, 1] and ties share the lowest rank. A paper with C_3 = 0 gets 1/cohort '
                    'size, not 0; >= 0.99 reads as top 1 %, but only relative to other patent-cited '
                    'papers.'),
        'pctl_c5': ("Percentile of the paper's patent-citation count C_5 (pcs_citation) within its "
                    "(FoS, year) cohort, on a 0-1 scale: pandas rank(method='min', pct=True) = (1 + "
                    'number of cohort papers with a strictly lower C_5) / cohort size, so values lie '
                    'in (0, 1] and ties share the lowest rank. A paper with C_5 = 0 gets 1/cohort '
                    'size, not 0; >= 0.99 reads as top 1 %, but only relative to other patent-cited '
                    'papers.'),
        'pctl_c10': ("Percentile of the paper's patent-citation count C_10 (pcs_citation) within its "
                     "(FoS, year) cohort, on a 0-1 scale: pandas rank(method='min', pct=True) = (1 + "
                     'number of cohort papers with a strictly lower C_10) / cohort size, so values lie'
                     ' in (0, 1] and ties share the lowest rank. A paper with C_10 = 0 gets 1/cohort '
                     'size, not 0; >= 0.99 reads as top 1 %, but only relative to other patent-cited '
                     'papers.'),
        'pctl_call': ("Percentile of the paper's patent-citation count C_all (pcs_citation) within its"
                      " (FoS, year) cohort, on a 0-1 scale: pandas rank(method='min', pct=True) = (1 +"
                      ' number of cohort papers with a strictly lower C_all) / cohort size, so values '
                      'lie in (0, 1] and ties share the lowest rank. A paper with C_all = 0 gets '
                      '1/cohort size, not 0; >= 0.99 reads as top 1 %, but only relative to other '
                      'patent-cited papers.'),
    },
    'PPP/output/ppp_paper_trend.parquet': {
        'paperid': ("OpenAlex work id ('W' + integer) of the pair's paper; a PPP pairs a paper with "
                    'the US patent judged to embody the same discovery, from '
                    '_patent_paper_pairs_plus.csv (548,315 pairs over 335,917 papers and 309,729 '
                    'patents, ppp_score 1-4; see PPP/ppprev1.pdf). Pairs whose paper is not in the '
                    'OpenAlex citation graph (1.1 % of pairs) or that received no citations are '
                    'absent.'),
        'patent': ("The pair's US patent as written in the pair list: 'US-' + PatentsView patent "
                   "number (e.g. 'US-10000036', reissues 'US-RE…', plant 'US-PP…'). The counts in this"
                   ' table belong to the paper, so they repeat identically for every pair that shares '
                   'the paper.'),
        'pub_year': ("Publication year of the pair's paper from the OpenAlex citation graph cache "
                     '(OpenAlex/cache/paper_csr.npz, works publication_year).'),
        'cite_year': ("Year of the citing documents: the citing work's OpenAlex publication year for "
                      "p2p, and the citing US patent's PatentsView grant year for pat2p_*."),
        'yrs_since_pub': ('cite_year - pub_year in years, >= 0 (rows with a citing year before '
                          'publication are dropped; same-year citations kept).'),
        'p2p': ('Paper->paper citations: number of OpenAlex works (any type, 2026-09-23 release '
                "reference graph) published in cite_year that cite the pair's paper. Rows exist only "
                'for years with >= 1 p2p or pat2p citation, so 0 here means the row exists because of '
                'patent citations.'),
        'pat2p_examiner': ("Patent->paper citations to the pair's paper from US patents granted in "
                           "cite_year whose Reliance on Science reftype is 'exm' (examiner). "
                           'Near-empty (max 2); not usable for analysis.'),
        'pat2p_non_examiner': ("Patent->paper citations to the pair's paper from US patents granted in"
                               " cite_year with any reftype other than 'exm' (applicant 'app'), from "
                               'pcs/pcs_oa_uspto.csv; citing documents without a PatentsView grant '
                               'year are excluded. Built from the same file and year sources as '
                               'pcs_citation_trend.pcs_non_examiner, so per-year values should agree '
                               'for the same paper.'),
    },
    'PPP/output/ppp_patent_trend.parquet': {
        'paperid': ("OpenAlex work id ('W' + integer) of the pair's paper (pair list "
                    '_patent_paper_pairs_plus.csv: 548,315 paper-patent pairs judged to describe the '
                    'same discovery; see PPP/ppprev1.pdf). It only identifies the pair: the counts '
                    'belong to the patent and repeat for every pair sharing that patent.'),
        'patent': ("The pair's US patent: 'US-' + PatentsView patent number (e.g. 'US-10000036', "
                   "'US-RE…'); the cited patent whose forward citations are counted."),
        'grant_year': ("Grant year of the pair's patent (year of PatentsView g_patent patent_date); "
                       '1976-2023 in this table.'),
        'cite_year': 'Grant year of the citing US patents (PatentsView g_patent).',
        'yrs_since_grant': ('cite_year - grant_year in years, >= 0 (same-year citations kept, earlier '
                            'ones dropped). Rows exist only for years with >= 1 counted citation.'),
        'pat2pat_examiner': ('Number of citation records in PatentsView g_us_patent_citation from '
                             "patents granted in cite_year to the pair's patent with citation_category"
                             " 'cited by examiner' (rows counted, not de-duplicated). PatentsView "
                             'records examiner origin only for citing patents granted from 2001 on, so'
                             ' this is essentially 0 for earlier cite years.'),
        'pat2pat_non_examiner': ("Same count for every other citation_category ('cited by applicant', "
                                 "'cited by other', and blank/NULL), with 'cited by third party' "
                                 'excluded. Because citations from patents granted up to 2000 have a '
                                 'blank category, all of them land here; this is not an applicant-only'
                                 ' count.'),
    },
    'Case law/output/case_citation.parquet': {
        'case_id': ('Caselaw Access Project (CAP) integer case id (metadata.csv `id`; values '
                    '1-12,707,012, 5,179,698 cases exist). One row per case, including never-cited '
                    '(C_* = 0) and pre-1800 cases.'),
        'C_3': ('Number of cases citing this case decided 0 to 3 years after it (0 <= y_c - y_P <= 3, '
                'same year included), by decision year of the citing case. The source GML is a simple '
                'directed graph, so this counts distinct citing cases.'),
        'C_5': ('Number of cases citing this case decided 0 to 5 years after it (0 <= y_c - y_P <= 5, '
                'same year included), by decision year of the citing case. The source GML is a simple '
                'directed graph, so this counts distinct citing cases.'),
        'C_10': ('Number of cases citing this case decided 0 to 10 years after it (0 <= y_c - y_P <= '
                 '10, same year included), by decision year of the citing case. The source GML is a '
                 'simple directed graph, so this counts distinct citing cases.'),
        'C_all': ('Number of cases citing this case whose decision year is at or after its own (0 <= '
                  'y_c - y_P, no upper bound). No edge in the graph has a negative lag, so this equals'
                  " the case's in-degree; 0 for 1,391,837 never-cited cases."),
    },
    'Case law/output/case_citation_trend.parquet': {
        'case_id': ('Caselaw Access Project (CAP) integer case id (metadata.csv `id`; values '
                    '1-12,707,012, 5,179,698 cases exist). The cited case; only cases cited at least '
                    'once appear (3,787,861).'),
        'decision_year': ('Decision year of the cited case (same derivation as '
                          'case_metadata.decision_year); no 1800 floor here, so years from 1666 '
                          'appear.'),
        'cite_year': 'Decision year of the citing cases.',
        'yrs_since_decision': 'cite_year - decision_year in years, always >= 0 (asserted).',
        'C': ('Number of cases decided in cite_year that cite the case; >= 1 (sparse table, zero years'
              " are absent). Summing over a case's rows gives case_citation.C_all."),
    },
    'Case law/output/case_disruption.parquet': {
        'case_id': ('Caselaw Access Project (CAP) integer case id (metadata.csv `id`; values '
                    '1-12,707,012, 5,179,698 cases exist). One row per case.'),
        'CD_3': ('CD disruption index (ni - nj) / (ni + nj + nk) over cases decided 0 to 3 years after'
                 ' the focal case (0 <= y - y_F <= 3); -1 consolidating to +1 disruptive. Null when '
                 'the case is never cited at all, or when the window holds neither a citer nor an nk '
                 "case; if the window has no citer but nk > 0 it is exactly 0 (not 'balanced')."),
        'F_3': ('Foundation share (0-1) of the in-window citers c with e_i > e_j, ties e_i = e_j > 0 '
                "counted half; e_j = number of the focal case's references c also cites, e_i = number "
                "of the focal case's in-window citers c also cites. F + E + G = 1; null when the case "
                'has no citer in the window (C_3 = 0). Decomposition of Fang & Evans (2025), '
                'arXiv:2510.03240.'),
        'E_3': ('Extension share (0-1) of the in-window citers with e_j > e_i (cites more of the focal'
                " case's references than of its citers), ties e_i = e_j > 0 counted half; null when "
                'C_3 = 0. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'G_3': ('Generalization share (0-1) of the in-window citers with e_i = e_j = 0 (cites neither '
                "the focal case's references nor its other citers); null when C_3 = 0. Decomposition "
                'of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_3': ('Count (stored as float) of cases decided 0 to 3 years after the focal case (0 <= y -'
                 ' y_F <= 3) that cite the focal case but none of its references. ni + nj equals '
                 'case_citation.C_3; null exactly where CD_3 is null.'),
        'nj_3': ('Count (float) of cases decided 0 to 3 years after the focal case (0 <= y - y_F <= 3)'
                 ' that cite the focal case and at least one of its references; null where CD_3 is '
                 'null.'),
        'nk_3': ('Count (float) of cases decided 0 to 3 years after the focal case (0 <= y - y_F <= 3)'
                 " that cite at least one of the focal case's references but not the focal case; null "
                 'where CD_3 is null.'),
        'CD_5': ('CD disruption index (ni - nj) / (ni + nj + nk) over cases decided 0 to 5 years after'
                 ' the focal case (0 <= y - y_F <= 5); -1 consolidating to +1 disruptive. Null when '
                 'the case is never cited at all, or when the window holds neither a citer nor an nk '
                 "case; if the window has no citer but nk > 0 it is exactly 0 (not 'balanced')."),
        'F_5': ('Foundation share (0-1) of the in-window citers c with e_i > e_j, ties e_i = e_j > 0 '
                "counted half; e_j = number of the focal case's references c also cites, e_i = number "
                "of the focal case's in-window citers c also cites. F + E + G = 1; null when the case "
                'has no citer in the window (C_5 = 0). Decomposition of Fang & Evans (2025), '
                'arXiv:2510.03240.'),
        'E_5': ('Extension share (0-1) of the in-window citers with e_j > e_i (cites more of the focal'
                " case's references than of its citers), ties e_i = e_j > 0 counted half; null when "
                'C_5 = 0. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'G_5': ('Generalization share (0-1) of the in-window citers with e_i = e_j = 0 (cites neither '
                "the focal case's references nor its other citers); null when C_5 = 0. Decomposition "
                'of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_5': ('Count (stored as float) of cases decided 0 to 5 years after the focal case (0 <= y -'
                 ' y_F <= 5) that cite the focal case but none of its references. ni + nj equals '
                 'case_citation.C_5; null exactly where CD_5 is null.'),
        'nj_5': ('Count (float) of cases decided 0 to 5 years after the focal case (0 <= y - y_F <= 5)'
                 ' that cite the focal case and at least one of its references; null where CD_5 is '
                 'null.'),
        'nk_5': ('Count (float) of cases decided 0 to 5 years after the focal case (0 <= y - y_F <= 5)'
                 " that cite at least one of the focal case's references but not the focal case; null "
                 'where CD_5 is null.'),
        'CD_10': ('CD disruption index (ni - nj) / (ni + nj + nk) over cases decided 0 to 10 years '
                  'after the focal case (0 <= y - y_F <= 10); -1 consolidating to +1 disruptive. Null '
                  'when the case is never cited at all, or when the window holds neither a citer nor '
                  "an nk case; if the window has no citer but nk > 0 it is exactly 0 (not 'balanced')."),
        'F_10': ('Foundation share (0-1) of the in-window citers c with e_i > e_j, ties e_i = e_j > 0 '
                 "counted half; e_j = number of the focal case's references c also cites, e_i = number"
                 " of the focal case's in-window citers c also cites. F + E + G = 1; null when the "
                 'case has no citer in the window (C_10 = 0). Decomposition of Fang & Evans (2025), '
                 'arXiv:2510.03240.'),
        'E_10': ('Extension share (0-1) of the in-window citers with e_j > e_i (cites more of the '
                 "focal case's references than of its citers), ties e_i = e_j > 0 counted half; null "
                 'when C_10 = 0. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'G_10': ('Generalization share (0-1) of the in-window citers with e_i = e_j = 0 (cites neither'
                 " the focal case's references nor its other citers); null when C_10 = 0. "
                 'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_10': ('Count (stored as float) of cases decided 0 to 10 years after the focal case (0 <= y'
                  ' - y_F <= 10) that cite the focal case but none of its references. ni + nj equals '
                  'case_citation.C_10; null exactly where CD_10 is null.'),
        'nj_10': ('Count (float) of cases decided 0 to 10 years after the focal case (0 <= y - y_F <= '
                  '10) that cite the focal case and at least one of its references; null where CD_10 '
                  'is null.'),
        'nk_10': ('Count (float) of cases decided 0 to 10 years after the focal case (0 <= y - y_F <= '
                  "10) that cite at least one of the focal case's references but not the focal case; "
                  'null where CD_10 is null.'),
        'CD_all': ('CD disruption index (ni - nj) / (ni + nj + nk) over cases decided at or after the '
                   'focal case (0 <= y - y_F); -1 consolidating to +1 disruptive. Null when the case '
                   'is never cited at all, or when the window holds neither a citer nor an nk case; if'
                   " the window has no citer but nk > 0 it is exactly 0 (not 'balanced')."),
        'F_all': ('Foundation share (0-1) of the in-window citers c with e_i > e_j, ties e_i = e_j > 0'
                  " counted half; e_j = number of the focal case's references c also cites, e_i = "
                  "number of the focal case's in-window citers c also cites. F + E + G = 1; null when "
                  'the case has no citer in the window (C_all = 0). Decomposition of Fang & Evans '
                  '(2025), arXiv:2510.03240.'),
        'E_all': ('Extension share (0-1) of the in-window citers with e_j > e_i (cites more of the '
                  "focal case's references than of its citers), ties e_i = e_j > 0 counted half; null "
                  'when C_all = 0. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'G_all': ('Generalization share (0-1) of the in-window citers with e_i = e_j = 0 (cites '
                  "neither the focal case's references nor its other citers); null when C_all = 0. "
                  'Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_all': ('Count (stored as float) of cases decided at or after the focal case (0 <= y - y_F)'
                   ' that cite the focal case but none of its references. ni + nj equals '
                   'case_citation.C_all; null exactly where CD_all is null.'),
        'nj_all': ('Count (float) of cases decided at or after the focal case (0 <= y - y_F) that cite'
                   ' the focal case and at least one of its references; null where CD_all is null.'),
        'nk_all': ('Count (float) of cases decided at or after the focal case (0 <= y - y_F) that cite'
                   " at least one of the focal case's references but not the focal case; null where "
                   'CD_all is null.'),
    },
    'Case law/output/case_feg_disruption_trend.parquet': {
        'year': ('Decision-year cohort (cases with decision_year >= 1800; 1800-2020, one row per '
                 'year). The snapshot ends in 2020, so late years have windows that have not elapsed '
                 '(right-truncated).'),
        'n': 'Number of cases decided in that year, whether or not their CD is defined.',
        'CD_3_mean': ("Mean of case_disruption.CD_3 (3-year window) over the year's cases where it is "
                      'defined (n_3_defined of them); nulls skipped, not counted as 0.'),
        'F_3_mean': ("Mean Foundation share F_3 over the year's cases with at least one in-window "
                     'citer (F_3 non-null; can be fewer than n_3_defined). Decomposition of Fang & '
                     'Evans (2025), arXiv:2510.03240.'),
        'E_3_mean': ("Mean Extension share E_3 over the year's cases with at least one in-window "
                     'citer. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'G_3_mean': ("Mean Generalization share G_3 over the year's cases with at least one in-window "
                     'citer. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_3_mean': ("Mean ni_3 (in-window citers that cite none of the case's references) over the "
                      "year's cases where CD_3 is defined."),
        'nj_3_mean': ("Mean nj_3 (in-window citers that also cite the case's references) over the "
                      "year's cases where CD_3 is defined."),
        'nk_3_mean': ("Mean nk_3 (in-window cases citing the case's references but not the case) over "
                      "the year's cases where CD_3 is defined."),
        'njfrac_3_mean': ("Mean over the year's cases with ni_3 + nj_3 > 0 of the per-case share nj_3 "
                          '/ (ni_3 + nj_3), i.e. the fraction of in-window citers that also cite the '
                          "case's references (0-1)."),
        'CD_5_mean': ("Mean of case_disruption.CD_5 (5-year window) over the year's cases where it is "
                      'defined (n_5_defined of them); nulls skipped, not counted as 0.'),
        'F_5_mean': ("Mean Foundation share F_5 over the year's cases with at least one in-window "
                     'citer (F_5 non-null; can be fewer than n_5_defined). Decomposition of Fang & '
                     'Evans (2025), arXiv:2510.03240.'),
        'E_5_mean': ("Mean Extension share E_5 over the year's cases with at least one in-window "
                     'citer. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'G_5_mean': ("Mean Generalization share G_5 over the year's cases with at least one in-window "
                     'citer. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_5_mean': ("Mean ni_5 (in-window citers that cite none of the case's references) over the "
                      "year's cases where CD_5 is defined."),
        'nj_5_mean': ("Mean nj_5 (in-window citers that also cite the case's references) over the "
                      "year's cases where CD_5 is defined."),
        'nk_5_mean': ("Mean nk_5 (in-window cases citing the case's references but not the case) over "
                      "the year's cases where CD_5 is defined."),
        'njfrac_5_mean': ("Mean over the year's cases with ni_5 + nj_5 > 0 of the per-case share nj_5 "
                          '/ (ni_5 + nj_5), i.e. the fraction of in-window citers that also cite the '
                          "case's references (0-1)."),
        'CD_10_mean': ("Mean of case_disruption.CD_10 (10-year window) over the year's cases where it "
                       'is defined (n_10_defined of them); nulls skipped, not counted as 0.'),
        'F_10_mean': ("Mean Foundation share F_10 over the year's cases with at least one in-window "
                      'citer (F_10 non-null; can be fewer than n_10_defined). Decomposition of Fang & '
                      'Evans (2025), arXiv:2510.03240.'),
        'E_10_mean': ("Mean Extension share E_10 over the year's cases with at least one in-window "
                      'citer. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'G_10_mean': ("Mean Generalization share G_10 over the year's cases with at least one "
                      'in-window citer. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_10_mean': ("Mean ni_10 (in-window citers that cite none of the case's references) over the"
                       " year's cases where CD_10 is defined."),
        'nj_10_mean': ("Mean nj_10 (in-window citers that also cite the case's references) over the "
                       "year's cases where CD_10 is defined."),
        'nk_10_mean': ("Mean nk_10 (in-window cases citing the case's references but not the case) "
                       "over the year's cases where CD_10 is defined."),
        'njfrac_10_mean': ("Mean over the year's cases with ni_10 + nj_10 > 0 of the per-case share "
                           'nj_10 / (ni_10 + nj_10), i.e. the fraction of in-window citers that also '
                           "cite the case's references (0-1)."),
        'CD_all_mean': ("Mean of case_disruption.CD_all (all-time window) over the year's cases where "
                        'it is defined (n_all_defined of them); nulls skipped, not counted as 0.'),
        'F_all_mean': ("Mean Foundation share F_all over the year's cases with at least one in-window "
                       'citer (F_all non-null; can be fewer than n_all_defined). Decomposition of Fang'
                       ' & Evans (2025), arXiv:2510.03240.'),
        'E_all_mean': ("Mean Extension share E_all over the year's cases with at least one in-window "
                       'citer. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'G_all_mean': ("Mean Generalization share G_all over the year's cases with at least one "
                       'in-window citer. Decomposition of Fang & Evans (2025), arXiv:2510.03240.'),
        'ni_all_mean': ("Mean ni_all (in-window citers that cite none of the case's references) over "
                        "the year's cases where CD_all is defined."),
        'nj_all_mean': ("Mean nj_all (in-window citers that also cite the case's references) over the "
                        "year's cases where CD_all is defined."),
        'nk_all_mean': ("Mean nk_all (in-window cases citing the case's references but not the case) "
                        "over the year's cases where CD_all is defined."),
        'njfrac_all_mean': ("Mean over the year's cases with ni_all + nj_all > 0 of the per-case share"
                            ' nj_all / (ni_all + nj_all), i.e. the fraction of in-window citers that '
                            "also cite the case's references (0-1)."),
        'n_3_defined': ("Number of the year's cases with a non-null CD_3, i.e. the denominator of "
                        'CD_3_mean and of the ni/nj/nk means.'),
        'n_5_defined': ("Number of the year's cases with a non-null CD_5, i.e. the denominator of "
                        'CD_5_mean and of the ni/nj/nk means.'),
        'n_10_defined': ("Number of the year's cases with a non-null CD_10, i.e. the denominator of "
                         'CD_10_mean and of the ni/nj/nk means.'),
        'n_all_defined': ("Number of the year's cases with a non-null CD_all, i.e. the denominator of "
                          'CD_all_mean and of the ni/nj/nk means.'),
    },
    'Case law/output/case_hit_probability.parquet': {
        'case_id': ('Caselaw Access Project (CAP) integer case id (metadata.csv `id`; values '
                    '1-12,707,012, 5,179,698 cases exist). Cases with decision_year >= 1800 and a '
                    'jurisdiction (5,177,903).'),
        'jurisdiction': ("CAP jurisdiction short name (as case_metadata.jurisdiction, e.g. 'U.S.', "
                         "'N.Y.'); first half of the cohort key."),
        'decision_year': 'Decision year of the case (>= 1800 floor); second half of the cohort key.',
        'cohort_n': ("Number of cases in the case's (jurisdiction, decision_year) cohort (1 to "
                     '37,200); filter on it, a percentile from a tiny cohort is weak evidence.'),
        'pctl_C_3': ('Percentile of case_citation.C_3 within the (jurisdiction, decision_year) cohort '
                     'on a 0-1 scale, DuckDB percent_rank = (rank - 1) / (cohort_n - 1) with ties at '
                     'the lowest rank, i.e. the share of other cohort cases with strictly fewer '
                     'citations. Uncited ties sit at 0, a unique maximum is 1, and a single-case '
                     'cohort gives 0; >= 0.99 reads as top 1 %.'),
        'pctl_C_5': ('Percentile of case_citation.C_5 within the (jurisdiction, decision_year) cohort '
                     'on a 0-1 scale, DuckDB percent_rank = (rank - 1) / (cohort_n - 1) with ties at '
                     'the lowest rank, i.e. the share of other cohort cases with strictly fewer '
                     'citations. Uncited ties sit at 0, a unique maximum is 1, and a single-case '
                     'cohort gives 0; >= 0.99 reads as top 1 %.'),
        'pctl_C_10': ('Percentile of case_citation.C_10 within the (jurisdiction, decision_year) '
                      'cohort on a 0-1 scale, DuckDB percent_rank = (rank - 1) / (cohort_n - 1) with '
                      'ties at the lowest rank, i.e. the share of other cohort cases with strictly '
                      'fewer citations. Uncited ties sit at 0, a unique maximum is 1, and a '
                      'single-case cohort gives 0; >= 0.99 reads as top 1 %.'),
        'pctl_C_all': ('Percentile of case_citation.C_all within the (jurisdiction, decision_year) '
                       'cohort on a 0-1 scale, DuckDB percent_rank = (rank - 1) / (cohort_n - 1) with '
                       'ties at the lowest rank, i.e. the share of other cohort cases with strictly '
                       'fewer citations. Uncited ties sit at 0, a unique maximum is 1, and a '
                       'single-case cohort gives 0; >= 0.99 reads as top 1 %.'),
    },
    'Case law/output/case_metadata.parquet': {
        'case_id': ('Caselaw Access Project (CAP) integer case id (metadata.csv `id`; values '
                    '1-12,707,012, 5,179,698 cases exist). One row per case; the join key for every '
                    'Case law table.'),
        'decision_year': ('Decision year: the leading four digits of CAP decision_date_original, kept '
                          'if within 1600-2030, else null; populated for all cases (1666-2020). This '
                          'is the time anchor of every Case law window.'),
        'decision_date': ("Raw CAP decision_date_original string, mostly 'YYYY-MM-DD'; about 7 % are "
                          "not full dates (e.g. '1666-10'), kept so the year derivation is auditable."),
        'jurisdiction': ("CAP jurisdiction short name (jurisdiction__name), 61 values, e.g. 'U.S.' "
                         "(federal), 'Mass.', 'N.Y.'; the cohort key of case_hit_probability."),
        'jurisdiction_id': 'CAP integer id of the jurisdiction (metadata.csv jurisdiction_id).',
        'court': ("CAP court name abbreviation (court__name_abbreviation), e.g. 'Mass. App. Dec.', "
                  "'10th Cir.'; 3,221 courts, 1 null. A jurisdiction's highest court is the one whose "
                  'abbreviation equals the jurisdiction name.'),
        'court_id': 'CAP integer id of the court (metadata.csv court_id).',
        'reporter': ('CAP short name of the reporter series the opinion is published in '
                     "(reporter__short_name), e.g. 'A.2d', 'Mass. App. Dec.'; 413 reporters."),
        'reporter_id': 'CAP integer id of the reporter (metadata.csv reporter_id).',
        'name_abbreviation': ("CAP abbreviated case name (e.g. 'Levenson v. Bertolet'); contains the "
                              'names of the parties, often private individuals.'),
        'ref_count': ('Number of cases in this corpus that the case cites: its out-degree in '
                      'Edge_list.parquet (source cites target), no time window; 0 for 372,314 cases. '
                      'Citations to authorities outside the CAP graph are not counted.'),
    },
    'Case law/output/case_sb.parquet': {
        'case_id': ('Caselaw Access Project (CAP) integer case id (metadata.csv `id`; values '
                    '1-12,707,012, 5,179,698 cases exist). Only cases with at least one dated citation'
                    ' appear (3,787,861).'),
        'SB_B': ('Ke et al. (2015) beauty coefficient B from the yearly citation counts c_t at age t ='
                 ' citing decision year - decision year (t >= 0): sum over t = 0..t_m of the gap '
                 'between the straight line from (0, c_0) to the first peak (t_m, c_m) and c_t, '
                 'divided by max(c_t, 1). Unitless; 0 when the peak is in the decision year, and it '
                 'can be negative.'),
        'SB_T': ('Awakening time in years since decision: the age t in [0, t_m] whose (t, c_t) lies '
                 'farthest from the line joining (0, c_0) and the peak (t_m, c_m); 0 when the peak is '
                 'at age 0.'),
        'n_cite': ('Number of dated citations the curve was built from (all citing cases with lag >= '
                   '0, equal to case_citation.C_all). B is noisy for small n_cite, so filter on it.'),
    },
}

# columns whose values are people's names or name-derived ids: no example on the page
PERSONAL = {
    'PatentView/output/patent_metadata.parquet': {'inventor_list'},
    'Case law/output/case_metadata.parquet': {'name_abbreviation'},
}


def describe(path: str, column: str) -> str | None:
    return TABLES.get(path, {}).get(column) or SHARED.get(column)


def is_personal(path: str, column: str) -> bool:
    return column in PERSONAL.get(path, ())
