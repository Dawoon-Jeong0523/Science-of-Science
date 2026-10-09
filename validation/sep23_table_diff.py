"""Compare every result table (CSV) written by the Atypicality notebooks before and after the 2026-10-08 OpenAlex rebuild.

The Renly-era tables were copied to Atypicality/Old/pre_sep23_2026-10-08/{Tables,Tables_rev}/ before the reruns. For every
CSV present in both places this writes one row: shape old/new, the numeric columns they share, and for those columns the
largest absolute change and the median relative change of the cell values (rows matched by position when the shapes
agree, otherwise by the table's first column when it is a key, otherwise only column means are compared).

    python sep23_table_diff.py            # -> validation/data/sep23_table_diff.csv
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

SOS = Path('/project/jevans/Dawoon/Science of Science')
A = SOS / 'Atypicality'
OLD = A / 'Old' / 'pre_sep23_2026-10-08'
OUT = SOS / 'validation' / 'data' / 'sep23_table_diff.csv'


def compare(old_fp: Path, new_fp: Path) -> dict:
    o, n = pd.read_csv(old_fp, low_memory=False), pd.read_csv(new_fp, low_memory=False)
    num = [c for c in o.columns if c in n.columns and pd.api.types.is_numeric_dtype(o[c]) and pd.api.types.is_numeric_dtype(n[c])]
    row = {'table': str(new_fp.relative_to(A)), 'rows_old': len(o), 'rows_new': len(n), 'cols_old': o.shape[1],
           'cols_new': n.shape[1], 'numeric_shared': len(num), 'match': 'none', 'max_abs_change': np.nan,
           'median_rel_change': np.nan, 'mean_shift_max_rel': np.nan, 'mtime_new': pd.Timestamp(new_fp.stat().st_mtime, unit='s')}
    if not num:
        return row
    key = o.columns[0]
    if len(o) == len(n) and (o.columns[:1].equals(n.columns[:1])) and (o[key].astype(str).values == n[key].astype(str).values).all():
        a, b = o[num].to_numpy(float), n[num].to_numpy(float); row['match'] = 'position'
    elif key in n.columns and not pd.api.types.is_float_dtype(o[key]) and o[key].is_unique and n[key].is_unique:
        j = o[[key] + num].merge(n[[key] + num], on=key, suffixes=('_o', '_n'))
        a = j[[c + '_o' for c in num]].to_numpy(float); b = j[[c + '_n' for c in num]].to_numpy(float); row['match'] = f'key {key} ({len(j)} rows)'
    else:
        a = b = None
    if a is not None and a.size:
        d = np.abs(b - a); ok = np.isfinite(d)
        if ok.any():
            row['max_abs_change'] = float(d[ok].max())
            rel = d[ok] / np.maximum(np.abs(a[ok]), 1e-12)
            row['median_rel_change'] = float(np.median(rel))
    mo, mn = o[num].mean(numeric_only=True), n[num].mean(numeric_only=True)
    rel_m = ((mn - mo).abs() / mo.abs().replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)
    row['mean_shift_max_rel'] = float(rel_m.max()) if rel_m.notna().any() else np.nan
    return row


def main() -> None:
    rows = []
    for sub in ('Tables', 'Tables_rev'):
        for old_fp in sorted((OLD / sub).rglob('*.csv')):
            new_fp = A / sub / old_fp.relative_to(OLD / sub)
            if not new_fp.exists():
                rows.append({'table': str(new_fp.relative_to(A)), 'match': 'missing in new'}); continue
            if new_fp.stat().st_mtime <= old_fp.stat().st_mtime + 1:
                rows.append({'table': str(new_fp.relative_to(A)), 'match': 'not rewritten'}); continue
            try:
                rows.append(compare(old_fp, new_fp))
            except Exception as e:                      # a malformed or binary CSV should not stop the sweep
                rows.append({'table': str(new_fp.relative_to(A)), 'match': f'error: {type(e).__name__}'})
    df = pd.DataFrame(rows)
    df.to_csv(OUT, index=False)
    print(df['match'].map(lambda m: m if m in ('not rewritten', 'missing in new', 'position', 'none') else
                          ('key' if str(m).startswith('key') else 'error' if str(m).startswith('error') else m)).value_counts().to_string())
    print(f'wrote {OUT} ({len(df)} tables)')


if __name__ == '__main__':
    main()
