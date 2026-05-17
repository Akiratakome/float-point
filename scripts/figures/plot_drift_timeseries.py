#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _load_summary(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("pairs"), list):
        return list(payload["pairs"])
    if isinstance(payload, list):
        return payload
    raise ValueError("summary JSON must be a list or contain a 'pairs' list")


def _plot_l1(records: list[dict[str, Any]], out_path: Path, normalise_time: bool) -> Path:
    fig, ax = plt.subplots(figsize=(9.5, 5.2), constrained_layout=True)
    for record in records:
        times = record.get("times", [])
        l1 = record.get("l1", [])
        if not times or not l1:
            continue
        x_values = list(times)
        if normalise_time:
            t_end = max(float(t) for t in times)
            if t_end <= 0.0:
                continue
            x_values = [float(t) / t_end for t in times]
        label_parts = [
            str(record.get("case", "")),
            str(record.get("pair", "")),
            str(record.get("variable", "")),
        ]
        label = ": ".join(part for part in label_parts if part)
        ax.plot(x_values, l1, marker="o", linewidth=1.5, markersize=3.5, label=label)

    ax.set_xlabel("normalised time t/t_end" if normalise_time else "time")
    ax.set_ylabel("L1 drift")
    ax.set_yscale("log")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.35)
    if ax.lines:
        ax.legend(
            fontsize=7,
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            borderaxespad=0.0,
            frameon=True,
        )
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot(summary_path: Path, output_dir: Path) -> list[Path]:
    records = _load_summary(summary_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_path = output_dir / "drift_timeseries_l1.png"
    normalised_path = output_dir / "drift_timeseries_l1_normalized.png"
    return [
        _plot_l1(records, raw_path, normalise_time=False),
        _plot_l1(records, normalised_path, normalise_time=True),
    ]


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot HRSC drift time-series summaries.")
    parser.add_argument("--input", type=Path, required=True, help="drift summary JSON")
    parser.add_argument("--output", type=Path, required=True, help="output figure directory")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    plot(args.input, args.output)


if __name__ == "__main__":
    main()
