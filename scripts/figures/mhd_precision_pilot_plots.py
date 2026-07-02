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
