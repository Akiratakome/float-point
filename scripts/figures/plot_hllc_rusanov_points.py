from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


VAR_COLS = {"rho": 1, "u": 2, "p": 4}
VAR_LABELS = {"rho": r"Density $\rho$", "u": r"Velocity $u$", "p": r"Pressure $p$"}

DEFAULT_DATA_DIR = Path("experiments/week3/week3_rusanov/data")
DEFAULT_OUT_DIR = Path("experiments/week7/verificarlo_report1_refresh/figures")


@dataclass(frozen=True)
class TestCase:
    name: str
    title: str


TEST_CASES = (
    TestCase("sod", "Sod"),
    TestCase("toro3", "Blast Wave"),
    TestCase("toro4", "Lax"),
    TestCase("toro5", "Slow Contact"),
    TestCase("stationary_contact", "Stationary Contact"),
)


def load_text(path: Path) -> np.ndarray:
    return np.loadtxt(path)


def _validate_solution(name: str, data: np.ndarray) -> None:
    if data.ndim != 2 or data.shape[1] <= max(VAR_COLS.values()):
        raise ValueError(f"{name} must be a 2D array with columns x,rho,u,v,p")


def plot_point_comparison(
    test_title: str,
    exact: np.ndarray,
    hllc: np.ndarray,
    rusanov: np.ndarray,
    out_path: Path,
    reference_label: str = "Reference",
) -> None:
    _validate_solution("exact", exact)
    _validate_solution("hllc", hllc)
    _validate_solution("rusanov", rusanov)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharex=True)
    for ax, (var, col) in zip(axes, VAR_COLS.items()):
        ax.plot(exact[:, 0], exact[:, col], color="black", linewidth=1.2, label=reference_label)
        ax.plot(hllc[:, 0], hllc[:, col], "o", markersize=2.0, alpha=0.55, label="HLLC")
        ax.plot(rusanov[:, 0], rusanov[:, col], "s", markersize=2.0, alpha=0.45, label="Rusanov")
        ax.set_title(VAR_LABELS[var])
        ax.set_xlabel("x")
        ax.grid(True, alpha=0.25)
    axes[0].set_ylabel(test_title)
    axes[0].legend(fontsize=8)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def plot_summary(cases: list[tuple[TestCase, np.ndarray, np.ndarray]], out_path: Path) -> None:
    if not cases:
        raise ValueError("No HLLC/Rusanov cases were available for plotting")

    fig, axes = plt.subplots(len(cases), 3, figsize=(13, 3.2 * len(cases)), squeeze=False, sharex=False)
    for row, (case, hllc, rusanov) in enumerate(cases):
        for col_idx, (var, col) in enumerate(VAR_COLS.items()):
            ax = axes[row, col_idx]
            ax.plot(hllc[:, 0], hllc[:, col], color="black", linewidth=1.0, label="HLLC line")
            ax.plot(hllc[:, 0], hllc[:, col], "o", markersize=1.7, alpha=0.45, label="HLLC")
            ax.plot(rusanov[:, 0], rusanov[:, col], "s", markersize=1.7, alpha=0.40, label="Rusanov")
            if row == 0:
                ax.set_title(VAR_LABELS[var])
            if col_idx == 0:
                ax.set_ylabel(case.title)
            ax.grid(True, alpha=0.25)
            if row == 0 and col_idx == 0:
                ax.legend(fontsize=8)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def available_cases(data_dir: Path) -> list[tuple[TestCase, np.ndarray, np.ndarray]]:
    cases = []
    for case in TEST_CASES:
        hllc_path = data_dir / f"{case.name}_hllc.txt"
        rusanov_path = data_dir / f"{case.name}_rusanov.txt"
        if not hllc_path.exists() or not rusanov_path.exists() or rusanov_path.stat().st_size == 0:
            continue
        hllc = load_text(hllc_path)
        rusanov = load_text(rusanov_path)
        cases.append((case, hllc, rusanov))
    return cases


def write_point_figures(data_dir: Path, out_dir: Path) -> list[Path]:
    outputs = []
    cases = available_cases(data_dir)
    for case, hllc, rusanov in cases:
        out_path = out_dir / f"hllc_rusanov_points_{case.name}.png"
        plot_point_comparison(
            case.title,
            hllc,
            hllc,
            rusanov,
            out_path,
            reference_label="HLLC line",
        )
        outputs.append(out_path)

    if cases:
        summary_path = out_dir / "hllc_rusanov_points_summary.png"
        plot_summary(cases, summary_path)
        outputs.append(summary_path)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    for path in write_point_figures(args.data_dir, args.out_dir):
        print(path)


if __name__ == "__main__":
    main()
