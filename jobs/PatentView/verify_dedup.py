#!/usr/bin/env python3
"""Verify the de-duplicated patent_disruption.parquet.

Three questions, in order of what they would invalidate:

1. Is CD back inside its mathematical range? Duplicate (citing, cited) rows made the same citer
   appear twice in the citer list, so n_j counted it twice while B (built with np.unique) counted
   it once -- n_k = |B_w| - n_j could go NEGATIVE, the denominator n_i+n_j+n_k could fall below
   |n_i-n_j|, and CD escaped [-1, 1] (the old file reached -2.0). Nothing about the old numbers
   is defensible where that happened.

2. Does it now agree EXACTLY with patent_disruption_app.parquet where the two are provably the
   same graph? Application citations are carried by documents published from 2001 on, and a
   patent granted in year y draws its window-w citers from [y, y+w], so for y <= 2000-w the
   extended network cannot differ from the granted one by a single edge. Every metric must match
   bit for bit there. CD_all has no such range -- its window is unbounded -- so it is exempt.

3. What actually moved relative to the pre-dedup table?
"""
import sys
import duckdb

OUT = "/project/jevans/Dawoon/Science of Science/PatentView/output"
NEW = f"{OUT}/patent_disruption.parquet"
OLD = f"{OUT}/patent_disruption.parquet.pre-dedup"
APP = f"{OUT}/patent_disruption_app.parquet"
META = f"{OUT}/patent_metadata.parquet"
WS = ['_3', '_5', '_10', '_all']
MET = ['CD', 'F', 'E', 'G', 'ni', 'nj', 'nk']
SAFE = {'_3': 1997, '_5': 1995, '_10': 1990}          # last grant year application citations cannot reach
PGPUB_START = 2001

con = duckdb.connect()
con.execute("SET memory_limit='200GB'")
ok = True

print("=" * 78)
print("1. CD range and n_k sign")
print("=" * 78)
print(f"{'window':<8}{'file':<14}{'min CD':>10}{'max CD':>10}{'CD<-1':>10}{'CD>1':>8}{'nk<0':>8}")
for w in WS:
    for lab, f in [('pre-dedup', OLD), ('deduped', NEW)]:
        r = con.execute(f"""SELECT min(CD{w}), max(CD{w}),
              sum(CASE WHEN CD{w} < -1 THEN 1 ELSE 0 END),
              sum(CASE WHEN CD{w} >  1 THEN 1 ELSE 0 END),
              sum(CASE WHEN nk{w} < 0 THEN 1 ELSE 0 END) FROM read_parquet('{f}')""").fetchone()
        print(f"{w:<8}{lab:<14}{r[0]:>+10.4f}{r[1]:>+10.4f}{r[2]:>10,}{r[3]:>8,}{r[4]:>8,}")
        if lab == 'deduped' and (r[2] or r[3] or r[4]):
            ok = False
            print(f"    FAIL: deduped table still has out-of-range CD or negative nk at {w}")
print()

print("=" * 78)
print("2. Exact agreement with the extended table where the graphs are identical")
print("=" * 78)
n_new = con.execute(f"SELECT count(*) FROM read_parquet('{NEW}')").fetchone()[0]
n_old = con.execute(f"SELECT count(*) FROM read_parquet('{OLD}')").fetchone()[0]
n_app = con.execute(f"SELECT count(*) FROM read_parquet('{APP}')").fetchone()[0]
print(f"rows: pre-dedup {n_old:,} | deduped {n_new:,} | extended {n_app:,}")
if n_new != n_old:
    ok = False
    print("    FAIL: de-duplication must not change the node set (allids is built before the dedup)")
print()

for w, last in SAFE.items():
    conds = " OR ".join(f"g.{m}{w} IS DISTINCT FROM a.{m}{w}" for m in MET)
    q = f"""SELECT count(*) n,
              sum(CASE WHEN {conds} THEN 1 ELSE 0 END) differ,
              max(abs(g.CD{w} - a.CD{w})) maxdiff
            FROM read_parquet('{NEW}') g
            JOIN read_parquet('{APP}') a USING (patent_id)
            JOIN read_parquet('{META}') m USING (patent_id)
            WHERE m.grant_year <= {last}"""
    n, differ, maxdiff = con.execute(q).fetchone()
    differ = int(differ or 0)
    verdict = "EXACT MATCH" if differ == 0 else f"*** {differ:,} PATENTS DIFFER ***"
    print(f"window {w:<5} grant year <= {last}: {n:,} patents, all {len(MET)} metrics -> {verdict}")
    if differ:
        ok = False
        print(f"    max |delta CD{w}| = {maxdiff}")
        cols = ", ".join(f"g.{m}{w} g_{m}, a.{m}{w} a_{m}" for m in MET)
        for row in con.execute(f"""SELECT g.patent_id, m.grant_year, {cols}
              FROM read_parquet('{NEW}') g JOIN read_parquet('{APP}') a USING (patent_id)
              JOIN read_parquet('{META}') m USING (patent_id)
              WHERE m.grant_year <= {last} AND ({conds}) LIMIT 5""").fetchall():
            print("    ", row)
print()
print(f"(CD_all is exempt: its window is unbounded, so every patent can pick up a post-{PGPUB_START}")
print(" application citer no matter how early it was granted.)")
print()

print("=" * 78)
print("3. What changed against the pre-dedup table")
print("=" * 78)
for w in WS:
    conds = " OR ".join(f"o.{m}{w} IS DISTINCT FROM g.{m}{w}" for m in MET)
    r = con.execute(f"""SELECT count(*) n, sum(CASE WHEN {conds} THEN 1 ELSE 0 END) changed,
          avg(o.CD{w}) old_mean, avg(g.CD{w}) new_mean
        FROM read_parquet('{OLD}') o JOIN read_parquet('{NEW}') g USING (patent_id)""").fetchone()
    n, ch = r[0], int(r[1] or 0)
    print(f"window {w:<5} {ch:>8,} of {n:,} patents changed ({100*ch/n:.3f}%)   "
          f"mean CD {r[2]:+.6f} -> {r[3]:+.6f}  (delta {r[3]-r[2]:+.6f})")
print()
print("=" * 78)
print("VERDICT:", "ALL CHECKS PASSED" if ok else "FAILURES ABOVE")
print("=" * 78)
sys.exit(0 if ok else 1)
