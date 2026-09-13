#!/bin/bash
# Submit the OpenAlex paper-metric notebooks to the jevans CPU partition, in dependency order.
#
#   ./submit_openalex.sh          # the whole chain
#   ./submit_openalex.sh plan     # print the order and the dependencies, submit nothing
#
# ORDER, and why:
#   referenced_works_w_year   walks renli's tree once -> cache/work_year_source_map.npz and
#                             output/referenced_works_w_year/. Everything else asserts these
#                             exist, so it goes first and alone.
#        |
#   paper_metadata            journal + FoS caches, and the per-paper table
#   paper_citation            builds cache/paper_graph.npz            } these two touch
#        |                                                             different caches and
#   paper_disruption          builds cache/paper_csr.npz from it       run in parallel
#        |
#   paper_sb / paper_z_score / paper_citation_trend / paper_hit_probability
#                             all readers: CSR, CSR+journal, graph, and the two parquets
#
# afterok throughout: every edge here is a DATA dependency. A notebook that fails leaves the
# cache its successors read either absent or half-written, and running on that would produce
# numbers nobody could characterise.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p logs

if [ "${1:-}" = "plan" ]; then
  cat <<'MSG'
  0  referenced_works_w_year                      (no dependency)
  1  paper_metadata            <- 0
  2  paper_citation            <- 0
  3  paper_disruption          <- 2
  4  paper_sb                  <- 3
  5  paper_z_score             <- 3
  6  paper_citation_trend      <- 3
  7  paper_hit_probability     <- 1, 2
  8  paper_author_country      (no dependency; scans works_au_affs_fixed.csv.gz like paper_author,
                                and cross-checks paper_author.parquet only if it exists)
MSG
  exit 0
fi

sub() {   # name  [dependency...]  -> job id on stdout
  local nb="$1"; shift
  local dep=()
  [ $# -gt 0 ] && dep=(--dependency="afterok:$(IFS=:; echo "$*")")
  local jid
  jid=$(sbatch --parsable ${dep[@]+"${dep[@]}"} \
        -J "oa_$nb" --export=ALL,NB="$nb" nb.sbatch)
  printf '  %-26s job %s%s\n' "$nb" "$jid" \
         "$([ $# -gt 0 ] && echo "   after $*")" >&2
  echo "$jid"
}

echo "submitting the OpenAlex chain to partition jevans:" >&2
J0=$(sub referenced_works_w_year)
J1=$(sub paper_metadata        "$J0")
J2=$(sub paper_citation        "$J0")
J3=$(sub paper_disruption      "$J2")
J4=$(sub paper_sb              "$J3")
J5=$(sub paper_z_score         "$J3")
J6=$(sub paper_citation_trend  "$J3")
J7=$(sub paper_hit_probability "$J1" "$J2")
J8=$(sub paper_author_country)

cat <<'MSG'

watch:
  squeue -u $USER -p jevans
  tail -f logs/oa_<notebook>-<jobid>.out

referenced_works_w_year is the long one: one pass over 1,334 partitions of works/,
primary_locations/, locations/ and referenced_works/, ~1.78B edges out. Everything after it
reads caches.
MSG
