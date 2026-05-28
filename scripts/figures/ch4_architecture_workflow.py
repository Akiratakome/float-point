"""Chapter 4 architecture workflow.

Three-row system diagram of the Report-1 experiment pipeline:
SETUP (input, build flags, dispatch) -> EXECUTE (time-stepping
loop drawn as a five-station bar with a while-feedback) -> ANALYSE
(saved state, post-processing, aggregation). AI-paper style with
thesis-matched serif (Times) typography at caption size.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Circle


REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "report1" / "phd-thesis-template-2.4" / "Figs" / "report1"


SETUP_DARK   = "#3A5A8C"
SETUP_FILL   = "#EAF0F8"
SETUP_BAND   = "#F5F8FC"

EXEC_DARK    = "#3F7A5A"
EXEC_FILL    = "#ECF5EE"
EXEC_BAND    = "#F5FAF6"

ANALYSE_DARK = "#B26A3F"
ANALYSE_FILL = "#FBEFE5"
ANALYSE_BAND = "#FCF6EF"

CARD_FILL    = "#FFFFFF"
CARD_BORDER  = "#C8CCD2"
RULE         = "#DCDFE4"
TEXT         = "#1A1A1A"
MUTED        = "#555A63"
ARROW        = "#2B2F36"


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
            "font.size": 9.0,
            "axes.linewidth": 0.6,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "savefig.dpi": 450,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.05,
        }
    )


def rounded_box(ax, x, y, w, h, facecolor, edgecolor, lw=0.6, radius=0.08):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h,
            boxstyle=f"round,pad=0.0,rounding_size={radius}",
            facecolor=facecolor, edgecolor=edgecolor, lw=lw,
        )
    )


def phase_band(ax, x, y, w, h, fill, label, dark):
    rounded_box(ax, x, y, w, h, facecolor=fill, edgecolor="none", radius=0.09)
    ax.text(x + 0.16, y + h - 0.04, label,
            ha="left", va="top", fontsize=8.4, color=dark, weight="bold")


def card(ax, x, y, w, h, badge_n, badge_color, title, lines,
         title_pt=9.0, body_pt=7.8, bullet_x=0.20, text_x=0.36):
    rounded_box(ax, x, y, w, h, facecolor=CARD_FILL, edgecolor=CARD_BORDER, lw=0.7)
    cx, cy = x + 0.20, y + h - 0.22
    ax.add_patch(Circle((cx, cy), 0.13, facecolor=badge_color, edgecolor="none", zorder=4))
    ax.text(cx, cy, str(badge_n), ha="center", va="center",
            color="white", fontsize=7.4, weight="bold", zorder=5)
    title_lines = title.split("\n")
    ax.text(x + 0.40, y + h - 0.18, "\n".join(title_lines),
            ha="left", va="top", fontsize=title_pt, color=TEXT,
            linespacing=1.10, weight="bold")
    rule_y = y + h - 0.18 - 0.19 * len(title_lines) - 0.08
    ax.plot([x + 0.16, x + w - 0.16], [rule_y, rule_y], color=RULE, lw=0.55)
    yy = rule_y - 0.16
    line_dy = 0.20
    for entry in lines:
        if isinstance(entry, tuple):
            text, family = entry
        else:
            text, family = entry, "serif"
        ax.text(x + bullet_x, yy, u"•", ha="left", va="top",
                fontsize=body_pt - 0.4, color=MUTED)
        ax.text(x + text_x, yy, text, ha="left", va="top",
                fontsize=body_pt, color=TEXT, family=family, linespacing=1.18)
        yy -= line_dy


def dispatch_card(ax, x, y, w, h, badge_n=3):
    rounded_box(ax, x, y, w, h, facecolor=CARD_FILL, edgecolor=CARD_BORDER, lw=0.7)
    cx, cy = x + 0.20, y + h - 0.22
    ax.add_patch(Circle((cx, cy), 0.13, facecolor=SETUP_DARK, edgecolor="none", zorder=4))
    ax.text(cx, cy, str(badge_n), ha="center", va="center",
            color="white", fontsize=7.4, weight="bold", zorder=5)
    ax.text(x + 0.40, y + h - 0.18, "Runtime dispatch",
            ha="left", va="top", fontsize=9.0, color=TEXT, weight="bold")
    rule_y = y + h - 0.40
    ax.plot([x + 0.16, x + w - 0.16], [rule_y, rule_y], color=RULE, lw=0.55)

    mw = w - 0.32
    mh = 0.32
    cpu_y = rule_y - 0.18 - mh
    gpu_y = cpu_y - mh - 0.08
    for text, top in [("CPU path", cpu_y), ("CUDA GPU path", gpu_y)]:
        rounded_box(ax, x + 0.16, top, mw, mh,
                    facecolor=SETUP_FILL, edgecolor=SETUP_DARK, lw=0.5, radius=0.06)
        ax.text(x + w / 2, top + mh / 2, text,
                ha="center", va="center", fontsize=7.7, color=TEXT)
    ax.text(x + w / 2, gpu_y - 0.10,
            "shared source",
            ha="center", va="top", fontsize=7.0, color=MUTED, style="italic")

    # Anchor for downstream arrow: clear of the caption, near card bottom edge.
    return (x + w / 2, y - 0.02)


def station(ax, cx, cy, idx, label, color=EXEC_DARK):
    """A numbered station node with a 2-line label below."""
    ax.add_patch(Circle((cx, cy), 0.18, facecolor=color, edgecolor="white", lw=1.4, zorder=4))
    ax.text(cx, cy, str(idx), ha="center", va="center",
            color="white", fontsize=8.0, weight="bold", zorder=5)
    ax.text(cx, cy - 0.36, label, ha="center", va="top",
            fontsize=7.8, color=TEXT, linespacing=1.15)


def arrow(ax, x0, y0, x1, y1, lw=0.85, color=ARROW, ms=8):
    ax.add_patch(
        FancyArrowPatch(
            (x0, y0), (x1, y1),
            arrowstyle="-|>", mutation_scale=ms,
            linewidth=lw, color=color,
            shrinkA=0, shrinkB=0, clip_on=False,
        )
    )


def main() -> int:
    setup_style()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    W, H = 6.6, 7.25
    fig, ax = plt.subplots(figsize=(W, H))
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")

    # Header.
    ax.text(W / 2, H - 0.16,
            "Report-1 experiment pipeline: shared CPU / CUDA source, "
            "matched binary across precision and device",
            ha="center", va="top", fontsize=9.4, color=TEXT, style="italic")

    margin = 0.20
    band_w = W - 2 * margin
    band_x = margin

    band_setup_h = 2.05
    band_exec_h = 1.65
    band_analyse_h = 2.00

    band_setup_y = H - 0.45 - band_setup_h
    band_exec_y = band_setup_y - 0.35 - band_exec_h
    band_analyse_y = band_exec_y - 0.35 - band_analyse_h
    # band_analyse_y should now be ~0.40, leaving room for a footer below.

    phase_band(ax, band_x, band_setup_y, band_w, band_setup_h, SETUP_BAND, "SETUP", SETUP_DARK)
    phase_band(ax, band_x, band_exec_y, band_w, band_exec_h, EXEC_BAND, "EXECUTE", EXEC_DARK)
    phase_band(ax, band_x, band_analyse_y, band_w, band_analyse_h, ANALYSE_BAND, "ANALYSE", ANALYSE_DARK)

    # ---------- SETUP row ----------
    setup_inner_x = band_x + 0.20
    setup_inner_w = band_w - 0.40
    setup_card_h = band_setup_h - 0.40
    setup_card_y = band_setup_y + 0.10
    gap = 0.20
    cw = (setup_inner_w - 2 * gap) / 3
    c1_x = setup_inner_x
    c2_x = c1_x + cw + gap
    c3_x = c2_x + cw + gap

    card(ax, c1_x, setup_card_y, cw, setup_card_h, 1, SETUP_DARK,
         "Input configuration",
         ["test case",
          "grid resolution",
          "boundary mode",
          "solver: HLLC / Rusanov",
          "precision and device"])
    card(ax, c2_x, setup_card_y, cw, setup_card_h, 2, SETUP_DARK,
         "Build-time controls",
         [("HRSC_REAL", "monospace"),
          ("ENABLE_CUDA", "monospace"),
          ("STRICT_IEEE", "monospace"),
          ("FAST_MATH", "monospace"),
          ("STRICT_INEQUALITY", "monospace")])
    dispatch_bottom = dispatch_card(ax, c3_x, setup_card_y, cw, setup_card_h)

    s_arrow_y = setup_card_y + setup_card_h / 2
    arrow(ax, c1_x + cw + 0.02, s_arrow_y, c2_x - 0.02, s_arrow_y)
    arrow(ax, c2_x + cw + 0.02, s_arrow_y, c3_x - 0.02, s_arrow_y)

    # ---------- EXECUTE band: 5 station bar ----------
    exec_inner_x = band_x + 0.28
    exec_inner_w = band_w - 0.56
    # Stations sit on a horizontal line; below = labels, above = feedback arc.
    station_y = band_exec_y + 0.62
    station_xs = [exec_inner_x + i * (exec_inner_w / 4) for i in range(5)]
    station_labels = [
        "refill\nghost cells",
        r"CFL $\Delta t$" + "\nclip to $t_{\\mathrm{end}}$",
        "X / Y sweep\nalternating order",
        "MUSCL–Hancock\n+ HLLC / Rusanov",
        "Kahan time\naccumulation",
    ]

    # Connector line under the stations.
    for i in range(4):
        x_a = station_xs[i] + 0.20
        x_b = station_xs[i + 1] - 0.20
        ax.plot([x_a, x_b - 0.02], [station_y, station_y], color=EXEC_DARK, lw=1.0)
        arrow(ax, x_b - 0.02, station_y, x_b + 0.0, station_y,
              lw=0.0, color=EXEC_DARK, ms=8)
    for i, (sx, label) in enumerate(zip(station_xs, station_labels), start=1):
        station(ax, sx, station_y, i, label)

    # Title for the strip, placed inside the EXECUTE band just below its label.
    title_y = band_exec_y + band_exec_h - 0.28
    ax.text(exec_inner_x, title_y, "Time-stepping loop",
            ha="left", va="top", fontsize=9.0, color=TEXT, weight="bold")
    ax.text(exec_inner_x + 1.40, title_y - 0.02,
            r"(per step, repeated until $t \geq t_{\mathrm{end}}$)",
            ha="left", va="top", fontsize=7.6, color=MUTED, style="italic")

    # Feedback arrow above the station line.
    fb_y = title_y - 0.30
    ax.plot([station_xs[-1], station_xs[-1]], [station_y + 0.18, fb_y],
            color=EXEC_DARK, lw=0.7)
    ax.plot([station_xs[-1], station_xs[0]], [fb_y, fb_y],
            color=EXEC_DARK, lw=0.7)
    arrow(ax, station_xs[0], fb_y, station_xs[0], station_y + 0.20,
          lw=0.7, color=EXEC_DARK, ms=6)
    ax.text((station_xs[0] + station_xs[-1]) / 2, fb_y + 0.02,
            r"while  $t < t_{\mathrm{end}}$",
            ha="center", va="bottom", fontsize=7.4, color=EXEC_DARK, style="italic")

    # SETUP -> EXECUTE arrow: straight vertical drop from below dispatch into the
    # top edge of the EXECUTE band, on the right of the figure where it avoids the
    # EXECUTE label, the time-stepping title, and the feedback arc.
    arrow_x = dispatch_bottom[0]
    arrow(ax, arrow_x, dispatch_bottom[1] - 0.02,
          arrow_x, band_exec_y + band_exec_h + 0.02,
          lw=0.95, ms=9)

    # ---------- ANALYSE row ----------
    analyse_inner_x = band_x + 0.20
    analyse_inner_w = band_w - 0.40
    analyse_card_h = band_analyse_h - 0.40
    analyse_card_y = band_analyse_y + 0.10
    aw = (analyse_inner_w - 2 * gap) / 3
    a5_x = analyse_inner_x
    a6_x = a5_x + aw + gap
    a7_x = a6_x + aw + gap

    card(ax, a5_x, analyse_card_y, aw, analyse_card_h, 5, ANALYSE_DARK,
         "Saved\nconservative state",
         [("raw binary grids", "monospace"),
          "per-case checkpoints",
          "cell-major layout"])
    card(ax, a6_x, analyse_card_y, aw, analyse_card_h, 6, ANALYSE_DARK,
         "Post-processing",
         [r"$L_1,\; L_\infty$",
          r"$\mathrm{ULP}_{\max}$",
          "SSIM",
          "reference-scaled ratios"])
    card(ax, a7_x, analyse_card_y, aw, analyse_card_h, 7, ANALYSE_DARK,
         "Aggregation\nand reporting",
         [("CSV / JSON", "monospace"),
          "tables",
          "figures"])

    a_arrow_y = analyse_card_y + analyse_card_h / 2
    arrow(ax, a5_x + aw + 0.02, a_arrow_y, a6_x - 0.02, a_arrow_y)
    arrow(ax, a6_x + aw + 0.02, a_arrow_y, a7_x - 0.02, a_arrow_y)

    # EXECUTE -> ANALYSE arrow: vertical from EXECUTE band bottom-center down to
    # top of the Saved-state card.
    exec_out_x = a5_x + aw / 2  # align with card 5 (Saved state) horizontally
    target_top_y = analyse_card_y + analyse_card_h + 0.02
    arrow(ax, exec_out_x, band_exec_y - 0.04,
          exec_out_x, target_top_y, lw=0.95, ms=9)

    # Footer (clear of ANALYSE band).
    ax.text(W / 2, 0.04,
            "Matched CPU / GPU claims are limited to saved states "
            "under fixed case, precision, solver, binary, and strict-IEEE controls.",
            ha="center", va="bottom", fontsize=7.4, color=MUTED, style="italic")

    out_base = OUT_DIR / "ch4_architecture_workflow"
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
