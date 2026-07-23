#!/usr/bin/env python3
"""Generate publication-grade Report 2 figures from Week 16/17 evidence.

The script is read-only with respect to numerical summaries. It does not rerun
solvers. Figures are written with explicit claim boundaries for use in the
Report 2 results/discussion chapters.
"""

from __future__ import annotations

import json
import math
import pathlib
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "week17" / "paper_figures"

SOURCES = {
    "hardware": ROOT / "experiments/week16/cpu_gpu_hardware_axis/summary.json",
    "kh_hll": ROOT / "experiments/week16/kelvin_helmholtz_precision/hll_p1/summary.json",
    "kh_hlld": ROOT / "experiments/week16/kelvin_helmholtz_precision/hlld_p1/summary.json",
    "kh_hll_smoke": ROOT / "experiments/week16/kelvin_helmholtz_precision/hll_p1_smoke/summary.json",
    "kh_hlld_smoke": ROOT / "experiments/week16/kelvin_helmholtz_precision/hlld_p1_smoke/summary.json",
    "kh_mca_smoke_hll": ROOT / "experiments/week16/kelvin_helmholtz_precision/mca_smoke/hll/summary.json",
    "kh_mca_smoke_hlld": ROOT / "experiments/week16/kelvin_helmholtz_precision/mca_smoke/hlld/summary.json",
    "consolidation": ROOT / "experiments/week16/ot_kh_512_consolidation/summary.json",
    "synthesis": ROOT / "experiments/week17/report2_synthesis/summary.json",
}


plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "Times New Roman", "Times"],
        "mathtext.fontset": "cm",
        "font.size": 9.5,
        "axes.titlesize": 10,
        "axes.labelsize": 9.5,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8.2,
        "axes.linewidth": 0.8,
        "axes.edgecolor": "#222222",
        "xtick.direction": "in",
        "ytick.direction": "in",
        "savefig.dpi": 360,
        "figure.dpi": 180,
        "savefig.bbox": "tight",
    }
)

C_BLUE = "#2b6cb0"
C_RED = "#c43c39"
C_GREEN = "#1b7f5a"
C_AMBER = "#b7791f"
C_GRAY = "#4a5568"
C_LIGHT = "#edf2f7"
C_DARK = "#1a202c"
GRID = "#d8dee9"


def load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rows(packet: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(packet.get("rows"), list):
        return list(packet["rows"])
    if isinstance(packet.get("deterministic"), list):
        return list(packet["deterministic"])
    return []


def style_axis(ax: plt.Axes, *, ygrid: bool = True) -> None:
    ax.set_axisbelow(True)
    if ygrid:
        ax.grid(axis="y", color=GRID, linewidth=0.55)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.08,
        1.03,
        label,
        transform=ax.transAxes,
        fontsize=11,
        fontweight="bold",
        ha="right",
        va="bottom",
        color=C_DARK,
    )


def fig_hardware_axis() -> tuple[pathlib.Path, dict[str, str]]:
    data = load(SOURCES["hardware"])
    hw_rows = data["rows"]
    labels = [f"{r['case'].replace('_', ' ')}\n{r['precision']}" for r in hw_rows]
    speedups = [float(r["speedup_cpu_over_gpu"]) for r in hw_rows]
    ulps = [int(r["ulp_max"]) for r in hw_rows]
    colors = [C_BLUE if r["case"] == "orszag_tang_2d" else C_GRAY for r in hw_rows]

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.25), constrained_layout=True)
    ax = axes[0]
    ax.scatter(range(len(ulps)), ulps, marker="D", s=68, color=C_GREEN, zorder=3)
    ax.axhline(0, color=C_GREEN, linewidth=1.8, alpha=0.55)
    ax.set_ylim(-0.08, 0.42)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=0)
    ax.set_ylabel("maximum ULP difference")
    ax.set_title("Same-precision CPU/GPU output agreement")
    for i, u in enumerate(ulps):
        ax.annotate(
            f"{u} ULP",
            (i, u),
            xytext=(0, 11),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8.5,
            fontweight="bold",
        )
    style_axis(ax)
    panel_label(ax, "(a)")

    ax = axes[1]
    ax.bar(range(len(speedups)), speedups, color=colors, width=0.58)
    ax.axhline(1.0, color=C_DARK, linestyle="--", linewidth=0.9)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=0)
    ax.set_ylabel(r"CPU wall time $/$ GPU wall time")
    ax.set_title("Performance is case-size dependent")
    for i, v in enumerate(speedups):
        ax.text(i, v * 1.04 if v >= 1 else v + 0.08, f"{v:.2f}x", ha="center", va="bottom")
    ax.set_ylim(0, max(speedups) * 1.22)
    style_axis(ax)
    panel_label(ax, "(b)")

    fig.suptitle("Week 16 HLL hardware-axis validation", y=1.03, fontsize=11)
    path = OUT / "fig_w16_hardware_axis.png"
    fig.savefig(path)
    plt.close(fig)
    return path, {
        "conclusion": "For the covered HLL Brio-Wu and Orszag-Tang cases, CPU and GPU outputs are bit-exact within the same precision; GPU performance benefit appears only for the larger 2D case.",
        "boundary": "Does not validate HLLD-on-GPU, KH-on-GPU, GPU MCA, or a broad hardware-performance matrix.",
    }


def _kh_precision_points(packet: dict[str, Any]) -> dict[str, list[float]]:
    out = {"double": [], "float": []}
    for row in rows(packet):
        if row.get("is_reference"):
            continue
        precision = row.get("precision")
        if precision in out and row.get("Linf_rho") is not None:
            out[precision].append(max(float(row["Linf_rho"]), 1.0e-18))
    return out


def fig_kh_precision_and_mca() -> tuple[pathlib.Path, dict[str, str]]:
    hll = load(SOURCES["kh_hll"])
    hlld = load(SOURCES["kh_hlld"])
    hll_smoke = load(SOURCES["kh_hll_smoke"])
    hlld_smoke = load(SOURCES["kh_hlld_smoke"])

    fig, axes = plt.subplots(1, 3, figsize=(13.0, 4.35), constrained_layout=True)

    ax = axes[0]
    positions = []
    values = []
    colors = []
    labels = []
    x = 0
    for solver, packet in (("HLL", hll), ("HLLD", hlld)):
        pts = _kh_precision_points(packet)
        for precision, color in (("double", C_BLUE), ("float", C_RED)):
            vals = pts[precision]
            positions.append(x)
            values.append(np.median(vals))
            colors.append(color)
            labels.append(f"{solver}\n{precision}")
            ax.scatter([x] * len(vals), vals, color=color, s=16, alpha=0.48, edgecolors="none")
            x += 1
        x += 0.35
    ax.bar(positions, values, color=colors, width=0.55, alpha=0.78)
    ax.set_yscale("log")
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel(r"$L_\infty(\rho)$ vs fp64 reference")
    ax.set_title(r"Full KH 256$^2$, $t=1$: deterministic precision separation")
    style_axis(ax)
    panel_label(ax, "(a)")

    ax = axes[1]
    labels = []
    p53 = []
    p24 = []
    for solver, packet in (("HLL", hll_smoke), ("HLLD", hlld_smoke)):
        labels.append(solver)
        p53.append(float(packet["mca"]["p53"]["spread_rho"]))
        p24.append(float(packet["mca"]["p24"]["spread_rho"]))
    idx = np.arange(len(labels))
    width = 0.34
    ax.bar(idx - width / 2, p53, width, color=C_BLUE, label="p53")
    ax.bar(idx + width / 2, p24, width, color=C_RED, label="p24")
    ax.set_yscale("log")
    ax.set_xticks(idx)
    ax.set_xticklabels(labels)
    ax.set_ylabel(r"MCA spread of $\rho$ (N=30)")
    ax.set_title(r"Reduced KH 64$^2$, $t=0.05$: Verificarlo noise floor")
    ax.legend(loc="upper left")
    style_axis(ax)
    panel_label(ax, "(b)")

    ax = axes[2]
    categories = ["Full 256^2\nMCA", "Reduced 64^2\nMCA", "Full 256^2\ndeterministic"]
    status = [0, 1, 1]
    colors = [C_AMBER, C_GREEN, C_GREEN]
    ax.bar(categories, status, color=colors, width=0.55)
    ax.set_ylim(0, 1.25)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["not claimed", "evidence"])
    ax.set_title("Claim boundary kept explicit")
    ax.text(0, 0.18, "runtime\nblocked", ha="center", va="bottom", color=C_DARK)
    ax.text(1, 1.04, "completed\nN=30", ha="center", va="bottom", color=C_DARK)
    ax.text(2, 1.04, "24 rows\nper solver", ha="center", va="bottom", color=C_DARK)
    style_axis(ax)
    panel_label(ax, "(c)")

    fig.suptitle("Week 16 Kelvin-Helmholtz precision evidence and MCA boundary", y=1.03, fontsize=11)
    path = OUT / "fig_w16_kh_precision_mca_boundary.png"
    fig.savefig(path)
    plt.close(fig)
    return path, {
        "conclusion": "Full KH deterministic packets show fp32/fp64 separation for both HLL and HLLD; reduced KH Docker-Verificarlo smoke confirms p24 MCA spread is much larger than p53 for the same KH setup family.",
        "boundary": "The reduced 64^2 MCA smoke does not replace the full 256^2 t=1 MCA gate, which remains not claimed because the full N=30 run exceeded the local runtime budget.",
    }


def fig_consolidation_and_synthesis() -> tuple[pathlib.Path, dict[str, str]]:
    cons = load(SOURCES["consolidation"])
    syn = load(SOURCES["synthesis"])
    records = cons["records"]
    cases = [r["case"].replace("_", " ") for r in records]
    l1 = [float(r["L1_rho"]) for r in records]
    divb = [float(r["divB_max"]) for r in records]

    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.35), constrained_layout=True)
    ax = axes[0]
    idx = np.arange(len(cases))
    ax.bar(idx - 0.18, l1, 0.36, color=C_BLUE, label=r"$L_1(\rho)$")
    ax.bar(idx + 0.18, divb, 0.36, color=C_AMBER, label=r"$\max |\nabla\cdot B|$")
    ax.set_yscale("log")
    ax.set_xticks(idx)
    ax.set_xticklabels(cases)
    ax.set_title(r"OT/KH 256$^2$ vs 512$^2$ gate metrics")
    ax.legend()
    style_axis(ax)
    panel_label(ax, "(a)")

    ax = axes[1]
    gates = syn["gates"]
    names = [
        "source\npresent",
        "hardware\ngate",
        "OT/KH\n512 gate",
        "KH full\nMCA",
        "synthesis\ncomplete",
    ]
    vals = [
        bool(gates["source_summaries_present"]),
        bool(gates["hardware_gate_passed"]),
        bool(gates["ot_kh_512_gate_passed"]),
        bool(gates.get("kh_mca_completed", False)),
        bool(gates["synthesis_complete"]),
    ]
    colors = [C_GREEN if v else C_AMBER for v in vals]
    ax.bar(names, [1] * len(vals), color=colors, width=0.62)
    ax.set_ylim(0, 1.25)
    ax.set_yticks([])
    ax.set_title("Week 17 synthesis gate matrix")
    for i, v in enumerate(vals):
        ax.text(
            i,
            0.5,
            "pass" if v else "no\nclaim",
            ha="center",
            va="center",
            color="white",
            fontsize=8.5,
            fontweight="bold",
        )
    style_axis(ax, ygrid=False)
    panel_label(ax, "(b)")

    fig.suptitle("Week 16 validation gates feeding Week 17 synthesis", y=1.03, fontsize=11)
    path = OUT / "fig_w17_gates_and_boundaries.png"
    fig.savefig(path)
    plt.close(fig)
    return path, {
        "conclusion": "Both 2D self-reference gates pass and the Week 17 synthesis has complete source coverage; the synthesis preserves the full-KH-MCA no-claim boundary.",
        "boundary": "Two resolutions do not establish asymptotic convergence, and the full 256^2 KH MCA gate is not promoted.",
    }


def fig_axis_synthesis() -> tuple[pathlib.Path, dict[str, str]]:
    syn = load(SOURCES["synthesis"])
    axes_data = sorted(syn["axis_ranking"], key=lambda r: int(r["rank"]))
    labels = [r["axis"].replace("_", " ") for r in axes_data]
    ranks = [5 - int(r["rank"]) for r in axes_data]
    status_colors = {
        "bounded_primary_effect": C_RED,
        "bounded_cpu_deterministic_variation": C_AMBER,
        "report-grade": C_GREEN,
        "small_or_zero_in_available_packets": C_GRAY,
    }
    colors = [status_colors.get(r["status"], C_GRAY) for r in axes_data]

    fig, ax = plt.subplots(figsize=(8.2, 4.2), constrained_layout=True)
    y = np.arange(len(labels))
    ax.barh(y, ranks, color=colors, height=0.58)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("relative synthesis strength")
    ax.set_title("Week 17 bounded ranking of reproducibility axes")
    for i, row in enumerate(axes_data):
        ax.text(ranks[i] + 0.05, i, f"rank {row['rank']}", va="center", color=C_DARK)
    ax.set_xlim(0, 4.6)
    style_axis(ax)
    path = OUT / "fig_w17_axis_synthesis.png"
    fig.savefig(path)
    plt.close(fig)
    return path, {
        "conclusion": "Within the available W16/W17 synthesis, precision is the dominant observed axis; hardware is report-grade but bit-exact for covered HLL cases, so it is a performance rather than accuracy separator here.",
        "boundary": "Ranking is bounded to available committed packets and does not promote provisional source rows or excluded GPU/MPI axes.",
    }


def write_manifest(entries: list[dict[str, Any]]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": {"name": "hrsc.report2-paper-figures", "version": 1},
        "scope": "Week 16/17 report-facing figures only",
        "sources": {name: str(path.relative_to(ROOT)).replace("\\", "/") for name, path in SOURCES.items()},
        "figures": entries,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Report 2 Week 16/17 Paper Figures",
        "",
        "These figures are generated from Week 16/17 evidence summaries. They are intended for paper/results discussion use and keep claim boundaries explicit.",
        "",
        "| figure | validates / supports | boundary |",
        "|---|---|---|",
    ]
    for entry in entries:
        lines.append(
            f"| `{entry['path']}` | {entry['conclusion']} | {entry['boundary']} |"
        )
    lines.append("")
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    entries: list[dict[str, Any]] = []
    for func in (
        fig_hardware_axis,
        fig_kh_precision_and_mca,
        fig_consolidation_and_synthesis,
        fig_axis_synthesis,
    ):
        path, claim = func()
        entries.append(
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                **claim,
            }
        )
    write_manifest(entries)
    print(OUT.relative_to(ROOT))
    for entry in entries:
        print(entry["path"])
    print(str((OUT / "manifest.json").relative_to(ROOT)).replace("\\", "/"))
    print(str((OUT / "README.md").relative_to(ROOT)).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
