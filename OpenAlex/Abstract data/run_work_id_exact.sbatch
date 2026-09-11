#!/bin/bash
#SBATCH --job-name=work_id_exact
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=1000G
#SBATCH -t 24:00:00
# 2026-09-09: 64G was OOM-killed in stage 2 at year 2012 (step MaxRSS 63 GB, per-year memory grows
# with the row count; 2011 had 3.75 M rows). jevans nodes have 1.5-2 TB, so ask for 1000G outright.
# Relative on purpose: the folder name has a space. Submit from this folder.
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err

# Stage 1: re-extract the paper training corpus from the tip dump with `id` (405 shards, 8 procs, ~4 GB each).
# Stage 2: prove per year that the row set equals work_{year}.parquet, attach ids by exact key,
#          write work_by_year_with_id_exact/ and work_id_exact_verification.{csv,tex}.
#
#   cd "/project/jevans/Dawoon/Science of Science/OpenAlex/Abstract data"
#   sbatch run_work_id_exact.sbatch
#   sbatch --export=ALL,NB_LIMIT=3,NB_YEARS=1976-1977 run_work_id_exact.sbatch   # smoke (report marked partial)

HERE="/project/jevans/Dawoon/Science of Science/OpenAlex/Abstract data"
cd "$HERE" || exit 2
source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh
conda activate /project/jevans/Dawoon/env/Curvature || { echo "[ERROR] conda env not found"; exit 2; }
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}
set -euo pipefail
export PYTHONUNBUFFERED=1

echo "==================== START $(date)  node $(hostname)  cpus ${SLURM_CPUS_PER_TASK:-?} ===================="
LIMIT=(); [ -n "${NB_LIMIT:-}" ] && LIMIT=(--limit "$NB_LIMIT")
srun python extract_work_ids.py --workers "${SLURM_CPUS_PER_TASK:-8}" "${LIMIT[@]}"
echo "==================== stage 2 $(date) ===================="
srun python verify_attach_ids.py
echo "==================== DONE  $(date) ===================="
