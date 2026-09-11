#!/bin/bash
#SBATCH --job-name=case_nb
#SBATCH -p jevans                     # lab CPU partition
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=8             # numba prange in case_sb; duckdb in case_hit_probability
#SBATCH --mem=200G                    # the CD engine holds the CSR plus per-case scratch
#SBATCH -t 24:00:00                   # case_disruption is the long one; the rest are minutes
# Relative on purpose: submit from this folder so the logs land in its logs/.
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err

# Run ONE notebook of Science of Science/Case law/notebook.
#   sbatch --export=ALL,NB=case_metadata -J cl_case_metadata nb.sbatch
# submit_case_law.sh wires the dependency order; use that rather than this directly.

: "${NB:?NB must be set (the notebook name, without .ipynb)}"

BASE="/project/jevans/Dawoon/Science of Science"
NBDIR="$BASE/Case law/notebook"

cd "$NBDIR" || { echo "[ERROR] cannot cd $NBDIR"; exit 2; }

source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh
conda activate /project/jevans/Dawoon/env/Curvature \
  || { echo "[ERROR] conda env not found"; exit 2; }

# The ENV's libstdc++: /software/gcc-12.2.0-el8-x86_64/lib64 stops at CXXABI_1.3.13, which
# fixes 'import pandas' and then breaks 'import matplotlib'.
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}

set -euo pipefail
export PYTHONUNBUFFERED=1
export MPLBACKEND=Agg                 # no display on a compute node
export NUMBA_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

echo "==================== $NB START $(date) ===================="
echo "node    : $(hostname)   cpus ${SLURM_CPUS_PER_TASK:-?}   mem ${SLURM_MEM_PER_NODE:-?}MB"
echo "cwd     : $(pwd)"
echo "python  : $(python -V 2>&1)"
free -g | head -2

# --save-outputs so the results are visible in the notebook, not only in this log. Safe here:
# these notebooks print tens of lines and a few small tables, none of the tqdm flood
# run_notebook.py warns about (case_disruption's bar is throttled to mininterval=10).
srun python "$BASE/run_notebook.py" "$NB.ipynb" --save-outputs

echo "==================== $NB DONE  $(date) ===================="
