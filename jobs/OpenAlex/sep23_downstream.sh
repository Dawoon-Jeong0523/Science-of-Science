#!/bin/bash
# Rerun everything downstream of the 2026-10-08 OpenAlex rebuild (sep23_rebuild.sh), in dependency order. Steps 1-2a
# (pcs, PPP, build_master_rev -> build_master_paper -> build_curvature) were submitted by hand earlier the same day;
# their ids are passed in. Everything else is submitted here.
#
#   ./sep23_downstream.sh
#
# Rules this encodes (from the 2026-10-08 audit of the notebooks):
#  * Data dependencies are afterok on the job that writes the input.
#  * Notebooks that hard-code the shared DuckDB spill folder SOS/.duckdb_tmp (the Atypicality rev notebooks) run one
#    after another (afterany on the previous one): two DuckDB processes in one temp folder crashed on 2026-09-14.
#    Validation notebooks get a private folder each through NB_DUCKDB_TMP (val_common.TMP).
#  * Caches that are reused when present were moved aside beforehand (Data/rev/curvature_paper.parquet, the four rev
#    _traj_cache paper files, validation/data/author_country_base.parquet); paper2000_DA_vs_metrics (FORCE_CACHE) runs
#    before every reader of its cache; paper_year_DA_vs_metrics rebuilds on its input signature.
#  * Not rerun: build_master (legacy, calls the live API), make_groupz.py, patent_year_DA_vs._metrics_groupz (would
#    overwrite the shared patent cache with v1 code), the never-run *_pppl variants of nb_da_distributions and
#    nb_citation_trajectory, nb_f_01_grow_knowledge (interactive, pre-existing NameError), and every notebook that
#    reads no OpenAlex data (patent_*, ppp_cohorts, PPPL_robustness, ppp_example, the grow_knowledge heatmap).
#  * Jobs are submitted with hkg_venv removed from PATH and VIRTUAL_ENV unset (the nb.sbatch scripts call a bare python).
set -euo pipefail
SOS="/project/jevans/Dawoon/Science of Science"
LOG="$SOS/jobs/OpenAlex/logs/sep23_downstream_jobs.txt"
CLEAN="$(echo "$PATH" | tr ':' '\n' | grep -v hkg_venv | paste -sd:)"
sb() { env -u VIRTUAL_ENV PATH="$CLEAN" sbatch --parsable "$@"; }

# OpenAlex chain (sep23_rebuild.sh) and the steps submitted earlier
JM=60310238; JAC=60310240; JP=60310241; JTR=60310242; JD=60310244; JH=60310245; JR=60310246; JZ=60310266
P3=60314475; B1=60314486; B2=60314487; B3=60314488

# ── Atypicality: caches (own spill folders) ───────────────────────────────────────────────────────────────────────
cd "$SOS/Atypicality/jobs"
C1=$(sb --dependency=afterok:$JZ:$B1 --mem=256G -t 4:00:00 -J nb_paper_year_DA --export=ALL,NB=paper_year_DA_vs_metrics nb.sbatch)
C2=$(sb --dependency=afterok:$B1 --mem=256G -t 2:00:00 -J nb_patent_year_DA --export=ALL,NB=patent_year_DA_vs._metrics nb.sbatch)
C3=$(sb --dependency=afterok:$JZ:$B1 --mem=192G -t 2:00:00 -J nb_paper2000 --export=ALL,NB=paper2000_DA_vs_metrics nb.sbatch)
C4=$(sb --dependency=afterok:$C3 --mem=64G -t 2:00:00 -J nb_paper2000_gz --export=ALL,NB=paper2000_DA_vs_metrics_groupz nb.sbatch)
C5=$(sb --dependency=afterok:$JZ:$B1 --mem=256G -t 2:00:00 -J nb_paper2020 --export=ALL,NB=paper2020_DA_vs_metrics nb.sbatch)

# ── Atypicality: the rev notebooks, one at a time (shared SOS/.duckdb_tmp) ─────────────────────────────────────────
rev() {   # name cpus mem hours data-deps prev -> job id
  local nb=$1 c=$2 m=$3 h=$4 deps=$5 prev=$6 d="afterok:$5"
  [ -n "$prev" ] && d="$d,afterany:$prev"
  sb --dependency="$d" --cpus-per-task=$c --mem=$m -t $h:00:00 -J rev_$nb --export=ALL,NB=$nb nb_rev.sbatch
}
R1=$(rev paper_citation              16 256G 1 $B3            "")
R2=$(rev paper_citation_master        8 128G 1 $B2:$JTR       $R1)
R3=$(rev curvature_vs_metrics        16 256G 2 $B3:$JZ        $R2)
R4=$(rev citation_age_by_field       16 256G 1 $B1:$JTR       $R3)
R5=$(rev paper_disruption_feg        16 256G 2 $B1:$JR        $R4)
R6=$(rev ppp_citation                 8 128G 2 $B3:$B1        $R5)
R7=$(rev ppp_citation_trajectory_DA   8  64G 1 $B3            $R6)
R8=$(rev ppp_disruption_feg           8  96G 2 $B1            $R7)
R9=$(rev ppp_DA_investigation         8  64G 1 $B1            $R8)
R10=$(rev Correlation                 8  64G 1 $B1            $R9)

# ── Atypicality: analyses ──────────────────────────────────────────────────────────────────────────────────────────
A1=$(sb --dependency=afterok:$C3:$B1 --mem=96G -t 4:00:00 -J nb_ppp_DA --export=ALL,NB=PPP_DA_vs._metrics nb.sbatch)
A2=$(sb --dependency=afterok:$C4:$B1 --mem=96G -t 4:00:00 -J nb_ppp_DA_gz --export=ALL,NB=PPP_DA_vs._metrics_groupz nb.sbatch)
A3=$(sb --dependency=afterok:$C3:$C2 --mem=96G -t 3:00:00 -J nb_fig2 --export=ALL,NB=Figure_2_Citation_distribution nb.sbatch)
A4=$(sb --dependency=afterok:$C3:$C2 --mem=96G -t 2:00:00 -J nb_fig2_gz --export=ALL,NB=Figure_2_Citation_distribution_groupz nb.sbatch)
A5=$(sb --dependency=afterok:$C1:$C2 --mem=128G -t 3:00:00 -J nb_correlation --export=ALL,NB=nb_correlation nb.sbatch)
A6=$(sb --dependency=afterok:$C1:$B3 --cpus-per-task=16 --mem=192G -t 3:00:00 -J nb_paper_traj --export=ALL,NB=nb_paper_trajectory_DA nb.sbatch)
A7=$(sb --dependency=afterok:$C3:$C2:$JTR:$JD --mem=200G -t 3:00:00 -J nb_citation_trajectory --export=ALL,NB=nb_citation_trajectory nb.sbatch)
# nb_da_distributions writes Figures/main/DA_kde_by_group like nb_main, and nb_headline writes nb_main's headline
# figures: both run before nb_main, so nb_main's 7-cohort versions are the ones left on disk.
A8=$(sb --dependency=afterok:$C3:$C2:$JD --mem=128G -t 1:00:00 -J nb_da_dist --export=ALL,NB=nb_da_distributions nb.sbatch)
A9=$(sb --dependency=afterok:$C1:$C2 --mem=256G -t 2:00:00 -J nb_headline --export=ALL,NB=nb_headline nb.sbatch)
A10=$(sb --dependency=afterok:$C1:$C2 --mem=256G -t 2:00:00 -J nb_headline_pppl --export=ALL,NB=nb_headline_pppl nb.sbatch)
A11=$(sb --dependency=afterok:$C1:$C2,afterany:$A9:$A8 --mem=256G -t 4:00:00 -J nb_main --export=ALL,NB=nb_main nb.sbatch)
A12=$(sb --dependency=afterok:$C1:$C2,afterany:$A10 --mem=256G -t 4:00:00 -J nb_main_pppl --export=ALL,NB=nb_main_pppl nb.sbatch)

# ── validation (private spill folders) ─────────────────────────────────────────────────────────────────────────────
cd "$SOS/jobs/validation"
val() {   # notebook mem deps -> job id
  sb --dependency=afterok:$3 --mem=$2 -J val_$1 --export=ALL,NB=$1,NB_DUCKDB_TMP="$SOS/.duckdb_tmp/val_$1" nb.sbatch
}
V1=$(val case_law_validation          32G  $JM)
V2=$(val ppp_validation              200G  $JM:$JTR)
V3=$(val pcs_validation               32G  $P3)
V4=$(val dimension_validation         64G  $JP:$JD)
V5=$(val disruption_crosscheck        96G  $JD)
V6=$(val author_country_validation   250G  $JAC:$JD:$JH)
V7=$(val inventor_country_validation  32G  $V6)
V8=$(val paper_validation            250G  $JTR:$JD:$JH:$JZ)

# ── comparisons ────────────────────────────────────────────────────────────────────────────────────────────────────
cd "$SOS/jobs/OpenAlex"
K1=$(sb --dependency=afterok:$JZ:$JR:$JAC:$JH --cpus-per-task=32 --mem=250G -t 3:00:00 -J sep23_output_comparison \
        --export=ALL,NBPATH=OpenAlex/notebook/output_comparison.ipynb,SAVE=1,NB_DUCKDB_MEM=200GB nbsave.sbatch)
K2=$(sb --dependency=afterany:$P3:$B1:$B2:$B3:$C1:$C3:$C5:$R3:$R4:$R5:$A7 --cpus-per-task=16 --mem=200G -t 3:00:00 \
        -J sep23_downstream_comparison --export=ALL,NBPATH=validation/sep23_downstream_comparison.ipynb,SAVE=1,NB_DUCKDB_MEM=150GB nbsave.sbatch)

{
echo "sep23 downstream $(date '+%F %T'):"
echo "  caches: paper_year_DA $C1 | patent_year_DA $C2 | paper2000 $C3 | paper2000_gz $C4 | paper2020 $C5"
echo "  rev: $R1 $R2 $R3 $R4 $R5 $R6 $R7 $R8 $R9 $R10 (paper_citation .. Correlation)"
echo "  analyses: ppp_DA $A1 | ppp_DA_gz $A2 | fig2 $A3 | fig2_gz $A4 | nb_correlation $A5 | paper_traj $A6 | citation_trajectory $A7"
echo "            da_dist $A8 | headline $A9 | headline_pppl $A10 | nb_main $A11 | nb_main_pppl $A12"
echo "  validation: case_law $V1 | ppp $V2 | pcs $V3 | dimension $V4 | crosscheck $V5 | author_country $V6 | inventor_country $V7 | paper $V8"
echo "  comparisons: output $K1 | downstream $K2"
} | tee -a "$LOG"
