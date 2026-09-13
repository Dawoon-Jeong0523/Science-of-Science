"""Paths and figure output for the four validation notebooks, on Midway.

The notebooks were written against a Windows layout: a `for _ in range(6): os.chdir('..')`
hunt for a marker directory, then `notebook/<side>/output`. None of that exists here, and the
chdir hunt is actively harmful -- it walks up from wherever the kernel happens to start and
silently settles somewhere arbitrary, so the same notebook reads different files depending on
where it was launched. This module replaces all of it with absolute paths.

    import val_common as V
    V.init('paper_validation')       # names the figures, makes Figures/
    V.preflight()                    # what is present, what is missing
    df = pd.read_parquet(V.paper('paper_metadata.parquet'))
    ...plot...
    V.save('3b')                     # -> Figures/paper_validation_3b.jpg and .pdf at 600 dpi

Figure naming is `<notebook stem>_<section>.{jpg,pdf}`, where <section> is the number of the
markdown heading the plot sits under (`## 3b. Atypicality ...` -> `3b`). A cell that draws
more than one figure gets `-1`, `-2` appended.
"""
from __future__ import annotations

import os

BASE = "/project/jevans/Dawoon/Science of Science"
VAL  = f"{BASE}/validation"
FIG  = f"{VAL}/Figures"

# Where each upstream pipeline writes. These are the notebook/<side>/output directories of
# the Windows layout, relocated.
OA_BASE = f"{BASE}/OpenAlex"
OA_OUT  = f"{OA_BASE}/output"           # was notebook/paper/output
PV_OUT  = f"{BASE}/PatentView/output"    # was notebook/patent/output
PCS_OUT = f"{BASE}/pcs/output"           # was notebook/pcs/output
PPP_OUT = f"{BASE}/PPP/output"           # was notebook/PPP/output
CL_OUT  = f"{BASE}/Case law/output"       # Case law metrics (case_* notebooks)
DIM_OUT = f"{BASE}/Dimensions/output"     # the same paper metrics on the Dimensions June 2025 index

# duckdb spills here when a query exceeds memory_limit. Was 'E:/duckdb_tmp'.
TMP = f"{BASE}/.duckdb_tmp"

# SciSciNet's own per-paper metrics, for the §2 team size and the §3b / §3c comparisons.
# 249,803,279 rows; `paperid` is already the 'W…' form, so it joins our paper_id directly.
SCISCINET_FOS = f"{OA_BASE}/sciscinet_papers_fos_feg.parquet"

# Country boundaries for the world maps of the two *_country_validation notebooks. Natural
# Earth 1:50m Admin 0, public domain, trimmed and simplified; provenance in the .source.json
# beside it. Checked in, because geopandas 1.0 removed its bundled naturalearth_lowres and a
# compute node cannot be assumed to reach the internet.
WORLD_GEOJSON = f"{VAL}/data/world_countries.geojson"

DPI = 600          # raster resolution for .jpg, and for rasterised elements inside .pdf

for _d in (FIG, TMP):
    os.makedirs(_d, exist_ok=True)

_NB: str | None = None
_SEEN: dict[str, int] = {}


def paper(name: str) -> str:
    return f"{OA_OUT}/{name}"


def patent(name: str) -> str:
    return f"{PV_OUT}/{name}"


def pcs(name: str) -> str:
    return f"{PCS_OUT}/{name}"


def ppp(name: str) -> str:
    return f"{PPP_OUT}/{name}"


def case(name: str) -> str:
    return f"{CL_OUT}/{name}"


def dim(name: str) -> str:
    return f"{DIM_OUT}/{name}"


def init(notebook: str) -> None:
    """Name the figures this notebook writes. Call once, in cell 0."""
    global _NB, _SEEN
    _NB = notebook
    _SEEN = {}
    print(f"[val] {notebook}  ->  {FIG}/{notebook}_<section>.{{jpg,pdf}}  @ {DPI} dpi")


def save(section: str, fig=None, show: bool = True, tight: bool = True):
    """Write the current figure as <notebook>_<section>.jpg and .pdf, then show it.

    Called in place of plt.show(). Both formats every time: the jpg for pasting into a
    document or a message, the pdf because it stays vector wherever the plot is vector.
    dpi=600 sets the jpg resolution and the resolution of any RASTERISED element inside the
    pdf (hexbin, imshow, a scatter with `rasterized=True`); pure line and text art in the pdf
    is resolution-independent and unaffected.
    """
    import matplotlib.pyplot as plt
    if _NB is None:
        raise RuntimeError("call val_common.init('<notebook stem>') in cell 0 first")
    fig = fig if fig is not None else plt.gcf()
    if tight:
        try:
            fig.tight_layout()
        except Exception:
            pass                       # some layouts (host_subplot, 3d) refuse; not fatal
    _SEEN[section] = _SEEN.get(section, 0) + 1
    stem = f"{_NB}_{section}"
    paths = []
    for ext in ("jpg", "pdf"):
        p = f"{FIG}/{stem}.{ext}"
        # JPEG has no alpha channel -- without an explicit facecolor a transparent figure
        # background is composited onto black.
        fig.savefig(p, dpi=DPI, bbox_inches="tight", facecolor="white", format=ext)
        paths.append(p)
    print(f"  [fig] {stem}.jpg + .pdf  ({DPI} dpi)")
    if show:
        plt.show()
    return paths


# What each notebook reads. Used by preflight() so a missing input is a sentence rather than
# a stack trace partway down the notebook.
NEEDS = {
    "paper_validation": [
        paper("paper_disruption.parquet"), paper("paper_citation.parquet"),
        paper("paper_metadata.parquet"), paper("paper_sb.parquet"),
        paper("paper_hit_probability.parquet"), paper("paper_z_score.parquet"),
        paper("paper_citation_trend.parquet"), SCISCINET_FOS,
    ],
    "patent_validation": [
        patent("patent_metadata.parquet"), patent("patent_citation.parquet"),
        patent("patent_disruption.parquet"), patent("patent_z_score.parquet"),
        patent("patent_hit_probability.parquet"), patent("patent_sb.parquet"),
        patent("patent_citation_trend.parquet"),
        patent("patent_disruption_app.parquet"),
    ],
    "pcs_validation": [pcs("pcs_citation.parquet"), pcs("pcs_hit_probability.parquet")],
    # Case law has no atypicality, no CPC and no application-stage network, so the list is
    # shorter than the patent one by exactly those metrics rather than by omission.
    "case_law_validation": [
        case("case_metadata.parquet"), case("case_citation.parquet"),
        case("case_citation_trend.parquet"), case("case_disruption.parquet"),
        case("case_feg_disruption_trend.parquet"), case("case_hit_probability.parquet"),
        case("case_sb.parquet"),
        # section 11b puts the beauty coefficient of all three families side by side; the
        # kernel is the same function in all three notebooks, so B is directly comparable.
        paper("paper_sb.parquet"), paper("paper_metadata.parquet"),
        patent("patent_sb.parquet"), patent("patent_metadata.parquet"),
    ],
    # Dimensions: the first three are required; the rest are written later in the chain
    # (jobs/Dimensions/submit_dimensions.sh) and the notebook guards each section on them, so
    # a MISSING here is a section that prints one line, not a failure.
    "dimension_validation": [
        dim("paper_metadata.parquet"), dim("paper_citation.parquet"), dim("paper_author.parquet"),
        dim("paper_disruption.parquet"), dim("paper_sb.parquet"), dim("paper_hit_probability.parquet"),
        dim("paper_citation_trend.parquet"), dim("paper_z_score.parquet"),
        # section 14 puts the two paper indices side by side
        paper("paper_metadata.parquet"), paper("paper_citation.parquet"),
        paper("paper_disruption.parquet"), paper("paper_sb.parquet"),
    ],
    # Author / inventor countries (added 2026-09-13). §7 of each reads the other family's table
    # and is guarded, so only the own-family inputs are required.
    "author_country_validation": [
        paper("paper_author_country.parquet"), paper("paper_metadata.parquet"),
        paper("paper_hit_probability.parquet"), paper("paper_disruption.parquet"),
        paper("paper_citation.parquet"), WORLD_GEOJSON,
    ],
    "inventor_country_validation": [
        patent("patent_inventor_country.parquet"), patent("patent_metadata.parquet"),
        patent("patent_hit_probability.parquet"), patent("patent_disruption.parquet"),
        WORLD_GEOJSON,
    ],
    # Citation histories now come from the DOCUMENT-level trends, not a pair-level build.
    "ppp_validation": [
        paper("paper_citation_trend.parquet"), patent("patent_citation_trend.parquet"),
        paper("paper_metadata.parquet"), patent("patent_metadata.parquet"),
        paper("paper_sb.parquet"), patent("patent_sb.parquet"),
    ],
}


def preflight(notebook: str | None = None) -> bool:
    """Report which inputs are present. True if everything this notebook needs is there."""
    names = [notebook or _NB] if (notebook or _NB) else sorted(NEEDS)
    ok_all = True
    for nb in names:
        miss = [p for p in NEEDS.get(nb, []) if not os.path.exists(p)]
        print(f"  {nb:<20}{'OK' if not miss else f'MISSING {len(miss)}'}")
        for p in miss:
            print(f"      {p.replace(BASE + '/', '')}  <- not present")
        ok_all &= not miss
    return ok_all
