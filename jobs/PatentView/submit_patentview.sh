#!/bin/bash
# Submit the PatentView patent-metric notebooks to the jevans CPU partition.
#
#   ./submit_patentview.sh        # everything that can run
#   ./submit_patentview.sh plan   # the order, and what is blocked
#
# All ten run. pg_granted_pgpubs_crosswalk.tsv.zip arrived on 2026-08-28, which unblocked
# patent_citation, patent_citation_trend and patent_disruption_app_add, and with them the two
# that read their outputs.
#
# afterok throughout: every edge is a DATA dependency. A notebook that fails leaves the
# parquet its successors read absent or half-written.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs

if [ "${1:-}" = "plan" ]; then
  cat <<'MSG'
    1  patent_metadata               (no dependency)
    2  patent_disruption             (no dependency)
    3  patent_sb                     (no dependency)
    4  patent_citation               (no dependency)
    5  patent_citation_trend         (no dependency)
    6  patent_disruption_app_add     (no dependency)
    7  patent_z_score                <- 1
    8  patent_feg_disruption_trend   <- 1, 2
    9  patent_hit_probability        <- 1, 4
   10  patent_disruption_app_compare <- 1, 2, 6
MSG
  exit 0
fi

sub() {
  local nb="$1"; shift
  local dep=()
  [ $# -gt 0 ] && dep=(--dependency="afterok:$(IFS=:; echo "$*")")
  local jid
  jid=$(sbatch --parsable ${dep[@]+"${dep[@]}"} \
        -J "pv_$nb" --export=ALL,NB="$nb" nb.sbatch)
  printf '  %-30s job %s%s\n' "$nb" "$jid" \
         "$([ $# -gt 0 ] && echo "   after $*")" >&2
  echo "$jid"
}

echo "submitting the PatentView chain to partition jevans:" >&2
P1=$(sub patent_metadata)
P2=$(sub patent_disruption)
P3=$(sub patent_sb)
P4=$(sub patent_citation)
P5=$(sub patent_citation_trend)
P6=$(sub patent_disruption_app_add)
P7=$(sub patent_z_score                "$P1")
P8=$(sub patent_feg_disruption_trend   "$P1" "$P2")
P9=$(sub patent_hit_probability        "$P1" "$P4")
PA=$(sub patent_disruption_app_compare "$P1" "$P2" "$P6")

cat <<'MSG'

watch:
  squeue -u $USER -p jevans
  tail -f logs/pv_<notebook>-<jobid>.out
MSG
