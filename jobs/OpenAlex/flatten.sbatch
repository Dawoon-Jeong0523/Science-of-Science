#!/bin/bash
#SBATCH -p jevans -A pi-jevans --qos=jevans
#SBATCH -N 1 -n 1 --cpus-per-task=16 --mem=160G -t 4:00:00
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err
# Flatten the official OpenAlex parquet snapshot into the notebooks' table layout (OpenAlex/flatten_snapshot.py).
#   sbatch -J oa_flatten_<k> --export=ALL,CMD="parts <k> 4 16" flatten.sbatch     # one shard per jevans node
#   sbatch -J oa_flatten_lookups --export=ALL,CMD=lookups flatten.sbatch
#   sbatch -J oa_flatten_verify  --export=ALL,CMD=verify  flatten.sbatch
: "${CMD:?CMD must be set}"
set -euo pipefail
unset VIRTUAL_ENV
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib:${LD_LIBRARY_PATH:-}
export PYTHONUNBUFFERED=1
cd "/project/jevans/Dawoon/Science of Science/OpenAlex"
echo "==================== flatten $CMD START $(date) on $(hostname) ===================="
/project/jevans/Dawoon/env/Curvature/bin/python flatten_snapshot.py $CMD
echo "==================== flatten $CMD DONE  $(date) ===================="
