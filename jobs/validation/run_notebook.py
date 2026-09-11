#!/usr/bin/env python3
"""Execute a Jupyter notebook's code cells in order, as a plain script.

Why not `jupyter nbconvert --execute`: this run emits ~1M tqdm updates, and nbconvert
stores every one of them back into the .ipynb. Executing the cells directly keeps the
notebook as the single source of truth while sending all output to the SLURM log.

    python run_notebook.py <notebook.ipynb> [--from N] [--to N] [--list]

Cell numbers are code-cell indices (0-based) as printed by --list; markdown is skipped.
"""
import argparse, json, sys, time, traceback


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("notebook")
    ap.add_argument("--from", dest="start", type=int, default=0)
    ap.add_argument("--to", dest="end", type=int, default=10**6)
    ap.add_argument("--list", action="store_true", help="list code cells and exit")
    a = ap.parse_args()

    nb = json.load(open(a.notebook))

    def strip_magics(src):
        """Drop IPython magics: they are a SyntaxError to `exec`.

        `%%time` at the top of a cell and `%matplotlib inline` are the two that appear here.
        A kernel understands them; a plain interpreter does not, and the cell dies on line 1
        before any of the work in it runs."""
        out = []
        for line in src.splitlines():
            t = line.lstrip()
            if t.startswith(("%%", "%", "!")) and not t.startswith("%%%"):
                continue
            out.append(line)
        return "\n".join(out)

    cells = [strip_magics(''.join(c["source"])) for c in nb["cells"]
             if c["cell_type"] == "code"]
    cells = [c for c in cells if c.strip()]

    if a.list:
        for i, src in enumerate(cells):
            print(f"[{i}] {src.splitlines()[0][:100]}")
        return 0

    # A notebook kernel provides display(); a plain interpreter does not.
    import builtins
    if not hasattr(builtins, "display"):
        builtins.display = print

    g = {"__name__": "__main__", "__file__": a.notebook}
    t0 = time.time()
    for i, src in enumerate(cells):
        if not (a.start <= i <= a.end):
            continue
        head = src.splitlines()[0][:90]
        print(f"\n{'=' * 78}\n[cell {i}] {head}\n{'=' * 78}", flush=True)
        try:
            exec(compile(src, f"<cell {i}>", "exec"), g)
        except Exception:
            print(f"\n[FAILED] cell {i} after {time.time() - t0:.0f}s", flush=True)
            traceback.print_exc()
            return 1
    print(f"\nALL CELLS OK in {time.time() - t0:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
