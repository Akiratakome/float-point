"""Pilot figures for the Week 14 MHD precision summary payload."""

from __future__ import annotations

from pathlib import Path
import math

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

FIELDS = ("rho", "By", "p", "vx")
NORMS = ("L1", "L2", "Linf")
MCA_SPREAD_KEYS = ("spread_rho", "spread_By", "spread_p", "spread_vx")
MCA_SNR_KEYS = ("snr_rho", "snr_By", "snr_p")
MCA_BLOCK_ORDER = ("p53", "p24")


def plot_precision_variant_norms(summary, path) -> None:
    """Plot deterministic non-reference error norms by variant."""
    rows = [
        row for row in summary.get("deterministic", [])
        if isinstance(row, dict) and not row.get("is_reference")
    ]
    labels = [str(row.get("variant", f"row-{idx}")) for idx, row in enumerate(rows)]

    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True)
    for ax, field in zip(axes.ravel(), FIELDS):
        for norm in NORMS:
            values = [_number(row.get(f"{norm}_{field}")) for row in rows]
            if rows:
                ax.plot(range(len(rows)), values, marker="o", linewidth=1.4, label=norm)
        if not rows:
            ax.text(0.5, 0.5, "No non-reference rows", ha="center", va="center",
                    transform=ax.transAxes)
        ax.set_title(f"{field} norms")
        ax.set_ylabel("error")
        ax.grid(True, axis="y", alpha=0.3)
        if any(
            (value is not None and value > 0.0)
            for row in rows
            for norm in NORMS
            for value in (_number(row.get(f"{norm}_{field}")),)
        ):
            ax.set_yscale("log")
        if rows:
            ax.legend(fontsize=8)

    for ax in axes[-1]:
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)

    fig.suptitle("Precision pilot deterministic norms")
    fig.tight_layout()
    _save_png(fig, path)


def plot_mca_noise_floor(summary, path) -> None:
    """Plot MCA spread and SNR summaries for completed precision blocks."""
    mca = summary.get("mca", {})
    blocks = _completed_numeric_mca_blocks(mca)
    names = [name for name, _block in blocks]

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    _plot_grouped_bars(axes[0], names, [block for _name, block in blocks], MCA_SPREAD_KEYS)
    axes[0].set_title("MCA spread")
    axes[0].set_ylabel("spread")
    if _any_positive(blocks, MCA_SPREAD_KEYS):
        axes[0].set_yscale("log")

    _plot_grouped_bars(axes[1], names, [block for _name, block in blocks], MCA_SNR_KEYS)
    axes[1].set_title("MCA SNR")
    axes[1].set_ylabel("SNR")
    if _any_positive(blocks, MCA_SNR_KEYS):
        axes[1].set_yscale("log")

    for ax in axes:
        if not blocks:
            ax.text(0.5, 0.5, "No completed MCA evidence", ha="center", va="center",
                    transform=ax.transAxes)
        ax.grid(True, axis="y", alpha=0.3)
        handles, labels = ax.get_legend_handles_labels()
        if handles and labels:
            ax.legend(fontsize=8)

    fig.suptitle("Precision pilot MCA noise floor")
    fig.tight_layout()
    _save_png(fig, path)


def plot_solver_summary_comparison(summaries, out_dir):
    """Write HLL-vs-HLLD comparison figures from precision-pilot summaries."""
    out = Path(out_dir)
    slug = "_".join(_solver_label(summary).lower() for summary in summaries)
    paths = [
        out / f"compare_{slug}_deterministic_linf.png",
        out / f"compare_{slug}_mca_spread.png",
        out / f"compare_{slug}_mca_snr.png",
    ]
    plot_solver_deterministic_linf(summaries, paths[0])
    plot_solver_mca_metric_comparison(summaries, paths[1], MCA_SPREAD_KEYS, "MCA spread", "spread")
    plot_solver_mca_metric_comparison(summaries, paths[2], MCA_SNR_KEYS, "MCA SNR", "SNR")
    return paths


def plot_solver_deterministic_linf(summaries, path) -> None:
    """Compare worst non-reference deterministic Linf errors by solver."""
    labels = [_solver_label(summary).upper() for summary in summaries]
    worst = [_worst_linf_by_field(summary) for summary in summaries]
    fig, ax = plt.subplots(figsize=(7, 4))
    width = 0.8 / max(len(summaries), 1)
    x_positions = list(range(len(FIELDS)))
    for offset, (label, values_by_field) in enumerate(zip(labels, worst)):
        shift = (offset - (len(worst) - 1) / 2.0) * width
        values = [_number(values_by_field.get(field)) or 0.0 for field in FIELDS]
        ax.bar([x + shift for x in x_positions], values, width=width, label=label)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(FIELDS)
    ax.set_title("HLL vs HLLD deterministic worst Linf")
    ax.set_ylabel("max Linf vs reference")
    if any(
        value is not None and value > 0.0
        for values_by_field in worst
        for value in (_number(values_by_field.get(field)) for field in FIELDS)
    ):
        ax.set_yscale("log")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    _save_png(fig, path)


def plot_solver_mca_metric_comparison(summaries, path, keys, title, ylabel) -> None:
    """Compare completed MCA blocks by solver for the requested metric keys."""
    names, blocks = _ordered_solver_mca_blocks(summaries)
    fig, ax = plt.subplots(figsize=(8, 4))
    _plot_grouped_bars(ax, names, blocks, keys)
    ax.set_title(f"HLL vs HLLD {title}")
    ax.set_ylabel(ylabel)
    if _any_positive(list(zip(names, blocks)), keys):
        ax.set_yscale("log")
    if not blocks:
        ax.text(0.5, 0.5, "No completed MCA evidence", ha="center", va="center",
                transform=ax.transAxes)
    ax.grid(True, axis="y", alpha=0.3)
    handles, labels = ax.get_legend_handles_labels()
    if handles and labels:
        ax.legend(fontsize=8)
    fig.tight_layout()
    _save_png(fig, path)


def _plot_grouped_bars(ax, names, blocks, keys):
    if not blocks:
        return
    width = 0.8 / len(keys)
    x_positions = list(range(len(blocks)))
    for offset, key in enumerate(keys):
        values = [_number(block.get(key)) or 0.0 for block in blocks]
        shift = (offset - (len(keys) - 1) / 2.0) * width
        ax.bar([x + shift for x in x_positions], values, width=width, label=key)
    ax.set_xticks(x_positions)
    ax.set_xticklabels(names)


def _solver_label(summary):
    if isinstance(summary, dict):
        solver = summary.get("solver")
        if solver:
            return str(solver)
    return "solver"


def _worst_linf_by_field(summary):
    rows = [
        row for row in summary.get("deterministic", [])
        if isinstance(row, dict) and not row.get("is_reference")
    ]
    values = {}
    for field in FIELDS:
        candidates = [_number(row.get(f"Linf_{field}")) for row in rows]
        finite = [value for value in candidates if value is not None]
        values[field] = max(finite) if finite else 0.0
    return values


def _ordered_solver_mca_blocks(summaries):
    names = []
    blocks = []
    for block_name in MCA_BLOCK_ORDER:
        for summary in summaries:
            block = summary.get("mca", {}).get(block_name)
            if not isinstance(block, dict) or block.get("status") != "completed":
                continue
            names.append(f"{block_name} {_solver_label(summary).upper()}")
            blocks.append(block)
    return names, blocks


def _number(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if math.isfinite(number):
            return number
    return None


def _completed_numeric_mca_blocks(mca):
    blocks = []
    if not isinstance(mca, dict):
        return blocks
    required = (*MCA_SPREAD_KEYS, *MCA_SNR_KEYS)
    for name, block in sorted(mca.items()):
        if not isinstance(block, dict) or block.get("status") != "completed":
            continue
        if all(_number(block.get(key)) is not None for key in required):
            blocks.append((name, block))
    return blocks


def _any_positive(blocks, keys):
    return any(
        (value is not None and value > 0.0)
        for _name, block in blocks
        for key in keys
        for value in (_number(block.get(key)),)
    )


def _save_png(fig, path):
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150)
    plt.close(fig)
