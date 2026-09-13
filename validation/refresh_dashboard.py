"""Refresh exported figures and the Parquet inventory without running notebooks.

The page is never rebuilt from scratch: the existing HTML is parsed, every gallery is
re-populated from the saved ``Figures/<notebook>_<section>.jpg`` exports, a gallery whose
family is new gets its section, nav entry, accent colour, raw-data row and KPI card
injected, and the inventory table is regenerated from Parquet footers. Idempotent: a
re-run replaces what it injected rather than adding a second copy.

Only figures written by the validation notebooks (``validation/Figures``) are shown.
Analysis figures drawn elsewhere in the project (Atypicality, Case law/Figures, ...) are
deliberately not part of this page.
"""
from pathlib import Path
from datetime import datetime
import argparse, hashlib, json, re, shutil
from bs4 import BeautifulSoup
from PIL import Image
from dashboard_inventory import build_inventory

VAL = Path(__file__).resolve().parent
DASH = VAL / 'metrics_dashboard.html'

# One entry per gallery, in page order. `prefix` is the stem val_common.save() writes;
# `pipeline` marks the metric pipelines (they get a bar in the header pipebar and are
# counted in the lede), as opposed to a cross-check that reads several families at once.
FAMILIES = [
 dict(key='paper', prefix='paper_validation', accent=1, title='Papers', chip='OpenAlex', nav='Papers', pipeline=True),
 dict(key='dimension', prefix='dimension_validation', accent=6, title='Papers — Dimensions', chip='Dimensions', nav='Papers (Dimensions)', pipeline=True,
  intro=('The OpenAlex paper pipeline re-run, kernel for kernel, on the Dimensions June 2025 index: 153.8 M publications and 2.14 B reference edges. '
         'Fields are ANZSRC FoR 2020 divisions, a journal is source_titles.type = "journal", and the patent→paper channel is Dimensions\' own patent index rather than Reliance on Science, '
         'so a difference from the OpenAlex figures is a property of the index, not of the metric. Section numbers follow case_law_validation so the families read side by side; '
         'a section whose Dimensions input has not been written yet is absent rather than empty.')),
 dict(key='patent', prefix='patent_validation', accent=2, title='Patents', chip='PatentsView', nav='Patents', pipeline=True),
 dict(key='pcs', prefix='pcs_validation', accent=3, title='Patent → paper', chip='Reliance on Science', nav='Patent→paper', pipeline=True),
 dict(key='ppp', prefix='ppp_validation', accent=4, title='Paper–patent pairs', chip='PPP', nav='Patent Paper Pair', pipeline=True),
 dict(key='caselaw', prefix='case_law_validation', accent=5, title='Case law', chip='CASE', nav='Case law', pipeline=True),
 dict(key='authorcountry', prefix='author_country_validation', accent=8, title='Author countries', chip='OpenAlex', nav='Author countries', pipeline=False,
  intro=('Where the authors of 251.7 M OpenAlex works sit: ISO2 countries from the institution each affiliation resolved to, one row per work in paper_author_country.parquet. '
         '44.6% of works have at least one located author. Coverage, country shares under full and fractional counting, international collaboration by team size, '
         'its relation to impact and disruption, partner pairs, country profiles, and a cross-check against the Dimensions author countries.')),
 dict(key='inventorcountry', prefix='inventor_country_validation', accent=9, title='Inventor countries', chip='PatentsView', nav='Inventor countries', pipeline=False,
  intro=('Where the inventors of 8.5 M US utility patents sit: the country of the address printed on the grant, one row per patent in patent_inventor_country.parquet, with the assignee countries beside it. '
         '99.3% of patents are located. The same sections as the author-country gallery, plus inventor-vs-assignee country and the CPC-section mix of each country, and a side-by-side with the paper table.')),
 dict(key='crosscheck', prefix='disruption_crosscheck', accent=7, title='Cross-checks', chip='all families', nav='Cross-checks', pipeline=False,
  intro=('An independent transcription of the CD<sub>5</sub> reference algorithm, scored against this pipeline\'s stored disruption values on the identical cached graphs '
         'for papers (OpenAlex) and patents (PatentsView). The reference drops the focal document from the n<sub>k</sub> set, so the prediction is '
         'n<sub>k</sub><sup>ref</sup> = n<sub>k</sub><sup>ours</sup> + 1; the figure reports how often the counting terms agree exactly and how close CD is under both variants.')),
]
ACCENTS = {6: '#b7791f', 7: '#6b7280', 8: '#0f766e', 9: '#7c3aed'}     # --p1..--p5 already live in the page

# section -> (title, what the figure tests). Existing cards keep the caption written into the
# page unless their section is listed here; a card created by this script needs an entry or it
# is titled "Section <n>".
CAPTIONS = {
 'paper': {
  '2': ('Team size → disruption percentile & impact', 'Native team size from distinct author IDs in paper_author.parquet; disruption percentile and citation impact by team size.'),
  '3': ('Atypicality 2×2 — hit-paper probability', 'Corrected merged atypicality scores, 1980–2020; journal-only mapping. Conventionality and tail novelty are evaluated within publication-year cohorts.'),
  '3b': ('Atypicality 2×2 — SciSciNet scores', 'The same 2×2 on SciSciNet\'s own Atyp_Median_Z × Atyp_10pct_Z, high/low relative to the paper\'s own publication-year median. External comparison only; SciSciNet is not an input to the derived metrics.'),
  '4': ('Atypicality Z-score CDF', 'CDF of median and 10th-percentile Z from the corrected merged 1980–2020 run.'),
  '6c': ('Citation trajectories by field — hit top 1%', 'Mean cumulative citation curves by FoS level-0 field.'),
  '6d': ('Citation trajectories — all eligible papers', 'Corpus-wide trajectories with the citation-count and observation-span filters required by the metric.'),
  '6e': ('Trajectories by field — hit top 1% vs all papers', 'Compare selected high-impact papers with all eligible papers in each field.'),
  '8': ('Disruption over publication years', 'Mean CD by window, indexed trends, and field-level comparisons with closed citation windows.'),
  '9a': ('Earlier 2000–2005 run — atypicality coverage', 'Historical restricted run, before the journal-mapping fix; separate from the merged scores in §3–4.'),
  '9b1': ('Earlier 2000–2005 run — Z-score distributions', 'Historical restricted-run median, 10th-percentile and minimum Z distributions.'),
  '9b2': ('Earlier 2000–2005 run — Z-score CDF', 'Historical restricted-run cumulative distributions; do not pool with the corrected merged run.'),
  '9c': ('Earlier 2000–2005 run — hit-paper probability', 'Historical restricted-run conventionality and novelty split within publication-year cohorts.'),
  '9d': ('Earlier 2000–2005 run — SciSciNet agreement', 'Historical restricted-run atypicality comparison; the latest merged-run comparison is in §3c.'),
 },
 'dimension': {
  '1': ('Coverage by metric', 'How many of the 153.8 M publications have each metric defined.'),
  '2': ('The corpus in time', 'Publications per year with the document-type mix (article, chapter, proceeding, preprint, monograph, book) and doc_class for articles; 1900–2025, half the corpus published after 2012.'),
  '3': ('Forward citations & windowed monotonicity', 'C<sub>3</sub> ≤ C<sub>5</sub> ≤ C<sub>10</sub> ≤ C<sub>all</sub> asserted on every publication (0 violations); C<sub>all</sub> against Dimensions\' own times_cited, which counts the whole index at export.'),
  '4': ('Mean citations by publication year', 'Each window drawn solid only up to snapshot − w; C<sub>all</sub> has no closing year and is the series most damaged by right truncation.'),
  '5': ('Citation age profile', 'When a publication is cited, overall and by publication era, from the full yearly history; the third panel is the patent→paper channel from Dimensions\' own patent index.'),
  '6': ('Disruption — distribution, trend, composition', 'CD in [−1, 1]; the spikes at 0 and ±1 are one-citer arithmetic, so the distribution is repeated for ≥ 10 citers. n<sub>i</sub> / n<sub>j</sub> / n<sub>k</sub> composition by publication year.'),
  '7': ('F / E / G decomposition', 'Foundation / Extension / Generalization in the five-year window; F + E + G = 1 asserted, then the three shares by publication year.'),
  '8': ('Hit percentile', 'Percentile within (FoR division, year) with ties at the lowest rank; the block at 0 is the never-cited share.'),
  '9': ('Metric means by FoR division', 'ANZSRC FoR 2020 divisions with at least 20,000 publications: citations, disruption and hit rate by field.'),
  '10': ('Cross-metric correlations', 'Spearman on a 500k sample: C<sub>all</sub> vs times_cited +0.999, C<sub>all</sub> vs hit percentile +0.924, team size vs C<sub>all</sub> +0.311.'),
  '11': ('Sleeping beauties', 'B and awakening time T for publications with n_cite ≥ 50; high-B publications should awaken well after year 0.'),
  '12': ('Atypicality — Z-score CDF and 2×2', 'Uzzi journal-pair Z on the Dimensions journal flag; requires the merged paper_z_score, of which only the 1990–2000 partition exists so far.'),
  '13': ('Authors — team size, resolved authors, countries', 'team_size counts every author slot (mean 3.49), 77.1% of slots resolve to a researcher id, 60.7% of publications have a located author; team size against disruption and impact (Wu et al.).'),
  '14': ('Dimensions against OpenAlex', 'The same kernels on two indices, side by side: corpus per year, forward-citation distribution, never-cited share, CD distribution and beauty coefficient. Differences are properties of the indices (coverage, reference completeness, typing), not of the metrics.'),
 },
 'patent': {
  '15a': ('Trajectories by CPC — hit top 1%', 'Granted-only and extended citation networks compared within each CPC section.'),
  '15b': ('Trajectories — all eligible patents', 'Corpus-wide cumulative curves on the granted-only and extended networks.'),
  '15c': ('Trajectories by CPC — all eligible patents', 'Granted-only and extended curves by technology section, with the same eligibility filters.'),
  '20': ('Disruption over grant years', 'Windowed mean CD, indexed trends and CPC comparisons; account for left and right truncation.'),
  '21': ('Extended network — disruption coverage and distributions', 'Granted citations plus mapped application citations; compare CD coverage and distributions.'),
  '22': ('Extended network — CD and F/E/G over time', 'Granted-only versus extended CD, counting terms and five-year F/E/G shares by grant year.'),
  '23': ('Extended network — CPC differences and paired shifts', 'Compare five-year CD by CPC section and its per-patent change across networks.'),
  '24a': ('Extended network — disruption decline', 'Repeat the grant-year decline analysis using granted and application citations.'),
  '24b': ('Disruption decline — granted vs extended', 'Compare the grant-year trends across the two citation networks.'),
  '25a': ('Extended network — yearly trends and convexity', 'Scaled yearly metric trends and their convexity over the notebook analysis window.'),
  '25b': ('Extended network — trend convexity by CPC', 'Compare yearly-trend convexity across CPC sections.'),
  '26': ('Extended network — team size and disruption', 'Inventor count versus disruption percentile recomputed on the extended citation network.'),
 },
 'authorcountry': {
  '1': ('Coverage by year and team size', 'Share of works with ≥ 1 located author and share of author slots located, by publication year; located share by team size (1990+).'),
  '2': ('Country composition over time', 'Top-12 countries\' share of located works by year under full counting; full vs fractional share 2010–2020, the gap being each country\'s internationalisation.'),
  '3': ('International collaboration', 'Share of located multi-author works spanning ≥ 2 countries, overall and by team-size band; distribution of the number of countries, 2010–2020.'),
  '4': ('Internationality vs impact and disruption', 'Mean within-(field, year) citation percentile, top-10% share and mean CD<sub>5</sub> by number of countries, within team-size bands, 1990–2015.'),
  '5': ('Country pairs', 'Row-normalised co-authorship between the 15 most international countries, 2015–2020: the share of A\'s international works that involve B.'),
  '6': ('Country profiles', 'Top-30 producers 2000–2015: international share against mean citation percentile and against mean CD<sub>5</sub>; marker area ∝ works.'),
  '7': ('Cross-check against Dimensions', 'Located share by year and top-15 country shares 2010–2020 from the Dimensions author countries beside the OpenAlex ones; agreement is on ranking and trend, not on coverage level.'),
  '8': ('First and last author', 'Share of multi-author works whose first and last author share a country, by year; the most common cross-country first→last pairs 2015–2020.'),
  '9': ('World map — output, openness, impact, change', 'Robinson choropleths: share of world output 2015–2020 on a log scale (fractional counting), international collaboration rate, mean citation percentile 1990–2015, and the log₂ change in share since 2000–2005. Grey is "no value", not zero; panels 3 and 4 carry volume floors.'),
  '10': ('World map — collaboration flows', 'The 70 largest country pairs of 2015–2020 as great-circle arcs, width ∝ √(joint papers). The same data as §5, with distance restored.'),
 },
 'inventorcountry': {
  '1': ('Coverage by grant year', 'Share of patents with a located inventor, of located inventor slots and of patents with a located assignee, by grant year; team-size distribution for located vs unlocated patents.'),
  '2': ('Country composition and inventor vs assignee', 'Top-10 inventor countries\' share of located patents by grant year; full vs fractional share 2010–2020; share of patents whose first inventor\'s country is among the assignee countries.'),
  '3': ('International co-invention', 'Share of located multi-inventor patents spanning ≥ 2 countries, overall and by team-size band; number-of-countries distribution, 2010–2020.'),
  '4': ('Internationality vs impact and disruption', 'Mean within-(sector, grant year) citation percentile, top-10% share and mean CD<sub>5</sub> by number of inventor countries, within team-size bands, 1990–2015.'),
  '5': ('Country pairs', 'Row-normalised co-invention between the 15 most international countries, 2010–2020.'),
  '6': ('Country profiles and CPC mix', 'Top-25 inventor countries 2000–2015: international share against impact and disruption; CPC-section mix of the ten largest.'),
  '7': ('Papers against patents', 'Coverage, international share and countries-per-document for the OpenAlex author table and the PatentsView inventor table, side by side.'),
  '8': ('World map — output, openness, impact, change', 'The same four Robinson choropleths as the author gallery, on patents: share of world patenting 2015–2020 (log, fractional counting), international co-invention rate, mean citation percentile 1990–2015, and the log₂ change in share since 2000–2005.'),
  '9': ('World map — co-invention flows', 'The 70 largest inventor-country pairs of 2010–2020 as great-circle arcs. Nearly every heavy arc lands in the United States: this is the US patent record.'),
 },
 'crosscheck': {
  '1': ('CD<sub>5</sub> cross-check — reference algorithm vs this pipeline', 'Sampled papers and patents scored by an independent transcription of the CD index on the same cached graphs; exact agreement of n<sub>i</sub> / n<sub>j</sub> / n<sub>k</sub>, the predicted n<sub>k</sub> + 1 offset, and CD closeness under both focal-handling variants.'),
 },
}
# Saved exports whose producing cell no longer exists in the notebook. They stay on disk as a
# record but are not shown: a figure nobody can regenerate is not evidence.
ORPHANS = {
 'paper': {'2b': 'superseded 2026-09-06 by §2 (native team size from paper_author.parquet); the current notebook has no §2b'},
}
FAMILY_DESC = {'paper': 'Foundation / Extension / Generalization shares in the five-year citation window; shares sum to one.'}

def human_size(size):
 for unit, divisor in [('GB', 10**9), ('MB', 10**6), ('KB', 10**3)]:
  if size >= divisor:
   return f'{size / divisor:,.2f} {unit}'
 return f'{size:,} B'


def ensure_family_scaffold(soup, fam, previous):
 """Create the section, nav entry and accent CSS of a gallery family that is not in the page yet."""
 a = fam['accent']
 style = soup.style
 css = style.string
 # accent colour variable, once, after --p5 (light theme only, like --p5 itself)
 if a in ACCENTS and f'--p{a}:' not in css:
  css = css.replace('  --p5:#e34948;', f'  --p5:#e34948;\n  --p{a}:{ACCENTS[a]};', 1)
 style.string = css
 section = soup.find(id=f'val-{fam["key"]}')
 if section is None:
  section = BeautifulSoup(
   f'<section class="valsec" id="val-{fam["key"]}">\n<div class="shead sub"><span class="rule p{a}"></span><h2>{fam["title"]}</h2>\n'
   f'<span class="chip p{a}">{fam["chip"]}</span>\n<span class="meta"></span></div>\n'
   f'<p class="intro">{fam.get("intro", "")}</p>\n<div class="gallery"></div>\n</section>', 'html.parser').section
  anchor = soup.find(id=f'val-{previous["key"]}') if previous else None
  if anchor is not None:
   anchor.insert_after('\n'); anchor.insert_after(section)
  else:
   gaps = soup.find(id='gaps'); gaps.insert_before(section); gaps.insert_before('\n')
 nav = soup.select_one('.subnav')
 if nav.select_one(f'a[href="#val-{fam["key"]}"]') is None:
  li = BeautifulSoup(f'<li><a href="#val-{fam["key"]}"><span class="dot p{a}"></span>{fam["nav"]}</a></li>', 'html.parser').li
  prev_li = nav.select_one(f'a[href="#val-{previous["key"]}"]') if previous else None
  if prev_li is not None:
   prev_li.parent.insert_after(li); prev_li.parent.insert_after('\n')
  else:
   nav.append(li); nav.append('\n')
 return section


def refresh_accent_css(soup):
 """One delimited block with the colour rules of every accent this script owns; regenerated per run."""
 style = soup.style
 css = re.sub(r'\n/\* families-inject \*/.*?/\* /families-inject \*/', '', style.string, flags=re.S)
 rules = ['\n/* families-inject */']
 for a in sorted(ACCENTS):
  rules += [f'.dot.p{a} {{ background:var(--p{a}); }}',
            f'.chip.p{a} {{ color:var(--p{a}); background:color-mix(in srgb, var(--p{a}) 12%, transparent); }}',
            f'.shead .rule.p{a} {{ background:var(--p{a}); }}',
            f'.cardhead .sec.p{a} {{ color:var(--p{a}); }}']
 pipelines = [f for f in FAMILIES if f['pipeline']]
 for n, fam in enumerate(pipelines, 1):
  rules.append(f'.pipebar i:nth-child({n}) {{ background:var(--p{fam["accent"]}); }}')
 rules.append('/* /families-inject */')
 style.string = css + '\n'.join(rules)
 pipebar = soup.select_one('.pipebar')
 pipebar.clear()
 for _ in pipelines:
  pipebar.append(soup.new_tag('i'))


def update_inventory_page(soup, inventory):
 files = inventory['files']
 by_path = {item['path']: item for item in files}
 rows = sum(item['rows'] for item in files)
 size = sum(item['bytes'] for item in files)
 ppp = inventory['ppp_provenance']
 ppp_verified = ppp['status'] == 'run_log_matches_current_output_counts'
 checked = datetime.fromisoformat(inventory['generated_utc'].replace('Z', '+00:00')).strftime('%d %b %Y').lstrip('0')
 n_pipelines = sum(f['pipeline'] for f in FAMILIES)
 soup.select_one('.railfoot').string = f'Inventory checked {checked} (UTC). Figures from saved validation exports.'
 eyebrow = soup.select_one('.eyebrow')
 eyebrow.contents[0].replace_with('Pipeline reference · OpenAlex 2026-01-16 · Dimensions June 2025 ')
 soup.select_one('.band .lede').string = (f'{["Four","Five","Six","Seven"][n_pipelines-4]} research pipelines cover papers on two bibliographic indices (OpenAlex and Dimensions), patents, patent-to-paper citations, paper–patent pairs and court opinions. Explore their inputs, derived tables, metric definitions and validation figures. Coverage and computation choices are stated alongside the results.')
 kpis = soup.select('.kpi')
 for kpi, value, label, subtitle in [
  (kpis[0], f'{rows / 10**9:.2f} B', 'stored rows', f'across {len(files)} derived tables'),
  (kpis[1], human_size(size), 'derived Parquet', 'canonical outputs · decimal GB'),
 ]:
  kpi.select_one('.v').string = value
  kpi.select_one('.k').string = label
  kpi.select_one('.sub').string = subtitle
 # a KPI card for the Dimensions corpus, after the OpenAlex papers card
 if soup.select_one('.kpi[data-inject="dimension"]') is None:
  papers = next(k for k in kpis if k.select_one('.k').get_text() == 'papers')
  card = BeautifulSoup('<div class="kpi" data-inject="dimension"><div class="v"></div><div class="k">Dimensions publications</div><div class="sub"></div></div>', 'html.parser').div
  papers.insert_after(card); papers.insert_after('\n')
 for kpi in soup.select('.kpi'):
  label = kpi.select_one('.k').get_text()
  metadata_path = {'papers':'OpenAlex/output/paper_metadata.parquet', 'Dimensions publications':'Dimensions/output/paper_metadata.parquet',
                   'patents':'PatentView/output/patent_metadata.parquet', 'court opinions':'Case law/output/case_metadata.parquet'}.get(label)
  if metadata_path:
   kpi.select_one('.v').string = f'{by_path[metadata_path]["rows"] / 10**6:.2f} M'
  if label == 'papers':
   count = by_path['OpenAlex/output/paper_citation.parquet']['rows']
   kpi.select_one('.sub').string = f'{count / 10**6:.2f} M citation-table rows'
  elif label == 'Dimensions publications':
   count = by_path['Dimensions/output/paper_citation.parquet']['rows']
   kpi.select_one('.sub').string = f'{count / 10**6:.2f} M citation-table rows · June 2025'
  elif label == 'patent→paper links':
   count = by_path['pcs/output/pcs_citation.parquet']['rows']
   kpi.select_one('.sub').string = f'{count / 10**6:.2f} M cited papers'
  elif label == 'court opinions':
   kpi.select_one('.sub').string = '47.5 M citations · 1666–2020'
 soup.select_one('#raw > .intro').string = (f'These source collections supply the {["four","five","six","seven"][n_pipelines-4]} pipelines. Authorship records provide native paper team sizes. SciSciNet is used for external validation only; it is not an input to the derived metrics. Source scales describe the available snapshots and need not equal the eligible sample in a figure.')
 raw_rows = soup.select('#raw tbody tr')
 if soup.select_one('#raw tr[data-inject="dimension"]') is None:
  after = next(r for r in raw_rows if 'OpenAlex author' in r.get_text())
  row = BeautifulSoup(
   '<tr data-inject="dimension">\n<td><span class="dot p6"></span><b>Dimensions June 2025 dump</b><br/><code class="path">jevans/dimensions/dimensions_june_2025</code></td>\n'
   '<td class="num nowrap">155.5M publications · 2.14B reference edges</td>\n<td><span class="flag info">read-only</span></td>\n'
   '<td class="note">Digital Science BigQuery export: <code>publications</code> (one nested row per publication with references, authors and affiliations, ANZSRC FoR 2020 categories, source), '
   '<code>source_titles</code> and <code>patents</code>. Supplies the Dimensions paper citation graph, metadata, author lists and patent→paper channel.</td></tr>', 'html.parser').tr
  after.insert_after(row); after.insert_after('\n')
 for row in soup.select('#raw tbody tr'):
  cells = row.find_all('td', recursive=False)
  text = cells[0].get_text(' ', strip=True)
  if 'OpenAlex author' in text:
   cells[3].string = 'One row per (work, author, affiliation). Distinct author IDs are aggregated into paper_author.parquet, the native source of team size in the current validation.'
  elif 'SciSciNet (comparison only)' in text:
   cells[3].string = 'External comparison only: metric-specific agreement in paper figure §3c and the SciSciNet-score 2×2 in §3b. The current team-size figure uses native OpenAlex author IDs. Earlier restricted-run atypicality comparisons are identified separately in §9d.'
  elif 'Patent–paper pair list' in text:
   cells[0].select_one('code').string = ppp.get('source', 'PPP/ppp_common.py')
   cells[1].string = f'{ppp["pairs"]:,} pairs' if ppp_verified else 'Unverified source cohort'
   if ppp_verified:
    cells[3].string = (f'{ppp["distinct_papers"]:,} distinct papers · {ppp["distinct_patents"]:,} distinct patents. The current trend outputs use the {ppp["source_option"]} list, verified against the completed production log and Parquet row counts. Pair-list selection is configurable and must accompany comparisons across runs.')
   else:
    cells[3].string = 'No producing run log matches the current trend output counts. Confirm the source list before interpreting this cohort; configuration alone does not prove output provenance.'
  elif 'OpenAlex snapshot' in text:
   cells[3].string = 'Works, references, locations, topics, concepts and IDs: 14 datasets under works/. This snapshot supplies the paper citation graph and metadata.'
 outputs = soup.find(id='outputs')
 outputs.select_one('.shead .meta').string = f'{len(files)} Parquet files · {checked} UTC'
 intro = outputs.select_one('.intro')
 intro.clear()
 intro.append('Counts come from current Parquet footers; sizes come from the filesystem. Rows have different meanings across tables and must not be summed as unique documents. The inventory includes the legacy team-size table and the Dimensions 1990–2000 atypicality partition (the only one written so far), but excludes backups, dated OpenAlex score partitions already represented by merged files, and sharded reference intermediates. ')
 link = soup.new_tag('a', href='https://github.com/Dawoon-Jeong0523/SciSci#refresh-from-saved-research-outputs')
 link.string = 'How this inventory is refreshed.'
 intro.append(link)
 table = outputs.select_one('table')
 table.thead.clear()
 head = soup.new_tag('tr')
 for label in ['Table / location', 'Rows', 'Size', 'Row meaning / columns']:
  th = soup.new_tag('th', scope='col'); th.string = label; head.append(th)
 table.thead.append(head)
 table.tbody.clear()
 colors = {f['key']: f['accent'] for f in FAMILIES}
 for item in files:
  tr = soup.new_tag('tr', attrs={'data-pipe':item['family'], 'data-path':item['path']})
  td = soup.new_tag('td')
  dot = soup.new_tag('span', attrs={'class':f'dot p{colors[item["family"]]}'})
  td.append(dot)
  code = soup.new_tag('code'); code.string = Path(item['path']).name; td.append(code)
  td.append(soup.new_tag('br'))
  location = soup.new_tag('span', attrs={'class':'path'})
  location.string = str(Path(item['path']).parent); td.append(location); tr.append(td)
  for value in [f'{item["rows"]:,}', human_size(item['bytes'])]:
   td = soup.new_tag('td', attrs={'class':'num'}); td.string = value; tr.append(td)
  td = soup.new_tag('td', attrs={'class':'cols'})
  td.append(item['grain'])
  notes = item.get('notes', [])
  if isinstance(notes, str): notes = [notes]
  if item.get('note'): notes = [*notes, item['note']]
  for note in notes:
   p = soup.new_tag('p'); p.string = note; td.append(p)
  details = soup.new_tag('details')
  summary = soup.new_tag('summary'); summary.string = f'{len(item["columns"])} columns'; details.append(summary)
  column_text = soup.new_tag('span'); column_text.string = ', '.join(item['columns']); details.append(column_text)
  td.append(details); tr.append(td); table.tbody.append(tr)
 soup.select_one('#val-ppp > .intro').string = ('The 548,315-pair plus list links scientific and technological contributions. These validation figures join the document-level paper and patent citation histories, then apply figure-specific eligibility filters; the average cumulative trajectory in §5b covers 107,260 pairs. The separately inventoried PPP trend files are pair-level outputs. The hypothesis under test is that the paper side is convex and the patent side concave.')
 for article in soup.select('#gaps article'):
  if 'pair list' in article.h3.get_text():
   article.p.string = 'The saved validation figures use the 548,315-pair plus list; the adjusted list contains 42,967 pairs. Pair choice and eligibility filters determine the analysis sample. The Raw data section reports separately verified provenance for the current stored trend outputs. Record both when comparing results or rerunning the pipeline.'
 # a gap card for the Dimensions atypicality coverage, once
 gaps = soup.select_one('#gaps .gaps')
 if soup.select_one('#gaps article[data-inject="dimension"]') is None:
  card = BeautifulSoup(
   '<article class="gap warn" data-inject="dimension">\n<div class="gaphead"><span class="flag warn">coverage</span>\n<span class="chip p6">Papers — Dimensions</span></div>\n'
   '<h3>Dimensions atypicality exists for 1990–2000 only</h3><p></p></article>', 'html.parser').article
  gaps.append(card); gaps.append('\n')
 soup.select_one('#gaps article[data-inject="dimension"] p').string = ('The Dimensions chain has written paper_z_score_1990_2000.parquet and its pair table, not a merged corpus-wide file, so dimension_validation §12 (Z-score CDF and the Uzzi 2×2) is not drawn yet and the Dimensions-vs-OpenAlex comparison in §14 excludes atypicality. Every other Dimensions metric is corpus-wide.')
 soup.select_one('footer p').string = (f'Inventory checked {checked} (UTC) across OpenAlex, Dimensions, PatentView, pcs, PPP and Case law. Row counts and schemas come from Parquet footers; file sizes and modification times come from filesystem metadata. Figures are saved exports from {len(FAMILIES)} validation notebooks. Refreshing this page does not recompute metrics or rerun those notebooks. The inventory snapshot and each figure’s analysis coverage are distinct; earlier atypicality exports remain explicitly labelled.')
 style = soup.style
 css = style.string
 for minimum in [158, 300, 320, 370]:
  css = css.replace(f'minmax({minimum}px,1fr)', f'minmax(min(100%,{minimum}px),1fr)')
 if '/* responsive inventory */' not in css:
  css += '\n/* responsive inventory */\n.card, .metric, .gap { min-width:0; overflow-wrap:anywhere; }\n#outputs td { overflow-wrap:anywhere; }\n#outputs details { margin-top:6px; }\n#outputs summary { cursor:pointer; color:var(--accent); }\n.pipebar i:nth-child(5) { background:var(--p5); }\n'
 style.string = css


def standard_document(soup):
 if soup.html is None:
  document = BeautifulSoup('<html lang="en"><head></head><body></body></html>', 'html.parser')
  for child in list(soup.contents):
   target = document.head if getattr(child, 'name', None) in ('title', 'meta', 'link', 'style') else document.body
   target.append(child.extract())
  soup = document
 soup.html['lang'] = 'en'
 for attributes in [{'charset':'utf-8'}, {'name':'viewport', 'content':'width=device-width, initial-scale=1'}]:
  selector = 'meta[charset]' if 'charset' in attributes else 'meta[name="viewport"]'
  tag = soup.head.select_one(selector)
  if tag is None:
   tag = soup.new_tag('meta'); soup.head.insert(0, tag)
  tag.attrs.update(attributes)
 return '<!DOCTYPE html>\n' + str(soup.html) + '\n'


def section_key(k):
 return (int(re.match(r'\d+', k)[0]), k)


def refresh(source=None, output=None):
 global VAL, DASH
 VAL = Path(source).resolve() if source else VAL
 DASH = Path(output).resolve() if output else VAL / 'metrics_dashboard.html'
 source_html = VAL / 'metrics_dashboard.html'
 old = source_html.read_text(encoding='utf-8')
 inventory = build_inventory(VAL.parent)
 soup = BeautifulSoup(old, 'html.parser')
 total = 0
 previous = None
 shown = {}
 for fam in FAMILIES:
  pipe, prefix, accent = fam['key'], fam['prefix'], fam['accent']
  section = ensure_family_scaffold(soup, fam, previous)
  previous = fam
  gallery = section.select_one('.gallery')
  cards = {f.img['alt'].removeprefix(prefix+'_'): f for f in gallery.select('figure')}
  # every saved export of this notebook is a card, whether or not the page had it before
  exported = {p.stem.removeprefix(prefix+'_'): p for p in (VAL / 'Figures').glob(f'{prefix}_*.jpg')}
  for key in ORPHANS.get(pipe, {}):
   exported.pop(key, None); cards.pop(key, None)
  for key in exported:
   if key not in cards:
    cards[key] = BeautifulSoup(f'<figure class="card" data-pipe="{pipe}"><div class="cardhead"><span class="sec p{accent}">§{key}</span><code class="src">{prefix}.ipynb</code></div><h3></h3><p class="tests"></p><button class="figwrap" type="button"><img class="figimg" loading="lazy"></button></figure>', 'html.parser').figure
    title, desc = CAPTIONS.get(pipe, {}).get(key, (f'Section {key}', ''))
    cards[key].h3.string = ''; cards[key].h3.append(BeautifulSoup(title, 'html.parser'))
    cards[key].select_one('.tests').string = ''; cards[key].select_one('.tests').append(BeautifulSoup(desc, 'html.parser'))
  for key, (title, desc) in CAPTIONS.get(pipe, {}).items():
   if key in cards:
    cards[key].h3.clear(); cards[key].h3.append(BeautifulSoup(title, 'html.parser'))
    cards[key].select_one('.tests').clear(); cards[key].select_one('.tests').append(BeautifulSoup(desc, 'html.parser'))
  # a card whose export has gone is dropped rather than left pointing at a missing file
  cards = {k: v for k, v in cards.items() if k in exported}
  gallery.clear()
  for key in sorted(cards, key=section_key):
   f = cards[key]
   path = exported[key]
   data = path.read_bytes()
   with Image.open(path) as im: width,height = im.size; im.verify()
   f.img.attrs.update(src=f'Figures/{path.name}?v={hashlib.sha256(data).hexdigest()[:12]}', alt=path.stem, width=width, height=height, decoding='async')
   f.button['aria-label'] = 'Enlarge figure: '+f.h3.get_text()
   # Old numerical captions describe an earlier run, not the newly saved figure.
   for caption in f.select('figcaption'): caption.decompose()
   if pipe in ('patent','caselaw','dimension') and key=='7': f.select_one('.tests').string = FAMILY_DESC['paper']
   gallery.append(f); gallery.append('\n')
  section.select_one('.shead .meta').string = f'{len(cards)} figure{"s" if len(cards) != 1 else ""} · {prefix}.ipynb'
  shown[pipe] = len(cards)
  total += len(cards)
 refresh_accent_css(soup)
 n_nb = len(FAMILIES)
 soup.select_one('#validation .shead .meta').string = f'{total} figures · {n_nb} notebooks'
 soup.select_one('#validation .intro').string = (f'There is no gold standard for any of these metrics, so validation is face validity: each figure either reproduces a published result, or checks an invariant the build must satisfy. The {n_nb} notebooks are kept apart below, because they are validated against different literature and different invariants; the last one cross-checks the disruption kernel against an independent implementation. Only figures exported by the validation notebooks are shown. Click any figure to enlarge it.')
 for kpi in soup.select('.kpi'):
  if kpi.select_one('.k').get_text() == 'validation figures':
   kpi.select_one('.v').string = str(total); kpi.select_one('.sub').string = f'{n_nb} notebooks'
 # Point readers to current evidence instead of a hand-copied table from the previous run.
 agreement = soup.find(id='agreement')
 if agreement:
  chart = agreement.select_one('.chartbox')
  if chart:
   chart.clear(); chart.append(BeautifulSoup('<p class="intro">See the updated <a href="#val-paper">Agreement with SciSciNet figure (§3c)</a> for metric-specific correlations, sample sizes and coverage from the current validation run, and §3b for the Uzzi 2×2 on SciSciNet\'s own scores. Earlier restricted-run atypicality results are shown separately in §9d. The <a href="#val-dimension">Dimensions section</a> (§14) compares the same metrics across the OpenAlex and Dimensions indices, and the <a href="#val-crosscheck">cross-check</a> compares the disruption kernel with an independent implementation.</p>', 'html.parser'))
 for article in soup.select('#gaps article'):
  title = article.h3.get_text()
  if 'paper_z_score.parquet' in title or title == 'Atypicality coverage and computation vintage':
   article.h3.string = 'Atypicality coverage and computation vintage'
   article.p.string = 'The saved figures in sections 3–4 use the corrected merged 1980–2020 run (41,425,041 papers, 14 partitions at export). Section 9 preserves the earlier 2000–2005 run, before the journal-mapping fix; these vintages must not be pooled. Derived tables reports current stored-table counts, while each figure retains its stated analysis window.'
   article.select_one('.flag').string = 'coverage'
  elif 'author_list' in title:
   article.h3.string = 'Native author-based team size'
   article.p.string = 'The team-size figure uses distinct author IDs per paper from paper_author.parquet, built from the OpenAlex authorship snapshot.'
   article.select_one('.flag').string = 'updated'
  elif 'Disruption transfers' in title: article.p.string = 'Agreement depends on the citation graph and observation window. Consult the current §3c comparison before carrying disruption values or rankings across sources.'
  elif 'Beauty coefficient' in title: article.p.string = 'B depends on the whole citation history and therefore on snapshot coverage. Consult §3c for the current cross-source comparison.'
  elif 'Pre-grant citations' in title:
   article.h3.string = 'Citation-network choice changes trajectory shape'
   article.p.string = 'Granted-only and extended networks can produce different convexity classifications. Sections 15 and 21–26 show the comparisons; state the citation network with every result.'
 update_inventory_page(soup, inventory)
 result = standard_document(soup)
 result = result.replace('Generated 1 Sep 2026', 'Updated 6 Sep 2026')
 result = result.replace('Built from the four validation notebooks', 'Built from the five validation notebooks')
 result = result.replace('every result quoted in a caption is taken from the stored output of the notebook cell\n  that produced the figure beside it.', 'validation figures are refreshed from the saved notebook exports. Figure values and analysis coverage are shown in each plot.')
 DASH.parent.mkdir(parents=True, exist_ok=True)
 # The detailed diagnostic report stays local and is excluded by .gitignore.
 (DASH.parent / 'data').mkdir(exist_ok=True)
 (DASH.parent / 'data' / 'inventory.json').write_text(json.dumps(inventory, indent=2) + '\n', encoding='utf-8')
 wanted = set()
 for img in soup.select('.gallery img'):
  relative = img['src'].split('?', 1)[0]
  wanted.add(relative)
  src, dst = VAL / relative, DASH.parent / relative
  if src.resolve() != dst.resolve():
   dst.parent.mkdir(exist_ok=True)
   if not dst.exists() or hashlib.sha256(src.read_bytes()).digest() != hashlib.sha256(dst.read_bytes()).digest():
    shutil.copy2(src, dst)
 if (DASH.parent / 'Figures').resolve() != (VAL / 'Figures').resolve():
  # a published copy carries exactly the figures the page references, nothing stale
  for stale in (DASH.parent / 'Figures').glob('*.jpg'):
   if f'Figures/{stale.name}' not in wanted:
    stale.unlink()
 DASH.write_text(result, encoding='utf-8')
 print(f'Updated {DASH}: {total} figures ({", ".join(f"{k} {v}" for k, v in shown.items())}), {len(result):,} characters')

if __name__ == '__main__':
 parser = argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--source', type=Path, required=True, help='Upstream validation directory containing HTML and Figures')
 parser.add_argument('--output', type=Path, default=Path('metrics_dashboard.html'))
 args = parser.parse_args()
 refresh(args.source, args.output)
