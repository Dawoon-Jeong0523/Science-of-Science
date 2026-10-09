#!/bin/bash
#SBATCH --job-name=oa_build_journal_fos
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=32
#SBATCH --mem=250G
#SBATCH -t 6:00:00
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err
# Build cache/paper_fos.parquet (works/topics x topics.csv.gz) and cache/paper_journal.parquet (from the work map) (works/topics x topics.csv.gz)
# once, before the notebooks that read them start: on an empty cache several of them would otherwise race to write
# the same file. Run after referenced_works_w_year (the journal map reads its work_year_source_map.npz).
set -euo pipefail
unset VIRTUAL_ENV
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib:${LD_LIBRARY_PATH:-}
export PYTHONUNBUFFERED=1 NB_WORKERS=$SLURM_CPUS_PER_TASK
echo "==================== build_journal_fos START $(date) on $(hostname) ===================="
srun /project/jevans/Dawoon/env/Curvature/bin/python -c "
import sys; sys.path.insert(0, '/project/jevans/Dawoon/Science of Science/OpenAlex')
import oa_common as oa
oa.build_fos(); oa.build_journal()"   # FoS first: its worker pool forks before the parent has written any parquet
echo "==================== build_journal_fos DONE  $(date) ===================="
