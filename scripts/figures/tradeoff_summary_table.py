"""Headline conclusion table for the supervisor.

Joins three CSVs into an 8-column markdown table per (solver, precision):

    Solver | Precision | μ_trunc_L1 | σ_FP_L1 | s_worst_q05 | s_req(N) |
            s_worst − s_req | regime

Rows are discovered from the intersection of the SNR and LoSoS CSV inputs, so
p53 and p24-real-float rows can live in the same headline table. Per-variable
values are reported for ρ in the headline; full breakdown lives in the source
CSVs.

Conventions:
- μ_trunc_L1 is taken from s_req CSV (reference-anchored), NOT from
  snr_scalars.csv (which is self-referenced — see plan §A4.4 component
  coupling note).
- σ_FP_L1 is taken from snr_scalars.csv.
- s_worst_q05 / s_reliability_q05 / s_accuracy_q05 are taken from the
  re-run losos CSV (with 800² block-avg reference).

No magic numbers — regime margins live in scripts/_tradeoff_thresholds.py.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _tradeoff_thresholds import (
    REGIME_MARGIN_OVER_PROVISIONED,
    REGIME_MARGIN_WELL_MATCHED,
)

_HEADLINE_VAR = "rho"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _classify_regime(margin: float) -> str:
    if margin > REGIME_MARGIN_OVER_PROVISIONED:
        return "over-provisioned"
    if margin > REGIME_MARGIN_WELL_MATCHED:
        return "well-matched"
    if margin > 0.0:
        return "marginal"
    return "round-off-limited"


def _row_for_solver(
    solver: str, precision: str,
    snr_rows: list[dict], losos_rows: list[dict], s_req_rows: list[dict],
) -> dict[str, object]:
    """Pick out the headline-variable row from each source CSV and join."""
    def pick(rows, **filters):
        for r in rows:
            if all(r.get(k) == v for k, v in filters.items()):
                return r
        raise KeyError(f"no row matches {filters} in {rows[0].keys() if rows else 'empty'}")

    s_req_row = pick(s_req_rows, solver=solver, variable=_HEADLINE_VAR)
    snr_row = pick(snr_rows, solver=solver, precision=precision, variable=_HEADLINE_VAR)
    losos_row = pick(losos_rows, solver=solver, precision=precision, variable=_HEADLINE_VAR)

    mu_trunc_l1 = float(s_req_row["mu_trunc_l1"])
    sigma_fp_l1 = float(snr_row["sigma_fp_l1"])
    s_worst_q05 = float(losos_row["s_worst_q05"])
    s_req = float(s_req_row["s_req"])
    margin = s_worst_q05 - s_req
    return {
        "solver": solver,
        "precision": precision,
        "mu_trunc_l1": mu_trunc_l1,
        "sigma_fp_l1": sigma_fp_l1,
        "s_worst_q05": s_worst_q05,
        "s_req": s_req,
        "margin": margin,
        "regime": _classify_regime(margin),
    }


def build_rows(
    snr_rows: list[dict], losos_rows: list[dict], s_req_rows: list[dict],
) -> list[dict[str, object]]:
    """Build all headline rows present in both SNR and LoSoS inputs."""
    snr_keys = {
        (r.get("solver"), r.get("precision"))
        for r in snr_rows
        if r.get("variable") == _HEADLINE_VAR
    }
    losos_keys = {
        (r.get("solver"), r.get("precision"))
        for r in losos_rows
        if r.get("variable") == _HEADLINE_VAR
    }
    keys = sorted(
        snr_keys & losos_keys,
        key=lambda item: (item[0] or "", item[1] or ""),
    )
    return [
        _row_for_solver(str(solver), str(precision), snr_rows, losos_rows, s_req_rows)
        for solver, precision in keys
    ]


def _format_markdown(rows: list[dict], N: int) -> str:
    """Render the headline 8-col markdown table + footnote + conclusion stub."""
    lines: list[str] = []
    lines.append(f"# LW Config 3 — Tradeoff conclusion (N={N}², headline row = ρ)\n")
    lines.append("| Solver  | Precision   | μ_trunc_L1 | σ_FP_L1 | s_worst_q05 | s_req(N) | s_worst − s_req | regime |")
    lines.append("|---------|-------------|-----------:|--------:|------------:|---------:|----------------:|--------|")
    for r in rows:
        lines.append(
            f"| {r['solver'].upper():<7} | {r['precision']:<11} | "
            f"{r['mu_trunc_l1']:.3e} | {r['sigma_fp_l1']:.3e} | "
            f"{r['s_worst_q05']:.2f} | {r['s_req']:.2f} | "
            f"{r['margin']:+.2f} | {r['regime']} |"
        )
    lines.append("")
    lines.append("**Notes:**")
    lines.append("")
    lines.append(f"- All values shown for the ρ variable; full per-variable breakdown is in `experiments/week4/metrics/s_req_lw_config3_{N}.csv` and `experiments/week4/metrics/losos_lw_config3_{N}.csv`.")
    lines.append("- `μ_trunc_L1` is reference-anchored (candidate 200² minus 800² block-averaged reference, primitive variables); the column overrides the self-referenced value present in `snr_scalars.csv`.")
    lines.append(f"- `s_worst_q05 = min(s_reliability, s_accuracy)` 5th-percentile over cells; the LoSoS reference is the same 800² block-averaged primitive `.npz` produced by `s_req_metric.py`. No upper-bound footnote is needed in this round.")
    lines.append("- `regime` is classified by `s_worst − s_req`: `> 2.0 = over-provisioned`, `(1.0, 2.0] = well-matched`, `(0, 1.0] = marginal`, `≤ 0 = round-off-limited`. Thresholds in `scripts/_tradeoff_thresholds.py`.")
    precisions = ", ".join(sorted({str(r["precision"]) for r in rows}))
    lines.append(f"- Included precision labels: {precisions}. Each non-p53 row must come from an MCA ensemble, not a single deterministic float run.")
    return "\n".join(lines) + "\n"


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build the headline LW-Config-3 tradeoff table.")
    p.add_argument("--snr-csv", required=True, type=Path)
    p.add_argument("--losos-csv", required=True, type=Path)
    p.add_argument("--s-req-csv", required=True, type=Path)
    p.add_argument("--N", required=True, type=int)
    p.add_argument("--out", required=True, type=Path)
    return p.parse_args()


def main() -> None:
    args = _parse_args()
    snr = _read_csv(args.snr_csv)
    losos = _read_csv(args.losos_csv)
    s_req = _read_csv(args.s_req_csv)

    rows = build_rows(snr, losos, s_req)
    if not rows:
        raise RuntimeError("No matching headline rows found between SNR and LoSoS CSVs")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(_format_markdown(rows, args.N))
    print(f"[summary] wrote {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
