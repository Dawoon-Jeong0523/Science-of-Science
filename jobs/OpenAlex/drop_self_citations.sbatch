#!/bin/bash
#SBATCH --job-name=oa_drop_selfcite
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G                     # one ~16 MB part (~1.3M rows) in memory at a time
#SBATCH -t 4:00:00
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err
# One-off (2026-10-03): drop self-citation rows from output/referenced_works_w_year, see drop_self_citations.py.
# The Curvature interpreter is called by path: hkg_venv can lead PATH in an --export=ALL job.
set -euo pipefail
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib:${LD_LIBRARY_PATH:-}
export PYTHONUNBUFFERED=1
echo "==================== drop_self_citations START $(date) on $(hostname) ===================="
srun /project/jevans/Dawoon/env/Curvature/bin/python drop_self_citations.py
echo "==================== drop_self_citations DONE  $(date) ===================="
