"""Chapter 3 Fig 3.2: HLLC interface wave fan.

Renders the three-wave HLLC fan in the (x, t) plane:
left acoustic S_L, contact S_*, right acoustic S_R, separating
U_L, U_{*L}, U_{*R}, U_R. Top-journal style with thesis-matched
serif (Times) typography.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "report1" / "phd-thesis-template-2.4" / "Figs" / "report1"

# Palette: match scripts/figures/_style.PALETTE.
BLUE = "#1F4E79"     # outer acoustic waves S_L, S_R
ORANGE = "#E76F51"   # contact S_* and star states
AXIS = "#9AA0A6"     # pale axes so wave rays read first
TEXT = "#1A1A1A"
MUTED = "#4A4A4A"


def setup_style() -> None:
    """Times-like serif + STIX math, sized to look natural next to 12 pt body text."""
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": [
                "Times New Roman",
                "Liberation Serif",
                "STIX Two Text",
                "Nimbus Roman",
                "DejaVu Serif",
            ],
            "mathtext.fontset": "stix",
            "text.usetex": False,
            "font.size": 9.5,
            "axes.linewidth": 0.7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.dpi": 450,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.04,
        }
    )


def axis_arrow(ax, x0, y0, x1, y1, color=AXIS, lw=0.7):
    ax.add_patch(
        FancyArrowPatch(
            (x0, y0),
            (x1, y1),
            arrowstyle="-|>",
            mutation_scale=8,
            linewidth=lw,
            color=color,
            shrinkA=0,
            shrinkB=0,
            clip_on=False,
        )
    )


def main() -> int:
    setup_style()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Width chosen to display unscaled inside a 12 pt thesis figure env (~6 in textwidth).
    fig, ax = plt.subplots(figsize=(4.8, 3.3))
    ax.set_xlim(-3.6, 3.6)
    ax.set_ylim(-0.55, 2.95)
    ax.set_aspect("equal")
    ax.axis("off")

    # Coordinate axes.
    axis_arrow(ax, -3.40, 0.0, 3.40, 0.0)
    axis_arrow(ax, 0.0, -0.35, 0.0, 2.80)
    ax.text(3.45, -0.02, r"$x$", ha="left", va="center", fontsize=10, color=TEXT)
    ax.text(-0.10, 2.85, r"$t$", ha="right", va="bottom", fontsize=10, color=TEXT)

    # Wave rays from origin.
    sL_end = (-2.65, 2.55)
    sR_end = (2.65, 2.55)
    sStar_end = (0.55, 2.55)

    ax.plot([0, sL_end[0]], [0, sL_end[1]], color=BLUE, lw=1.5, solid_capstyle="round")
    ax.plot([0, sR_end[0]], [0, sR_end[1]], color=BLUE, lw=1.5, solid_capstyle="round")
    ax.plot(
        [0, sStar_end[0]],
        [0, sStar_end[1]],
        color=ORANGE,
        lw=1.4,
        linestyle=(0, (5, 3)),
        solid_capstyle="round",
    )

    # Wave-speed labels.
    ax.text(sL_end[0] - 0.05, sL_end[1] + 0.10, r"$S_L$", ha="right", va="bottom",
            fontsize=10, color=BLUE)
    ax.text(sR_end[0] + 0.05, sR_end[1] + 0.10, r"$S_R$", ha="left", va="bottom",
            fontsize=10, color=BLUE)
    ax.text(sStar_end[0] + 0.10, sStar_end[1] + 0.10, r"$S_{\ast}$", ha="left",
            va="bottom", fontsize=10, color=ORANGE)

    # Region labels.
    ax.text(-2.25, 1.05, r"$U_L$", ha="center", va="center", fontsize=10.5, color=TEXT)
    ax.text(2.25, 1.05, r"$U_R$", ha="center", va="center", fontsize=10.5, color=TEXT)
    ax.text(-0.85, 1.62, r"$U_{\ast L}$", ha="center", va="center",
            fontsize=10, color=ORANGE)
    ax.text(1.25, 1.62, r"$U_{\ast R}$", ha="center", va="center",
            fontsize=10, color=ORANGE)

    # Origin marker.
    ax.plot([0], [0], marker="o", markersize=2.6, color=TEXT, zorder=5)
    ax.text(0.10, -0.22, r"$0$", ha="left", va="top", fontsize=8.5, color=MUTED)

    out_base = OUT_DIR / "ch3_hllc_fan"
    fig.savefig(out_base.with_suffix(".svg"))
    fig.savefig(out_base.with_suffix(".pdf"))
    fig.savefig(out_base.with_suffix(".png"), dpi=450)
    plt.close(fig)
    print(out_base.with_suffix(".svg"))
    print(out_base.with_suffix(".pdf"))
    print(out_base.with_suffix(".png"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
