#!/bin/bash
#SBATCH -J oa-works.                    # Job name
#SBATCH -p jevans                       # Lab CPU partition
#SBATCH --account=pi-jevans             # Project account
#SBATCH -N 1                            # One node
#SBATCH --cpus-per-task=4               # CPU cores
#SBATCH --mem=200G                      # Memory
#SBATCH -t 48:00:00                     # Walltime (adjust if needed)
#SBATCH -o logs/%x-%j.out               # STDOUT log
#SBATCH -e logs/%x-%j.err               # STDERR log

module load python

# If you use conda, uncomment and edit the following lines:
source /project/jevans/Dawoon/env/miniforge3/etc/profile.d/conda.sh

# Activate the exact Conda env (prefix)
conda activate /project/jevans/Dawoon/env/GSMArena \
  || { echo "[ERROR] Conda env not found at /project/jevans/Dawoon/env/GSMArena"; exit 2; }

cd /project/jevans/Dawoon/OpenAlex

python Works_oa.py
