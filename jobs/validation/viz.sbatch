#!/bin/bash
#SBATCH --job-name=val_viz
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=400G
#SBATCH -t 12:00:00
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err
cd "/project/jevans/Dawoon/Science of Science/jobs/validation" || exit 2
source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh
conda activate /project/jevans/Dawoon/env/Curvature || exit 2
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}
export PYTHONUNBUFFERED=1 MPLBACKEND=Agg
S=/home/jdwoon0523/claude-30299883/-project-jevans-Dawoon/d2360fc7-c732-453c-aedc-f89f419ee9c0/scratchpad
echo "==== val_viz START $(date) on $(hostname) ===="
for T in tmp_pat_viz tmp_pap_viz; do
  echo "---- $T ----"
  jupyter nbconvert --to notebook --execute --inplace \
      --ExecutePreprocessor.timeout=39600 "$S/$T.ipynb" && echo "$T OK" || echo "$T FAILED"
done
echo "==== val_viz DONE $(date) ===="
