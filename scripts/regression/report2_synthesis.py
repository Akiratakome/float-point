"""Build the Week 17 bounded Report 2 synthesis packet from committed summaries."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from pathlib import Path
from typing import Any


SOURCE_SUMMARIES = {
    "brio_wu_hll": "experiments/week15/brio_wu_precision_pilot_p1/summary.json",
    "brio_wu_hlld": "experiments/week15/brio_wu_precision_pilot_hlld_p1/summary.json",
    "ot_hll": "experiments/week15/orszag_tang_precision_smoke/headline256_p1/summary.json",
    "ot_hll_mca": "experiments/week15/orszag_tang_precision_smoke/mca_n30/summary.json",
    "ot_hlld": "experiments/week15/orszag_tang_precision_smoke_hlld/headline256_p1/summary.json",
    "ot_hlld_mca": "experiments/week15/orszag_tang_precision_smoke_hlld/mca_n30/summary.json",
    "temporal_divergence": "experiments/week15/mhd_temporal_divergence/summary.json",
    "hardware_axis": "experiments/week16/cpu_gpu_hardware_axis/summary.json",
    "kh_hll_precision": "experiments/week16/kelvin_helmholtz_precision/hll_p1/summary.json",
    "kh_hlld_precision": "experiments/week16/kelvin_helmholtz_precision/hlld_p1/summary.json",
    "ot_kh_512": "experiments/week16/ot_kh_512_consolidation/summary.json",
}

CSV_COLUMNS = ["section", "item", "status", "metric", "value", "authority"]


def load_json(repo_root: Path, relative_path: str) -> dict[str, Any]:
    return json.loads((repo_root / relative_path).read_text(encoding="utf-8"))


def load_summary(repo_root: Path, name: str) -> dict[str, Any]:
    return load_json(repo_root, SOURCE_SUMMARIES[name])


def _git_commit(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def _rows_from_precision_packet(packet: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(packet.get("rows"), list):
        return list(packet["rows"])
    deterministic = packet.get("deterministic", [])
    if isinstance(deterministic, list):
        return list(deterministic)
    if isinstance(deterministic, dict) and isinstance(deterministic.get("rows"), list):
        return list(deterministic["rows"])
    return []


def _max_linf_rho(rows: list[dict[str, Any]], precision: str | None = None) -> float | None:
    values: list[float] = []
    for row in rows:
        if precision is not None and row.get("precision") != precision:
            continue
        value = row.get("Linf_rho")
        if value is not None:
            values.append(float(value))
    return max(values) if values else None


def _max_pair_difference(rows: list[dict[str, Any]], key: str) -> float:
    grouped: dict[tuple[Any, ...], dict[Any, float]] = {}
    for row in rows:
        if row.get("is_reference"):
            continue
        value = row.get("Linf_rho")
        if value is None:
            continue
        group_key = (
            row.get("precision"),
            row.get("opt"),
            row.get("fastmath"),
            row.get("riemann"),
        )
        if key == "fastmath":
            group_key = (row.get("precision"), row.get("opt"), row.get("riemann"))
        elif key == "riemann":
            group_key = (row.get("precision"), row.get("opt"), row.get("fastmath"))
        grouped.setdefault(group_key, {})[row.get(key)] = float(value)
    differences = [
        max(values.values()) - min(values.values())
        for values in grouped.values()
        if len(values) >= 2
    ]
    return max(differences) if differences else 0.0


def _collect_precision_rows(summaries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in ("brio_wu_hll", "brio_wu_hlld", "ot_hll", "ot_hlld", "kh_hll_precision", "kh_hlld_precision"):
        for row in _rows_from_precision_packet(summaries[name]):
            row = dict(row)
            row["authority"] = SOURCE_SUMMARIES[name]
            row["packet"] = name
            rows.append(row)
    return rows


def _hardware_summary(packet: dict[str, Any]) -> dict[str, Any]:
    rows = list(packet["rows"])
    ot_speedups = [
        float(row["speedup_cpu_over_gpu"])
        for row in rows
        if row["case"] == "orszag_tang_2d"
    ]
    return {
        "axis": "hardware",
        "rank": 3,
        "status": "report-grade",
        "bounded_result": "bit_exact_for_covered_hll_cases",
        "covered_rows": len(rows),
        "max_ulp": max(int(row["ulp_max"]) for row in rows),
        "ot_speedup_min": min(ot_speedups),
        "ot_speedup_max": max(ot_speedups),
        "authority": SOURCE_SUMMARIES["hardware_axis"],
    }


def _source_entries(summaries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    entries = []
    for name, path in SOURCE_SUMMARIES.items():
        entries.append(
            {
                "name": name,
                "path": path,
                "git_commit": summaries[name].get("git_commit"),
            }
        )
    return entries


def _temporal_records(packet: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for row in packet["records"]:
        samples = row["samples"]
        sample_count = len(samples) if isinstance(samples, list) else int(samples)
        records.append(
            {
                "case": row["case"],
                "samples": sample_count,
                "fit_window": row["fit_window"],
                "lambda_l1": float(row["lambda_l1"]),
                "lambda_linf": float(row["lambda_linf"]),
                "authority": SOURCE_SUMMARIES["temporal_divergence"],
            }
        )
    return records


def _case_sensitivity(summaries: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    records = list(summaries["ot_kh_512"]["records"])
    return [
        {
            "case": row["case"],
            "L1_rho": float(row["L1_rho"]),
            "Linf_rho": float(row["Linf_rho"]),
            "divB_max": float(row["divB_max"]),
            "gate_pass": bool(row["gate_pass"]),
            "authority": SOURCE_SUMMARIES["ot_kh_512"],
        }
        for row in records
    ]


def build_synthesis(repo_root: Path) -> dict[str, Any]:
    summaries = {
        name: load_summary(repo_root, name)
        for name in SOURCE_SUMMARIES
    }
    precision_rows = _collect_precision_rows(summaries)
    max_float_linf = _max_linf_rho(precision_rows, "float")
    max_double_linf = _max_linf_rho(precision_rows, "double")
    max_fastmath_delta = _max_pair_difference(precision_rows, "fastmath")
    max_riemann_delta = _max_pair_difference(precision_rows, "riemann")
    hardware = _hardware_summary(summaries["hardware_axis"])
    temporal = _temporal_records(summaries["temporal_divergence"])
    ot_lambda = next(row["lambda_l1"] for row in temporal if row["case"].startswith("orszag_tang"))
    brio_lambda = next(row["lambda_l1"] for row in temporal if row["case"].startswith("brio_wu"))
    kh_mca_completed = (
        summaries["kh_hll_precision"]["gates"]["mca"]["status"] == "completed"
        and summaries["kh_hlld_precision"]["gates"]["mca"]["status"] == "completed"
    )
    kh_mca_blocked = (
        summaries["kh_hll_precision"]["gates"]["mca"]["status"] == "blocked_environment"
        and summaries["kh_hlld_precision"]["gates"]["mca"]["status"] == "blocked_environment"
    )

    axis_ranking = [
        {
            "axis": "precision",
            "rank": 1,
            "status": "bounded_primary_effect",
            "bounded_result": "float_rows_depart_from_double_baselines_in_available_packets",
            "max_float_linf_rho": max_float_linf,
            "max_double_linf_rho": max_double_linf,
            "authority": "multiple committed Week 15-16 precision summaries",
        },
        {
            "axis": "compiler_flags",
            "rank": 2,
            "status": "bounded_cpu_deterministic_variation",
            "bounded_result": "optimization_and_fastmath_change_some deterministic packets but do not form a unified report-grade gate",
            "max_fastmath_delta_linf_rho": max_fastmath_delta,
            "authority": "multiple committed Week 15-16 precision summaries",
        },
        hardware,
        {
            "axis": "implementation_variant",
            "rank": 4,
            "status": "small_or_zero_in_available_packets",
            "bounded_result": "leq_vs_strict differences are small relative to precision effects in the available CPU packets",
            "max_riemann_delta_linf_rho": max_riemann_delta,
            "authority": "multiple committed Week 15-16 precision summaries",
        },
    ]

    return {
        "schema": {"name": "hrsc.report2-synthesis", "version": 1},
        "experiment": "week17-report2-results-synthesis",
        "git_commit": _git_commit(repo_root),
        "source_summaries": _source_entries(summaries),
        "gates": {
            "synthesis_complete": True,
            "source_summaries_present": all((repo_root / path).is_file() for path in SOURCE_SUMMARIES.values()),
            "kh_mca_block_recorded": kh_mca_blocked,
            "kh_mca_completed": kh_mca_completed,
            "hardware_gate_passed": summaries["hardware_axis"]["gate"]["pass"] is True,
            "ot_kh_512_gate_passed": summaries["ot_kh_512"]["gates"]["all_512_gates_pass"] is True,
        },
        "axis_ranking": axis_ranking,
        "case_sensitivity": _case_sensitivity(summaries),
        "temporal_divergence": temporal,
        "temporal_interpretation": {
            "planned_ot_gt_brio_wu_observed": ot_lambda > brio_lambda,
            "status": "negative-result",
            "authority": SOURCE_SUMMARIES["temporal_divergence"],
        },
        "mpi_omission": {
            "status": "justified_future_work",
            "reason": "single-node OpenMP and CUDA isolate precision, compiler, and hardware effects without MPI reduction-order variability",
            "future_work": "MPI thread and reduction ordering could be explored separately after Report 2",
        },
        "claim_boundaries": {
            "kh_mca": "completed" if kh_mca_completed else "blocked_environment",
            "asymptotic_convergence": False,
            "formal_lyapunov_exponent": False,
            "hll_gpu_scope": ["brio_wu_1d", "orszag_tang_2d"],
            "hll_gpu_excluded": ["hlld_on_gpu", "kh_on_gpu", "gpu_mca", "broad_gpu_matrix"],
            "provisional_rows_promoted": False,
        },
    }


def flatten_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in data["axis_ranking"]:
        rows.append(
            {
                "section": "axis_ranking",
                "item": entry["axis"],
                "status": entry["status"],
                "metric": "rank",
                "value": entry["rank"],
                "authority": entry["authority"],
            }
        )
    for entry in data["temporal_divergence"]:
        rows.append(
            {
                "section": "temporal_divergence",
                "item": entry["case"],
                "status": data["temporal_interpretation"]["status"],
                "metric": "lambda_l1",
                "value": entry["lambda_l1"],
                "authority": entry["authority"],
            }
        )
    for entry in data["case_sensitivity"]:
        rows.append(
            {
                "section": "case_sensitivity",
                "item": entry["case"],
                "status": "gate_pass" if entry["gate_pass"] else "gate_fail",
                "metric": "L1_rho",
                "value": entry["L1_rho"],
                "authority": entry["authority"],
            }
        )
    rows.append(
        {
            "section": "report_method",
            "item": "mpi_omission",
            "status": data["mpi_omission"]["status"],
            "metric": "reason",
            "value": data["mpi_omission"]["reason"],
            "authority": "docs/requirement/overall.md",
        }
    )
    for key, value in data["claim_boundaries"].items():
        rows.append(
            {
                "section": "claim_boundaries",
                "item": key,
                "status": "bounded",
                "metric": "value",
                "value": json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else value,
                "authority": "docs/experiment_logs/report2_evidence_map.md",
            }
        )
    return rows


def render_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# Week 17 Report 2 Results Synthesis",
        "",
        "This packet synthesizes committed Week 15-16 evidence. It does not rerun solvers or widen claim boundaries.",
        "",
        "## Axis Ranking",
        "",
        "| rank | axis | status | bounded result | authority |",
        "|---:|---|---|---|---|",
    ]
    for row in data["axis_ranking"]:
        lines.append(
            f"| {row['rank']} | `{row['axis']}` | `{row['status']}` | "
            f"{row['bounded_result']} | `{row['authority']}` |"
        )
    lines.extend(
        [
            "",
            "## Temporal Divergence",
            "",
            "| case | samples | lambda_l1 | lambda_linf | authority |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for row in data["temporal_divergence"]:
        lines.append(
            f"| `{row['case']}` | {row['samples']} | {row['lambda_l1']:.6e} | "
            f"{row['lambda_linf']:.6e} | `{row['authority']}` |"
        )
    lines.extend(
        [
            "",
            "The planned Orszag-Tang > Brio-Wu temporal-divergence contrast was not observed.",
            "",
            "## 512 Grid Gates",
            "",
            "| case | L1 rho | Linf rho | divB max | gate |",
            "|---|---:|---:|---:|---|",
        ]
    )
    for row in data["case_sensitivity"]:
        lines.append(
            f"| `{row['case']}` | {row['L1_rho']:.6e} | {row['Linf_rho']:.6e} | "
            f"{row['divB_max']:.6e} | `{row['gate_pass']}` |"
        )
    lines.extend(["", "## MPI Omission", "", data["mpi_omission"]["reason"], "", "## Claim Boundaries", ""])
    for key, value in data["claim_boundaries"].items():
        lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines).rstrip() + "\n"


def _plot_axis_ranking(data: dict[str, Any], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = sorted(data["axis_ranking"], key=lambda row: row["rank"], reverse=True)
    labels = [row["axis"].replace("_", " ") for row in rows]
    values = [5 - int(row["rank"]) for row in rows]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(labels, values, color=["#4b5563", "#0f766e", "#2563eb", "#9333ea"])
    ax.set_xlabel("bounded synthesis strength")
    ax.set_title("Report 2 primary-axis synthesis")
    ax.set_xlim(0, 4.5)
    for idx, row in enumerate(rows):
        ax.text(values[idx] + 0.05, idx, f"rank {row['rank']}", va="center")
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def _plot_temporal(data: dict[str, Any], output: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = data["temporal_divergence"]
    labels = [row["case"].replace("_", " ") for row in rows]
    values = [row["lambda_l1"] for row in rows]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(labels, values, color=["#0f766e", "#b45309"])
    ax.set_yscale("log")
    ax.set_ylim(min(values) * 0.5, max(values) * 2.5)
    ax.set_ylabel("lambda_l1")
    ax.set_title("Fixed-window temporal divergence")
    for index, value in enumerate(values):
        ax.text(index, value * 1.15, f"{value:.2e}", ha="center", va="bottom")
    ax.text(
        0.98,
        0.94,
        "planned OT > Brio-Wu contrast not observed",
        ha="right",
        va="top",
        transform=ax.transAxes,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85},
    )
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def write_outputs(data: dict[str, Any], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    summary_json = output_dir / "summary.json"
    summary_csv = output_dir / "summary.csv"
    summary_md = output_dir / "summary.md"
    axis_plot = figures_dir / "axis_ranking.png"
    temporal_plot = figures_dir / "temporal_divergence.png"

    summary_json.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(flatten_rows(data))
    summary_md.write_text(render_markdown(data), encoding="utf-8", newline="\n")
    _plot_axis_ranking(data, axis_plot)
    _plot_temporal(data, temporal_plot)
    return [summary_json, summary_csv, summary_md, axis_plot, temporal_plot]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("experiments/week17/report2_synthesis"),
    )
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    written = write_outputs(build_synthesis(repo_root), args.output_dir)
    for path in written:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
