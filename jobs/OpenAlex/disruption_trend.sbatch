#!/bin/bash
#SBATCH --job-name=oa_paper_disruption_trend
#SBATCH -p jevans                     # lab CPU partition: 4 nodes, 48 cores, 1.5-2 TB each
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=32            # the numba kernel is prange over focal papers
#SBATCH --mem=400G                    # CSR ~24 GB + per-window table 39 GB for the exhaustive check + batch buffers
#SBATCH -t 12:00:00                   # paper_disruption took 7 h on 8 cores; this kernel does less per focal
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err

# Run OpenAlex/notebook/paper_disruption_trend.ipynb and write its cell outputs back into the
# notebook. Submit from jobs/OpenAlex so the logs land in its logs/.
#   sbatch disruption_trend.sbatch

BASE="/project/jevans/Dawoon/Science of Science"
cd "$BASE" || { echo "[ERROR] cannot cd $BASE"; exit 2; }

source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh
conda activate /project/jevans/Dawoon/env/Curvature || { echo "[ERROR] conda env not found"; exit 2; }
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}

set -euo pipefail
export PYTHONUNBUFFERED=1
export MPLBACKEND=Agg

echo "==================== paper_disruption_trend START $(date) ===================="
echo "node    : $(hostname)   cpus $SLURM_CPUS_PER_TASK   mem ${SLURM_MEM_PER_NODE:-?}MB"
free -g | head -2

# --save-outputs is safe here: the notebook prints one line per batch (~45) and three tables.
srun python run_notebook.py OpenAlex/notebook/paper_disruption_trend.ipynb --save-outputs

echo "==================== paper_disruption_trend DONE  $(date) ===================="
