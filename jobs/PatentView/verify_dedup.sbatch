#!/bin/bash
#SBATCH --job-name=pv_verify_dedup
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=250G
#SBATCH -t 4:00:00
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err

# Checks the regenerated patent_disruption.parquet: CD back inside [-1,1], exact agreement
# with patent_disruption_app.parquet where the two networks are provably the same graph, and
# what moved against the pre-dedup table. Submit with a dependency on the notebook job:
#   sbatch --dependency=afterok:<jobid> verify_dedup.sbatch

BASE="/project/jevans/Dawoon/Science of Science"
JOBDIR="$BASE/jobs/PatentView"
cd "$JOBDIR" || exit 2

source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh
conda activate /project/jevans/Dawoon/env/Curvature || { echo "[ERROR] conda env"; exit 2; }
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}
export PYTHONUNBUFFERED=1 MPLBACKEND=Agg

echo "==================== verify_dedup START $(date) ===================="
echo "node: $(hostname)"
srun python "$JOBDIR/verify_dedup.py"
rc=$?
echo "==================== verify_dedup DONE  $(date)  rc=$rc ===================="
exit $rc
