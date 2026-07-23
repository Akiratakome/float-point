#!/usr/bin/env python3
"""Consolidate Orszag-Tang and Kelvin-Helmholtz 512-grid validation gates."""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "experiments" / "week16" / "ot_kh_512_consolidation"
DEFAULT_OT = ROOT / "experiments" / "week13" / "orszag_tang" / "summary.json"
DEFAULT_KH = ROOT / "experiments" / "week16" / "kelvin_helmholtz_precision" / "validation" / "summary.json"


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def collect_case(case: str, summary_path: pathlib.Path) -> dict:
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    results = payload["results"]
    gates = {
        "gate_norms": bool(results.get("gate_norms")),
        "gate_mass": bool(results.get("gate_mass")),
        "gate_divb": bool(results.get("gate_divb")),
    }
    return {
        "case": case,
        "authority": summary_path.relative_to(ROOT).as_posix() if summary_path.is_relative_to(ROOT) else str(summary_path),
        "source_experiment": payload.get("experiment", ""),
        "source_git_commit": payload.get("git_commit", ""),
        "L1_rho": results.get("L1_rho"),
        "L2_rho": results.get("L2_rho"),
        "Linf_rho": results.get("Linf_rho"),
        "mass_rel": results.get("mass_rel"),
        "divB_max": results.get("divB_max_cr018"),
        **gates,
        "gate_pass": all(gates.values()),
    }


def _fmt(value) -> str:
    return "n/a" if value is None else f"{float(value):.3e}"


def write_outputs(out_dir: pathlib.Path, records: list[dict]) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    all_pass = all(record["gate_pass"] for record in records)
    payload = {
        "experiment": "week16-ot-kh-512-consolidation",
        "git_commit": git_commit(),
        "gates": {
            "all_512_gates_pass": all_pass,
            "asymptotic_convergence_claim": False,
        },
        "claim_boundary": (
            "The paired 256^2-vs-512^2 gates are engineering sensitivity checks. "
            "Two resolutions do not establish asymptotic convergence."
        ),
        "records": records,
    }

    fieldnames = [
        "case",
        "authority",
        "L1_rho",
        "L2_rho",
        "Linf_rho",
        "mass_rel",
        "divB_max",
        "gate_norms",
        "gate_mass",
        "gate_divb",
        "gate_pass",
    ]
    with (out_dir / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow({key: record.get(key) for key in fieldnames})

    lines = [
        "# Week 16 OT/KH 512^2 Consolidation",
        "",
        "This packet consolidates the completed 256^2 candidate vs 512^2 double-reference gates for the 2D MHD benchmarks.",
        "",
        "| case | authority | L1(rho) | Linf(rho) | mass_rel | divB_max | gate pass? |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for record in records:
        lines.append(
            "| {case} | `{authority}` | {l1} | {linf} | {mass} | {divb} | {gate} |".format(
                case=record["case"],
                authority=record["authority"],
                l1=_fmt(record["L1_rho"]),
                linf=_fmt(record["Linf_rho"]),
                mass=_fmt(record["mass_rel"]),
                divb=_fmt(record["divB_max"]),
                gate=record["gate_pass"],
            )
        )
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "The two-resolution gates support bounded engineering sensitivity checks; they do not establish asymptotic convergence.",
            "",
            f"All 512 gates pass: `{all_pass}`.",
            "Asymptotic convergence claim: `False`.",
            "",
        ]
    )

    (out_dir / "summary.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (out_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--ot-summary", type=pathlib.Path, default=DEFAULT_OT)
    parser.add_argument("--kh-summary", type=pathlib.Path, default=DEFAULT_KH)
    args = parser.parse_args()

    records = [
        collect_case("orszag_tang", args.ot_summary),
        collect_case("kelvin_helmholtz", args.kh_summary),
    ]
    payload = write_outputs(args.out, records)
    print((args.out / "summary.md").read_text(encoding="utf-8"), end="")
    if not payload["gates"]["all_512_gates_pass"]:
        raise SystemExit("GATE FAIL: one or more 512 validation gates failed")


if __name__ == "__main__":
    main()
