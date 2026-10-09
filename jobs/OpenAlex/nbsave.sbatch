#!/bin/bash
#SBATCH --job-name=sos_nb
#SBATCH -p jevans
#SBATCH -A pi-jevans
#SBATCH --qos=jevans
#SBATCH -N 1 -n 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=250G
#SBATCH -t 24:00:00
#SBATCH -o logs/%x-%j.out
#SBATCH -e logs/%x-%j.err
# Run one notebook with the root runner, from the notebook's own folder.
#   sbatch --export=ALL,NBPATH=OpenAlex/notebook/paper_sb.ipynb,SAVE=1 -J oa_paper_sb nbsave.sbatch
# NBPATH is relative to the Science of Science root. SAVE=1 writes the outputs back into the notebook; leave it
# unset for a notebook run several times at once (the paper_z_score year ranges). The Curvature interpreter is
# called by path, since hkg_venv can lead PATH in an --export=ALL job.
: "${NBPATH:?NBPATH must be set}"
BASE="/project/jevans/Dawoon/Science of Science"
PY=/project/jevans/Dawoon/env/Curvature/bin/python
set -euo pipefail
unset VIRTUAL_ENV
export LD_LIBRARY_PATH=/project/jevans/Dawoon/env/Curvature/lib:${LD_LIBRARY_PATH:-}
export PYTHONUNBUFFERED=1 MPLBACKEND=Agg
export NB_WORKERS=${NB_WORKERS:-$SLURM_CPUS_PER_TASK}
export NUMBA_NUM_THREADS=$SLURM_CPUS_PER_TASK
cd "$BASE/$(dirname "$NBPATH")"
echo "==================== $NBPATH START $(date) ===================="
echo "node $(hostname)   cpus $SLURM_CPUS_PER_TASK   mem ${SLURM_MEM_PER_NODE:-?}MB   $($PY -V 2>&1)   ${NB_Z_YEARS:+NB_Z_YEARS=$NB_Z_YEARS}"
srun $PY "$BASE/run_notebook.py" "$(basename "$NBPATH")" ${SAVE:+--save-outputs}
echo "==================== $NBPATH DONE  $(date) ===================="
