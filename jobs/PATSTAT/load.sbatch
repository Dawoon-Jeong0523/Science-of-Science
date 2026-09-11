#!/bin/bash
#SBATCH --job-name=patstat_load
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH -t 12:00:00
#SBATCH --array=0-20
#SBATCH -o logs/%x-%A_%a.out
#SBATCH -e logs/%x-%A_%a.err

# Stage 0 of Science of Science/PATSTAT: one zip part of the dump -> one zstd parquet under
# PATSTAT/raw/<tls>/. The array index selects the (table, part) from ps_common.load_jobs()
# (21 parts over the 11 registered tables; `python -c 'import ps_common as ps; print(ps.load_jobs())'`).
#
#   cd jobs/PATSTAT && sbatch load.sbatch            # everything not yet loaded
#   sbatch --array=13-15 load.sbatch                 # just tls212
#   sbatch --export=ALL,FORCE=1 --array=0 load.sbatch # rewrite a part
#
# A part already present is skipped, so re-submitting the whole array after a failure is safe.

BASE="/project/jevans/Dawoon/Science of Science"
cd "$BASE/PATSTAT" || exit 2

source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh
conda activate /project/jevans/Dawoon/env/Curvature || { echo "[ERROR] conda env not found"; exit 2; }
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}
set -euo pipefail
export PYTHONUNBUFFERED=1

echo "==== load task ${SLURM_ARRAY_TASK_ID} on $(hostname)  $(date)"
srun python - <<EOF
import os, sys
import ps_common as ps
jobs = ps.load_jobs()
i = int(os.environ['SLURM_ARRAY_TASK_ID'])
tls, part = jobs[i]
print(f'task {i}: {tls}  {os.path.basename(part)}  ({os.path.getsize(part)/1e9:.2f} GB zip)')
ps.load_table(tls, part, force=bool(os.environ.get('FORCE')))
EOF
echo "==== done  $(date)"
