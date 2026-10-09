#!/bin/bash
#SBATCH --job-name=oa_compare_selfcite
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=16
#SBATCH --mem=250G
#SBATCH -t 8:00:00
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err
# Before / after the 2026-10-03 self-citation fix; see compare_selfcite.py.
set -euo pipefail
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib:${LD_LIBRARY_PATH:-}
export PYTHONUNBUFFERED=1 NB_DUCKDB_MEM=200GB
mkdir -p "/project/jevans/Dawoon/Science of Science/.duckdb_tmp/compare_selfcite"
echo "==================== compare_selfcite START $(date) on $(hostname) ===================="
srun /project/jevans/Dawoon/env/Curvature/bin/python compare_selfcite.py
echo "==================== compare_selfcite DONE  $(date) ===================="
