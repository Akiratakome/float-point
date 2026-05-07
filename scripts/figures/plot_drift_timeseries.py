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


def plot(summary_path: Path, output_dir: Path) -> list[Path]:
    records = _load_summary(summary_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "drift_timeseries_l1.png"

    fig, ax = plt.subplots(figsize=(7.0, 4.5), constrained_layout=True)
    for record in records:
        times = record.get("times", [])
        l1 = record.get("l1", [])
        if not times or not l1:
            continue
        label = f"{record.get('case', '')}: {record.get('pair', '')}".strip(": ")
        ax.plot(times, l1, marker="o", linewidth=1.5, markersize=3.5, label=label)

    ax.set_xlabel("time")
    ax.set_ylabel("L1 drift")
    ax.set_yscale("log")
    ax.grid(True, which="both", linewidth=0.4, alpha=0.35)
    if ax.lines:
        ax.legend(fontsize=8)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return [out_path]


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
