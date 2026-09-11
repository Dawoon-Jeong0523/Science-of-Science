#!/bin/bash
#SBATCH --job-name=dimensions_nb
#SBATCH -p jevans                     # lab CPU partition: 4 nodes, 48 cores, 1.5-2 TB each
#SBATCH -A pi-jevans
#SBATCH --qos=jevans                  # the partition allows only its own QOS
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=250G                    # graph/CSR passes peak well under this; headroom is free here
#SBATCH -t 48:00:00
# Relative on purpose: submit from this folder so the logs land in its logs/.
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err

# Run ONE notebook of Science of Science/Dimensions/notebook.
#   sbatch --export=ALL,NB=paper_metadata -J dim_paper_metadata nb.sbatch
# submit_dimensions.sh wires the dependency order; use that rather than this directly.
#
# Knobs (all optional, passed through --export=ALL):
#   NB_DIM_BASE    redirect cache/ and output/ (smoke tests)
#   NB_FILE_LIMIT  read a strided sample of this many dump files (smoke tests)
#   NB_WORKERS     processes for the per-file passes (default 8 = --cpus-per-task)
#   NB_Z_MODE / NB_Z_YEARS  paper_z_score's year range (see that notebook's header)

: "${NB:?NB must be set (the notebook name, without .ipynb)}"

BASE="/project/jevans/Dawoon/Science of Science"
NBDIR="$BASE/Dimensions/notebook"
JOBDIR="$BASE/jobs/Dimensions"

cd "$NBDIR" || { echo "[ERROR] cannot cd $NBDIR"; exit 2; }

source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh
conda activate /project/jevans/Dawoon/env/Curvature \
  || { echo "[ERROR] conda env not found"; exit 2; }

# The ENV's libstdc++. /software/gcc-12.2.0-el8-x86_64/lib64 stops at CXXABI_1.3.13, which
# fixes 'import pandas' and then breaks 'import matplotlib'.
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}

set -euo pipefail
export PYTHONUNBUFFERED=1
export MPLBACKEND=Agg                 # no display on a compute node
export NB_WORKERS=${NB_WORKERS:-${SLURM_CPUS_PER_TASK:-8}}

echo "==================== $NB START $(date) ===================="
echo "node    : $(hostname)   cpus $SLURM_CPUS_PER_TASK   mem ${SLURM_MEM_PER_NODE:-?}MB"
echo "cwd     : $(pwd)"
echo "python  : $(python -V 2>&1)"
echo "base    : ${NB_DIM_BASE:-<default>}   file limit: ${NB_FILE_LIMIT:-<all>}"
free -g | head -2

srun python "$JOBDIR/run_notebook.py" "$NB.ipynb" --save-outputs

echo "==================== $NB DONE  $(date) ===================="
