"""Unified plot style for report1 figures.

Usage in any plot_*.py:
    from _style import apply, PALETTE, DIVERGING_CMAP, save_pair
    apply()
    ...
    save_pair(fig, "stem", outdir)

Palette references review.md §6 / spec §2.2.
"""
import matplotlib as mpl
import os
from cycler import cycler

# Multiple semantic keys share colors by design — see spec §2.2.
# fp64/cpu/hllc all map to deep blue; gray/rusanov both map to neutral grey.
PALETTE = {
    "fp64":    "#1F4E79",
    "fp32":    "#E76F51",
    "cpu":     "#1F4E79",
    "gpu":     "#2A9D8F",
    "hllc":    "#1F4E79",
    "rusanov": "#6C757D",
    "ref":     "#000000",
    "gray":    "#6C757D",
    "accent":  "#9B2226",
}
CYCLE = ["#1F4E79", "#E76F51", "#2A9D8F", "#6C757D", "#9B2226"]
DIVERGING_CMAP = "RdBu_r"
SEQUENTIAL_CMAP = "viridis"


def apply():
    mpl.rcParams.update({
        "font.family":        "serif",
        "font.serif":         ["Latin Modern Roman", "DejaVu Serif"],
        "mathtext.fontset":   "cm",
        "axes.labelsize":     10,
        "axes.titlesize":     10,
        "xtick.labelsize":    9,
        "ytick.labelsize":    9,
        "legend.fontsize":    9,
        "legend.frameon":     False,
        "axes.linewidth":     0.8,
        "lines.linewidth":    1.3,
        "lines.markersize":   4,
        "grid.linewidth":     0.5,
        "grid.alpha":         0.4,
        "savefig.dpi":        200,
        "savefig.bbox":       "tight",
        "savefig.pad_inches": 0.02,
        "axes.prop_cycle":    cycler(color=CYCLE),
        "image.cmap":         SEQUENTIAL_CMAP,
    })


def save_pair(fig, stem, outdir):
    """Save both PDF (preferred) and PNG (backup) so LaTeX graphicx picks PDF."""
    os.makedirs(outdir, exist_ok=True)
    fig.savefig(os.path.join(outdir, f"{stem}.pdf"))
    fig.savefig(os.path.join(outdir, f"{stem}.png"), dpi=200)
