#!/bin/bash
#SBATCH -J patent-reference             # Job name
#SBATCH -p jevans                       # Lab CPU partition
#SBATCH --account=pi-jevans             # Project account
#SBATCH -N 1                            # One node
#SBATCH --cpus-per-task=8               # duckdb sorts the 200M+ edge union in parallel
#SBATCH --mem=200G                      # login nodes cap the session at 8 GiB; this needs more
#SBATCH -t 08:00:00                     # measured ~40 min, headroom for a cold filesystem
#SBATCH -o logs/%x-%j.out               # STDOUT log
#SBATCH -e logs/%x-%j.err               # STDERR log

set -euo pipefail

# The Curvature env's pandas/pyarrow are built against a newer libstdc++ than /lib64 has;
# without this the first `import pandas` dies on GLIBCXX_3.4.29.
ENV=/project/jevans/Dawoon/env/Curvature
export LD_LIBRARY_PATH="$ENV/lib:${LD_LIBRARY_PATH:-}"

# Sized for the node this actually runs on, not for the 8 GiB login cap the notebook
# defaults to. Bigger chunks amortise the per-chunk hash-index probes.
export PV_CHUNK=10000000
export PV_DUCKDB_MEM=150GB

cd "/project/jevans/Dawoon/Science of Science"
# --save-outputs writes each cell's result back into the .ipynb, so opening the notebook
# shows the run instead of an empty shell. Safe here: this notebook prints a few dozen
# lines and four small tables, none of the tqdm flood run_notebook.py warns about.
"$ENV/bin/python" run_notebook.py PatentView/notebook/patent_reference.ipynb --save-outputs
