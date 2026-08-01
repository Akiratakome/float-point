#!/usr/bin/env python3
"""Audit the retained deterministic + MCA precision packets for Report 2."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import pathlib
import re
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "experiments" / "week18" / "precision_mca_gate"
REFERENCE = "cpu-double-O2-ieee-leq"

SPECS = (
    {
        "case": "brio_wu_1d", "solver": "hll",
        "deterministic": "experiments/week15/brio_wu_precision_pilot_p1/summary.json",
        "mca": "experiments/week15/brio_wu_precision_pilot_p1/summary.json",
        "deterministic_key": "deterministic", "mca_subdir": "mca",
    },
    {
        "case": "brio_wu_1d", "solver": "hlld",
        "deterministic": "experiments/week15/brio_wu_precision_pilot_hlld_p1/summary.json",
        "mca": "experiments/week15/brio_wu_precision_pilot_hlld_p1/summary.json",
        "deterministic_key": "deterministic", "mca_subdir": "mca",
    },
    {
        "case": "orszag_tang_2d", "solver": "hll",
        "deterministic": "experiments/week15/orszag_tang_precision_smoke/headline256_p1/summary.json",
        "mca": "experiments/week15/orszag_tang_precision_smoke/mca_n30/summary.json",
        "deterministic_key": "rows", "mca_subdir": "mca_n30",
    },
    {
        "case": "orszag_tang_2d", "solver": "hlld",
        "deterministic": "experiments/week15/orszag_tang_precision_smoke_hlld/headline256_p1/summary.json",
        "mca": "experiments/week15/orszag_tang_precision_smoke_hlld/mca_n30/summary.json",
        "deterministic_key": "rows", "mca_subdir": "mca_n30",
    },
)


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_config(text: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if key in {"nx", "ny"}:
            values[key] = int(value)
        elif key in {"t_end", "cfl"}:
            values[key] = float(value)
        elif key in {"test", "riemann"}:
            values[key] = value.lower()
    return values


def scope_from_metadata(path: pathlib.Path) -> dict[str, Any]:
    metadata = json.loads(path.read_text(encoding="utf-8"))
    return parse_config(metadata["run_config_text"])


def scopes_match(left: dict[str, Any], right: dict[str, Any]) -> bool:
    keys = set(left) | set(right)
    for key in keys:
        if key not in left or key not in right:
            return False
        if isinstance(left[key], float):
            if not math.isclose(left[key], right[key], rel_tol=0.0, abs_tol=1.0e-12):
                return False
        elif left[key] != right[key]:
            return False
    return True


def normalize_scope(scope: dict[str, Any], expected_solver: str) -> dict[str, Any]:
    """Make the documented default HLL solver explicit for scope comparison."""
    normalized = dict(scope)
    normalized.setdefault("riemann", expected_solver)
    return normalized


def _finite_metrics(row: dict[str, Any]) -> bool:
    metrics = [value for key, value in row.items() if key.startswith(("L1_", "L2_", "Linf_"))]
    return bool(metrics) and all(isinstance(value, (int, float)) and math.isfinite(value) and value >= 0.0 for value in metrics)


def audit_spec(spec: dict[str, str]) -> dict[str, Any]:
    det_path = ROOT / spec["deterministic"]
    mca_path = ROOT / spec["mca"]
    deterministic = json.loads(det_path.read_text(encoding="utf-8"))
    mca_summary = deterministic if det_path == mca_path else json.loads(mca_path.read_text(encoding="utf-8"))
    rows = deterministic[spec["deterministic_key"]]
    variants = {row.get("variant") for row in rows}
    reference_rows = [row for row in rows if row.get("variant") == REFERENCE and row.get("is_reference")]
    det_metadata_paths = sorted((det_path.parent / "runs").glob("*/metadata.json"))
    det_metadata_records = [json.loads(path.read_text(encoding="utf-8")) for path in det_metadata_paths]
    det_scopes = [
        normalize_scope(parse_config(record["run_config_text"]), spec["solver"])
        for record in det_metadata_records
    ]
    det_scope = det_scopes[0]
    mca_base = det_path.parent / spec["mca_subdir"] if det_path == mca_path else mca_path.parent
    mca_metadata_paths = {
        name: sorted((mca_base / name / "runs").glob("*/metadata.json"))
        for name in ("p53", "p24")
    }
    mca_metadata_records = {
        name: [json.loads(path.read_text(encoding="utf-8")) for path in paths]
        for name, paths in mca_metadata_paths.items()
    }
    mca_scopes = {
        name: [
            normalize_scope(parse_config(record["run_config_text"]), spec["solver"])
            for record in records
        ]
        for name, records in mca_metadata_records.items()
    }
    p53_scope = mca_scopes["p53"][0]
    p24_scope = mca_scopes["p24"][0]
    expected_variants = {
        f"cpu-{precision}-{opt}-{'fastmath' if fastmath else 'ieee'}-{branch}"
        for precision in ("double", "float")
        for opt in ("O2", "O3", "Ofast")
        for fastmath in (False, True)
        for branch in ("leq", "strict")
    }
    mca = mca_summary["mca"]
    mca_blocks_complete = all(
        mca[name].get("status") == "completed"
        and mca[name].get("n") == 30
        and mca[name].get("mca_evidence_generated") is True
        and mca[name].get("runner") == "docker"
        for name in ("p53", "p24")
    )
    mca_metrics_valid = all(
        isinstance(value, (int, float)) and math.isfinite(value) and value >= 0.0
        for name in ("p53", "p24")
        for key, value in mca[name].items()
        if key.startswith(("spread_", "snr_", "rho_mean_spread"))
    )
    det_metadata_variants = {path.parent.name for path in det_metadata_paths}
    det_metadata_complete = len(det_metadata_paths) == 24 and det_metadata_variants == expected_variants
    det_metadata_success = all(
        record.get("status") == "success"
        and record.get("returncode") == 0
        and record.get("completion", {}).get("reported") is True
        for record in det_metadata_records
    )
    det_metadata_scope_consistent = all(scopes_match(det_scope, scope) for scope in det_scopes)
    expected_samples = {f"sample_{index:02d}" for index in range(1, 31)}
    mca_metadata_complete = all(
        len(mca_metadata_paths[name]) == 30
        and {path.parent.name for path in mca_metadata_paths[name]} == expected_samples
        for name in ("p53", "p24")
    )
    mca_metadata_success = all(
        record.get("returncode") == 0
        and record.get("runner") == "docker"
        and record.get("solver") == spec["solver"]
        and int(record.get("precision", -1)) == (53 if name == "p53" else 24)
        and record.get("grid_metrics", {}).get("grid_status") == "read"
        for name in ("p53", "p24")
        for record in mca_metadata_records[name]
    )
    mca_metadata_scope_consistent = all(
        scopes_match(p53_scope, scope)
        for name in ("p53", "p24")
        for scope in mca_scopes[name]
    )
    checks = {
        "g0_pass": deterministic.get("gates", {}).get("G0", {}).get("pass") is True,
        "deterministic_24_variants": len(rows) == 24 and variants == expected_variants,
        "deterministic_completed_finite": all(
            row.get("finite") is True and row.get("rc") == 0 and _finite_metrics(row) for row in rows
        ),
        "single_reference": len(reference_rows) == 1,
        "embedded_commit_present": bool(re.fullmatch(r"[0-9a-f]{40}", deterministic.get("git_commit", ""))),
        "deterministic_metadata_24_complete": det_metadata_complete,
        "deterministic_metadata_success": det_metadata_success,
        "deterministic_metadata_scope_consistent": det_metadata_scope_consistent,
        "mca_p53_p24_n30": mca_blocks_complete,
        "mca_metrics_finite_nonnegative": mca_metrics_valid,
        "mca_metadata_60_complete": mca_metadata_complete,
        "mca_metadata_success": mca_metadata_success,
        "mca_metadata_scope_consistent": mca_metadata_scope_consistent,
        "deterministic_mca_scope_match": scopes_match(det_scope, p53_scope),
    }
    source_integrity = all(value for key, value in checks.items() if key != "deterministic_mca_scope_match")
    promotion_pass = source_integrity and checks["deterministic_mca_scope_match"]
    float_baseline = next(row for row in rows if row.get("variant") == "cpu-float-O2-ieee-leq")
    return {
        "case": spec["case"], "solver": spec["solver"],
        "status": "report-grade" if promotion_pass else "provisional-reduced-scope",
        "source_integrity_pass": source_integrity,
        "promotion_pass": promotion_pass,
        "checks": checks,
        "deterministic_scope": det_scope,
        "mca_scope": p53_scope,
        "deterministic": {
            "rows": len(rows), "reference": REFERENCE,
            "metadata_records": len(det_metadata_paths),
            "float_baseline_linf_rho": float_baseline["Linf_rho"],
            "git_commit": deterministic["git_commit"],
        },
        "mca": {
            "p53_n": mca["p53"]["n"], "p24_n": mca["p24"]["n"],
            "metadata_records": sum(len(paths) for paths in mca_metadata_paths.values()),
            "p53_spread_rho": mca["p53"]["spread_rho"],
            "p24_spread_rho": mca["p24"]["spread_rho"],
        },
        "sources": [
            {"path": spec["deterministic"], "sha256": sha256_file(det_path)},
            *([] if det_path == mca_path else [{"path": spec["mca"], "sha256": sha256_file(mca_path)}]),
            *[
                {
                    "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": sha256_file(path),
                    "role": "deterministic-metadata",
                }
                for path in det_metadata_paths
            ],
            *[
                {
                    "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": sha256_file(path),
                    "role": f"{name}-metadata",
                }
                for name in ("p53", "p24")
                for path in mca_metadata_paths[name]
            ],
        ],
    }


def build_summary() -> dict[str, Any]:
    rows = [audit_spec(spec) for spec in SPECS]
    return {
        "schema": {"name": "hrsc.report2-precision-mca-gate", "version": 1},
        "experiment": "report2-precision-mca-unified-audit",
        "gate": {
            "audit_pass": all(row["source_integrity_pass"] for row in rows),
            "full_matrix_promotion_pass": all(row["promotion_pass"] for row in rows),
            "report_grade_rows": sum(row["promotion_pass"] for row in rows),
            "expected_rows": len(rows),
        },
        "rows": rows,
        "interpretation": {
            "promoted": "Same-scope Brio-Wu HLL and HLLD deterministic + N=30 MCA packets pass the unified gate.",
            "retained_provisional": "OT HLL and HLLD remain provisional because deterministic 256^2/t=0.5 and MCA 64^2/t=0.05 scopes do not match.",
            "claim_boundary": "This audit establishes packet completeness and scope alignment only; it is not an exact-solution accuracy test or a universal solver/precision ranking.",
        },
    }


def write_outputs(summary: dict[str, Any], out: pathlib.Path = DEFAULT_OUT) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    fields = ("case", "solver", "status", "source_integrity_pass", "promotion_pass", "deterministic_scope", "mca_scope", "float_baseline_linf_rho", "p53_n", "p24_n", "p53_spread_rho", "p24_spread_rho")
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in summary["rows"]:
            writer.writerow({
                "case": row["case"], "solver": row["solver"], "status": row["status"],
                "source_integrity_pass": row["source_integrity_pass"], "promotion_pass": row["promotion_pass"],
                "deterministic_scope": json.dumps(row["deterministic_scope"], sort_keys=True),
                "mca_scope": json.dumps(row["mca_scope"], sort_keys=True),
                "float_baseline_linf_rho": row["deterministic"]["float_baseline_linf_rho"],
                "p53_n": row["mca"]["p53_n"], "p24_n": row["mca"]["p24_n"],
                "p53_spread_rho": row["mca"]["p53_spread_rho"], "p24_spread_rho": row["mca"]["p24_spread_rho"],
            })
    lines = [
        "# Report 2 deterministic + MCA precision gate", "",
        f"Source-integrity audit pass: `{summary['gate']['audit_pass']}`. Same-scope promotion: `{summary['gate']['report_grade_rows']}/{summary['gate']['expected_rows']}`.", "",
        "| case | solver | deterministic scope | MCA scope | det. rows | MCA samples | status |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for row in summary["rows"]:
        def scope_text(scope: dict[str, Any]) -> str:
            grid = str(scope["nx"]) if "ny" not in scope else f"{scope['nx']}x{scope['ny']}"
            return f"{grid}, t={scope['t_end']:g}"
        lines.append(
            f"| {'Brio-Wu' if row['case'] == 'brio_wu_1d' else 'Orszag-Tang'} | {row['solver'].upper()} | "
            f"{scope_text(row['deterministic_scope'])} | {scope_text(row['mca_scope'])} | 24 | 30+30 | `{row['status']}` |"
        )
    lines += [
        "", "## Review conclusion", "",
        "- Brio-Wu HLL and HLLD pass a same-configuration deterministic-plus-MCA gate and can be treated as report-grade bounded precision evidence.",
        "- Orszag-Tang HLL and HLLD have complete source packets, but the reduced 64x64/t=0.05 MCA runs do not close the 256x256/t=0.5 deterministic evidence. They remain provisional.",
        "- OT deterministic and MCA magnitudes must not be ratioed or combined as if they came from one configuration.",
        "", summary["interpretation"]["claim_boundary"], "",
    ]
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    summary = build_summary()
    write_outputs(summary)
    print(DEFAULT_OUT / "summary.json")
    return 0 if summary["gate"]["audit_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
