#!/bin/bash
# Second pass after the 2026-10-08 OpenAlex rebuild: paper_hit_probability was truncated. Its pyarrow Table.join
# kept 293.2 M of the 364.3 M matching rows (19.5 % of every field missing) on the 2026-09-23 release; the notebook
# now joins and ranks in DuckDB and asserts the row count. This script rebuilds that table and reruns everything
# that reads hit percentiles, in the order of sep23_downstream.sh. Notebooks that read no hit percentile are not
# rerun (build_curvature, the rev paper_citation, citation_age_by_field, paper_disruption_feg,
# ppp_citation_trajectory_DA, nb_correlation, and the validation notebooks other than author_country, inventor_country,
# dimension and paper). Correlation runs because its first-pass job was cancelled with the rest.
#
#   ./sep23_hitfix.sh
#
# Done by hand before submitting (2026-10-09): the truncated table moved to
# OpenAlex/Old/pre_sep23_2026-10-08/paper_hit_probability.truncated-2026-10-08.parquet, and the two caches that are
# reused whenever present renamed *.hittrunc-2026-10-09 (validation/data/author_country_base.parquet,
# Atypicality/Data/_traj_cache/citation_trajectory/). The paper_year_DA and patent_year_DA caches rebuild on their
# input signatures, and paper2000 / paper2020 and curvature_vs_metrics force their own caches.
set -euo pipefail
SOS="/project/jevans/Dawoon/Science of Science"
LOG="$SOS/jobs/OpenAlex/logs/sep23_downstream_jobs.txt"
CLEAN="$(echo "$PATH" | tr ':' '\n' | grep -v hkg_venv | paste -sd:)"
sb() { env -u VIRTUAL_ENV PATH="$CLEAN" sbatch --parsable "$@"; }

# ── OpenAlex: the table itself ─────────────────────────────────────────────────────────────────────────────────────
cd "$SOS/jobs/OpenAlex"
H=$(sb --cpus-per-task=16 --mem=300G -t 4:00:00 -J oa_paper_hit_probability \
       --export=ALL,NBPATH=OpenAlex/notebook/paper_hit_probability.ipynb,SAVE=1 nbsave.sbatch)

# ── Atypicality: builders and caches ───────────────────────────────────────────────────────────────────────────────
cd "$SOS/Atypicality/jobs"
B1=$(sb --dependency=afterok:$H --mem=128G -t 1:00:00 build_master_rev.sbatch)
B2=$(sb --dependency=afterok:$B1 --cpus-per-task=16 --mem=200G -t 1:00:00 -J rev_build_master_paper --export=ALL,NB=build_master_paper nb_rev.sbatch)
C1=$(sb --dependency=afterok:$H:$B1 --mem=256G -t 4:00:00 -J nb_paper_year_DA --export=ALL,NB=paper_year_DA_vs_metrics nb.sbatch)
C2=$(sb --dependency=afterok:$B1 --mem=256G -t 2:00:00 -J nb_patent_year_DA --export=ALL,NB=patent_year_DA_vs._metrics nb.sbatch)
C3=$(sb --dependency=afterok:$H:$B1 --mem=192G -t 2:00:00 -J nb_paper2000 --export=ALL,NB=paper2000_DA_vs_metrics nb.sbatch)
C4=$(sb --dependency=afterok:$C3 --mem=64G -t 2:00:00 -J nb_paper2000_gz --export=ALL,NB=paper2000_DA_vs_metrics_groupz nb.sbatch)
C5=$(sb --dependency=afterok:$H:$B1 --mem=256G -t 2:00:00 -J nb_paper2020 --export=ALL,NB=paper2020_DA_vs_metrics nb.sbatch)

# ── Atypicality: the rev notebooks that read hit percentiles, one at a time (shared SOS/.duckdb_tmp) ──────────────────
rev() {   # name cpus mem hours data-deps prev -> job id
  local nb=$1 c=$2 m=$3 h=$4 d="afterok:$5"
  [ -n "$6" ] && d="$d,afterany:$6"
  sb --dependency="$d" --cpus-per-task=$c --mem=$m -t $h:00:00 -J rev_$nb --export=ALL,NB=$nb nb_rev.sbatch
}
R2=$(rev paper_citation_master   8 128G 1 $B2    "")
R3=$(rev curvature_vs_metrics   16 256G 2 $H:$B2 $R2)
R6=$(rev ppp_citation            8 128G 2 $B1    $R3)
R8=$(rev ppp_disruption_feg      8  96G 2 $B1    $R6)
R9=$(rev ppp_DA_investigation    8  64G 1 $B1    $R8)
R10=$(rev Correlation            8  64G 1 $B1    $R9)

# ── Atypicality: analyses ──────────────────────────────────────────────────────────────────────────────────────────
A1=$(sb --dependency=afterok:$C3:$C2:$B1 --mem=96G -t 4:00:00 -J nb_ppp_DA --export=ALL,NB=PPP_DA_vs._metrics nb.sbatch)
A2=$(sb --dependency=afterok:$C4:$C2:$B1 --mem=96G -t 4:00:00 -J nb_ppp_DA_gz --export=ALL,NB=PPP_DA_vs._metrics_groupz nb.sbatch)
A3=$(sb --dependency=afterok:$C3:$C2 --mem=96G -t 3:00:00 -J nb_fig2 --export=ALL,NB=Figure_2_Citation_distribution nb.sbatch)
A4=$(sb --dependency=afterok:$C3:$C2 --mem=96G -t 2:00:00 -J nb_fig2_gz --export=ALL,NB=Figure_2_Citation_distribution_groupz nb.sbatch)
A6=$(sb --dependency=afterok:$C1 --cpus-per-task=16 --mem=192G -t 3:00:00 -J nb_paper_traj --export=ALL,NB=nb_paper_trajectory_DA nb.sbatch)
A7=$(sb --dependency=afterok:$C3:$C2 --mem=200G -t 3:00:00 -J nb_citation_trajectory --export=ALL,NB=nb_citation_trajectory nb.sbatch)
# nb_da_distributions and nb_headline write some of nb_main's figures: both run before nb_main (see sep23_downstream.sh).
A8=$(sb --dependency=afterok:$C3:$C2 --mem=128G -t 1:00:00 -J nb_da_dist --export=ALL,NB=nb_da_distributions nb.sbatch)
A9=$(sb --dependency=afterok:$C1:$C2 --mem=256G -t 2:00:00 -J nb_headline --export=ALL,NB=nb_headline nb.sbatch)
A10=$(sb --dependency=afterok:$C1:$C2 --mem=256G -t 2:00:00 -J nb_headline_pppl --export=ALL,NB=nb_headline_pppl nb.sbatch)
A11=$(sb --dependency=afterok:$C1:$C2,afterany:$A9:$A8 --mem=256G -t 4:00:00 -J nb_main --export=ALL,NB=nb_main nb.sbatch)
A12=$(sb --dependency=afterok:$C1:$C2,afterany:$A10 --mem=256G -t 4:00:00 -J nb_main_pppl --export=ALL,NB=nb_main_pppl nb.sbatch)

# ── validation: the four notebooks that read paper_hit_probability (private spill folders) ─────────────────────────
cd "$SOS/jobs/validation"
val() {   # notebook mem deps -> job id
  sb --dependency=afterok:$3 --mem=$2 -J val_$1 --export=ALL,NB=$1,NB_DUCKDB_TMP="$SOS/.duckdb_tmp/val_$1" nb.sbatch
}
V4=$(val dimension_validation         64G  $H)
V6=$(val author_country_validation   250G  $H)
V7=$(val inventor_country_validation  32G  $V6)
V8=$(val paper_validation            250G  $H)

# ── comparisons ────────────────────────────────────────────────────────────────────────────────────────────────────
cd "$SOS/jobs/OpenAlex"
K1=$(sb --dependency=afterok:$H --cpus-per-task=32 --mem=250G -t 3:00:00 -J sep23_output_comparison \
        --export=ALL,NBPATH=OpenAlex/notebook/output_comparison.ipynb,SAVE=1,NB_DUCKDB_MEM=200GB nbsave.sbatch)
K2=$(sb --dependency=afterany:$B1:$B2:$C1:$C3:$C5:$R3:$A7 --cpus-per-task=16 --mem=200G -t 3:00:00 \
        -J sep23_downstream_comparison --export=ALL,NBPATH=validation/sep23_downstream_comparison.ipynb,SAVE=1,NB_DUCKDB_MEM=150GB nbsave.sbatch)

{
echo "sep23 hit fix $(date '+%F %T'): paper_hit_probability $H"
echo "  builders/caches: master_rev $B1 | master_paper $B2 | paper_year_DA $C1 | patent_year_DA $C2 | paper2000 $C3 | paper2000_gz $C4 | paper2020 $C5"
echo "  rev: $R2 $R3 $R6 $R8 $R9 $R10 (paper_citation_master, curvature_vs_metrics, ppp_citation, ppp_disruption_feg, ppp_DA_investigation, Correlation)"
echo "  analyses: ppp_DA $A1 | ppp_DA_gz $A2 | fig2 $A3 | fig2_gz $A4 | paper_traj $A6 | citation_trajectory $A7"
echo "            da_dist $A8 | headline $A9 | headline_pppl $A10 | nb_main $A11 | nb_main_pppl $A12"
echo "  validation: dimension $V4 | author_country $V6 | inventor_country $V7 | paper $V8"
echo "  comparisons: output $K1 | downstream $K2"
} | tee -a "$LOG"
