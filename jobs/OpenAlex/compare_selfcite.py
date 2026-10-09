"""Before / after the self-citation fix (2026-10-03): every recomputed OpenAlex output and the two PPP trend tables.

Old copies are in OpenAlex/Old/pre_selfcite_2026-10-03/. Per-document tables are joined on their key and every
column is compared row by row (IS DISTINCT FROM); the long trend tables are compared by row counts and column
sums. The report is printed and written next to the old copies as comparison.txt.

    sbatch compare_selfcite.sbatch
"""
import os, sys, time
import duckdb

BASE = "/project/jevans/Dawoon/Science of Science"
OLD = f"{BASE}/OpenAlex/Old/pre_selfcite_2026-10-03"
NEW = f"{BASE}/OpenAlex/output"
SELF = f"{OLD}/self_citing.parquet"
lines = []


def say(s=""):
    print(s, flush=True)
    lines.append(s)


con = duckdb.connect()
con.execute(f"SET threads={os.environ.get('SLURM_CPUS_PER_TASK', '16')}; SET memory_limit='{os.environ.get('NB_DUCKDB_MEM', '200GB')}'; "
            f"SET temp_directory='{BASE}/.duckdb_tmp/compare_selfcite'; SET preserve_insertion_order=false")
q = lambda sql: con.execute(sql).fetchdf()

# the works that cited themselves, from the OLD edge table
if not os.path.exists(SELF):
    con.execute(f"""COPY (SELECT work_id AS paper_id, any_value(work_year) AS year FROM
        read_parquet('{OLD}/referenced_works_w_year/*.parquet') WHERE work_id = referenced_work_id GROUP BY 1)
        TO '{SELF}' (FORMAT parquet)""")
n_self = q(f"SELECT count(*) n FROM read_parquet('{SELF}')").n[0]
say(f"self-citing works (old edge table): {n_self:,}")


def per_doc(name, key='paper_id', old_dir=OLD + '/output', new_dir=NEW):
    """Rows, and per column the rows that differ, how many of them are self-citing works, and the mean change."""
    o, n = f"read_parquet('{old_dir}/{name}')", f"read_parquet('{new_dir}/{name}')"
    cols = [c for c in con.execute(f"DESCRIBE SELECT * FROM {n}").fetchdf().column_name if c != key]
    num = set(con.execute(f"SELECT column_name FROM (DESCRIBE SELECT * FROM {n}) WHERE column_type IN "
                          "('TINYINT','SMALLINT','INTEGER','BIGINT','FLOAT','DOUBLE','HUGEINT','UTINYINT','USMALLINT','UINTEGER')")
              .fetchdf().column_name)
    t0 = time.time()
    rows = q(f"SELECT (SELECT count(*) FROM {o}) old_rows, (SELECT count(*) FROM {n}) new_rows")
    sel = ", ".join(
        f"count(*) FILTER (WHERE o.{c} IS DISTINCT FROM n.{c}) AS d_{c}, "
        f"count(*) FILTER (WHERE o.{c} IS DISTINCT FROM n.{c} AND s.paper_id IS NOT NULL) AS s_{c}"
        + (f", avg(n.{c} - o.{c}) FILTER (WHERE o.{c} IS DISTINCT FROM n.{c}) AS m_{c}" if c in num else "")
        for c in cols)
    r = q(f"""SELECT count(*) FILTER (WHERE o.{key} IS NULL) only_new, count(*) FILTER (WHERE n.{key} IS NULL) only_old,
                     {sel}
              FROM {o} o FULL JOIN {n} n USING ({key}) LEFT JOIN read_parquet('{SELF}') s ON s.paper_id = coalesce(n.{key}, o.{key})""")
    say(f"\n=== {name}: rows {rows.old_rows[0]:,} -> {rows.new_rows[0]:,} (only in old {r.only_old[0]:,}, only in new "
        f"{r.only_new[0]:,})  [{time.time() - t0:.0f}s]")
    same = [c for c in cols if r[f'd_{c}'][0] == 0]
    if same:
        say(f"  identical: {', '.join(same)}")
    for c in cols:
        d = r[f'd_{c}'][0]
        if d:
            m = f", mean change {r[f'm_{c}'][0]:+.4g}" if c in num and r[f'm_{c}'][0] is not None else ""
            say(f"  {c:22s} {d:>12,} rows differ ({r[f's_{c}'][0]:,} of them self-citing works){m}")


def sums(name, old_path, new_path, cols):
    """Long tables: row counts, distinct documents and column totals."""
    agg = lambda p: q(f"SELECT count(*) rows, " + ", ".join(f"sum({c})::DOUBLE {c}" for c in cols) + f" FROM read_parquet('{p}')")
    a, b = agg(old_path), agg(new_path)
    say(f"\n=== {name}: rows {a.rows[0]:,} -> {b.rows[0]:,} ({b.rows[0] - a.rows[0]:+,})")
    for c in cols:
        say(f"  sum({c}): {a[c][0]:,.0f} -> {b[c][0]:,.0f} ({b[c][0] - a[c][0]:+,.0f})")


say(f"edge table rows: {q(f'''SELECT count(*) n FROM read_parquet('{OLD}/referenced_works_w_year/*.parquet')''').n[0]:,} -> "
    f"{q(f'''SELECT count(*) n FROM read_parquet('{NEW}/referenced_works_w_year/*.parquet')''').n[0]:,}; self rows left: "
    f"{q(f'''SELECT count(*) n FROM read_parquet('{NEW}/referenced_works_w_year/*.parquet') WHERE work_id = referenced_work_id''').n[0]:,}")
for name in ("paper_metadata.parquet", "paper_citation.parquet", "paper_disruption.parquet",
             "paper_hit_probability.parquet", "paper_sb.parquet", "paper_z_score.parquet"):
    per_doc(name)

# CD after the fix: no value below -1, no negative nk outside the -1 placeholder
say("\n=== paper_disruption sanity (new)")
say(q(f"""SELECT min(CD_all) min_CD_all, count(*) FILTER (WHERE CD_all < -1) cd_below_m1,
           count(*) FILTER (WHERE nk_all < 0 AND ni_all >= 0) nk_negative_with_counts,
           count(*) FILTER (WHERE CD_all IS NULL AND ni_all >= 0) cd_null_with_counts
           FROM read_parquet('{NEW}/paper_disruption.parquet')""").to_string(index=False))
say("--- same, old")
say(q(f"""SELECT min(CD_all) min_CD_all, count(*) FILTER (WHERE CD_all < -1) cd_below_m1,
           count(*) FILTER (WHERE nk_all < 0 AND ni_all >= 0) nk_negative_with_counts,
           count(*) FILTER (WHERE CD_all IS NULL AND ni_all >= 0) cd_null_with_counts
           FROM read_parquet('{OLD}/output/paper_disruption.parquet')""").to_string(index=False))

sums("paper_citation_trend.parquet", f"{OLD}/output/paper_citation_trend.parquet", f"{NEW}/paper_citation_trend.parquet",
     ["p2p", "pat2p_examiner", "pat2p_non_examiner"])
sums("paper_disruption_trend.parquet", f"{OLD}/output/paper_disruption_trend.parquet", f"{NEW}/paper_disruption_trend.parquet",
     ["ni_new", "nj_new", "nk_new"])
q_pairs = lambda p: q(f"SELECT count(*) n, avg(Z_score) z FROM read_parquet('{p}')")
a, b = q_pairs(f"{OLD}/output/z_score_pair.parquet"), q_pairs(f"{NEW}/z_score_pair.parquet")
say(f"\n=== z_score_pair.parquet: rows {a.n[0]:,} -> {b.n[0]:,}, mean Z {a.z[0]:.4f} -> {b.z[0]:.4f}")
for name in ("ppp_paper_trend.parquet", "ppp_patent_trend.parquet"):
    cols = ["p2p", "pat2p_examiner", "pat2p_non_examiner"] if "paper" in name else ["pat2pat_examiner", "pat2pat_non_examiner"]
    sums(name, f"{OLD}/PPP_output/{name}", f"{BASE}/PPP/output/{name}", cols)

open(f"{OLD}/comparison.txt", "w").write("\n".join(lines) + "\n")
print(f"\nreport -> {OLD}/comparison.txt")
