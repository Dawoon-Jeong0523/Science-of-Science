#!/bin/bash
# Submit the PATSTAT patent-metric notebooks to the jevans CPU partition, in dependency order.
#
#   ./submit_patstat.sh                 # the whole chain (raw parquet must already be loaded)
#   ./submit_patstat.sh plan            # print the order, submit nothing
#   ./submit_patstat.sh after <jobid>   # chain after a load.sbatch array (afterok on the array)
#   NB_PS_CLOCK=grant ./submit_patstat.sh   # the same chain on the grant clock -> PATSTAT/output_grant/
#   NB_PS_UNIT=family ./submit_patstat.sh   # the same chain on DOCDB families (priority year) -> PATSTAT/output_family/
#
# ORDER, and why:
#   load.sbatch (array)      dump zip parts -> raw/<tls>/*.parquet  (stage 0, separate script)
#        |
#   patstat_reference        the edge list at application level (tls212 x tls211 x tls201)
#        |
#   patstat_metadata         universe table; ref_count comes from the edge list
#        |
#   patstat_citation         } read the edge list + metadata, independent of each other
#   patstat_disruption       }
#   patstat_sb               }
#   patstat_z_score          } (tls224 + metadata)
#        |
#   patstat_inventor         } (tls207 + metadata)
#        |
#   patstat_citation_trend   <- citation (reconciles against it)
#   patstat_hit_probability  <- citation
#   patstat_feg_disruption_trend <- disruption
#   patstat_disruption_trend <- disruption (reads its CSR cache, checks against its windows)
#   patstat_inventor_country <- inventor (cross-checks n_inventors)
#        |
#   patstat_uniqueC_trend    <- citation_trend (identity check against it, and against citation)
#
# Smoke test of the whole chain on a 1/20 sample first:  sbatch smoke.sbatch
#
# afterok throughout: every edge is a DATA dependency.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs

if [ "${1:-}" = "plan" ]; then
  cat <<'MSG'
  1  patstat_reference             (needs raw/ tls201, tls211, tls212)
  2  patstat_metadata              <- 1
  3  patstat_citation              <- 2
  4  patstat_disruption            <- 2
  5  patstat_sb                    <- 2
  6  patstat_z_score               <- 2
  7  patstat_citation_trend        <- 3
  8  patstat_hit_probability       <- 3
  9  patstat_feg_disruption_trend  <- 4
 10  patstat_disruption_trend      <- 4
 11  patstat_inventor              <- 2
 12  patstat_inventor_country      <- 11
 13  patstat_uniqueC_trend         <- 3, 7
MSG
  exit 0
fi

AFTER=()
if [ "${1:-}" = "after" ]; then
  : "${2:?after needs a job id}"
  AFTER=("$2")
fi

sub() {
  local nb="$1"; shift
  local dep=()
  [ $# -gt 0 ] && dep=(--dependency="afterok:$(IFS=:; echo "$*")")
  local jid
  local pfx="ps"; [ "${NB_PS_CLOCK:-filing}" = "grant" ] && pfx="psg"; [ "${NB_PS_UNIT:-application}" = "family" ] && pfx="psf"
  jid=$(sbatch --parsable ${dep[@]+"${dep[@]}"} -J "${pfx}_$nb" --export=ALL,NB="$nb" nb.sbatch)
  printf '  %-30s job %s%s\n' "$nb" "$jid" "$([ $# -gt 0 ] && echo "   after $*")" >&2
  echo "$jid"
}

echo "submitting the PATSTAT chain (clock: ${NB_PS_CLOCK:-filing}, unit: ${NB_PS_UNIT:-application}) to partition jevans:" >&2
P1=$(sub patstat_reference            ${AFTER[@]+"${AFTER[@]}"})
P2=$(sub patstat_metadata             "$P1")
P3=$(sub patstat_citation             "$P2")
P4=$(sub patstat_disruption           "$P2")
P5=$(sub patstat_sb                   "$P2")
P6=$(sub patstat_z_score              "$P2")
P7=$(sub patstat_citation_trend       "$P3")
P8=$(sub patstat_hit_probability      "$P3")
P9=$(sub patstat_feg_disruption_trend "$P4")
P10=$(sub patstat_disruption_trend    "$P4")
P11=$(sub patstat_inventor            "$P2")
P12=$(sub patstat_inventor_country    "$P11")
P13=$(sub patstat_uniqueC_trend       "$P3" "$P7")

cat <<'MSG'

watch:
  squeue -u $USER -p jevans
MSG
