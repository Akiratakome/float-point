"""Full LW Config 3 Pareto example for sigma_FP_L1 and delivered digits.

Default inputs reuse existing Week 4 A4 metric CSVs and select headline rho
rows for HLLC/Rusanov. By default this uses the validated p53 and
p24-real-float rows already present in Week 4; callers can request additional
precision labels once the matching metric rows exist. An optional normalized
input CSV may be supplied with columns:

solver, precision_label, sigma_fp_l1, s_worst_q05, s_req, regime
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SNR_CSV = REPO_ROOT / "experiments" / "week4" / "metrics" / "a4_snr_with_float.csv"
DEFAULT_LOSOS_CSV = REPO_ROOT / "experiments" / "week4" / "metrics" / "a4_losos_with_float.csv"
DEFAULT_S_REQ_CSV = REPO_ROOT / "experiments" / "week4" / "metrics" / "s_req_lw_config3_200.csv"
HEADLINE_VARIABLE = "rho"
DEFAULT_PRECISIONS = ("p53", "p24-real-float")
DEFAULT_SOLVERS = ("hllc", "rusanov")
CSV_COLUMNS = (
    "solver",
    "precision_label",
    "sigma_fp_l1",
    "s_worst_q05",
    "s_req",
    "precision_margin",
    "regime",
)


@dataclass(frozen=True)
class ParetoRow:
    solver: str
    precision_label: str
    sigma_fp_l1: float
    s_worst_q05: float
    s_req: float
    regime: str

    @property
    def precision_margin(self) -> float:
        return self.s_worst_q05 - self.s_req

    @property
    def label(self) -> str:
        return f"{self.solver.upper()} {self.precision_label}"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def _pick(rows: Iterable[dict[str, str]], **filters: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in filters.items()):
            return row
    raise KeyError(f"no row matches {filters}")


def _regime_from_margin(margin: float) -> str:
    if margin <= 0.0:
        return "precision-adequacy deficit"
    if margin <= 1.0:
        return "marginal precision-adequacy margin"
    if margin <= 2.0:
        return "well-matched precision-adequacy margin"
    return "over-provisioned precision-adequacy margin"


def load_normalized_rows(path: Path) -> list[ParetoRow]:
    rows = _read_csv(path)
    required = {"solver", "precision_label", "sigma_fp_l1", "s_worst_q05", "s_req", "regime"}
    if rows:
        missing = required.difference(rows[0])
        if missing:
            raise ValueError(f"{path} missing columns: {', '.join(sorted(missing))}")

    return [
        ParetoRow(
            solver=row["solver"],
            precision_label=row["precision_label"],
            sigma_fp_l1=float(row["sigma_fp_l1"]),
            s_worst_q05=float(row["s_worst_q05"]),
            s_req=float(row["s_req"]),
            regime=row["regime"],
        )
        for row in rows
    ]


def build_rows_from_week4(
    snr_csv: Path = DEFAULT_SNR_CSV,
    losos_csv: Path = DEFAULT_LOSOS_CSV,
    s_req_csv: Path = DEFAULT_S_REQ_CSV,
    *,
    solvers: Sequence[str] = DEFAULT_SOLVERS,
    precisions: Sequence[str] = DEFAULT_PRECISIONS,
) -> list[ParetoRow]:
    snr_rows = _read_csv(snr_csv)
    losos_rows = _read_csv(losos_csv)
    s_req_rows = _read_csv(s_req_csv)

    points: list[ParetoRow] = []
    for solver in solvers:
        s_req_row = _pick(s_req_rows, solver=solver, variable=HEADLINE_VARIABLE)
        s_req = float(s_req_row["s_req"])
        for precision in precisions:
            filters = {"solver": solver, "precision": precision, "variable": HEADLINE_VARIABLE}
            try:
                snr_row = _pick(snr_rows, **filters)
                losos_row = _pick(losos_rows, **filters)
            except KeyError as exc:
                raise KeyError(f"missing requested Week 4 Pareto row: {filters}") from exc
            s_worst_q05 = float(losos_row["s_worst_q05"])
            margin = s_worst_q05 - s_req
            points.append(
                ParetoRow(
                    solver=solver,
                    precision_label=precision,
                    sigma_fp_l1=float(snr_row["sigma_fp_l1"]),
                    s_worst_q05=s_worst_q05,
                    s_req=s_req,
                    regime=_regime_from_margin(margin),
                )
            )
    return points


def write_rows(rows: Sequence[ParetoRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "solver": row.solver,
                    "precision_label": row.precision_label,
                    "sigma_fp_l1": f"{row.sigma_fp_l1:.12g}",
                    "s_worst_q05": f"{row.s_worst_q05:.12g}",
                    "s_req": f"{row.s_req:.12g}",
                    "precision_margin": f"{row.precision_margin:.6f}",
                    "regime": row.regime,
                }
            )


def _style_for(row: ParetoRow) -> tuple[str, str]:
    colors = {"hllc": "#1f77b4", "rusanov": "#d62728"}
    markers = {"p53": "o", "p32": "^", "p24-real-float": "s", "p16": "P", "p8": "X"}
    return colors.get(row.solver, "#333333"), markers.get(row.precision_label, "D")


def plot_logx(rows: Sequence[ParetoRow], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    for row in rows:
        color, marker = _style_for(row)
        ax.scatter(row.sigma_fp_l1, row.s_worst_q05, s=78, color=color, marker=marker, label=row.label)
        ax.annotate(row.label, (row.sigma_fp_l1, row.s_worst_q05), xytext=(8, 4), textcoords="offset points", fontsize=8)

    for s_req in sorted({round(row.s_req, 12) for row in rows}):
        ax.axhline(s_req, color="#666666", linestyle="--", linewidth=1.0, alpha=0.7)
        ax.text(max(row.sigma_fp_l1 for row in rows), s_req, f" s_req={s_req:.2f}", va="bottom", fontsize=8)

    ax.set_xscale("log")
    ax.set_xlabel("sigma_FP_L1 (rho)")
    ax.set_ylabel("s_worst_q05 (rho)")
    ax.set_title("LW Config 3 Pareto example, N=200")
    ax.grid(True, which="both", linestyle=":", alpha=0.45)
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def plot_twopanel(rows: Sequence[ParetoRow], path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.4))
    ax_digits, ax_margin = axes

    for row in rows:
        color, marker = _style_for(row)
        ax_digits.scatter(row.sigma_fp_l1, row.s_worst_q05, s=72, color=color, marker=marker, label=row.label)
        ax_digits.annotate(row.label, (row.sigma_fp_l1, row.s_worst_q05), xytext=(7, 4), textcoords="offset points", fontsize=8)
        ax_margin.scatter(row.sigma_fp_l1, row.precision_margin, s=72, color=color, marker=marker)
        ax_margin.annotate(row.label, (row.sigma_fp_l1, row.precision_margin), xytext=(7, 4), textcoords="offset points", fontsize=8)

    for ax in axes:
        ax.set_xscale("log")
        ax.set_xlabel("sigma_FP_L1 (rho)")
        ax.grid(True, which="both", linestyle=":", alpha=0.45)

    for s_req in sorted({round(row.s_req, 12) for row in rows}):
        ax_digits.axhline(s_req, color="#666666", linestyle="--", linewidth=1.0, alpha=0.7)

    ax_margin.axhline(0.0, color="#666666", linestyle="--", linewidth=1.0, alpha=0.8)
    ax_digits.set_ylabel("s_worst_q05 (rho)")
    ax_margin.set_ylabel("precision-adequacy margin")
    ax_digits.set_title("Delivered digits")
    ax_margin.set_title("Margin to s_req(N)")
    ax_digits.legend(fontsize=8, loc="best")
    fig.suptitle("LW Config 3 full Pareto example, N=200")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def write_summary(rows: Sequence[ParetoRow], path: Path) -> None:
    min_margin = min(row.precision_margin for row in rows)
    max_margin = max(row.precision_margin for row in rows)
    precision_labels = ", ".join(sorted({row.precision_label for row in rows}, key=_precision_sort_key))
    p24 = [row for row in rows if row.precision_label == "p24-real-float"]
    p53 = [row for row in rows if row.precision_label == "p53"]
    sigma_ratio = ""
    if p24 and p53:
        quietest_p53 = min(row.sigma_fp_l1 for row in p53)
        loudest_p24 = max(row.sigma_fp_l1 for row in p24)
        sigma_ratio = f"\nThe plotted p24-real-float noise is about {loudest_p24 / quietest_p53:.2e} times the quietest p53 noise."

    path.write_text(
        "# Full Pareto Example For Philip\n\n"
        "The plot demonstrates the trade-off between emitted FP noise "
        "(sigma_FP_L1, x-axis) and delivered significant digits "
        "(s_worst_q05, y-axis). The s_req(N) target marks the significant "
        "digits implied by truncation error at the same grid resolution.\n\n"
        "Log scaling is required because p24-real-float and p53 differ by many "
        "orders of magnitude in emitted noise. The two-panel view separates "
        "the delivered digits from the precision-adequacy margin "
        "s_worst_q05 - s_req(N), avoiding ambiguous round-off-limited wording.\n\n"
        f"Included precision labels: {precision_labels}.\n\n"
        f"Precision-adequacy margins in this input range from {min_margin:.2f} "
        f"to {max_margin:.2f}.{sigma_ratio}\n",
        encoding="ascii",
    )


def _precision_sort_key(label: str) -> tuple[int, str]:
    order = {"p8": 8, "p16": 16, "p24-real-float": 24, "p32": 32, "p53": 53}
    return order.get(label, 10_000), label


def _parse_csv_list(value: str) -> tuple[str, ...]:
    items = tuple(item.strip() for item in value.split(",") if item.strip())
    if not items:
        raise argparse.ArgumentTypeError("list must contain at least one item")
    return items


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the Week 7 full Pareto example.")
    parser.add_argument("--input", type=Path, help="Optional normalized Pareto CSV.")
    parser.add_argument("--output", required=True, type=Path, help="Output directory.")
    parser.add_argument("--snr-csv", type=Path, default=DEFAULT_SNR_CSV)
    parser.add_argument("--losos-csv", type=Path, default=DEFAULT_LOSOS_CSV)
    parser.add_argument("--s-req-csv", type=Path, default=DEFAULT_S_REQ_CSV)
    parser.add_argument(
        "--precisions",
        type=_parse_csv_list,
        default=DEFAULT_PRECISIONS,
        help="Comma-separated Week 4 precision labels to plot when --input is not supplied.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_args(argv)
    rows = (
        load_normalized_rows(args.input)
        if args.input
        else build_rows_from_week4(args.snr_csv, args.losos_csv, args.s_req_csv, precisions=args.precisions)
    )
    if not rows:
        raise ValueError("no Pareto rows to plot")

    args.output.mkdir(parents=True, exist_ok=True)
    write_rows(rows, args.output / "pareto_lw3_full.csv")
    plot_logx(rows, args.output / "pareto_lw3_full_logx.png")
    plot_twopanel(rows, args.output / "pareto_lw3_full_twopanel.png")
    write_summary(rows, args.output / "summary.md")
    print(f"[pareto-full] wrote {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
