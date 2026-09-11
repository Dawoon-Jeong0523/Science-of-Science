#!/usr/bin/env python3
"""Run a validation notebook and write its outputs back into the .ipynb.

Why this exists alongside run_notebook.py
-----------------------------------------
run_notebook.py execs the cells as a plain script and deliberately throws the outputs away:
the OpenAlex notebooks it was written for emit ~1M tqdm updates, and storing those back would
bloat the .ipynb beyond use. The cost of that choice is that a validation notebook's numbers
live only in a SLURM log, so opening the .ipynb shows whatever was last run interactively --
which is how a stale 110,254 from a local Windows run survived long enough to be mistaken for
a current result.

None of the four validation notebooks uses tqdm, so that cost buys nothing here. This runs
them on a real kernel instead, which also means %%time and %matplotlib inline work as written
and the figures land inline in the file.

The output cap below is insurance, not a fix for tqdm: it keeps one runaway loop from
bloating the notebook if a progress bar is ever added.

    python execute_inplace.py <notebook.ipynb>
"""
import os, sys, nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

MAX_STREAM_CHARS = 200_000   # per stream output
MAX_OUTPUTS_PER_CELL = 200

def trim(nb):
    """Cap runaway output so the .ipynb stays a readable record."""
    for c in nb.cells:
        if c.get("cell_type") != "code":
            continue
        outs = c.get("outputs", [])
        for o in outs:
            if o.get("output_type") == "stream":
                t = o.get("text", "")
                if isinstance(t, list):
                    t = "".join(t)
                if len(t) > MAX_STREAM_CHARS:
                    head, tail = t[: MAX_STREAM_CHARS // 2], t[-MAX_STREAM_CHARS // 2 :]
                    o["text"] = f"{head}\n... [{len(t) - MAX_STREAM_CHARS:,} chars trimmed] ...\n{tail}"
        if len(outs) > MAX_OUTPUTS_PER_CELL:
            c["outputs"] = outs[:MAX_OUTPUTS_PER_CELL] + [
                nbformat.v4.new_output("stream", name="stdout",
                                       text=f"... [{len(outs) - MAX_OUTPUTS_PER_CELL} further outputs trimmed] ...")]

path = sys.argv[1]
nb = nbformat.read(path, as_version=4)
client = NotebookClient(
    nb, timeout=86400, kernel_name="python3",
    resources={"metadata": {"path": os.path.dirname(os.path.abspath(path))}})

status = 0
try:
    client.execute()
except CellExecutionError:
    # Write what did run: the traceback is then in the notebook next to the cell that
    # raised it, not only in the SLURM log.
    status = 1
finally:
    trim(nb)
    nbformat.write(nb, path)

n_code = sum(1 for c in nb.cells if c.cell_type == "code")
n_err = sum(1 for c in nb.cells if c.cell_type == "code"
            for o in c.get("outputs", []) if o.get("output_type") == "error")
n_fig = sum(1 for c in nb.cells if c.cell_type == "code"
            for o in c.get("outputs", [])
            if o.get("output_type") == "display_data" and "image/png" in o.get("data", {}))
print(f"executed {n_code} code cells, {n_err} error(s), {n_fig} inline figure(s) -> {path}")
sys.exit(1 if (n_err or status) else 0)
