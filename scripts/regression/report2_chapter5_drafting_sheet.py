#!/usr/bin/env python3
"""Generate the Chapter 5 fact ledger and status-aware MCA table."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "experiments" / "week18" / "chapter5_drafting_sheet"
SOURCES = {
    "cross_system": ROOT / "experiments/week18/euler_mhd_cross_system/summary.json",
    "build_semantics": ROOT / "experiments/week20/brio_wu_build_semantics/summary.json",
    "kh_timing": ROOT / "experiments/week18/kh_solver_timing/summary.json",
    "hardware": ROOT / "experiments/week18/supplemental/hardware_repeats/summary.json",
    "resolution": ROOT / "experiments/week18/resolution_ladder/summary.json",
    "resolution_pair": ROOT / "experiments/week18/resolution_ladder_pair_completion/summary.json",
    "temporal": ROOT / "experiments/week15/mhd_temporal_divergence/summary.json",
    "thread": ROOT / "experiments/week18/supplemental/thread_repro/summary.json",
    "cfl": ROOT / "experiments/week18/supplemental/kh_cfl/summary.json",
    "precision_mca": ROOT / "experiments/week18/precision_mca_gate/summary.json",
    "csc": ROOT / "experiments/week18/csc_findings_synthesis/summary.json",
    "kh_local_hll": ROOT / "experiments/week16/kelvin_helmholtz_precision/mca_smoke/hll/summary.json",
    "kh_local_hlld": ROOT / "experiments/week16/kelvin_helmholtz_precision/mca_smoke/hlld/summary.json",
    "kh_hll": ROOT / "experiments/week16/kelvin_helmholtz_precision/hll_p1/summary.json",
    "kh_hlld": ROOT / "experiments/week16/kelvin_helmholtz_precision/hlld_p1/summary.json",
}
FACT_FIELDS = ("task", "subject", "metric", "value", "baseline", "scope", "status", "source")
MCA_FIELDS = ("case", "solver", "virtual_precision", "samples", "scope", "status", "allowed_use", "source")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def scope_text(scope: dict[str, Any]) -> str:
    ordered = ("test", "case", "nx", "ny", "t_end", "cfl", "riemann", "omp_num_threads")
    return ", ".join(f"{key}={scope[key]}" for key in ordered if key in scope)


def fact(task: str, subject: str, metric: str, value: Any, baseline: str,
         scope: str, status: str, source: Path) -> dict[str, Any]:
    return {"task": task, "subject": subject, "metric": metric, "value": value,
            "baseline": baseline, "scope": scope, "status": status, "source": rel(source)}


def build() -> dict[str, Any]:
    packets = {name: load(path) for name, path in SOURCES.items()}
    checks = {
        "cross_system": packets["cross_system"]["gate"]["pass"],
        "build_semantics": packets["build_semantics"]["gate"]["pass"],
        "kh_timing": packets["kh_timing"]["gate"]["pass"],
        "hardware": packets["hardware"]["gate"]["pass"],
        "resolution": packets["resolution"]["gate"]["pass"],
        "resolution_pair": packets["resolution_pair"]["gate"]["pass"],
        "resolution_precision_pairs": packets["resolution"]["claims"]["resolution_dependent_precision_separation"],
        "temporal": packets["temporal"]["gates"]["pass"],
        "thread": packets["thread"]["gate"]["pass"],
        "cfl": packets["cfl"]["gate"]["pass"],
        "precision_mca_audit": packets["precision_mca"]["gate"]["audit_pass"],
        "csc_validation": packets["csc"]["gate"]["pass"],
        "kh_full_mca_blocked": all(
            packets[key]["gates"]["mca"]["status"] == "blocked_environment"
            for key in ("kh_hll", "kh_hlld")
        ),
    }
    rows: list[dict[str, Any]] = []

    cross = packets["cross_system"]
    for item in (row for row in cross["comparisons"] if row["comparison"] == "precision_o2"):
        run = next(row for row in cross["runs"] if row["run_id"] == f"{item['case']}-double-o2")
        shape = "x".join(str(value) for value in run["shape"][:2])
        scope = f"{item['system']}, {item['dimension']}, grid={shape}, t={run['final_time']}, solver={item['solver']}"
        rows.append(fact("5.2", item["label"], "rho_L1_mean_relative", item["rho_l1_relative"],
                         "FP32 vs same-case FP64 / O2-default", scope, "report-grade", SOURCES["cross_system"]))
        rows.append(fact("5.2", item["label"], "rho_Linf", item["rho_linf"],
                         "FP32 vs same-case FP64 / O2-default", scope, "report-grade", SOURCES["cross_system"]))

    build_semantics = packets["build_semantics"]
    compiler = build_semantics["builds"][0]["compiler"]
    build_scope = (
        f"compiler={compiler['id']} {compiler['version']}, "
        f"{scope_text(build_semantics['configuration'])}"
    )
    for item in build_semantics["comparisons"]:
        subject = f"Brio-Wu {item['solver'].upper()} {item['precision']}"
        for metric in ("rho_l1_mean", "rho_linf"):
            rows.append(fact(
                "5.4", subject, f"{metric}_{item['axis']}", item[metric],
                item["changed_axis"], build_scope, "report-grade",
                SOURCES["build_semantics"],
            ))

    timing = packets["kh_timing"]
    timing_scope = scope_text({"case": "kelvin_helmholtz_2d", **timing["configuration"]})
    for item in timing["groups"]:
        subject = f"KH {item['solver'].upper()} {item['precision']}"
        rows.append(fact("5.5", subject, "wall_time_median_s", item["wall_time_median_s"],
                         "one warm-up excluded; five measured runs", timing_scope, "report-grade", SOURCES["kh_timing"]))
        rows.append(fact("5.5", subject, "wall_time_IQR_s", item["wall_time_iqr_s"],
                         "P75-P25", timing_scope, "report-grade", SOURCES["kh_timing"]))

    for item in packets["hardware"]["groups"]:
        scope = f"case={item['case']}, precision={item['precision']}, repeats={item['repeats']}"
        rows.append(fact("5.6", f"{item['case']} {item['precision']}", "CPU_median_over_GPU_median",
                         item["speedup_median"], "matched CPU/GPU saved-state runs", scope,
                         "report-grade", SOURCES["hardware"]))
        rows.append(fact("5.6", f"{item['case']} {item['precision']}", "max_ULP",
                         item["ulp_max"], "matched same-precision CPU/GPU state", scope,
                         "report-grade", SOURCES["hardware"]))

    resolution = packets["resolution"]
    pair = resolution["precision_pair_completion"]
    pair_packet = packets["resolution_pair"]
    pair_run = next(
        row for row in resolution["runs"]
        if row["case"] == "orszag_tang_2d" and row["solver"] == "hlld"
        and row["precision"] == "float" and int(row["resolution"]) == 512
    )
    pair_scope = (
        f"grid=512x512, t={pair_packet['scope']['target_time']}, CFL={pair_run['cfl']}, "
        f"steps={pair_run['steps']}"
    )
    for metric, value in pair["metrics"].items():
        rows.append(fact("5.7", "Orszag--Tang HLLD 512", metric, value,
                         "FP32 vs corrected retained FP64", pair_scope,
                         "report-grade", SOURCES["resolution_pair"]))
    rows.append(fact("5.7", "resolution ladder", "complete_self_refinement_groups", 8,
                     "three grids per case/solver/precision group", "OT/KH; HLL/HLLD; FP64/FP32; 128/256/512",
                     "report-grade", SOURCES["resolution"]))
    rows.append(fact("5.7", "resolution ladder", "complete_same_grid_precision_cells", 12,
                     "FP32 vs FP64 at each case/solver/grid", "OT/KH; HLL/HLLD; 128/256/512",
                     "report-grade", SOURCES["resolution"]))

    for item in packets["temporal"]["records"]:
        scope = f"case={item['case']}, samples={len(item['times'])}, fit_window={item['fit_window']}"
        for metric, value in (("lambda_L1_mean", item["lambda_l1"]), ("R2_log_L1_mean", item["fit_l1"]["r2_log"]),
                              ("lambda_Linf", item["lambda_linf"]), ("R2_log_Linf", item["fit_linf"]["r2_log"])):
            rows.append(fact("5.8", item["case"], metric, value, "aligned FP32 vs FP64 density states",
                             scope, "negative-result", SOURCES["temporal"]))

    for item in packets["cfl"]["groups"]:
        rows.append(fact("5.10", f"KH {item['solver'].upper()} CFL={item['cfl']}",
                         "rho_Linf_FP32_vs_FP64", item["Linf_rho_fp32_vs_fp64"],
                         "same-solver FP64", "grid=256x256, t=1.0", "report-grade", SOURCES["cfl"]))
    rows.append(fact("5.10", "OT/KH OpenMP", "max_ULP_across_threads",
                     packets["thread"]["gate"]["max_ulp"], "thread 1 saved state",
                     "threads=1,2,4,8; covered OT/KH rows", "report-grade", SOURCES["thread"]))

    mca_rows: list[dict[str, Any]] = []
    for item in packets["precision_mca"]["rows"]:
        for virtual in ("p53", "p24"):
            mca_rows.append({
                "case": item["case"], "solver": item["solver"], "virtual_precision": virtual,
                "samples": item["mca"][f"{virtual}_n"], "scope": scope_text(item["mca_scope"]),
                "status": item["status"],
                "allowed_use": "bounded deterministic-plus-MCA result" if item["promotion_pass"]
                else "reduced-scope context only; do not merge with deterministic headline",
                "source": rel(SOURCES["precision_mca"]),
            })
    csc_scope = scope_text(packets["csc"]["scope"])
    for solver in ("hll", "hlld"):
        mca_rows.append({"case": "kelvin_helmholtz_2d", "solver": solver,
                         "virtual_precision": "p53+p24", "samples": 4, "scope": csc_scope,
                         "status": "validation", "allowed_use": "pipeline and reduced-case directional evidence only",
                         "source": rel(SOURCES["csc"])})
    for solver, key in (("hll", "kh_local_hll"), ("hlld", "kh_local_hlld")):
        packet = packets[key]
        for virtual in ("p53", "p24"):
            mca_rows.append({"case": "kelvin_helmholtz_2d", "solver": solver,
                             "virtual_precision": virtual, "samples": packet["mca"][virtual]["n"],
                             "scope": "case=kelvin_helmholtz_2d, nx=64, ny=64, t_end=0.05, cfl=0.4",
                             "status": "reduced-scope-provenance",
                             "allowed_use": "local Docker toolchain and reduced-case noise-scale provenance only",
                             "source": rel(SOURCES[key])})
    for solver, key in (("hll", "kh_hll"), ("hlld", "kh_hlld")):
        mca_rows.append({"case": "kelvin_helmholtz_2d", "solver": solver,
                         "virtual_precision": "p53+p24", "samples": 0,
                         "scope": "grid=256x256, t=1.0", "status": "blocked",
                         "allowed_use": "limitation only; no MCA numerical claim",
                         "source": rel(SOURCES[key])})

    return {
        "schema": {"name": "hrsc.report2-chapter5-drafting-sheet", "version": 1},
        "gate": {"pass": all(checks.values()), "checks": checks},
        "claim_boundary": "Rows preserve their own metric, baseline, scope and status; no cross-axis ranking is defined.",
        "sources": [{"path": rel(path), "sha256": sha256(path)} for path in SOURCES.values()],
        "facts": rows,
        "mca_status": mca_rows,
    }


def write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(fields: tuple[str, ...], rows: list[dict[str, Any]]) -> list[str]:
    lines = ["| " + " | ".join(fields) + " |", "|" + "|".join("---" for _ in fields) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(row[field]).replace("|", "\\|") for field in fields) + " |")
    return lines


def write(payload: dict[str, Any], out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_csv(out / "facts.csv", FACT_FIELDS, payload["facts"])
    write_csv(out / "mca_status_table.csv", MCA_FIELDS, payload["mca_status"])
    summary = ["# Chapter 5 drafting sheet", "", f"Gate: `{payload['gate']['pass']}`.", "",
               payload["claim_boundary"], "", "## Fact ledger", ""]
    summary.extend(markdown_table(FACT_FIELDS, payload["facts"]))
    summary.extend(["", "## Table 5.1 candidate: MCA evidence status", ""])
    summary.extend(markdown_table(MCA_FIELDS, payload["mca_status"]))
    (out / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    table = ["# Table 5.1 candidate: MCA evidence status", ""]
    table.extend(markdown_table(MCA_FIELDS, payload["mca_status"]))
    (out / "mca_status_table.md").write_text("\n".join(table) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    payload = build()
    write(payload, args.out)
    print(args.out / "summary.json")
    return 0 if payload["gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
