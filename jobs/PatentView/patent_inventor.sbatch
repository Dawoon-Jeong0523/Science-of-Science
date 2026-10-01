#!/bin/bash
#SBATCH --job-name=pv_patent_inventor
#SBATCH -p jevans                     # lab CPU partition: 4 nodes, 48 cores, 1.5-2 TB each
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=100G                    # pandas holds 24M inventor rows as Python strings (~10 GB); the rest is headroom
#SBATCH -t 02:00:00                   # patent_inventor_country reads the same file plus the assignees in 6 min
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err

# Run PatentView/notebook/patent_inventor.ipynb and write its cell outputs back into the
# notebook. Submit from jobs/PatentView so the logs land in its logs/. The chain
# (submit_patentview.sh, step 12) runs the same notebook through nb.sbatch, without --save-outputs.
#   cd "/project/jevans/Dawoon/Science of Science/jobs/PatentView" && sbatch patent_inventor.sbatch

BASE="/project/jevans/Dawoon/Science of Science"
cd "$BASE" || { echo "[ERROR] cannot cd $BASE"; exit 2; }

source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh
conda activate /project/jevans/Dawoon/env/Curvature || { echo "[ERROR] conda env not found"; exit 2; }
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}

set -euo pipefail
export PYTHONUNBUFFERED=1
export MPLBACKEND=Agg

echo "==================== patent_inventor START $(date) ===================="
echo "node    : $(hostname)   cpus $SLURM_CPUS_PER_TASK   mem ${SLURM_MEM_PER_NODE:-?}MB"
echo "python  : $CONDA_PREFIX/bin/python ($("$CONDA_PREFIX/bin/python" -V 2>&1))"
free -g | head -2

# The interpreter is named by path: a login shell with another venv active exports its PATH
# into the job, and a bare `python` would then be the wrong one.
# --save-outputs is safe here: the notebook prints a few dozen lines and five small tables.
srun "$CONDA_PREFIX/bin/python" run_notebook.py PatentView/notebook/patent_inventor.ipynb --save-outputs

echo "==================== patent_inventor DONE  $(date) ===================="
