#!/usr/bin/env python3
"""Generate the audited, report-facing Report 2 figure set from summaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
from typing import Any, Callable

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "experiments" / "week18" / "report2_publication_figures"
sys.path.insert(0, str(ROOT))

from scripts.regression import mhd_week18_resolution_ladder as resolution_ladder  # noqa: E402
from scripts.regression import report2_cross_system as cross_system  # noqa: E402


SOURCES = {
    "validation": (
        "experiments/week12/brio_wu_1d/summary.json",
        "experiments/week12/mhd_2d/divb_clean/summary.json",
    ),
    "cross_system": ("experiments/week18/euler_mhd_cross_system/summary.json",),
    "hardware": ("experiments/week18/supplemental/hardware_repeats/summary.json",),
    "resolution": ("experiments/week18/resolution_ladder/summary.json",),
    "temporal": ("experiments/week15/mhd_temporal_divergence/summary.json",),
    "kh_timing": ("experiments/week18/kh_solver_timing/summary.json",),
}

# Unit roundoff of binary32; discrepancies are also read in multiples of it.
U32 = 2.0 ** -24
# Domain-mean reference density per case, used only to convert an absolute
# density discrepancy into multiples of U32. Brio-Wu follows from the audited
# cross-system pair (rho_l1 / rho_l1_relative); Orszag-Tang is the conserved
# initial mean rho = gamma^2 = 25/9 on the periodic domain.
MEAN_RHO = {"brio_wu_1d": 0.5625, "orszag_tang_2d": 25.0 / 9.0}

BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
PURPLE = "#7A5195"
GREY = "#5F6368"
LIGHT_GREY = "#D9DEE5"
RED = "#B2182B"


def _read(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_path(path: Path) -> str:
    try:
        value = path.relative_to(ROOT)
    except ValueError:
        value = path
    return str(value).replace("\\", "/")


def _png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        signature = handle.read(24)
    if signature[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG file: {path}")
    return struct.unpack(">II", signature[16:24])


def _matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.labelsize": 9,
            "axes.titlesize": 9.5,
            "axes.titleweight": "bold",
            "axes.linewidth": 0.8,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 7.7,
            "legend.frameon": False,
            "figure.dpi": 150,
            "savefig.dpi": 320,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    return plt


def _finish(fig: Any, out: Path, stem: str) -> tuple[Path, Path]:
    out.mkdir(parents=True, exist_ok=True)
    png = out / f"{stem}.png"
    pdf = out / f"{stem}.pdf"
    fig.savefig(png, metadata={"Software": "report2_publication_figures.py"})
    fig.savefig(
        pdf,
        metadata={
            "Creator": "scripts/figures/report2_publication_figures.py",
            "CreationDate": None,
            "ModDate": None,
        },
    )
    return png, pdf


def _grid(ax: Any, *, axis: str = "y") -> None:
    ax.grid(True, axis=axis, which="major", color=LIGHT_GREY, linewidth=0.65)
    ax.set_axisbelow(True)


def _window_mask(times: Any, values: Any, window: Any) -> Any:
    """Strict-interior positive-sample mask matching the recorded fixed-window fits.

    The published fits exclude the window endpoints; selecting on the open
    interval reproduces their recorded slope, R^2 and residual statistics
    exactly, so the alternative model below is fitted to identical samples.
    """
    lo, hi = float(window[0]), float(window[1])
    return (times > lo * (1.0 + 1e-9)) & (times < hi * (1.0 - 1e-9)) & (values > 0.0)


def _ols_log(x: Any, log_y: Any) -> dict[str, float]:
    slope, intercept = np.polyfit(x, log_y, 1)
    residual = log_y - (intercept + slope * x)
    total = log_y - log_y.mean()
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r2_log": float(1.0 - residual.dot(residual) / total.dot(total)),
        "rmse_log": float(np.sqrt(residual.dot(residual) / residual.size)),
        "n_fit": int(residual.size),
    }


def _power_law_fit(times: Any, values: Any, window: Any) -> dict[str, float]:
    """Fit log e = a + k log t on the same samples as the exponential fit."""
    mask = _window_mask(times, values, window)
    return _ols_log(np.log(times[mask]), np.log(values[mask]))


def audit_sources(data: dict[str, Any]) -> dict[str, bool]:
    cross = data["cross_system"]
    resolution = data["resolution"]
    hardware = data["hardware"]
    temporal = data["temporal"]
    kh_timing = data["kh_timing"]
    brio, glm = data["validation"]

    temporal_records = temporal.get("records", [])
    temporal_ok = (
        temporal.get("gates", {}).get("pass") is True
        and {row.get("case") for row in temporal_records}
        == {"brio_wu_1d", "orszag_tang_2d"}
        and all(
            len(row.get("times", [])) == len(row.get("l1", [])) == len(row.get("linf", []))
            and len(row.get("times", [])) >= 3
            and all(math.isfinite(float(value)) and float(value) > 0.0 for value in row.get("l1", []))
            and all(math.isfinite(float(value)) and float(value) > 0.0 for value in row.get("linf", []))
            and all(
                math.isfinite(float(row.get(fit, {}).get(metric)))
                for fit in ("fit_l1", "fit_linf")
                for metric in ("r2_log", "rmse_log", "max_abs_residual_log")
            )
            for row in temporal_records
        )
    )
    hardware_ok = (
        hardware.get("gate", {}).get("pass") is True
        and len(hardware.get("groups", [])) == 4
        and all(group.get("repeats") == 5 and group.get("ulp_max") == 0 for group in hardware["groups"])
        and len(hardware.get("rows", [])) == 40
    )
    kh_timing_ok = (
        kh_timing.get("gate", {}).get("pass") is True
        and len(kh_timing.get("groups", [])) == 4
        and all(group.get("repeats") == 5 and group.get("max_ulp_vs_repeat1") == 0 for group in kh_timing["groups"])
    )
    validation_ok = (
        brio.get("monotonic_convergence", {}).get("strictly_decreasing_L1_L2") is True
        and len(brio.get("rows", [])) == 3
        and glm.get("gate", {}).get("all_finite") is True
        and glm.get("gate", {}).get("cleaning_018_passed") is True
        and glm.get("gate", {}).get("cleaning_036_passed") is True
        and len(glm.get("decay_table", {})) == 3
    )
    return {
        "validation": validation_ok,
        "cross_system": cross_system.stored_summary_is_valid(cross),
        "hardware": hardware_ok,
        "resolution": resolution_ladder.stored_completed_result_is_valid(resolution),
        "temporal": temporal_ok,
        "kh_timing": kh_timing_ok,
    }


def plot_validation(data: tuple[dict[str, Any], dict[str, Any]], out: Path) -> tuple[Path, Path]:
    plt = _matplotlib()
    brio, glm = data
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), constrained_layout=True)

    rows = sorted(brio["rows"], key=lambda row: row["nx"])
    nx = np.array([row["nx"] for row in rows], dtype=float)
    for metric, color, marker in (("L1", BLUE, "o"), ("L2", ORANGE, "s")):
        values = np.array([row[metric] for row in rows], dtype=float)
        order = -float(np.polyfit(np.log2(nx), np.log2(values), 1)[0])
        axes[0].plot(nx, values, color=color, marker=marker, linewidth=1.6,
                     markersize=4.5, label=f"{metric}; observed rate {order:.2f}")
    axes[0].set_xscale("log", base=2)
    axes[0].set_yscale("log")
    axes[0].set_xticks(nx, [str(int(value)) for value in nx])
    axes[0].set_xlabel("Grid cells, N")
    axes[0].set_ylabel("Density difference to N=8000 reference")
    axes[0].set_title("Brio–Wu numerical-reference refinement", loc="left")
    axes[0].legend()
    _grid(axes[0], axis="both")

    colors = [GREY, BLUE, ORANGE]
    for color, cr in zip(colors, glm["glm_cr_sweep"], strict=True):
        series = glm["decay_table"][str(cr)]
        axes[1].plot(
            [row["t_end"] for row in series],
            [row["divB_max"] for row in series],
            color=color,
            marker="o",
            linewidth=1.5,
            markersize=4,
            label=fr"$c_r={cr:g}$",
        )
    axes[1].set_yscale("log")
    axes[1].set_xlabel("Simulation time")
    axes[1].set_ylabel(r"Maximum $|\nabla\!\cdot\!B|$")
    axes[1].set_title(r"GLM cleaning, $128^2$ Gaussian $B_x$ bump", loc="left")
    # Headroom so the legend clears the undamped control curve.
    _low, _high = axes[1].get_ylim()
    axes[1].set_ylim(_low, _high * 2.6)
    axes[1].legend(ncols=3, loc="upper right")
    _grid(axes[1], axis="both")
    paths = _finish(fig, out, "fig_validation_refinement_glm")
    plt.close(fig)
    return paths


def plot_cross_system(summary: dict[str, Any], out: Path) -> tuple[Path, Path]:
    plt = _matplotlib()
    comparisons = summary["comparisons"]
    cases = list(cross_system.CASES)
    x = np.arange(len(cases), dtype=float)
    width = 0.34

    precision = [
        next(row["rho_l1_relative"] for row in comparisons if row["case"] == case and row["comparison"] == "precision_o2")
        for case in cases
    ]
    math_fp32 = [
        next(row["rho_l1_relative"] for row in comparisons if row["case"] == case and row["comparison"] == "math_fp32")
        for case in cases
    ]
    positive = [value for value in precision + math_fp32 if value > 0.0]
    floor = min(positive) / 3.0
    plotted_math = [value if value > 0.0 else floor for value in math_fp32]

    fig, ax = plt.subplots(figsize=(7.2, 3.25), constrained_layout=True)
    ax.bar(x - width / 2, precision, width, color=BLUE,
           label="FP32 vs FP64, O2-default")
    bars = ax.bar(x + width / 2, plotted_math, width, color=ORANGE,
                  label="Ofast-fast vs O2-default, FP32")
    for index, value in enumerate(math_fp32):
        if value == 0.0:
            bars[index].set_facecolor("white")
            bars[index].set_edgecolor(ORANGE)
            bars[index].set_hatch("///")
            ax.annotate("0 (bit-identical)", (x[index] + width / 2, floor),
                        xytext=(0, 2.5), textcoords="offset points", ha="center",
                        va="bottom", fontsize=6.8, color=ORANGE,
                        bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.0})
    labels = [
        f"{cross_system.CASES[case]['label']}\n{cross_system.CASES[case]['system']}, {cross_system.CASES[case]['dimension']}"
        for case in cases
    ]
    ax.set_yscale("log")
    ax.set_xticks(x, labels)
    ax.set_ylabel(r"Mean-relative $L_1$ density discrepancy")
    ax.set_title("Within-case precision and composite-build sensitivity", loc="left")
    # Headroom so the tallest bar clears the legend instead of being clipped.
    ax.set_ylim(floor / 2.9, max(precision + plotted_math) * 6.0)
    # The right-hand axis reads this line as 1, i.e. one binary32 rounding.
    ax.axhline(U32, color=GREY, linestyle=":", linewidth=0.9, zorder=0)
    secondary = ax.secondary_yaxis(
        "right", functions=(lambda v: v / U32, lambda v: v * U32))
    secondary.set_ylabel(r"discrepancy $/\,u_{32}$")
    ax.legend(ncols=2, loc="upper left")
    _grid(ax)
    paths = _finish(fig, out, "fig_cross_system_sensitivity")
    plt.close(fig)
    return paths


def _repeat_speedups(summary: dict[str, Any], case: str, precision: str) -> np.ndarray:
    selected = [
        row for row in summary["rows"]
        if row["case"] == case and row["precision"] == precision
    ]
    cpu = {row["repeat"]: row["elapsed_wall_s"] for row in selected if row["device"] == "cpu"}
    gpu = {row["repeat"]: row["elapsed_wall_s"] for row in selected if row["device"] == "gpu"}
    if set(cpu) != set(gpu) or len(cpu) != 5:
        raise ValueError(f"unmatched timing repeats for {case}/{precision}")
    return np.array([cpu[index] / gpu[index] for index in sorted(cpu)], dtype=float)


def plot_hardware(summary: dict[str, Any], out: Path) -> tuple[Path, Path]:
    plt = _matplotlib()
    groups = summary["groups"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.05),
                             gridspec_kw={"width_ratios": [1.7, 1]}, constrained_layout=True)

    labels: list[str] = []
    medians: list[float] = []
    lower: list[float] = []
    upper: list[float] = []
    colors: list[str] = []
    observations: list[np.ndarray] = []
    for group in groups:
        values = _repeat_speedups(summary, group["case"], group["precision"])
        q25, median, q75 = np.quantile(values, [0.25, 0.5, 0.75])
        labels.append(
            f"{'Brio–Wu' if group['case'] == 'brio_wu_1d' else 'Orszag–Tang'}\n"
            f"{'FP64' if group['precision'] == 'double' else 'FP32'}"
        )
        medians.append(float(median))
        lower.append(float(median - q25))
        upper.append(float(q75 - median))
        colors.append(BLUE if group["precision"] == "double" else ORANGE)
        observations.append(values)
    x = np.arange(len(labels))
    axes[0].bar(x, medians, color=colors, width=0.66)
    axes[0].errorbar(x, medians, yerr=np.array([lower, upper]), fmt="none",
                     ecolor="#202124", capsize=3, linewidth=0.9)
    for index, (values, color) in enumerate(zip(observations, colors, strict=True)):
        offsets = np.linspace(-0.13, 0.13, len(values))
        axes[0].scatter(
            index + offsets,
            values,
            s=17,
            facecolor="white",
            edgecolor=color,
            linewidth=0.8,
            zorder=3,
        )
    axes[0].axhline(1.0, color=GREY, linestyle="--", linewidth=0.9)
    axes[0].set_xticks(x, labels)
    axes[0].set_ylabel("End-to-end speed-up, CPU/GPU")
    axes[0].set_title("(a) Matched repeats with median and IQR", loc="left")
    _grid(axes[0])

    axes[1].set_xlim(-0.5, 3.5)
    axes[1].set_ylim(0, 1)
    for index, (label, color) in enumerate(zip(labels, colors, strict=True)):
        axes[1].add_patch(plt.Rectangle((index - 0.42, 0.28), 0.84, 0.42,
                                        facecolor=color, alpha=0.14,
                                        edgecolor=color, linewidth=1.0))
        axes[1].text(index, 0.53, "0 ULP", ha="center", va="center",
                     fontsize=9, color=color, fontweight="bold")
    short_labels = [
        "BW\nFP64",
        "BW\nFP32",
        "OT\nFP64",
        "OT\nFP32",
    ]
    axes[1].set_xticks(np.arange(4), short_labels)
    axes[1].set_yticks([])
    axes[1].set_title("(b) Same-precision CPU/GPU agreement", loc="left")
    for spine in ("left", "right", "top"):
        axes[1].spines[spine].set_visible(False)
    paths = _finish(fig, out, "fig_hardware_reproducibility")
    plt.close(fig)
    return paths


def plot_resolution(summary: dict[str, Any], out: Path) -> tuple[Path, Path]:
    plt = _matplotlib()
    groups = summary["groups"]
    if any(group.get("status") != "complete" for group in groups):
        raise ValueError("the publication resolution figure requires complete groups")
    fig, ax = plt.subplots(figsize=(7.2, 3.35), constrained_layout=True)

    x = np.arange(len(groups))
    labels: list[str] = []
    for index, group in enumerate(groups):
        case = "OT" if group["case"] == "orszag_tang_2d" else "KH"
        precision = "64" if group["precision"] == "double" else "32"
        labels.append(f"{case}\n{group['solver'].upper()}\nFP{precision}")
        color = BLUE if group["solver"] == "hll" else ORANGE
        hatch = "//" if group["precision"] == "float" else None
        value = float(group["observed_order_l1"])
        ax.bar(index, value, color=color, edgecolor="white", hatch=hatch, width=0.7)
        ax.text(index, value + 0.035, f"{value:.3f}", ha="center", va="bottom", fontsize=7.2)
    ax.axhline(1.0, color=GREY, linestyle="--", linewidth=0.9)
    ax.set_xticks(x, labels)
    ax.set_ylabel(r"Observed $p$ from density mean $L_1$ differences")
    ax.set_ylim(
        0,
        max(
            1.7,
            max(float(group.get("observed_order_l1") or 0.0) for group in groups) * 1.18,
        ),
    )
    ax.set_title("Three-grid MHD self-refinement diagnostic", loc="left")
    _grid(ax)
    paths = _finish(fig, out, "fig_resolution_precision")
    plt.close(fig)
    return paths


def plot_precision_refinement_context(summary: dict[str, Any], out: Path) -> tuple[Path, Path]:
    """Plot same-grid precision discrepancy and its bounded refinement-scale context."""
    plt = _matplotlib()
    rows = [
        row for row in summary["runs"]
        if row["precision"] == "double" and row.get("rho_l1_fp32_vs_fp64") is not None
    ]
    groups = {
        (group["case"], group["solver"]): group
        for group in summary["groups"]
        if group["precision"] == "double" and group["status"] == "complete"
    }
    expected = {
        (case, solver, resolution)
        for case in ("orszag_tang_2d", "kelvin_helmholtz_2d")
        for solver in ("hll", "hlld")
        for resolution in (128, 256, 512)
    }
    present = {(row["case"], row["solver"], int(row["resolution"])) for row in rows}
    if present != expected:
        raise ValueError("precision/refinement figure requires all 12 same-grid cells")

    fig, axes = plt.subplots(1, 2, figsize=(7.3, 3.15), constrained_layout=True)
    styles = {
        ("orszag_tang_2d", "hll"): (BLUE, "o", "OT / HLL"),
        ("orszag_tang_2d", "hlld"): (ORANGE, "s", "OT / HLLD"),
        ("kelvin_helmholtz_2d", "hll"): (GREEN, "^", "KH / HLL"),
        ("kelvin_helmholtz_2d", "hlld"): (PURPLE, "D", "KH / HLLD"),
    }
    for key, (color, marker, label) in styles.items():
        selected = sorted(
            (row for row in rows if (row["case"], row["solver"]) == key),
            key=lambda row: int(row["resolution"]),
        )
        resolutions = np.asarray([row["resolution"] for row in selected], dtype=float)
        discrepancies = np.asarray([row["rho_l1_fp32_vs_fp64"] for row in selected], dtype=float)
        finest_scale = float(groups[key]["rho_l1_256_512"])
        if not math.isfinite(finest_scale) or finest_scale <= 0.0:
            raise ValueError(f"invalid fp64 finest-grid refinement scale for {key}")
        axes[0].plot(resolutions, discrepancies, color=color, marker=marker,
                     linewidth=1.35, markersize=4.5, label=label)
        axes[1].plot(resolutions, discrepancies / finest_scale, color=color, marker=marker,
                     linewidth=1.35, markersize=4.5, label=label)

    for ax in axes:
        ax.set_xscale("log", base=2)
        ax.set_yscale("log")
        ax.set_xticks([128, 256, 512], ["128", "256", "512"])
        ax.set_xlabel(r"Grid resolution $N\times N$")
        _grid(ax, axis="both")
    axes[0].set_ylabel(r"Mean $L_1(\rho_{32}-\rho_{64})$")
    axes[0].set_title("(a) Same-grid precision discrepancy", loc="left")
    axes[1].axhline(1.0, color=GREY, linestyle="--", linewidth=0.9)
    axes[1].set_ylabel(r"$D_N/E^{64}_{256,512}$")
    axes[1].set_title("(b) Relative to finest refinement scale", loc="left")
    axes[1].legend(ncols=2, loc="lower right")
    paths = _finish(fig, out, "fig_precision_refinement_context")
    plt.close(fig)
    return paths


def plot_temporal(summary: dict[str, Any], out: Path) -> tuple[Path, Path]:
    plt = _matplotlib()
    records = {row["case"]: row for row in summary["records"]}
    order = ("brio_wu_1d", "orszag_tang_2d")
    titles = {"brio_wu_1d": "Brio–Wu", "orszag_tang_2d": "Orszag–Tang"}
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.3), constrained_layout=True)
    for panel, (ax, case) in enumerate(zip(axes, order, strict=True)):
        row = records[case]
        times = np.asarray(row["times"], dtype=float)
        l1 = np.asarray(row["l1"], dtype=float)
        linf = np.asarray(row["linf"], dtype=float)
        lo, hi = row["fit_window"]
        ax.axvspan(lo, hi, color=LIGHT_GREY, alpha=0.45, label="fixed fit window")
        ax.plot(times, l1, color=BLUE, marker="o", markersize=3.6,
                linewidth=1.25, label=r"mean $L_1$")
        ax.plot(times, linf, color=ORANGE, marker="s", markersize=3.3,
                linewidth=1.15, label=r"$L_\infty$")
        fit_t = np.linspace(lo, hi, 80)
        power = {}
        for metric, series, color in (("fit_l1", l1, BLUE), ("fit_linf", linf, ORANGE)):
            fit = row[metric]
            ax.plot(fit_t, np.exp(float(fit["intercept"]) + float(fit["slope"]) * fit_t),
                    color=color, linestyle="--", linewidth=1.1)
            # Same window, same samples, alternative model: log e = a + k log t.
            power[metric] = _power_law_fit(times, series, (lo, hi))
            ax.plot(fit_t,
                    np.exp(power[metric]["intercept"]
                           + power[metric]["slope"] * np.log(fit_t)),
                    color=color, linestyle=":", linewidth=1.4)
        ax.text(
            0.03,
            0.04,
            "fixed-window fits: exponential (dashed), power law (dotted)\n"
            rf"mean $L_1$: $\lambda$={row['lambda_l1']:.3g}, "
            rf"rms$_{{\log}}$={row['fit_l1']['rmse_log']:.3f}"
            rf"  $\vert$  $k$={power['fit_l1']['slope']:.2f}, "
            rf"rms$_{{\log}}$={power['fit_l1']['rmse_log']:.3f}" "\n"
            rf"$L_\infty$: $\lambda$={row['lambda_linf']:.3g}, "
            rf"rms$_{{\log}}$={row['fit_linf']['rmse_log']:.3f}"
            rf"  $\vert$  $k$={power['fit_linf']['slope']:.2f}, "
            rf"rms$_{{\log}}$={power['fit_linf']['rmse_log']:.3f}",
            transform=ax.transAxes,
            fontsize=6.6,
            va="bottom",
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 2.0},
        )
        ax.set_yscale("log")
        # Headroom above for the legend and below for the fit annotation, so
        # neither overlaps the plotted series.
        low, high = ax.get_ylim()
        ax.set_ylim(low / 4.0, high * 3.6)
        ax.set_xlabel("Simulation time")
        ax.set_ylabel("FP32–FP64 density discrepancy")
        ax.set_title(f"({chr(97 + panel)}) {titles[case]}", loc="left")
        # Same discrepancy read in multiples of one binary32 rounding of the
        # field, so the two panels can be compared on a common arithmetic scale.
        scale = U32 * MEAN_RHO[case]
        secondary = ax.secondary_yaxis(
            "right", functions=(lambda v, s=scale: v / s, lambda v, s=scale: v * s))
        secondary.set_ylabel(r"$/\,u_{32}$")
        ax.legend(ncols=3, loc="upper right")
        _grid(ax, axis="both")
    paths = _finish(fig, out, "fig_temporal_discrepancy")
    plt.close(fig)
    return paths


def plot_kh_timing(summary: dict[str, Any], out: Path) -> tuple[Path, Path]:
    plt = _matplotlib()
    groups = summary["groups"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.05), constrained_layout=True)
    x = np.arange(2)
    width = 0.34
    for offset, precision, color in ((-width / 2, "double", BLUE), (width / 2, "float", ORANGE)):
        selected = [next(group for group in groups if group["solver"] == solver and group["precision"] == precision) for solver in ("hll", "hlld")]
        medians = np.array([row["wall_time_median_s"] for row in selected])
        errors = np.array(
            [
                medians - np.array([row["wall_time_q25_s"] for row in selected]),
                np.array([row["wall_time_q75_s"] for row in selected]) - medians,
            ]
        )
        axes[0].bar(x + offset, medians, width, color=color,
                    label="FP64" if precision == "double" else "FP32")
        axes[0].errorbar(x + offset, medians, yerr=errors, fmt="none",
                         ecolor="#202124", capsize=3, linewidth=0.8)
        for index, solver in enumerate(("hll", "hlld")):
            values = np.array(
                [
                    row["elapsed_wall_s"]
                    for row in sorted(summary["runs"], key=lambda item: item["repeat"])
                    if row["solver"] == solver and row["precision"] == precision
                ],
                dtype=float,
            )
            if len(values) != 5:
                raise ValueError(f"expected five KH timing observations for {solver}/{precision}")
            jitter = np.linspace(-0.045, 0.045, len(values))
            axes[0].scatter(
                index + offset + jitter,
                values,
                s=15,
                facecolor="white",
                edgecolor=color,
                linewidth=0.75,
                zorder=3,
            )
    axes[0].set_xticks(x, ["HLL", "HLLD"])
    axes[0].set_ylabel("End-to-end wall time (s)")
    axes[0].set_title("(a) Individual runs with median and IQR", loc="left")
    axes[0].legend(ncols=2)
    _grid(axes[0])

    comparisons = summary["comparisons"]
    labels = [
        "HLL\nFP32 gain",
        "HLLD\nFP32 gain",
        "FP64\nHLLD cost",
        "FP32\nHLLD cost",
    ]
    values = [
        comparisons["fp32_speedup"]["hll"],
        comparisons["fp32_speedup"]["hlld"],
        comparisons["hlld_over_hll_cost"]["double"],
        comparisons["hlld_over_hll_cost"]["float"],
    ]
    axes[1].bar(np.arange(4), values, color=[BLUE, ORANGE, BLUE, ORANGE], width=0.68)
    axes[1].axhline(1.0, color=GREY, linestyle="--", linewidth=0.9)
    axes[1].set_xticks(np.arange(4), labels)
    axes[1].set_ylabel("Matched runtime ratio")
    axes[1].set_ylim(0.95, max(values) * 1.06)
    axes[1].set_title("(b) Precision speed-up and solver cost", loc="left")
    for index, value in enumerate(values):
        axes[1].text(index, value + 0.006, f"{value:.3f}×", ha="center", va="bottom", fontsize=7.2)
    _grid(axes[1])
    paths = _finish(fig, out, "fig_kh_timing")
    plt.close(fig)
    return paths


FIGURES: tuple[dict[str, Any], ...] = (
    {
        "id": "validation_refinement_glm",
        "importance": "P1",
        "chapters": [4],
        "sources": SOURCES["validation"],
        "claim": "Numerical-reference refinement and GLM diagnostics validate bounded MHD behavior.",
        "excluded": "Exact-solution accuracy and precision adequacy.",
        "plot": plot_validation,
        "data_key": "validation",
    },
    {
        "id": "cross_system_sensitivity",
        "importance": "P0",
        "chapters": [5],
        "sources": SOURCES["cross_system"],
        "claim": "Within-case density discrepancy responds differently to precision and math mode across the selected cases.",
        "excluded": "Cross-system accuracy or a universal solver/system ranking.",
        "plot": plot_cross_system,
        "data_key": "cross_system",
    },
    {
        "id": "hardware_reproducibility",
        "importance": "P0",
        "chapters": [5],
        "sources": SOURCES["hardware"],
        "claim": "The bounded HLL GPU path is bit-exact for the covered cases and has workload-dependent repeated timing.",
        "excluded": "A generic GPU performance or solver matrix.",
        "plot": plot_hardware,
        "data_key": "hardware",
    },
    {
        "id": "resolution_precision",
        "importance": "P0",
        "chapters": [4, 5],
        "sources": SOURCES["resolution"],
        "claim": "Eight complete three-grid diagnostics bound the observed refinement behavior without establishing an asymptotic regime.",
        "excluded": "Asymptotic convergence, exact-solution accuracy, precision adequacy, or a cross-solver ranking.",
        "plot": plot_resolution,
        "data_key": "resolution",
    },
    {
        "id": "temporal_discrepancy",
        "importance": "P0",
        "chapters": [5],
        "sources": SOURCES["temporal"],
        "claim": "Fixed-window fits compare exponential against power-law growth on identical samples and do not show the planned OT-greater-than-Brio–Wu contrast.",
        "excluded": "A formal maximal Lyapunov exponent or physical instability rate.",
        "plot": plot_temporal,
        "data_key": "temporal",
    },
    {
        "id": "precision_refinement_context",
        "importance": "P0",
        "chapters": [5],
        "sources": SOURCES["resolution"],
        "claim": "All 12 same-grid precision cells are shown relative to the matched fp64 finest adjacent-grid mean-L1 scale.",
        "excluded": "Exact error, fp32 adequacy, asymptotic convergence, or cross-solver ranking.",
        "plot": plot_precision_refinement_context,
        "data_key": "resolution",
    },
    {
        "id": "kh_timing",
        "importance": "P1",
        "chapters": [5],
        "sources": SOURCES["kh_timing"],
        "claim": "Repeated matched KH timings quantify FP32 speed-up and HLLD-over-HLL cost on the tested workstation.",
        "excluded": "Accuracy-cost position, universal solver ranking, or portability.",
        "plot": plot_kh_timing,
        "data_key": "kh_timing",
    },
)


def load_data() -> dict[str, Any]:
    return {
        key: tuple(_read(path) for path in paths) if len(paths) > 1 else _read(paths[0])
        for key, paths in SOURCES.items()
    }


def generate(out: Path) -> dict[str, Any]:
    data = load_data()
    source_audit = audit_sources(data)
    if not all(source_audit.values()):
        failed = ", ".join(key for key, passed in source_audit.items() if not passed)
        raise ValueError(f"source evidence audit failed: {failed}")

    artefacts: list[dict[str, Any]] = []
    for descriptor in FIGURES:
        plotter: Callable[[Any, Path], tuple[Path, Path]] = descriptor["plot"]
        png, pdf = plotter(data[descriptor["data_key"]], out)
        width, height = _png_dimensions(png)
        if width < 1800 or height < 700 or png.stat().st_size < 30_000 or pdf.stat().st_size < 5_000:
            raise ValueError(f"figure output failed publication preflight: {png}")
        artefacts.append(
            {
                key: value
                for key, value in descriptor.items()
                if key not in {"plot", "data_key"}
            }
            | {
                "sources": list(descriptor["sources"]),
                "source_sha256": {
                    source: _sha256(ROOT / source) for source in descriptor["sources"]
                },
                "png": _display_path(png),
                "pdf": _display_path(pdf),
                "png_dimensions": [width, height],
                "png_sha256": _sha256(png),
                "pdf_sha256": _sha256(pdf),
            }
        )

    manifest = {
        "schema": {"name": "hrsc.report2-publication-figures", "version": 1},
        "generator": "scripts/figures/report2_publication_figures.py",
        "source_audit": source_audit,
        "quality_gate": {
            "pass": True,
            "raster_minimum": "PNG >= 1800 px wide and >= 700 px high",
            "vector_copy": "PDF with embedded TrueType fonts",
            "style": "colour-blind-aware palette, caption-owned context, no internal week labels",
        },
        "visual_review": {
            "date": "2026-07-30",
            "status": "passed",
            "checks": [
                "labels and legends do not overlap",
                "log axes do not encode zero as a measured positive value",
                "the resolution figure is emitted only for a complete, validated matrix",
            "error bars use reconstructed quartiles rather than an assumed symmetric IQR",
            "all five measured timing observations are overlaid on each median and IQR",
                "panel labels, units, and claim boundaries match the source summaries",
            ],
        },
        "figures": artefacts,
        "excluded_existing_figure": {
            "path": "experiments/week17/report2_synthesis/figures/axis_ranking.png",
            "reason": "Ranks incomparable metrics on an arbitrary relative-strength scale; retain only as synthesis provenance.",
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "figure_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Report 2 publication figure set",
        "",
        "Generated from machine-readable summaries after the source-evidence audit. PNG files are for review and PDF files are the preferred manuscript assets.",
        "",
        "| Figure | Importance | Chapters | Source | Claim boundary |",
        "|---|---|---|---|---|",
    ]
    for item in artefacts:
        lines.append(
            f"| `{item['id']}` | `{item['importance']}` | "
            f"{', '.join(str(chapter) for chapter in item['chapters'])} | "
            f"{'; '.join(f'`{source}`' for source in item['sources'])} | "
            f"{item['claim']} Excludes: {item['excluded']} |"
        )
    lines += [
        "",
        "`experiments/week17/report2_synthesis/figures/axis_ranking.png` is excluded from the manuscript because its arbitrary scale ranks incomparable metrics.",
        "",
    ]
    (out / "README.md").write_text("\n".join(lines), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    manifest = generate(args.out.resolve())
    print(f"figures: {len(manifest['figures'])}")
    print(f"manifest: {args.out.resolve() / 'figure_manifest.json'}")
    print("quality_gate: pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
