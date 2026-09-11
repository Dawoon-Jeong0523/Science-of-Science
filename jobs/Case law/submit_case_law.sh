#!/bin/bash
# Submit the Case law metric notebooks in dependency order.
#
#   ./submit_case_law.sh            # everything
#   ./submit_case_law.sh fast       # everything except case_disruption (+ its trend)
#
# case_metadata builds cache/case_graph.npz and cache/case_csr.npz and must land first.
# case_disruption is hours (a Python loop over 5.18M cases, 31.1e9 element touches assembling
# the B sets); the rest are minutes.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs
sub() {  # name [dependency] -> job id
  local nb="$1" dep="${2:-}" args=()
  [ -n "$dep" ] && args=(--dependency="afterok:$dep")
  sbatch --parsable ${args[@]+"${args[@]}"} --export=ALL,NB="$nb" -J "cl_$nb" nb.sbatch
}
META=$(sub case_metadata);                       echo "case_metadata             -> $META" >&2
CIT=$(sub case_citation "$META");                echo "case_citation             -> $CIT   (after $META)" >&2
TRD=$(sub case_citation_trend "$META");          echo "case_citation_trend       -> $TRD   (after $META)" >&2
SB=$(sub case_sb "$META");                       echo "case_sb                   -> $SB   (after $META)" >&2
HIT=$(sub case_hit_probability "$CIT");          echo "case_hit_probability      -> $HIT   (after $CIT)" >&2
if [ "${1:-all}" != "fast" ]; then
  DIS=$(sub case_disruption "$META");            echo "case_disruption           -> $DIS   (after $META)" >&2
  FEG=$(sub case_feg_disruption_trend "$DIS");   echo "case_feg_disruption_trend -> $FEG   (after $DIS)" >&2
fi
echo >&2
echo "watch: squeue -u \$USER -p jevans   |   tail -f logs/cl_<nb>-<jobid>.out" >&2
