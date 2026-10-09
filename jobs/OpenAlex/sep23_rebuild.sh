#!/bin/bash
# Rebuild every OpenAlex output on the official 2026-09-23 snapshot (2026-10-08). The outputs built on renli's
# 2026-01-16 conversion, which had lost 104M works, are kept in OpenAlex/output_Renly (caches in cache_Renly).
#
#   ./sep23_rebuild.sh <flatten-verify job id>     # afterok on the flatten verification
#
# flatten verify ─┬─ referenced_works_w_year ─┬─ build_caches (graph, CSR) ──┬─ paper_citation ── paper_hit_probability
#                 │                           └─ build_journal_fos ─────────┤  paper_citation_trend, paper_sb
#                 │                                   └─ paper_metadata ─────┼─ paper_disruption ── paper_disruption_trend
#                 │                                        ├─ snapshot_comparison   paper_z_score x 18 ── merge
#                 ├─ paper_topics                          └─ paper_author_country (also after paper_author)
#                 └─ paper_author
#
# The z-score year ranges are finer than the 2026-10-03 run's 14 (2007:2011 alone took 12 h): the notebook seeds its
# randomness per focal year, so a year's result does not depend on the range it runs in, and the merge only requires
# the ranges to tile 1980-2020. ppp_citation_trend (PPP/) is not part of this rebuild.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs
FV="${1:?flatten verify job id}"
dep() { local d=""; for j in "$@"; do d="${d:+$d:}$j"; done; echo "--dependency=afterok:$d"; }
nb() {   # name notebook-path sbatch-options env [dependency...] -> job id
  local name="$1" path="$2" opts="$3" envs="$4"; shift 4
  sbatch --parsable $(dep "$@") $opts -J "$name" --export="ALL,NBPATH=$path${envs:+,$envs}" nbsave.sbatch
}
JW=$(nb oa_referenced_works_w_year OpenAlex/notebook/referenced_works_w_year.ipynb "--cpus-per-task=32 --mem=250G -t 12:00:00" SAVE=1 $FV)
JC=$(sbatch --parsable $(dep $JW) --cpus-per-task=32 --mem=350G -t 12:00:00 build_caches.sbatch)
JJ=$(sbatch --parsable $(dep $JW) build_journal_fos.sbatch)
JT=$(nb oa_paper_topics          OpenAlex/notebook/paper_topics.ipynb          "--mem=64G -t 12:00:00"   SAVE=1 $FV)
JA=$(nb oa_paper_author          OpenAlex/notebook/paper_author.ipynb          "--mem=250G -t 6:00:00"   SAVE=1 $FV)
JM=$(nb oa_paper_metadata        OpenAlex/notebook/paper_metadata.ipynb        "--mem=128G -t 10:00:00"  SAVE=1 $JJ)
JX=$(nb oa_snapshot_comparison   OpenAlex/notebook/snapshot_comparison.ipynb   "--cpus-per-task=32 --mem=200G -t 1:00:00" SAVE=1,NB_DUCKDB_MEM=150GB $JM)
JAC=$(nb oa_paper_author_country OpenAlex/notebook/paper_author_country.ipynb  "--mem=250G -t 6:00:00"   SAVE=1 $JA $JM)
JP=$(nb oa_paper_citation        OpenAlex/notebook/paper_citation.ipynb        "-t 12:00:00"             SAVE=1 $JC $JJ)
JTR=$(nb oa_paper_citation_trend OpenAlex/notebook/paper_citation_trend.ipynb  "-t 6:00:00"              SAVE=1 $JC $JJ)
JS=$(nb oa_paper_sb              OpenAlex/notebook/paper_sb.ipynb              "-t 6:00:00"              SAVE=1 $JC $JJ)
JD=$(nb oa_paper_disruption      OpenAlex/notebook/paper_disruption.ipynb      "--cpus-per-task=32 --mem=400G -t 24:00:00" SAVE=1 $JC $JM)
JH=$(nb oa_paper_hit_probability OpenAlex/notebook/paper_hit_probability.ipynb "--mem=300G -t 6:00:00"   SAVE=1 $JP $JM)
JR=$(nb oa_paper_disruption_trend OpenAlex/notebook/paper_disruption_trend.ipynb "--cpus-per-task=32 --mem=500G -t 16:00:00" SAVE=1 $JD)
ZS=()
for r in 1980:1984 1985:1989 1990:1994 1995:1999 2000:2002 2003:2005 2006:2007 2008:2009 2010:2011; do
  ZS+=($(nb "oa_pzs_${r/:/_}" OpenAlex/notebook/paper_z_score.ipynb "--mem=220G -t 36:00:00" "NB_Z_YEARS=$r" $JC $JJ))
done
for y in 2012 2013 2014 2015 2016 2017; do
  ZS+=($(nb "oa_pzs_${y}_${y}" OpenAlex/notebook/paper_z_score.ipynb "--mem=260G -t 36:00:00" "NB_Z_YEARS=$y:$y" $JC $JJ))
done
for y in 2018 2019 2020; do
  ZS+=($(nb "oa_pzs_${y}_${y}" OpenAlex/notebook/paper_z_score.ipynb "--mem=360G -t 36:00:00" "NB_Z_YEARS=$y:$y" $JC $JJ))
done
JZ=$(nb oa_pzs_merge             OpenAlex/notebook/paper_z_score_merge.ipynb   "-t 2:00:00"              SAVE=1 "${ZS[@]}")
cat <<MSG
referenced_works_w_year $JW | build_caches $JC | build_journal_fos $JJ | paper_topics $JT | paper_author $JA
paper_metadata $JM | snapshot_comparison $JX | paper_author_country $JAC | paper_citation $JP
paper_citation_trend $JTR | paper_sb $JS | paper_disruption $JD | paper_hit_probability $JH | paper_disruption_trend $JR
paper_z_score ${ZS[*]} | merge $JZ
MSG
