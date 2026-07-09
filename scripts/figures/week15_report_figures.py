#!/usr/bin/env python3
"""Generate Week-15 supervisor-report figures from committed precision-study evidence.

Reads the four report-grade summary.json packets (Brio-Wu 1D and Orszag-Tang 2D,
each HLL and HLLD) and renders publication-style matplotlib PNGs for the four
primary findings plus copies the two real OT field/drift heatmaps into one bundle.

Colours use the dataviz reference palette (CVD-safe): double = blue #2a78d6,
float = red #e34948; MCA fields rho/By/p = blue/aqua/yellow. Light background for
slides/report. No data is recomputed here — every number comes from the summaries.
"""
from __future__ import annotations

import json
import pathlib
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "week15" / "figures"

# dataviz reference palette (light mode), CVD-validated.
C_DOUBLE = "#2a78d6"   # blue  — double / p53
C_FLOAT = "#e34948"    # red   — float  / p24
C_FIELD = {"rho": "#2a78d6", "By": "#1baf7a", "p": "#eda100"}  # blue / aqua / yellow
INK = "#0b0b0b"
MUTED = "#898781"
GRID = "#e1e0d9"

PACKETS = {
    "Brio-Wu 1D · HLL": ROOT / "experiments/week15/brio_wu_precision_pilot_p1/summary.json",
    "Brio-Wu 1D · HLLD": ROOT / "experiments/week15/brio_wu_precision_pilot_hlld_p1/summary.json",
    "Orszag-Tang 2D · HLL": ROOT / "experiments/week15/orszag_tang_precision_smoke/headline256_p1/summary.json",
    "Orszag-Tang 2D · HLLD": ROOT / "experiments/week15/orszag_tang_precision_smoke_hlld/headline256_p1/summary.json",
}

# The Brio-Wu pilot writes MCA inline in its summary; the OT smoke keeps MCA in a
# separate N=30 packet. Map each label to where its MCA block actually lives.
MCA_SOURCES = {
    "Brio-Wu 1D · HLL": ROOT / "experiments/week15/brio_wu_precision_pilot_p1/summary.json",
    "Brio-Wu 1D · HLLD": ROOT / "experiments/week15/brio_wu_precision_pilot_hlld_p1/summary.json",
    "Orszag-Tang 2D · HLL": ROOT / "experiments/week15/orszag_tang_precision_smoke/mca_n30/summary.json",
    "Orszag-Tang 2D · HLLD": ROOT / "experiments/week15/orszag_tang_precision_smoke_hlld/mca_n30/summary.json",
}


def _mca_for(label: str) -> dict:
    return _load(MCA_SOURCES[label]).get("mca", {})


def _load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _det_rows(summary: dict) -> list[dict]:
    # Brio-Wu pilot uses "deterministic"; OT smoke uses "rows".
    return summary.get("deterministic") or summary.get("rows") or []


def _mca(summary: dict) -> dict:
    return summary.get("mca", {})


def _style(ax):
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.yaxis.label.set_color(INK)
    ax.xaxis.label.set_color(INK)
    ax.title.set_color(INK)


def _variant_short(row: dict) -> str:
    return f"{row['opt']}·{'fm' if row['fastmath'] else 'ie'}·{row['riemann'][:1]}"


# ---------------------------------------------------------------------------
# Figure 1 — precision axis dominance (Linf(rho) per variant, log scale)
# ---------------------------------------------------------------------------
def fig_precision_axis():
    cases = ["Brio-Wu 1D · HLL", "Orszag-Tang 2D · HLL"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    floor = 1e-17
    for ax, case in zip(axes, cases):
        rows = [r for r in _det_rows(_load(PACKETS[case])) if not r.get("is_reference")]
        rows.sort(key=lambda r: (r["precision"] != "double", _variant_short(r)))
        vals = [max(abs(r["Linf_rho"]), floor) for r in rows]
        colors = [C_DOUBLE if r["precision"] == "double" else C_FLOAT for r in rows]
        ax.bar(range(len(rows)), vals, color=colors, width=0.8)
        ax.set_yscale("log")
        ax.set_xticks(range(len(rows)))
        ax.set_xticklabels([_variant_short(r) for r in rows], rotation=90, fontsize=6)
        ax.set_title(case, fontsize=11)
        ax.set_ylabel(r"$L_\infty(\rho)$ vs fp64 reference")
        ax.axhline(1e-15, color=MUTED, linewidth=0.7, linestyle=":")
        _style(ax)
    handles = [plt.Rectangle((0, 0), 1, 1, color=C_DOUBLE),
               plt.Rectangle((0, 0), 1, 1, color=C_FLOAT)]
    fig.legend(handles, ["double (fp64)", "float (fp32)"], loc="upper center",
               ncol=2, frameon=False, fontsize=9, bbox_to_anchor=(0.5, 1.02))
    fig.suptitle("Precision is the dominant error axis: fp32 ≈ 1e-6, fp64 ≈ machine-ε",
                 y=1.08, fontsize=12, color=INK)
    fig.tight_layout()
    fig.savefig(OUT / "fig1_precision_axis.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 2 — MCA noise floor: achievable significant digits (p53 vs p24)
# ---------------------------------------------------------------------------
def fig_mca_noise_floor():
    labels = list(PACKETS.keys())
    fig, ax = plt.subplots(figsize=(9, 5))
    x = range(len(labels))
    width = 0.38
    p53 = [_mca_for(k).get("p53", {}).get("spread_rho") for k in labels]
    p24 = [_mca_for(k).get("p24", {}).get("spread_rho") for k in labels]
    ax.bar([i - width / 2 for i in x], p53, width, color=C_DOUBLE, label="p53 (fp64 surrogate)")
    ax.bar([i + width / 2 for i in x], p24, width, color=C_FLOAT, label="p24 (fp32 surrogate)")
    ax.set_yscale("log")
    ax.set_xticks(list(x))
    ax.set_xticklabels([l.replace(" · ", "\n") for l in labels], fontsize=8)
    ax.set_ylabel(r"MCA per-cell spread of $\rho$  (N=30 samples)")
    ax.set_title("Monte-Carlo Arithmetic noise floor = significant digits actually delivered",
                 fontsize=11, pad=14)
    ax.axhline(1e-15, color=MUTED, linewidth=0.7, linestyle=":")
    ax.legend(frameon=False, fontsize=9, loc="center right")
    _style(ax)
    # Callout in the empty band between the p53 (~1e-15) and p24 (~1e-6) clusters.
    import math
    if p53[0] and p24[0]:
        gap = abs(math.log10(p24[0] / p53[0]))
        digits = abs(math.log10(p24[0]))
        ax.text(0.02, 0.42,
                f"fp32 vs fp64 noise floor:\n≈{gap:.0f} orders of magnitude\n"
                f"→ fp32 delivers only ≈{digits:.0f} significant digits,\n"
                f"   fp64 ≈ 15",
                transform=ax.transAxes, fontsize=9, color=INK, ha="left", va="center",
                bbox=dict(boxstyle="round,pad=0.5", fc="#f9f9f7", ec=GRID, lw=0.8))
    fig.tight_layout()
    fig.savefig(OUT / "fig2_mca_noise_floor.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 3 — compiler / fast-math axis within fp32 (secondary; ordering flags)
# ---------------------------------------------------------------------------
def fig_compiler_axis():
    cases = ["Brio-Wu 1D · HLLD", "Orszag-Tang 2D · HLLD"]  # HLLD carries the ordering flags
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    floor = 1e-9
    for ax, case in zip(axes, cases):
        summ = _load(PACKETS[case])
        rows = [r for r in _det_rows(summ)
                if not r.get("is_reference") and r["precision"] == "float"]
        rows.sort(key=lambda r: (r["opt"], r["fastmath"], r["riemann"]))
        labels = [f"{r['opt']}·{'fm' if r['fastmath'] else 'ie'}·{r['riemann'][:1]}" for r in rows]
        vals = [max(abs(r["Linf_rho"]), floor) for r in rows]
        colors = [C_FLOAT if r["fastmath"] else C_DOUBLE for r in rows]
        ax.bar(range(len(rows)), vals, color=colors, width=0.8)
        ax.set_xticks(range(len(rows)))
        ax.set_xticklabels(labels, rotation=90, fontsize=7)
        ax.set_ylabel(r"$L_\infty(\rho)$ (fp32 variants)")
        nflag = len(summ.get("gates", {}).get("G1", {}).get("ordering_flags", []))
        ax.set_title(f"{case}   ({nflag} fast-math ordering flags)", fontsize=10)
        _style(ax)
    handles = [plt.Rectangle((0, 0), 1, 1, color=C_DOUBLE),
               plt.Rectangle((0, 0), 1, 1, color=C_FLOAT)]
    fig.legend(handles, ["ieee (fp-strict)", "fast-math"], loc="upper center",
               ncol=2, frameon=False, fontsize=9, bbox_to_anchor=(0.5, 1.02))
    fig.suptitle("Compiler / fast-math is a secondary axis (note non-monotone fast-math ordering flags)",
                 y=1.06, fontsize=11, color=INK)
    fig.tight_layout()
    fig.savefig(OUT / "fig3_compiler_axis.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 4 — accuracy-vs-performance: wall-time by precision
# ---------------------------------------------------------------------------
def fig_walltime():
    """fp32 speed-up (fp64 walltime / fp32 walltime) — dimensionless so 1D and 2D
    are comparable on one axis, unlike absolute seconds (0.15 s vs 27 s)."""
    labels = list(PACKETS.keys())
    fig, ax = plt.subplots(figsize=(9, 4.8))
    x = range(len(labels))

    def mean_wt(summ, precision):
        vals = [r["walltime_s"] for r in _det_rows(summ)
                if r["precision"] == precision and r.get("walltime_s")]
        return sum(vals) / len(vals) if vals else 0.0

    speedup, abs_txt = [], []
    for k in labels:
        summ = _load(PACKETS[k])
        d, f = mean_wt(summ, "double"), mean_wt(summ, "float")
        speedup.append(d / f if f else 0.0)
        abs_txt.append(f"fp64 {d:.2g}s / fp32 {f:.2g}s")
    ax.bar(list(x), speedup, width=0.55, color=C_DOUBLE)
    ax.axhline(1.0, color=MUTED, linewidth=0.9, linestyle="--")
    ax.text(len(labels) - 0.5, 1.0, " 1.0 = no speed-up", va="bottom", ha="right",
            fontsize=8, color=MUTED)
    ax.set_xticks(list(x))
    ax.set_xticklabels([l.replace(" · ", "\n") for l in labels], fontsize=8)
    ax.set_ylabel("fp32 speed-up  (fp64 walltime / fp32 walltime)")
    ax.set_title("Accuracy-vs-performance: fp32 buys only a modest speed-up (CPU, single node)",
                 fontsize=11)
    ax.set_ylim(0, max(speedup) * 1.25)
    _style(ax)
    for i in x:
        ax.text(i, speedup[i], f"{speedup[i]:.2f}×", ha="center", va="bottom",
                fontsize=9, color=INK)
        ax.text(i, speedup[i] * 0.5, abs_txt[i], ha="center", va="center",
                fontsize=6.5, color="white", rotation=0)
    fig.tight_layout()
    fig.savefig(OUT / "fig4_walltime.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def copy_ot_heatmaps():
    pairs = {
        "fig5_ot_hll_reference_fields.png":
            ROOT / "experiments/week15/orszag_tang_precision_smoke/headline256_p1/figures/reference_fields.png",
        "fig6_ot_hll_fp32_drift.png":
            ROOT / "experiments/week15/orszag_tang_precision_smoke/headline256_p1/figures/drift_fields.png",
    }
    for dst, src in pairs.items():
        if src.is_file():
            shutil.copyfile(src, OUT / dst)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    fig_precision_axis()
    fig_mca_noise_floor()
    fig_compiler_axis()
    fig_walltime()
    copy_ot_heatmaps()
    print("wrote figures to", OUT)
    for p in sorted(OUT.glob("*.png")):
        print(" -", p.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
