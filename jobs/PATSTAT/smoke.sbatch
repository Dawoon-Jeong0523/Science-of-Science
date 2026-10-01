#!/bin/bash
#SBATCH --job-name=ps_smoke
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=16
#SBATCH --mem=300G
#SBATCH -t 08:00:00
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err
# Smoke test of the whole PATSTAT chain, in dependency order, on a 1/NB_PS_SAMPLE sample of the
# universe (appln_id % k = 0), into a scratch base; raw/ is the real one, so every raw scan is
# full-size. Stops at the first failing notebook. Outputs are NOT saved into the .ipynb files.
#   cd jobs/PATSTAT && sbatch smoke.sbatch            (NB_PS_SAMPLE=20, base PATSTAT/cache/smoke)
#   sbatch --export=ALL,NB_PS_CLOCK=grant smoke.sbatch   (the grant clock; outputs under the smoke base's output_grant/)
#   sbatch --export=ALL,NB_PS_UNIT=family smoke.sbatch   (the family unit; outputs under the smoke base's output_family/)
BASE="/project/jevans/Dawoon/Science of Science"
NBDIR="$BASE/PATSTAT/notebook"
JOBDIR="$BASE/jobs/PATSTAT"
export NB_PS_BASE="${NB_PS_BASE:-$BASE/PATSTAT/cache/smoke}"
export NB_PS_SAMPLE="${NB_PS_SAMPLE:-20}"
mkdir -p "$NB_PS_BASE"
cd "$NBDIR" || exit 2
source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh
conda activate /project/jevans/Dawoon/env/Curvature || exit 2
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}
set -euo pipefail
export PYTHONUNBUFFERED=1 MPLBACKEND=Agg
export NB_WORKERS=${SLURM_CPUS_PER_TASK:-8}
export NUMBA_NUM_THREADS=$NB_WORKERS
echo "smoke base $NB_PS_BASE   sample 1/$NB_PS_SAMPLE   clock ${NB_PS_CLOCK:-filing}   unit ${NB_PS_UNIT:-application}   node $(hostname)"
for NB in patstat_reference patstat_metadata patstat_citation patstat_citation_trend patstat_uniqueC_trend \
          patstat_hit_probability patstat_disruption patstat_feg_disruption_trend patstat_disruption_trend \
          patstat_sb patstat_z_score patstat_inventor patstat_inventor_country; do
  export NB
  echo "==================== $NB START $(date +%T) ===================="
  t0=$(date +%s)
  python "$JOBDIR/run_notebook.py" "$NB.ipynb"
  echo "==================== $NB DONE  $(( $(date +%s) - t0 ))s ===================="
done
echo "SMOKE CHAIN OK"
