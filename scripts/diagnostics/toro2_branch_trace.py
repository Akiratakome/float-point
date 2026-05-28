#!/usr/bin/env python3
"""Run and aggregate the Toro Test 2 HLLC branch-trace diagnostic."""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Variant:
    name: str
    build_dir: Path
    strict_inequality: bool


def run_command(
    command: list[str],
    *,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
    timeout_s: float | None = None,
    stdout_path: Path | None = None,
    stderr_path: Path | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    stdout_target = subprocess.PIPE if stdout_path is None else stdout_path.open("w", encoding="utf-8")
    stderr_target = subprocess.PIPE if stderr_path is None else stderr_path.open("w", encoding="utf-8")
    try:
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                env=env,
                text=True,
                stdout=stdout_target,
                stderr=stderr_target,
                timeout=timeout_s,
                check=False,
            )
            return {
                "command": command,
                "returncode": result.returncode,
                "timeout": False,
                "elapsed_s": time.perf_counter() - t0,
                "stdout": "" if stdout_path else result.stdout,
                "stderr": "" if stderr_path else result.stderr,
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "command": command,
                "returncode": None,
                "timeout": True,
                "elapsed_s": time.perf_counter() - t0,
                "stdout": "" if stdout_path else (exc.stdout or ""),
                "stderr": "" if stderr_path else (exc.stderr or ""),
            }
    finally:
        if stdout_path is not None:
            stdout_target.close()
        if stderr_path is not None:
            stderr_target.close()


def git_commit() -> str:
    result = run_command(["git", "rev-parse", "HEAD"])
    if result["returncode"] != 0:
        return "unknown"
    return str(result["stdout"]).strip()


def configure_build(variant: Variant) -> None:
    generator = ["-G", "Ninja"] if shutil.which("ninja") else []
    command = [
        "cmake",
        "-B",
        str(variant.build_dir),
        *generator,
        "-DFLOAT_PRECISION=double",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DSTRICT_IEEE=ON",
        "-DENABLE_OPENMP=OFF",
        f"-DRIEMANN_STRICT_INEQUALITY={'ON' if variant.strict_inequality else 'OFF'}",
    ]
    result = run_command(command)
    if result["returncode"] != 0:
        raise RuntimeError(f"configure failed for {variant.name}:\n{result['stderr']}")
    result = run_command(["cmake", "--build", str(variant.build_dir), "--target", "hrsc"])
    if result["returncode"] != 0:
        raise RuntimeError(f"build failed for {variant.name}:\n{result['stderr']}")


def replace_or_append_cfg_line(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or "=" not in line:
            out.append(line)
            continue
        lhs = line.split("=", 1)[0].strip()
        if lhs == key:
            out.append(f"{key} = {value}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{key} = {value}")
    return "\n".join(out) + "\n"


def materialise_config(base_config: Path, run_dir: Path) -> Path:
    text = base_config.read_text(encoding="utf-8")
    text = replace_or_append_cfg_line(text, "output_format", "binary")
    text = replace_or_append_cfg_line(text, "output_file", str(run_dir / "grid.bin"))
    target = run_dir / "config.cfg"
    target.write_text(text, encoding="utf-8")
    return target


def run_variant(
    variant: Variant,
    base_config: Path,
    output_root: Path,
    timeout_s: float,
    max_steps: int,
    dt_floor: str,
    face_window: tuple[int, int],
) -> dict[str, Any]:
    run_dir = output_root / "runs" / variant.name
    run_dir.mkdir(parents=True, exist_ok=True)
    config = materialise_config(base_config, run_dir)

    trace_file = run_dir / "hllc_trace.csv"
    dump_file = run_dir / "diagnostic_dump.bin"
    env = os.environ.copy()
    env.update(
        {
            "OMP_NUM_THREADS": "1",
            "HRSC_HLLC_TRACE_FILE": str(trace_file),
            "HRSC_HLLC_TRACE_MAX_RECORDS": "250000",
            "HRSC_HLLC_TRACE_FACE_MIN": str(face_window[0]),
            "HRSC_HLLC_TRACE_FACE_MAX": str(face_window[1]),
            "HRSC_HLLC_TRACE_LINE_MIN": "0",
            "HRSC_HLLC_TRACE_LINE_MAX": "0",
            "HRSC_DIAG_MAX_STEPS": str(max_steps),
            "HRSC_DIAG_DT_FLOOR": dt_floor,
            "HRSC_DIAG_DUMP_FILE": str(dump_file),
        }
    )
    binary = variant.build_dir / ("hrsc.exe" if os.name == "nt" else "hrsc")
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.txt"
    result = run_command(
        [str(binary), str(config)],
        env=env,
        timeout_s=timeout_s,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )
    metadata = {
        "name": variant.name,
        "strict_inequality": variant.strict_inequality,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "binary": str(binary),
        "config": str(config),
        "trace_file": str(trace_file),
        "dump_file": str(dump_file),
        "stdout": str(stdout_path),
        "stderr": str(stderr_path),
        "env": {key: env[key] for key in sorted(env) if key.startswith("HRSC_") or key == "OMP_NUM_THREADS"},
        "run_result": {k: v for k, v in result.items() if k not in {"stdout", "stderr"}},
    }
    (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def sign(value: float) -> int:
    if value > 0.0:
        return 1
    if value < 0.0:
        return -1
    return 0


def analyze_trace(trace_file: Path, window_file: Path) -> dict[str, Any]:
    rows: list[dict[str, str]] = []
    if trace_file.exists():
        with trace_file.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    if not rows:
        return {"records": 0}
    center_rows = [row for row in rows if row["sweep"] == "x" and row["face"] == "100" and row["line"] == "0"]

    groups: dict[tuple[str, str, str], list[dict[str, str]]] = {}
    for row in rows:
        key = (row["sweep"], row["face"], row["line"])
        groups.setdefault(key, []).append(row)

    best_key: tuple[str, str, str] | None = None
    best_score = -1
    best_changes: list[int] = []
    summaries: list[dict[str, Any]] = []
    for key, group in groups.items():
        branch_changes = 0
        sign_changes = 0
        change_indices: list[int] = []
        prev_branch = group[0]["branch"]
        prev_sign = sign(float(group[0]["Sstar"]))
        for idx, row in enumerate(group[1:], start=1):
            cur_branch = row["branch"]
            cur_sign = sign(float(row["Sstar"]))
            changed = False
            if cur_branch != prev_branch:
                branch_changes += 1
                changed = True
            if cur_sign != 0 and prev_sign != 0 and cur_sign != prev_sign:
                sign_changes += 1
                changed = True
            if changed:
                change_indices.append(idx)
            prev_branch = cur_branch
            if cur_sign != 0:
                prev_sign = cur_sign
        nstar_abs = [abs(float(row["Nstar"])) for row in group]
        dstar_values = [float(row["Dstar"]) for row in group]
        score = branch_changes + sign_changes
        summaries.append(
            {
                "sweep": key[0],
                "face": int(key[1]),
                "line": int(key[2]),
                "records": len(group),
                "branch_changes": branch_changes,
                "sstar_sign_changes": sign_changes,
                "max_abs_nstar": max(nstar_abs),
                "min_abs_dstar": min(abs(v) for v in dstar_values),
                "max_abs_dstar": max(abs(v) for v in dstar_values),
                "first_branch": group[0]["branch"],
                "last_branch": group[-1]["branch"],
            }
        )
        if score > best_score:
            best_key = key
            best_score = score
            best_changes = change_indices

    summaries.sort(key=lambda item: (item["branch_changes"] + item["sstar_sign_changes"], item["records"]), reverse=True)
    if best_key is not None and best_changes:
        group = groups[best_key]
        start = max(0, best_changes[0] - 5)
        end = min(len(group), best_changes[0] + 6)
        with window_file.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(group[0].keys()))
            writer.writeheader()
            writer.writerows(group[start:end])

    return {
        "records": len(rows),
        "groups": len(groups),
        "center_first": center_rows[0] if center_rows else None,
        "center_last": center_rows[-1] if center_rows else None,
        "top_faces": summaries[:8],
        "window_file": str(window_file) if best_changes else None,
    }


def write_summary(output_root: Path, run_metadata: list[dict[str, Any]], analyses: dict[str, dict[str, Any]]) -> None:
    lines = [
        "# Toro Test 2 HLLC Branch Trace Diagnostic",
        "",
        f"- timestamp_utc: `{datetime.now(timezone.utc).isoformat()}`",
        f"- git_commit: `{git_commit()}`",
        "",
        "## Runs",
        "",
        "| run | strict `<` | returncode | timeout | elapsed_s | trace_records | stop_reason |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for meta in run_metadata:
        stderr = Path(meta["stderr"]).read_text(encoding="utf-8", errors="replace")
        stop_reason = ""
        for line in stderr.splitlines():
            if line.startswith("[diagnostic] stop_reason="):
                stop_reason = line.split()[1].split("=", 1)[1]
                break
        analysis = analyses.get(meta["name"], {})
        result = meta["run_result"]
        lines.append(
            f"| {meta['name']} | {meta['strict_inequality']} | "
            f"{result['returncode']} | {result['timeout']} | "
            f"{result['elapsed_s']:.3f} | {analysis.get('records', 0)} | {stop_reason} |"
        )

    lines.extend(["", "## Top Branch-Change Faces", ""])
    for name, analysis in analyses.items():
        lines.append(f"### {name}")
        lines.append("")
        meta = next((item for item in run_metadata if item["name"] == name), None)
        if meta:
            stderr = Path(meta["stderr"]).read_text(encoding="utf-8", errors="replace")
            for line in stderr.splitlines():
                if line.startswith("[diagnostic] stop_reason="):
                    lines.append(f"Diagnostic stop: `{line}`")
                    lines.append("")
                    break
        center = analysis.get("center_first")
        if center:
            lines.append(
                "Center face first record: "
                f"`step={center['step']}`, `dt={float(center['dt']):.6e}`, "
                f"`Nstar={float(center['Nstar']):.6e}`, "
                f"`Dstar={float(center['Dstar']):.6e}`, "
                f"`Sstar={float(center['Sstar']):.6e}`, "
                f"`branch={center['branch']}`, "
                f"`flux_rho={float(center['flux_rho']):.6e}`."
            )
            lines.append("")
        center_last = analysis.get("center_last")
        if center_last and center_last != center:
            lines.append(
                "Center face last record: "
                f"`step={center_last['step']}`, "
                f"`Nstar={float(center_last['Nstar']):.6e}`, "
                f"`Dstar={float(center_last['Dstar']):.6e}`, "
                f"`Sstar={float(center_last['Sstar']):.6e}`, "
                f"`branch={center_last['branch']}`."
            )
            lines.append("")
        lines.append("| sweep | face | records | branch_changes | sstar_sign_changes | max_abs_nstar | min_abs_dstar | first->last |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---|")
        for item in analysis.get("top_faces", []):
            lines.append(
                f"| {item['sweep']} | {item['face']} | {item['records']} | "
                f"{item['branch_changes']} | {item['sstar_sign_changes']} | "
                f"{item['max_abs_nstar']:.6e} | {item['min_abs_dstar']:.6e} | "
                f"{item['first_branch']}->{item['last_branch']} |"
            )
        if analysis.get("window_file"):
            lines.append("")
            lines.append(f"First change window: `{analysis['window_file']}`")
        lines.append("")

    (output_root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-config", type=Path, default=ROOT / "tests/cases/toro_1d/toro2.cfg")
    parser.add_argument("--output-root", type=Path, default=ROOT / "experiments/report1_toro2_branch_trace")
    parser.add_argument("--timeout-s", type=float, default=120.0)
    parser.add_argument("--max-steps", type=int, default=20000)
    parser.add_argument("--dt-floor", default="1e-18")
    parser.add_argument("--face-min", type=int, default=95)
    parser.add_argument("--face-max", type=int, default=105)
    parser.add_argument("--skip-build", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_root = args.output_root
    output_root.mkdir(parents=True, exist_ok=True)
    variants = [
        Variant("toro2_hllc_leq_trace", ROOT / "build-report1-toro2-leq", False),
        Variant("toro2_hllc_lt_trace", ROOT / "build-report1-toro2-lt", True),
    ]
    if not args.skip_build:
        for variant in variants:
            configure_build(variant)

    metadata = [
        run_variant(
            variant,
            args.base_config,
            output_root,
            args.timeout_s,
            args.max_steps,
            args.dt_floor,
            (args.face_min, args.face_max),
        )
        for variant in variants
    ]
    analyses: dict[str, dict[str, Any]] = {}
    for meta in metadata:
        trace_file = Path(meta["trace_file"])
        window_file = trace_file.with_name("branch_flip_window.csv")
        analyses[meta["name"]] = analyze_trace(trace_file, window_file)

    summary = {
        "experiment": "report1_toro2_branch_trace",
        "output_root": str(output_root),
        "runs": metadata,
        "analyses": analyses,
    }
    (output_root / "matrix_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_summary(output_root, metadata, analyses)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[error] {exc}", file=sys.stderr)
        raise
