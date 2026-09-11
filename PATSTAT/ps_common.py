"""Paths, the raw-table registry and shared helpers for the PATSTAT patent-metric notebooks.

The PatentView twin (`../PatentView/pv_common.py`) reads PatentsView `.tsv.zip` bulk files
straight from pandas. PATSTAT Global 2023 Autumn is 65 zipped CSV parts (one CSV per zip,
~280 GB uncompressed) and the notebooks need to join them at scale, so there is one extra
stage here: `load_table()` streams a zip part to a zstd parquet under raw/<tls>/ once, and
every notebook reads the parquet through DuckDB. The dump under /project/jevans/PATSTAT is
never written to.

    import ps_common as ps
    ps.preflight('patstat_citation')      # which raw tables / outputs are present
    con = ps.connect()                    # duckdb with memory_limit + temp dir set
    con.execute(f"SELECT count(*) FROM {ps.raw('tls201')}")

Identifiers. The unit of analysis is the PATSTAT APPLICATION (`appln_id`, int) -- the twin of
PatentView's `patent_id`. Publications (`pat_publn_id`) are only a routing step: a citation
in tls212 is made BY a publication and points AT a publication (or directly at an
application), and both ends are resolved to `appln_id` through tls211 in patstat_reference.
"""
from __future__ import annotations

import glob
import os
import re
import subprocess
import time

BASE   = "/project/jevans/Dawoon/Science of Science/PATSTAT"
DUMP   = "/project/jevans/PATSTAT/unzipped_data"        # tlsNNN_partMM.zip, one CSV each
DOCS   = "/project/jevans/PATSTAT/index_documentation_scripts_PATSTAT_Global_2023_Autumn.zip"
RAW    = f"{BASE}/raw"                                   # raw/<tls>/partMM.parquet, from load_table()
OUT    = f"{BASE}/output"                                # every notebook writes its parquet here
CACHE  = f"{BASE}/cache"                                 # derived graphs / CSR, not results
TMP    = f"{BASE}/cache/duckdb_tmp"
for _d in (RAW, OUT, CACHE, TMP):
    os.makedirs(_d, exist_ok=True)

EDITION = "PATSTAT Global 2023 Autumn (2023b)"
SNAP_YEAR = 2023            # the last year with data; the Autumn edition is cut in ~Sep 2023

# ── The universe ───────────────────────────────────────────────────────────────────────────
# The twin of PatentView's "US utility patents with a grant year": patents of invention
# (ipr_type PI -- no utility models, no designs), real applications (PATSTAT creates
# 'artificial' applications with appln_id >= 900,000,000 to hold cited documents it does not
# otherwise know), with a filing year in range. Every notebook applies exactly this predicate.
ARTIFICIAL_MIN = 900_000_000
YEAR_MIN, YEAR_MAX = 1900, SNAP_YEAR
UNIVERSE_WHERE = (f"ipr_type = 'PI' AND appln_id < {ARTIFICIAL_MIN} "
                  f"AND appln_filing_year BETWEEN {YEAR_MIN} AND {YEAR_MAX}")

# ── Citation provenance (tls212.citn_origin) ───────────────────────────────────────────────
# PatentView splits citations into examiner / non-examiner / unknown and drops third-party
# submissions. PATSTAT carries the origin explicitly:
#   APP  cited by the applicant                       -> 'applicant'
#   SEA  search report      ISR  international SR     -> 'examiner'
#   SUP  supplementary SR   PRS  examination/prosec.  -> 'examiner'
#   EXA  examiner           FOP  further search/opp.  -> 'examiner'
#   CH2  PCT chapter II     OPP  opposition           -> 'examiner' / 'other'
#   115  Art. 115 EPC third-party observation, TPO third party -> EXCLUDED (as in PatentView)
#   ''   no origin recorded                            -> 'other'
ORIGIN_BUCKET = {
    'APP': 'applicant',
    'SEA': 'examiner', 'ISR': 'examiner', 'SUP': 'examiner', 'PRS': 'examiner',
    'EXA': 'examiner', 'FOP': 'examiner', 'CH2': 'examiner',
    'OPP': 'other', '': 'other',
}
THIRD_PARTY = ('115', 'TPO')
BUCKETS = ('examiner', 'applicant', 'other')

# What every counting notebook applies to patstat_reference.parquet: the citing application was
# filed no earlier than the cited one, and the citation is an original, not one replenished onto
# a publication from another member of its family.
EDGE_WHERE = "age >= 0 AND NOT replenished"

# SQL fragment: bucket from a citn_origin column expression
def bucket_sql(col: str = 'citn_origin') -> str:
    return (f"CASE WHEN trim({col}) = 'APP' THEN 'applicant' "
            f"WHEN trim({col}) IN ('SEA','ISR','SUP','PRS','EXA','FOP','CH2') THEN 'examiner' "
            f"ELSE 'other' END")

def third_party_sql(col: str = 'citn_origin') -> str:
    return f"trim({col}) IN ('115','TPO')"

# ── WIPO technology fields (tls230.techn_field_nr, 1..35) -> the five sectors ─────────────
# Schmoch (2008) concordance; the same five names PatentView's g_wipo_technology carries.
WIPO_SECTOR = {**{i: 'Electrical engineering' for i in range(1, 9)},
               **{i: 'Instruments' for i in range(9, 14)},
               **{i: 'Chemistry' for i in range(14, 25)},
               **{i: 'Mechanical engineering' for i in range(25, 33)},
               **{i: 'Other fields' for i in range(33, 36)}}
WIPO_FIELD = {1: 'Electrical machinery, apparatus, energy', 2: 'Audio-visual technology', 3: 'Telecommunications',
              4: 'Digital communication', 5: 'Basic communication processes', 6: 'Computer technology',
              7: 'IT methods for management', 8: 'Semiconductors', 9: 'Optics', 10: 'Measurement',
              11: 'Analysis of biological materials', 12: 'Control', 13: 'Medical technology',
              14: 'Organic fine chemistry', 15: 'Biotechnology', 16: 'Pharmaceuticals', 17: 'Macromolecular chemistry, polymers',
              18: 'Food chemistry', 19: 'Basic materials chemistry', 20: 'Materials, metallurgy', 21: 'Surface technology, coating',
              22: 'Micro-structural and nano-technology', 23: 'Chemical engineering', 24: 'Environmental technology',
              25: 'Handling', 26: 'Machine tools', 27: 'Engines, pumps, turbines', 28: 'Textile and paper machines',
              29: 'Other special machines', 30: 'Thermal processes and apparatus', 31: 'Mechanical elements', 32: 'Transport',
              33: 'Furniture, games', 34: 'Other consumer goods', 35: 'Civil engineering'}

def wipo_sector_sql(col: str = 'techn_field_nr') -> str:
    return (f"CASE WHEN {col} BETWEEN 1 AND 8 THEN 'Electrical engineering' "
            f"WHEN {col} BETWEEN 9 AND 13 THEN 'Instruments' "
            f"WHEN {col} BETWEEN 14 AND 24 THEN 'Chemistry' "
            f"WHEN {col} BETWEEN 25 AND 32 THEN 'Mechanical engineering' "
            f"WHEN {col} BETWEEN 33 AND 35 THEN 'Other fields' END")

# ── The raw-table registry ─────────────────────────────────────────────────────────────────
# Column types come from Documentation_Scripts/CreateScripts/CreateTableScripts/*.sql in DOCS
# (SQL Server DDL): int -> int64, smallint/tinyint -> int32, date -> date32, char/varchar ->
# string, real -> float64. Only the tables the notebooks read are registered; the rest of the
# dump (abstracts tls203, NPL tls214/215, legal events tls231, JP classes tls222, ...) can be
# added here and loaded the same way.
import pyarrow as pa

_I, _S, _D, _F = pa.int64(), pa.string(), pa.date32(), pa.float64()
TABLES = {
    'tls201': dict(name='tls201_appln', rows=127_966_159, types={
        'appln_id': _I, 'appln_auth': _S, 'appln_nr': _S, 'appln_kind': _S, 'appln_filing_date': _D,
        'appln_filing_year': _I, 'appln_nr_epodoc': _S, 'appln_nr_original': _S, 'ipr_type': _S,
        'receiving_office': _S, 'internat_appln_id': _I, 'int_phase': _S, 'reg_phase': _S, 'nat_phase': _S,
        'earliest_filing_date': _D, 'earliest_filing_year': _I, 'earliest_filing_id': _I,
        'earliest_publn_date': _D, 'earliest_publn_year': _I, 'earliest_pat_publn_id': _I, 'granted': _S,
        'docdb_family_id': _I, 'inpadoc_family_id': _I, 'docdb_family_size': _I, 'nb_citing_docdb_fam': _I,
        'nb_applicants': _I, 'nb_inventors': _I}),
    'tls202': dict(name='tls202_appln_title', rows=107_350_069, types={
        'appln_id': _I, 'appln_title_lg': _S, 'appln_title': _S}),
    'tls204': dict(name='tls204_appln_prior', rows=49_564_223, types={
        'appln_id': _I, 'prior_appln_id': _I, 'prior_appln_seq_nr': _I}),
    'tls206': dict(name='tls206_person', rows=90_458_473, types={
        'person_id': _I, 'person_name': _S, 'person_name_orig_lg': _S, 'person_address': _S, 'person_ctry_code': _S,
        'nuts': _S, 'nuts_level': _I, 'doc_std_name_id': _I, 'doc_std_name': _S, 'psn_id': _I, 'psn_name': _S,
        'psn_level': _I, 'psn_sector': _S, 'han_id': _I, 'han_name': _S, 'han_harmonized': _I}),
    'tls207': dict(name='tls207_pers_appln', rows=351_478_030, types={
        'person_id': _I, 'appln_id': _I, 'applt_seq_nr': _I, 'invt_seq_nr': _I}),
    'tls209': dict(name='tls209_appln_ipc', rows=340_946_365, types={
        'appln_id': _I, 'ipc_class_symbol': _S, 'ipc_class_level': _S, 'ipc_version': _D, 'ipc_value': _S,
        'ipc_position': _S, 'ipc_gener_auth': _S}),
    'tls211': dict(name='tls211_pat_publn', rows=151_566_589, types={
        'pat_publn_id': _I, 'publn_auth': _S, 'publn_nr': _S, 'publn_nr_original': _S, 'publn_kind': _S,
        'appln_id': _I, 'publn_date': _D, 'publn_lg': _S, 'publn_first_grant': _S, 'publn_claims': _I}),
    'tls212': dict(name='tls212_citation', rows=507_520_117, types={
        'pat_publn_id': _I, 'citn_replenished': _I, 'citn_id': _I, 'citn_origin': _S, 'cited_pat_publn_id': _I,
        'cited_appln_id': _I, 'pat_citn_seq_nr': _I, 'cited_npl_publn_id': _S, 'npl_citn_seq_nr': _I,
        'citn_gener_auth': _S}),
    'tls224': dict(name='tls224_appln_cpc', rows=382_631_077, types={
        'appln_id': _I, 'cpc_class_symbol': _S}),
    'tls228': dict(name='tls228_docdb_fam_citn', rows=263_216_992, types={
        'docdb_family_id': _I, 'cited_docdb_family_id': _I}),
    'tls230': dict(name='tls230_appln_techn_field', rows=150_950_092, types={
        'appln_id': _I, 'techn_field_nr': _I, 'weight': _F}),
}

# What each notebook needs: raw tables (bare 'tlsNNN') and outputs of earlier notebooks ('@file').
NEEDS = {
    'patstat_load':                 [],
    'patstat_metadata':             ['tls201', 'tls211', 'tls212', 'tls209', 'tls224', 'tls230', 'tls207', 'tls206',
                                     '@patstat_reference.parquet'],
    'patstat_reference':            ['tls201', 'tls211', 'tls212'],
    'patstat_citation':             ['@patstat_reference.parquet', '@patstat_metadata.parquet'],
    'patstat_citation_trend':       ['@patstat_reference.parquet', '@patstat_metadata.parquet'],
    'patstat_disruption':           ['@patstat_reference.parquet', '@patstat_metadata.parquet'],
    'patstat_sb':                   ['@patstat_reference.parquet', '@patstat_metadata.parquet'],
    'patstat_hit_probability':      ['@patstat_citation.parquet', '@patstat_metadata.parquet'],
    'patstat_z_score':              ['tls224', '@patstat_metadata.parquet'],
    'patstat_feg_disruption_trend': ['@patstat_disruption.parquet', '@patstat_metadata.parquet'],
}


def zip_parts(tls: str) -> list[str]:
    return sorted(glob.glob(f"{DUMP}/{tls}_part*.zip"))


def raw_dir(tls: str) -> str:
    return f"{RAW}/{tls}"


def raw_parts(tls: str) -> list[str]:
    return sorted(glob.glob(f"{raw_dir(tls)}/part*.parquet"))


def raw_complete(tls: str) -> bool:
    """Every zip part has its parquet (a part is written to a .tmp name until it is whole)."""
    zp = zip_parts(tls)
    return bool(zp) and len(raw_parts(tls)) == len(zp)


def raw(tls: str) -> str:
    """DuckDB source expression for a raw table: read_parquet over its parts."""
    if not raw_complete(tls):
        raise FileNotFoundError(
            f"{tls}: {len(raw_parts(tls))}/{len(zip_parts(tls))} parquet parts under {raw_dir(tls)}. "
            f"Run jobs/PATSTAT/load.sbatch (or notebook/patstat_load.ipynb) first.")
    return f"read_parquet('{raw_dir(tls)}/part*.parquet')"


def out(name: str) -> str:
    return f"{OUT}/{name}"


def cache(name: str) -> str:
    return f"{CACHE}/{name}"


def connect(memory: str | None = None, threads: int | None = None):
    """A DuckDB connection with the limits a jevans node allows (override via env for smoke runs)."""
    import duckdb
    con = duckdb.connect()
    mem = memory or os.environ.get('NB_DUCKDB_MEM', '200GB')
    con.execute(f"SET memory_limit='{mem}'")
    con.execute(f"SET temp_directory='{TMP}'")
    con.execute("SET preserve_insertion_order=false")
    thr = threads or int(os.environ.get('NB_WORKERS', os.environ.get('SLURM_CPUS_PER_TASK', '8')))
    con.execute(f"SET threads={thr}")
    return con


# ── Loading a zip part to parquet ──────────────────────────────────────────────────────────
def load_table(tls: str, part: str, force: bool = False, block_mb: int = 64, verbose: bool = True) -> str:
    """Stream one `tlsNNN_partMM.zip` to raw/tlsNNN/partMM.parquet (zstd). Returns the path.

    `unzip -p` decompresses to a pipe; pyarrow.csv reads it in blocks with the DDL types, so
    memory is one block (~ a few hundred MB) regardless of the 10 GB CSV inside. The parquet
    is written under a .tmp name and renamed when complete, so a killed job never leaves a
    part that looks finished.
    """
    import pyarrow.csv as pcsv
    import pyarrow.parquet as pq
    spec = TABLES[tls]
    m = re.search(r'_part(\d+)\.zip$', part)
    dst = f"{raw_dir(tls)}/part{m.group(1)}.parquet"
    if os.path.exists(dst) and not force:
        if verbose:
            print(f"  present  {dst}")
        return dst
    os.makedirs(raw_dir(tls), exist_ok=True)
    tmp = dst + '.tmp'
    t0 = time.time()
    proc = subprocess.Popen(['unzip', '-p', part], stdout=subprocess.PIPE, bufsize=1 << 24)
    reader = pcsv.open_csv(
        proc.stdout,
        read_options=pcsv.ReadOptions(block_size=block_mb << 20, use_threads=True),
        parse_options=pcsv.ParseOptions(delimiter=',', quote_char='"', double_quote=True, newlines_in_values=True),
        convert_options=pcsv.ConvertOptions(column_types=spec['types'], strings_can_be_null=False,
                                            include_columns=list(spec['types'])))
    writer = None
    n = 0
    try:
        for batch in reader:
            if writer is None:
                writer = pq.ParquetWriter(tmp, batch.schema, compression='zstd', compression_level=3)
            writer.write_batch(batch)
            n += batch.num_rows
            if verbose and n % 20_000_000 < batch.num_rows:
                print(f"    {tls} {os.path.basename(part)}: {n:>13,} rows  {time.time()-t0:6.0f}s", flush=True)
    finally:
        if writer is not None:
            writer.close()
        rc = proc.wait()
    if rc != 0:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise RuntimeError(f"unzip -p {part} exited {rc}")
    os.replace(tmp, dst)
    if verbose:
        print(f"  wrote    {dst}  {n:,} rows  {os.path.getsize(dst)/1e9:.2f} GB  {time.time()-t0:.0f}s")
    return dst


def load_jobs() -> list[tuple[str, str]]:
    """Every (tls, zip part) the registry covers, in dump order -- the SLURM array indexes this."""
    return [(tls, p) for tls in TABLES for p in zip_parts(tls)]


def raw_rows(tls: str) -> int:
    import pyarrow.parquet as pq
    return sum(pq.ParquetFile(p).metadata.num_rows for p in raw_parts(tls))


def preflight(notebook: str | None = None) -> bool:
    """Report which raw tables / upstream outputs are present. True if all needed are there."""
    names = [notebook] if notebook else sorted(NEEDS)
    print(f"dump   : {DUMP}   ({len(glob.glob(f'{DUMP}/*.zip'))} zip parts, {len(TABLES)} tables registered)")
    print(f"raw    : {RAW}")
    print(f"output : {OUT}\n")
    ok_all = True
    for nb in names:
        miss = []
        for need in NEEDS.get(nb, []):
            if need.startswith('@'):
                if not os.path.exists(out(need[1:])):
                    miss.append(need)
            elif not raw_complete(need):
                miss.append(f"{need} ({len(raw_parts(need))}/{len(zip_parts(need))} parts)")
        ok_all &= not miss
        print(f"  {nb:<30}{'OK' if not miss else 'MISSING ' + str(len(miss))}")
        for mm in miss:
            print(f"      {mm}  <- not available")
    return ok_all


def summary():
    """Row counts of the loaded raw tables against the edition's official counts."""
    print(f"{EDITION}\n  {'table':<28}{'parts':>7}{'rows loaded':>16}{'official':>16}  ok")
    for tls, spec in TABLES.items():
        zp, rp = zip_parts(tls), raw_parts(tls)
        if not rp:
            print(f"  {spec['name']:<28}{f'0/{len(zp)}':>7}{'-':>16}{spec['rows']:>16,}")
            continue
        n = raw_rows(tls)
        flag = 'YES' if (len(rp) == len(zp) and n == spec['rows']) else ('partial' if len(rp) < len(zp) else 'NO')
        print(f"  {spec['name']:<28}{f'{len(rp)}/{len(zp)}':>7}{n:>16,}{spec['rows']:>16,}  {flag}")
