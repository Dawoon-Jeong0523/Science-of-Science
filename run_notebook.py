#!/usr/bin/env python3
"""Execute a Jupyter notebook's code cells in order, as a plain script.

Why not `jupyter nbconvert --execute`: some of these runs emit ~1M tqdm updates, and
nbconvert stores every one of them back into the .ipynb. Executing the cells directly keeps
the notebook as the single source of truth while sending all output to the SLURM log.

    python run_notebook.py <notebook.ipynb> [--from N] [--to N] [--list] [--save-outputs]

Cell numbers are code-cell indices (0-based) as printed by --list; markdown is skipped.

`--save-outputs` additionally writes each cell's output back into the .ipynb, so the results
are visible when the notebook is opened. It is opt-in precisely because of the tqdm problem
above -- and even then each cell's stream output is capped at STREAM_CAP bytes, so a runaway
progress bar cannot bloat the file. Output still streams to stdout as it always did, so the
SLURM log stays live and unchanged; the notebook is written once at the end, or after a
failure with the traceback stored in the cell that raised.
"""
import argparse, io, json, os, sys, time, traceback

STREAM_CAP = 200_000        # bytes of stdout kept per cell when --save-outputs is on


class _Tee(io.TextIOBase):
    """stdout that goes to the SLURM log *and* into a buffer for the notebook."""

    def __init__(self, real, buf):
        self.real, self.buf = real, buf

    def write(self, s):
        self.real.write(s)
        self.real.flush()
        self.buf.append(s)
        return len(s)

    def flush(self):
        self.real.flush()

    def isatty(self):
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("notebook")
    ap.add_argument("--from", dest="start", type=int, default=0)
    ap.add_argument("--to", dest="end", type=int, default=10**6)
    ap.add_argument("--list", action="store_true", help="list code cells and exit")
    ap.add_argument("--save-outputs", action="store_true",
                    help="write cell outputs back into the .ipynb")
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

    # (index into nb['cells'], stripped source) -- the notebook index is kept so
    # --save-outputs can put the outputs back on the cell they came from.
    cells = [(j, strip_magics(''.join(c["source"]))) for j, c in enumerate(nb["cells"])
             if c["cell_type"] == "code"]
    cells = [(j, s) for j, s in cells if s.strip()]

    if a.list:
        for i, (_, src) in enumerate(cells):
            print(f"[{i}] {src.splitlines()[0][:100]}")
        return 0

    real_stdout = sys.stdout
    outs, buf = [], []          # nbformat outputs for the current cell, and its pending stdout

    def flush_stream():
        if not buf:
            return
        text = ''.join(buf)
        buf.clear()
        if len(text) > STREAM_CAP:              # a runaway progress bar, most likely
            text = (text[:STREAM_CAP]
                    + f'\n... [{len(text) - STREAM_CAP:,} more bytes truncated by '
                      f'run_notebook.py --save-outputs]\n')
        outs.append({'output_type': 'stream', 'name': 'stdout', 'text': text})

    # A notebook kernel provides display(); a plain interpreter does not. Without
    # --save-outputs this is print, exactly as before. With it, the rich repr is stored for
    # the notebook and the plain one still goes to the log -- via real_stdout, so the same
    # table is not recorded twice.
    def display(*objs):
        for o in objs:
            flush_stream()
            data = {'text/plain': repr(o)}
            html = getattr(o, '_repr_html_', None)
            if callable(html):
                try:
                    data['text/html'] = html()
                except Exception:
                    pass
            outs.append({'output_type': 'display_data', 'data': data, 'metadata': {}})
            print(o, file=real_stdout, flush=True)

    import builtins
    if not hasattr(builtins, "display"):
        builtins.display = display if a.save_outputs else print

    def save():
        """Write the notebook back atomically, so an interrupted write cannot truncate it."""
        tmp = a.notebook + '.tmp'
        with open(tmp, 'w') as fh:
            json.dump(nb, fh, indent=1, ensure_ascii=False)
            fh.write('\n')
        os.replace(tmp, a.notebook)
        print(f'[run_notebook] outputs written into {a.notebook}', file=real_stdout, flush=True)

    g = {"__name__": "__main__", "__file__": a.notebook}
    t0 = time.time()
    for i, (j, src) in enumerate(cells):
        if not (a.start <= i <= a.end):
            continue
        head = src.splitlines()[0][:90]
        print(f"\n{'=' * 78}\n[cell {i}] {head}\n{'=' * 78}", flush=True)
        outs, buf = [], []
        if a.save_outputs:
            sys.stdout = _Tee(real_stdout, buf)
        try:
            exec(compile(src, f"<cell {i}>", "exec"), g)
        except Exception:
            sys.stdout = real_stdout
            print(f"\n[FAILED] cell {i} after {time.time() - t0:.0f}s", flush=True)
            traceback.print_exc()
            if a.save_outputs:
                flush_stream()
                outs.append({'output_type': 'error', 'ename': sys.exc_info()[0].__name__,
                             'evalue': str(sys.exc_info()[1]),
                             'traceback': traceback.format_exc().splitlines()})
                nb['cells'][j]['outputs'] = outs
                nb['cells'][j]['execution_count'] = i + 1
                save()          # keep what ran, and the traceback, on the failing cell
            return 1
        finally:
            sys.stdout = real_stdout
        if a.save_outputs:
            flush_stream()
            nb['cells'][j]['outputs'] = outs
            nb['cells'][j]['execution_count'] = i + 1
    print(f"\nALL CELLS OK in {time.time() - t0:.0f}s", flush=True)
    if a.save_outputs:
        save()
    return 0


if __name__ == "__main__":
    sys.exit(main())
