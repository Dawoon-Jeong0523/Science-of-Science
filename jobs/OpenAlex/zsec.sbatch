#!/bin/bash
#SBATCH --job-name=oa_zsec9
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=250G
#SBATCH -t 8:00:00
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err
cd "/project/jevans/Dawoon/Science of Science/jobs/OpenAlex" || exit 2
source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh
conda activate /project/jevans/Dawoon/env/Curvature || exit 2
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}
export PYTHONUNBUFFERED=1 MPLBACKEND=Agg
T=/home/jdwoon0523/claude-30299883/-project-jevans-Dawoon/d2360fc7-c732-453c-aedc-f89f419ee9c0/scratchpad/tmp_z.ipynb
echo "==== zsec9 START $(date) on $(hostname) ===="
srun jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=25200 "$T"
echo "==== zsec9 DONE $(date) rc=$? ===="
