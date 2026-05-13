from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


COMPONENT_HINTS = {
    "muscl": ("muscl", "minmod", "limiter", "reconstruct"),
    "hancock": ("hancock", "predict"),
    "flux": ("hllc", "rusanov", "flux"),
    "eos": ("pressure", "sound_speed", "cons_to_prim", "eos"),
    "cfl": ("cfl", "timestep", "max_wave"),
}

FIELDNAMES = [
    "case",
    "solver",
    "symbol",
    "component",
    "minimum_precision_bits",
    "status",
    "criterion",
    "reference",
    "notes",
]

CRITERION = "density_l1_relative_and_pressure_linf_relative"


def classify_component(symbol: str) -> str:
    lower = symbol.lower()
    for component, hints in COMPONENT_HINTS.items():
        if any(hint in lower for hint in hints):
            return component
    return "unknown"


def _empty_status_row(
    *,
    case: str,
    solver: str,
    reference: str,
    status: str,
    notes: str,
) -> dict[str, Any]:
    return {
        "case": case,
        "solver": solver,
        "symbol": "",
        "component": "unknown",
        "minimum_precision_bits": "",
        "status": status,
        "criterion": CRITERION,
        "reference": reference,
        "notes": notes,
    }


def _coerce_bits(value: str | None) -> int | str:
    if value is None:
        return ""
    stripped = value.strip()
    if not stripped:
        return ""
    try:
        return int(stripped)
    except ValueError:
        return stripped


def _csv_lines(text: str) -> list[str]:
    lines = [line for line in text.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        headers = {part.strip() for part in line.split(",")}
        if "symbol" in headers or "function" in headers or "callsite" in headers:
            return lines[index:]
    return []


def parse_precision_rows(path: Path, case: str, solver: str, reference: str) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    raw_lines = [line for line in text.splitlines() if line.strip()]
    lines = _csv_lines(text)
    if not lines:
        if raw_lines:
            return [
                _empty_status_row(
                    case=case,
                    solver=solver,
                    reference=reference,
                    status="not_reported",
                    notes="Could not parse vfc_precexp output; inspect logs manually",
                )
            ]
        return [
            _empty_status_row(
                case=case,
                solver=solver,
                reference=reference,
                status="tool_unsupported",
                notes="vfc_precexp stdout was empty",
            )
        ]

    rows: list[dict[str, Any]] = []
    try:
        reader = csv.DictReader(lines)
        for raw in reader:
            symbol = raw.get("symbol") or raw.get("function") or raw.get("callsite") or ""
            bits = (
                raw.get("minimum_precision_bits")
                or raw.get("precision")
                or raw.get("bits")
                or raw.get("min_bits")
            )
            rows.append(
                {
                    "case": case,
                    "solver": solver,
                    "symbol": symbol,
                    "component": classify_component(symbol),
                    "minimum_precision_bits": _coerce_bits(bits),
                    "status": raw.get("status") or "accepted",
                    "criterion": CRITERION,
                    "reference": reference,
                    "notes": "",
                }
            )
    except csv.Error:
        rows = []

    if not rows:
        return [
            _empty_status_row(
                case=case,
                solver=solver,
                reference=reference,
                status="not_reported",
                notes="Could not parse vfc_precexp output; inspect logs manually",
            )
        ]
    return rows


def _component_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, int | str]]:
    summary: dict[str, dict[str, int | str]] = defaultdict(
        lambda: {"rows": 0, "min_bits": "", "max_bits": ""}
    )
    for row in rows:
        component = str(row.get("component") or "unknown")
        item = summary[component]
        item["rows"] = int(item["rows"]) + 1
        bits = row.get("minimum_precision_bits")
        if not isinstance(bits, int):
            continue
        item["min_bits"] = bits if item["min_bits"] == "" else min(int(item["min_bits"]), bits)
        item["max_bits"] = bits if item["max_bits"] == "" else max(int(item["max_bits"]), bits)
    return dict(summary)


def write_outputs(rows: list[dict[str, Any]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "function_precision.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    (out_dir / "function_precision.json").write_text(
        json.dumps(rows, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# vfc_precexp Function Precision Summary",
        "",
        "This summary reports only rows parsed from the new CSC rerun logs.",
        "",
        "| component | rows | min bits | max bits |",
        "|---|---:|---:|---:|",
    ]
    for component, item in sorted(_component_summary(rows).items()):
        lines.append(
            f"| {component} | {item['rows']} | {item['min_bits']} | {item['max_bits']} |"
        )
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--stdout",
        type=Path,
        default=Path("experiments/week7/vfc_precexp/logs/vfc_precexp_stdout.txt"),
    )
    parser.add_argument("--case", default="sod")
    parser.add_argument("--solver", default="hllc")
    parser.add_argument("--reference", default="experiments/week7/vfc_precexp/reference/grid.bin")
    parser.add_argument("--out-dir", type=Path, default=Path("experiments/week7/vfc_precexp"))
    args = parser.parse_args()

    rows = parse_precision_rows(args.stdout, args.case, args.solver, args.reference)
    write_outputs(rows, args.out_dir)


if __name__ == "__main__":
    main()
