#!/bin/bash
#SBATCH --job-name=pv_cd_pctl
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH -t 4:00:00
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err
# Runs ONLY the final section of PatentView/notebook/patent_disruption.ipynb (cohort percentiles of CD),
# which reads the finished patent_disruption.parquet and appends CD_*_pctl. FROM = its code-cell index.
#   cd "/project/jevans/Dawoon/Science of Science/jobs/PatentView" && sbatch cd_percentile.sbatch
: "${FROM:=7}"
BASE="/project/jevans/Dawoon/Science of Science"
cd "$BASE/PatentView/notebook" || exit 2
source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh
conda activate /project/jevans/Dawoon/env/Curvature || exit 2
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}
set -euo pipefail
export PYTHONUNBUFFERED=1 MPLBACKEND=Agg
echo "==================== patent_disruption cohort percentiles START $(date) ===================="
srun python "$BASE/run_notebook.py" patent_disruption.ipynb --from "$FROM" --save-outputs
echo "==================== DONE $(date) ===================="
