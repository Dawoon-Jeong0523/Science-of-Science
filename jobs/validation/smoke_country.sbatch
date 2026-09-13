#!/bin/bash
#SBATCH --job-name=val_smoke_country
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=250G
#SBATCH -t 4:00:00
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err

# Smoke-run the two country validation notebooks against a SMALL base table, with the figures
# redirected to a scratch directory, so every query and plot is proven before a real run
# overwrites validation/Figures/. The inventor notebook has no sampling hook -- it is 8.5M rows
# and runs in full here, which is the point: its smoke run IS a real run apart from the figures.
set -uo pipefail
BASE="/project/jevans/Dawoon/Science of Science"
S="${NB_SCRATCH:?NB_SCRATCH must be set (scratch dir for the sampled base and the figures)}"

cd "$BASE/validation" || exit 2
source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh
conda activate /project/jevans/Dawoon/env/Curvature || exit 2
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}
export PYTHONUNBUFFERED=1 MPLBACKEND=Agg

echo "==================== smoke START $(date) on $(hostname) ===================="
rm -f "$S/smoke_base.parquet"

echo "---------- author_country_validation (base limited to ${NB_BASE_LIMIT:-400000} papers) ----------"
NB_BASE_FP="$S/smoke_base.parquet" NB_BASE_LIMIT="${NB_BASE_LIMIT:-400000}" \
  python "$S/smoke_val.py" author_country_validation.ipynb "$S/figs_author"
A=$?

echo "---------- inventor_country_validation (full 8.5M patents, sampled paper side) ----------"
NB_BASE_FP="$S/smoke_base.parquet" \
  python "$S/smoke_val.py" inventor_country_validation.ipynb "$S/figs_inventor"
I=$?

echo "==================== smoke DONE $(date)  author=$A inventor=$I ===================="
exit $(( A || I ))
