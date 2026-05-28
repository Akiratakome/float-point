"""Chapter 3 Fig 3.3: Ideal-MHD seven-wave fan.

Two-panel layout: the wave fan on the left, a side panel on the right
that groups the four wave families with their physical character and
the magnitude ordering c_s <= c_a <= c_f. Top-journal style with
thesis-matched serif (Times) typography.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "report1" / "phd-thesis-template-2.4" / "Figs" / "report1"

# Palette: match scripts/figures/_style.PALETTE.
BLUE = "#1F4E79"        # fast magnetosonic
CYAN_GREEN = "#2A9D8F"  # Alfven
ORANGE = "#E76F51"      # slow magnetosonic
ENTROPY = "#1A1A1A"     # entropy / contact mode
AXIS = "#9AA0A6"        # axes (pale)
TEXT = "#1A1A1A"
MUTED = "#4A4A4A"
PANEL_BG = "#F5F6F8"
PANEL_BORDER = "#D5D8DC"


def setup_style() -> None:
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


def draw_fan(ax) -> None:
    ax.set_xlim(-4.0, 4.0)
    ax.set_ylim(-0.50, 3.20)
    ax.set_aspect("equal")
    ax.axis("off")

    # Coordinate axes.
    axis_arrow(ax, -3.80, 0.0, 3.80, 0.0)
    axis_arrow(ax, 0.0, -0.30, 0.0, 3.05)
    ax.text(3.85, -0.02, r"$x$", ha="left", va="center", fontsize=10, color=TEXT)
    ax.text(-0.12, 3.10, r"$t$", ha="right", va="bottom", fontsize=10, color=TEXT)

    # Seven wave rays: (dx, dy, color, label, anchor)
    rays = [
        (-3.30, 1.70, BLUE,       r"$u_n - c_f$", "left"),
        (-2.45, 2.05, CYAN_GREEN, r"$u_n - c_a$", "left"),
        (-1.25, 2.40, ORANGE,     r"$u_n - c_s$", "left"),
        ( 0.00, 2.70, ENTROPY,    r"$u_n$",       "center"),
        ( 1.25, 2.40, ORANGE,     r"$u_n + c_s$", "right"),
        ( 2.45, 2.05, CYAN_GREEN, r"$u_n + c_a$", "right"),
        ( 3.30, 1.70, BLUE,       r"$u_n + c_f$", "right"),
    ]

    for dx, dy, color, label, anchor in rays:
        lw = 1.55 if anchor == "center" else 1.45
        ax.plot([0, dx], [0, dy], color=color, lw=lw, solid_capstyle="round", zorder=3)
        if anchor == "left":
            ax.text(dx - 0.08, dy + 0.10, label, ha="right", va="bottom",
                    fontsize=9.5, color=color)
        elif anchor == "right":
            ax.text(dx + 0.08, dy + 0.10, label, ha="left", va="bottom",
                    fontsize=9.5, color=color)
        else:
            ax.text(dx + 0.18, dy + 0.05, label, ha="left", va="bottom",
                    fontsize=9.5, color=color)

    # Origin marker.
    ax.plot([0], [0], marker="o", markersize=2.5, color=TEXT, zorder=5)
    ax.text(0.12, -0.22, r"$0$", ha="left", va="top", fontsize=8.5, color=MUTED)

    # Region count annotation: six intermediate states between seven characteristics.
    ax.text(0.0, -0.50, r"seven characteristics, six intermediate states",
            ha="center", va="top", fontsize=8.0, color=MUTED, style="italic")


def draw_side_panel(ax) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Panel background.
    ax.add_patch(Rectangle((0.02, 0.04), 0.96, 0.92,
                           facecolor=PANEL_BG, edgecolor=PANEL_BORDER, lw=0.6))

    ax.text(0.50, 0.91, "Wave families",
            ha="center", va="center", fontsize=9.5, color=TEXT, weight="bold")

    # Each row: color swatch + family name + short character.
    rows = [
        (BLUE,       "fast magnetosonic",  "compressive, in phase"),
        (CYAN_GREEN, "Alfvén",             "transverse, shear"),
        (ORANGE,     "slow magnetosonic",  "compressive, out of phase"),
        (ENTROPY,    "entropy / contact",  r"advective, $\rho$ jump"),
    ]
    y0 = 0.78
    dy = 0.13
    for i, (color, name, character) in enumerate(rows):
        y = y0 - i * dy
        # Color bar.
        ax.add_patch(Rectangle((0.07, y - 0.012), 0.10, 0.022,
                               facecolor=color, edgecolor=color, lw=0))
        ax.text(0.21, y, name, ha="left", va="center", fontsize=8.8, color=TEXT)
        ax.text(0.21, y - 0.052, character, ha="left", va="center",
                fontsize=7.6, color=MUTED)

    # Speed-ordering inequality at the bottom.
    ax.plot([0.07, 0.93], [0.20, 0.20], color=PANEL_BORDER, lw=0.5)
    ax.text(0.50, 0.14,
            r"magnitudes: $\;|c_s| \;\leq\; |c_a| \;\leq\; |c_f|$",
            ha="center", va="center", fontsize=8.8, color=TEXT)
    ax.text(0.50, 0.075,
            r"central $u_n$ is the entropy mode",
            ha="center", va="center", fontsize=7.6, color=MUTED, style="italic")


def main() -> int:
    setup_style()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Two-column layout: fan on the left, info panel on the right (slightly wider).
    fig = plt.figure(figsize=(6.6, 3.7))
    gs = fig.add_gridspec(1, 2, width_ratios=[2.2, 1.2], wspace=0.06,
                          left=0.01, right=0.99, top=0.99, bottom=0.04)
    ax_fan = fig.add_subplot(gs[0, 0])
    ax_panel = fig.add_subplot(gs[0, 1])

    draw_fan(ax_fan)
    draw_side_panel(ax_panel)

    out_base = OUT_DIR / "ch3_mhd_seven_wave_fan"
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
