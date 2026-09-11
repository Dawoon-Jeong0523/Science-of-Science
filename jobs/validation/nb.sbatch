#!/bin/bash
#SBATCH --job-name=openalex_nb
#SBATCH -p jevans                     # lab CPU partition: 4 nodes, 48 cores, 1.5-2 TB each
#SBATCH -A pi-jevans
#SBATCH --qos=jevans                  # the partition allows only its own QOS
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=250G                    # the graph/CSR passes peak near 50 GB; headroom is free here
#SBATCH -t 48:00:00
# Relative on purpose: submit from this folder so the logs land in its logs/.
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err

# Run ONE notebook of Science of Science/validation.
#   sbatch --export=ALL,NB=<notebook> -J val_<notebook> nb.sbatch
# (none) wires the dependency order; use that rather than this directly.

: "${NB:?NB must be set (the notebook name, without .ipynb)}"

BASE="/project/jevans/Dawoon/Science of Science"
NBDIR="$BASE/validation"
JOBDIR="$BASE/jobs/validation"

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
export TOKENIZERS_PARALLELISM=false
export HF_HOME=/project/jevans/Dawoon/.cache/huggingface

echo "==================== $NB START $(date) ===================="
echo "node    : $(hostname)   cpus $SLURM_CPUS_PER_TASK   mem ${SLURM_MEM_PER_NODE:-?}MB"
echo "cwd     : $(pwd)"
echo "python  : $(python -V 2>&1)"
free -g | head -2

# execute_inplace.py runs the notebook on a real kernel and writes the outputs back, so
# the .ipynb is a current record rather than a script whose numbers live in a log.
# Set NB_EXEC=run_notebook.py to fall back to the exec-as-script runner that keeps the
# file unchanged (wanted only if a notebook here ever grows a tqdm loop).
srun python "$JOBDIR/${NB_EXEC:-execute_inplace.py}" "$NB.ipynb"

echo "==================== $NB DONE  $(date) ===================="
