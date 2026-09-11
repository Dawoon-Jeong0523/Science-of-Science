"""Refresh exported figures and the Parquet inventory without running notebooks."""
from pathlib import Path
from datetime import datetime
import argparse, hashlib, json, re, shutil
from bs4 import BeautifulSoup
from PIL import Image
from dashboard_inventory import build_inventory

VAL = Path(__file__).resolve().parent
DASH = VAL / 'metrics_dashboard.html'
EXTRA = {
 'paper': {
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
 }
}

def human_size(size):
 for unit, divisor in [('GB', 10**9), ('MB', 10**6), ('KB', 10**3)]:
  if size >= divisor:
   return f'{size / divisor:,.2f} {unit}'
 return f'{size:,} B'


def update_inventory_page(soup, inventory):
 files = inventory['files']
 by_path = {item['path']: item for item in files}
 rows = sum(item['rows'] for item in files)
 size = sum(item['bytes'] for item in files)
 ppp = inventory['ppp_provenance']
 ppp_verified = ppp['status'] == 'run_log_matches_current_output_counts'
 checked = datetime.fromisoformat(inventory['generated_utc'].replace('Z', '+00:00')).strftime('%d %b %Y').lstrip('0')
 soup.select_one('.railfoot').string = f'Inventory checked {checked} (UTC). Figures from saved validation exports.'
 soup.select_one('.band .lede').string = ('Five research pipelines cover papers, patents, patent-to-paper citations, paper–patent pairs and court opinions. Explore their inputs, derived tables, metric definitions and validation figures. Coverage and computation choices are stated alongside the results.')
 kpis = soup.select('.kpi')
 for kpi, value, label, subtitle in [
  (kpis[0], f'{rows / 10**9:.2f} B', 'stored rows', f'across {len(files)} derived tables'),
  (kpis[1], human_size(size), 'derived Parquet', 'canonical outputs · decimal GB'),
 ]:
  kpi.select_one('.v').string = value
  kpi.select_one('.k').string = label
  kpi.select_one('.sub').string = subtitle
 for kpi in kpis:
  label = kpi.select_one('.k').get_text()
  metadata_path = {'papers':'OpenAlex/output/paper_metadata.parquet', 'patents':'PatentView/output/patent_metadata.parquet', 'court opinions':'Case law/output/case_metadata.parquet'}.get(label)
  if metadata_path:
   kpi.select_one('.v').string = f'{by_path[metadata_path]["rows"] / 10**6:.2f} M'
  if label == 'papers':
   count = by_path['OpenAlex/output/paper_citation.parquet']['rows']
   kpi.select_one('.sub').string = f'{count / 10**6:.2f} M citation-table rows'
  elif label == 'patent→paper links':
   count = by_path['pcs/output/pcs_citation.parquet']['rows']
   kpi.select_one('.sub').string = f'{count / 10**6:.2f} M cited papers'
  elif label == 'court opinions':
   kpi.select_one('.sub').string = '47.5 M citations · 1666–2020'
 soup.select_one('#raw > .intro').string = ('These source collections supply the five pipelines. Authorship records provide native paper team sizes. SciSciNet is used for external validation only; it is not an input to the derived metrics. Source scales describe the available snapshots and need not equal the eligible sample in a figure.')
 for row in soup.select('#raw tbody tr'):
  cells = row.find_all('td', recursive=False)
  text = cells[0].get_text(' ', strip=True)
  if 'OpenAlex author' in text:
   cells[3].string = 'One row per (work, author, affiliation). Distinct author IDs are aggregated into paper_author.parquet, the native source of team size in the current validation.'
  elif 'SciSciNet (comparison only)' in text:
   cells[3].string = 'External comparison for metric-specific agreement in paper figure §3c. The current team-size figure uses native OpenAlex author IDs. Earlier restricted-run atypicality comparisons are identified separately in §9d.'
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
 intro.append('Counts come from current Parquet footers; sizes come from the filesystem. Rows have different meanings across tables and must not be summed as unique documents. The inventory includes the legacy team-size table, but excludes backups, dated score partitions already represented by merged files, and sharded reference intermediates. ')
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
 colors = {'paper':1, 'patent':2, 'pcs':3, 'ppp':4, 'caselaw':5}
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
 soup.select_one('footer p').string = (f'Inventory checked {checked} (UTC) across OpenAlex, PatentView, pcs, PPP and Case law. Row counts and schemas come from Parquet footers; file sizes and modification times come from filesystem metadata. Figures are saved exports from five validation notebooks. Refreshing this page does not recompute metrics or rerun those notebooks. The inventory snapshot and each figure’s analysis coverage are distinct; earlier atypicality exports remain explicitly labelled.')
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


def refresh(source=None, output=None):
 global VAL, DASH
 VAL = Path(source).resolve() if source else VAL
 DASH = Path(output).resolve() if output else VAL / 'metrics_dashboard.html'
 source_html = VAL / 'metrics_dashboard.html'
 old = source_html.read_text(encoding='utf-8')
 inventory = build_inventory(VAL.parent)
 soup = BeautifulSoup(old, 'html.parser')
 total = 0
 for pipe, prefix, accent in [('paper','paper',1),('patent','patent',2),('pcs','pcs',3),('ppp','ppp',4),('caselaw','case_law',5)]:
  section = soup.find(id=f'val-{pipe}')
  gallery = section.select_one('.gallery')
  cards = {f.img['alt'].removeprefix(prefix+'_validation_'): f for f in gallery.select('figure')}
  cards.pop('3b', None) if pipe == 'paper' else None
  for key, (title, desc) in EXTRA.get(pipe, {}).items():
   if key not in cards:
    f = BeautifulSoup(f'<figure class="card" data-pipe="{pipe}"><div class="cardhead"><span class="sec p{accent}">§{key}</span><code class="src">{prefix}_validation.ipynb</code></div><h3></h3><p class="tests"></p><button class="figwrap" type="button"><img class="figimg" loading="lazy"></button></figure>', 'html.parser').figure
    cards[key] = f
   cards[key].h3.string = title
   cards[key].select_one('.tests').string = desc
  gallery.clear()
  for key in sorted(cards, key=lambda k: (int(re.match(r'\d+', k)[0]),k)):
   f = cards[key]
   path = VAL / 'Figures' / f'{prefix}_validation_{key}.jpg'
   assert path.exists(), path
   data = path.read_bytes()
   with Image.open(path) as im: width,height = im.size; im.verify()
   f.img.attrs.update(src=f'Figures/{path.name}?v={hashlib.sha256(data).hexdigest()[:12]}', alt=path.stem, width=width, height=height, decoding='async')
   f.button['aria-label'] = 'Enlarge figure: '+f.h3.get_text()
   # Old numerical captions describe an earlier run, not the newly saved figure.
   for caption in f.select('figcaption'): caption.decompose()
   if pipe == 'paper' and key == '2': f.select_one('.tests').string = 'Native team size from distinct author IDs in paper_author.parquet; disruption percentile and citation impact by team size.'
   if pipe == 'paper' and key in ('3','4'): f.select_one('.tests').string = 'Corrected merged atypicality scores, 1980–2020; journal-only mapping. Conventionality and tail novelty are evaluated within publication-year cohorts.' if key=='3' else 'CDF of median and 10th-percentile Z from the corrected merged 1980–2020 run.'
   if pipe in ('patent','caselaw') and key=='7': f.select_one('.tests').string = 'Foundation / Extension / Generalization shares in the five-year citation window; shares sum to one.'
   gallery.append(f); gallery.append('\n')
  section.select_one('.shead .meta').string = f'{len(cards)} figures · {prefix}_validation.ipynb'
  total += len(cards)
 soup.select_one('#validation .shead .meta').string = f'{total} figures · 5 notebooks'
 for kpi in soup.select('.kpi'):
  if kpi.select_one('.k').get_text() == 'validation figures': kpi.select_one('.v').string = str(total)
 # Point readers to current evidence instead of a hand-copied table from the previous run.
 agreement = soup.find(id='agreement')
 if agreement:
  chart = agreement.select_one('.chartbox')
  if chart:
   chart.clear(); chart.append(BeautifulSoup('<p class="intro">See the updated <a href="#val-paper">Agreement with SciSciNet figure (§3c)</a> for metric-specific correlations, sample sizes and coverage from the current validation run. Earlier restricted-run atypicality results are shown separately in §9d.</p>', 'html.parser'))
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
 for img in soup.select('.gallery img'):
  relative = img['src'].split('?', 1)[0]
  src, dst = VAL / relative, DASH.parent / relative
  if src.resolve() != dst.resolve():
   dst.parent.mkdir(exist_ok=True)
   if not dst.exists() or hashlib.sha256(src.read_bytes()).digest() != hashlib.sha256(dst.read_bytes()).digest():
    shutil.copy2(src, dst)
 DASH.write_text(result, encoding='utf-8')
 print(f'Updated {DASH}: {total} figures, {len(result):,} characters')

if __name__ == '__main__':
 parser = argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--source', type=Path, required=True, help='Upstream validation directory containing HTML and Figures')
 parser.add_argument('--output', type=Path, default=Path('metrics_dashboard.html'))
 args = parser.parse_args()
 refresh(args.source, args.output)
