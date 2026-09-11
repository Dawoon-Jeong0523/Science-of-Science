#!/bin/bash
#SBATCH --job-name=oa_verify_stream
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=250G
#SBATCH -t 8:00:00
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err
BASE="/project/jevans/Dawoon/Science of Science/OpenAlex"
cd "$BASE" || exit 2
source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh
conda activate /project/jevans/Dawoon/env/Curvature || exit 2
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:${LD_LIBRARY_PATH:-}
export PYTHONUNBUFFERED=1 MPLBACKEND=Agg
echo "==== verify_stream START $(date) ===="
srun python verify_stream.py
echo "==== verify_stream DONE  $(date) ===="
