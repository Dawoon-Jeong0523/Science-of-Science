#!/bin/bash
#SBATCH --job-name=oa_build_caches
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=250G                    # graph build peaked ~100 GB, CSR build ~165 GB (2026-08-29)
#SBATCH -t 12:00:00
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err
# Build cache/paper_graph.npz and cache/paper_csr.npz from output/referenced_works_w_year in one job, so the
# notebooks that read them (paper_citation, paper_disruption, paper_z_score x 14, ...) can start together
# without racing to build the same file.
set -euo pipefail
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib:${LD_LIBRARY_PATH:-}
export PYTHONUNBUFFERED=1 NB_WORKERS=${SLURM_CPUS_PER_TASK:-8}
echo "==================== build_caches START $(date) on $(hostname) ===================="
srun /project/jevans/Dawoon/env/Curvature/bin/python -c "
import sys; sys.path.insert(0, '/project/jevans/Dawoon/Science of Science/OpenAlex')
import oa_common as oa
oa.build_graph(); oa.build_csr()"
echo "==================== build_caches DONE  $(date) ===================="
