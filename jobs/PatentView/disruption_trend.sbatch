#!/bin/bash
#SBATCH --job-name=pv_patent_disruption_trend
#SBATCH -p jevans                     # lab CPU partition: 4 nodes, 48 cores, 1.5-2 TB each
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=16            # the numba kernel is prange over focal patents
#SBATCH --mem=150G                    # 119M-edge graph + per-window table + per-batch buffers
#SBATCH -t 06:00:00                   # raw scan ~10 min; the kernel is far cheaper than patent_disruption's 1.9 h
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err

# Run PatentView/notebook/patent_disruption_trend.ipynb and write its cell outputs back into
# the notebook. Submit from jobs/PatentView so the logs land in its logs/.
#   sbatch disruption_trend.sbatch

BASE="/project/jevans/Dawoon/Science of Science"
cd "$BASE" || { echo "[ERROR] cannot cd $BASE"; exit 2; }

source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh
conda activate /project/jevans/Dawoon/env/Curvature || { echo "[ERROR] conda env not found"; exit 2; }
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}

set -euo pipefail
export PYTHONUNBUFFERED=1
export MPLBACKEND=Agg

echo "==================== patent_disruption_trend START $(date) ===================="
echo "node    : $(hostname)   cpus $SLURM_CPUS_PER_TASK   mem ${SLURM_MEM_PER_NODE:-?}MB"
free -g | head -2

# --save-outputs is safe here: the notebook prints one line per batch (~9) and three tables.
srun python run_notebook.py PatentView/notebook/patent_disruption_trend.ipynb --save-outputs

echo "==================== patent_disruption_trend DONE  $(date) ===================="
