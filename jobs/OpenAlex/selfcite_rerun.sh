#!/bin/bash
# Recompute every OpenAlex output (and the two PPP trend tables) after self-citations were dropped from the
# edge table, 2026-10-03. afterok throughout: a failed step leaves its successors pending, not running on
# half-written inputs.
#
#   drop_self_citations ─┬─ build_caches ─┬─ paper_citation ─┐
#                        │                ├─ paper_citation_trend, paper_sb, ppp_citation_trend
#                        │                ├─ paper_z_score x 14 year ranges ── paper_z_score_merge
#                        │                └─ paper_disruption ── paper_disruption_trend
#                        └─ paper_metadata ──┴─ (paper_disruption, paper_hit_probability <- paper_citation)
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs
nb() {   # name  notebook-path  sbatch-options  env  [dependency...]  -> job id
  local name="$1" path="$2" opts="$3" envs="$4"; shift 4
  local dep=(); [ $# -gt 0 ] && dep=(--dependency="afterok:$(IFS=:; echo "$*")")
  sbatch --parsable ${dep[@]+"${dep[@]}"} $opts -J "$name" --export="ALL,NBPATH=$path${envs:+,$envs}" nbsave.sbatch
}
J0=$(sbatch --parsable drop_self_citations.sbatch)
JC=$(sbatch --parsable --dependency=afterok:$J0 build_caches.sbatch)
JM=$(nb oa_paper_metadata      OpenAlex/notebook/paper_metadata.ipynb       "--mem=128G -t 8:00:00"  SAVE=1 $J0)
JP=$(nb oa_paper_citation      OpenAlex/notebook/paper_citation.ipynb       "-t 12:00:00"            SAVE=1 $JC)
JT=$(nb oa_paper_citation_trend OpenAlex/notebook/paper_citation_trend.ipynb "-t 6:00:00"            SAVE=1 $JC)
JS=$(nb oa_paper_sb            OpenAlex/notebook/paper_sb.ipynb             "-t 6:00:00"             SAVE=1 $JC)
JQ=$(nb ppp_citation_trend     PPP/notebook/ppp_citation_trend.ipynb        "-t 6:00:00"             SAVE=1 $JC)
JD=$(nb oa_paper_disruption    OpenAlex/notebook/paper_disruption.ipynb     "--cpus-per-task=32 --mem=300G -t 24:00:00" SAVE=1 $JC $JM)
JH=$(nb oa_paper_hit_probability OpenAlex/notebook/paper_hit_probability.ipynb "-t 6:00:00"          SAVE=1 $JP $JM)
JR=$(nb oa_paper_disruption_trend OpenAlex/notebook/paper_disruption_trend.ipynb "--cpus-per-task=32 --mem=400G -t 12:00:00" SAVE=1 $JD)
ZS=()
for r in 1980:1984 1985:1989 1990:2000 2001:2006 2007:2011 2012:2012 2013:2013 2014:2014 2015:2015 2016:2016 2017:2017 2018:2018 2019:2019 2020:2020; do
  ZS+=($(nb "oa_pzs_${r/:/_}" OpenAlex/notebook/paper_z_score.ipynb "-t 30:00:00" "NB_Z_YEARS=$r" $JC))
done
JZ=$(nb oa_pzs_merge           OpenAlex/notebook/paper_z_score_merge.ipynb  "-t 2:00:00"             SAVE=1 "${ZS[@]}")
cat <<MSG
drop_self_citations $J0 | build_caches $JC | paper_metadata $JM | paper_citation $JP | paper_citation_trend $JT
paper_sb $JS | ppp_citation_trend $JQ | paper_disruption $JD | paper_hit_probability $JH | paper_disruption_trend $JR
paper_z_score ${ZS[*]} | merge $JZ
MSG
