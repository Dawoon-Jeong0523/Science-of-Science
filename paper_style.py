"""paper_style.py — uniform plot style for PPP manuscript figures.

Import once at the top of every Final notebook:
    import paper_style
    SCI, TECH, BOTH, GRAY = paper_style.SCI, paper_style.TECH, paper_style.BOTH, paper_style.GRAY

All rcParams are applied on import.
"""
from __future__ import annotations
import urllib.request
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib import font_manager

# ── Font setup ────────────────────────────────────────────────────────────────
_FONTS_DIR = Path(__file__).parent / "fonts"
_FONTS_DIR.mkdir(exist_ok=True)

_LATO = {
    "Lato-Regular.ttf":    "https://raw.githubusercontent.com/google/fonts/main/ofl/lato/Lato-Regular.ttf",
    "Lato-Bold.ttf":       "https://raw.githubusercontent.com/google/fonts/main/ofl/lato/Lato-Bold.ttf",
    "Lato-Italic.ttf":     "https://raw.githubusercontent.com/google/fonts/main/ofl/lato/Lato-Italic.ttf",
    "Lato-BoldItalic.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/lato/Lato-BoldItalic.ttf",
}


def _ensure_lato() -> None:
    for fname, url in _LATO.items():
        dest = _FONTS_DIR / fname
        if not dest.exists():
            try:
                urllib.request.urlretrieve(url, str(dest))
            except Exception:
                pass
    for ttf in _FONTS_DIR.glob("*.ttf"):
        try:
            font_manager.addfont(str(ttf))
        except Exception:
            pass


def _pick_font() -> str:
    _ensure_lato()
    available = {f.name for f in font_manager.fontManager.ttflist}
    for candidate in ("Gill Sans MT", "Gill Sans", "Lato"):
        if candidate in available:
            return candidate
    return "DejaVu Sans"


BODY_FONT: str = _pick_font()

# ── Palette ───────────────────────────────────────────────────────────────────
PALETTE: dict[str, str] = {
    "crimson": "#C13B5A",
    "teal":    "#175A73",
    "orange":  "#F08C21",
    "green":   "#2E8B65",
    "blue":    "#3B76B4",
    "red":     "#D62728",
    "royal":   "#2062C8",
}

# Semantic aliases — drop-in replacements for notebook colour vars
SCI:  str = PALETTE["crimson"]   # science / paper side
TECH: str = PALETTE["blue"]      # technology / patent side
BOTH: str = PALETTE["green"]     # pair-level / shared
GRAY: str = "#8C8C8C"

# ── rcParams ──────────────────────────────────────────────────────────────────
def apply() -> None:
    """Apply manuscript rcParams. Called automatically on import."""
    plt.rcParams.update({
        "font.family":        BODY_FONT,
        "font.size":          12,
        "axes.labelsize":     15,
        "axes.labelweight":   "bold",
        "axes.linewidth":     1.3,
        "axes.edgecolor":     "0.15",
        "xtick.direction":    "out",
        "ytick.direction":    "out",
        "xtick.major.size":   4.5,
        "ytick.major.size":   4.5,
        "xtick.major.width":  1.2,
        "ytick.major.width":  1.2,
        "xtick.labelsize":    11.5,
        "ytick.labelsize":    11.5,
        "xtick.color":        "0.15",
        "ytick.color":        "0.15",
        "axes.axisbelow":     True,
        "grid.color":         "#d6d6d6",
        "grid.linewidth":     0.9,
        "figure.facecolor":   "white",
        "savefig.facecolor":  "white",
        "savefig.dpi":        300,
        "pdf.fonttype":       42,
        "ps.fonttype":        42,
        "legend.frameon":     False,
        "legend.fontsize":    11,
        "axes.unicode_minus": False,   # use ASCII hyphen-minus; Gill Sans MT lacks U+2212
    })


apply()

# ── Helper functions ──────────────────────────────────────────────────────────

def despine(ax, keep_left: bool = True, keep_bottom: bool = True) -> None:
    """Remove top and right spines (default). For twinx axes call on each ax separately."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if not keep_left:
        ax.spines["left"].set_visible(False)
    if not keep_bottom:
        ax.spines["bottom"].set_visible(False)


def kilo_fmt() -> mticker.FuncFormatter:
    """Y-axis formatter: 25000 → '25k'."""
    return mticker.FuncFormatter(lambda v, _: f"{v / 1000:g}k")


def fixed_fmt(decimals: int = 2) -> mticker.FuncFormatter:
    """Fixed-decimal formatter."""
    return mticker.FuncFormatter(lambda v, _: f"{v:.{decimals}f}")


def ref_hline(ax, y: float, **kw) -> None:
    """Horizontal reference line (black, lw=1.8)."""
    ax.axhline(y, **{"color": "k", "lw": 1.8, "zorder": 3, **kw})


def ref_vline(ax, x: float, **kw) -> None:
    """Vertical reference line (black, lw=1.8)."""
    ax.axvline(x, **{"color": "k", "lw": 1.8, "zorder": 3, **kw})


def align_twinx_zero(ax1, ax2) -> None:
    """Align y=0 on both twinx axes so the zero line is at the same height."""
    import numpy as np
    def _span(ax):
        lo, hi = ax.get_ylim()
        return lo, hi, hi - lo
    l1, h1, r1 = _span(ax1)
    l2, h2, r2 = _span(ax2)
    frac1 = -l1 / r1 if r1 else 0.5
    frac2 = -l2 / r2 if r2 else 0.5
    target = max(frac1, frac2)
    ax1.set_ylim(-target * r1, (1 - target) * r1)
    ax2.set_ylim(-target * r2, (1 - target) * r2)


print(f"[paper_style] font={BODY_FONT!r}  SCI={SCI}  TECH={TECH}  BOTH={BOTH}")
