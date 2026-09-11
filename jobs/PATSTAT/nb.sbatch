#!/bin/bash
#SBATCH --job-name=patstat_nb
#SBATCH -p jevans                     # lab CPU partition: 4 nodes, 48 cores, 1.5-2 TB each
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=16
#SBATCH --mem=400G                    # DuckDB gets 200 GB (ps.connect); the CSR + numba pass peaks well under this
#SBATCH -t 48:00:00
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err

# Run ONE notebook of Science of Science/PATSTAT/notebook.
#   sbatch --export=ALL,NB=patstat_reference -J ps_patstat_reference nb.sbatch
# submit_patstat.sh wires the dependency order; use that rather than this directly.
#
# Knobs (optional, via --export=ALL):
#   NB_DUCKDB_MEM   DuckDB memory_limit (default 200GB)
#   NB_WORKERS      DuckDB / numba threads (default = --cpus-per-task)

: "${NB:?NB must be set (the notebook name, without .ipynb)}"

BASE="/project/jevans/Dawoon/Science of Science"
NBDIR="$BASE/PATSTAT/notebook"
JOBDIR="$BASE/jobs/PATSTAT"

cd "$NBDIR" || { echo "[ERROR] cannot cd $NBDIR"; exit 2; }

source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh
conda activate /project/jevans/Dawoon/env/Curvature \
  || { echo "[ERROR] conda env not found"; exit 2; }
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}

set -euo pipefail
export PYTHONUNBUFFERED=1
export MPLBACKEND=Agg
export NB_WORKERS=${NB_WORKERS:-${SLURM_CPUS_PER_TASK:-8}}
export NUMBA_NUM_THREADS=$NB_WORKERS

echo "==================== $NB START $(date) ===================="
echo "node    : $(hostname)   cpus $SLURM_CPUS_PER_TASK   mem ${SLURM_MEM_PER_NODE:-?}MB"
echo "python  : $(python -V 2>&1)"
free -g | head -2

srun python "$JOBDIR/run_notebook.py" "$NB.ipynb" --save-outputs

echo "==================== $NB DONE  $(date) ===================="
