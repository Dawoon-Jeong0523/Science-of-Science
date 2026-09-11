#!/bin/bash
# Submit the Dimensions paper-metric notebooks to the jevans CPU partition, in dependency order.
#
#   ./submit_dimensions.sh          # the whole chain
#   ./submit_dimensions.sh plan     # print the order and the dependencies, submit nothing
#
# ORDER, and why:
#   references_w_year   the ONE pass over the dump -> cache/pub_scalars, cache/pub_authors,
#                       cache/pub_year_source_map.npz, output/references_w_year/. Everything
#                       else asserts these exist, so it goes first and alone.
#        |
#   paper_metadata      journal + FoS caches, and the per-publication table
#   paper_author        consolidates cache/pub_authors                    } independent of
#   paper_citation      builds cache/paper_graph.npz                      } each other
#        |
#   paper_disruption    builds cache/paper_csr.npz from the graph
#        |
#   paper_sb / paper_z_score / paper_citation_trend / paper_hit_probability
#                       all readers: CSR, CSR+journal, graph (+ the patents folder), and the
#                       two parquets
#
# afterok throughout: every edge here is a DATA dependency. A notebook that fails leaves the
# cache its successors read either absent or half-written.
#
# paper_z_score runs the MAG-comparable 1990-2000 range by default; for the production range
# submit it separately, e.g.
#   sbatch --export=ALL,NB=paper_z_score,NB_Z_MODE=extended -J dim_paper_z_score_ext nb.sbatch
# and then NB=paper_z_score_merge to promote the partitions to the bare file name.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs

if [ "${1:-}" = "plan" ]; then
  cat <<'MSG'
  0  references_w_year         (no dependency)
  1  paper_metadata            <- 0
  2  paper_author              <- 0
  3  paper_citation            <- 0
  4  paper_disruption          <- 3
  5  paper_sb                  <- 4
  6  paper_z_score             <- 4        (default range 1990-2000; see header)
  7  paper_citation_trend      <- 4
  8  paper_hit_probability     <- 1, 3
MSG
  exit 0
fi

sub() {   # name  [dependency...]  -> job id on stdout
  local nb="$1"; shift
  local dep=()
  [ $# -gt 0 ] && dep=(--dependency="afterok:$(IFS=:; echo "$*")")
  local jid
  jid=$(sbatch --parsable ${dep[@]+"${dep[@]}"} \
        -J "dim_$nb" --export=ALL,NB="$nb" nb.sbatch)
  printf '  %-26s job %s%s\n' "$nb" "$jid" \
         "$([ $# -gt 0 ] && echo "   after $*")" >&2
  echo "$jid"
}

echo "submitting the Dimensions chain to partition jevans:" >&2
J0=$(sub references_w_year)
J1=$(sub paper_metadata        "$J0")
J2=$(sub paper_author          "$J0")
J3=$(sub paper_citation        "$J0")
J4=$(sub paper_disruption      "$J3")
J5=$(sub paper_sb              "$J4")
J6=$(sub paper_z_score         "$J4")
J7=$(sub paper_citation_trend  "$J4")
J8=$(sub paper_hit_probability "$J1" "$J3")

cat <<'MSG'

watch:
  squeue -u $USER -p jevans
  tail -f logs/dim_<notebook>-<jobid>.out

references_w_year is the long one: one pass over 4,219 publication files (~490 GB, nested
columns) with 8 processes, then the reference explosion. Everything after it reads caches.
MSG
