#!/usr/bin/env python3
"""Probe and optionally run a tiny Verificarlo MCA smoke for Brio-Wu MHD.

This driver is an experiment-harness entry point. It copies the source cfg into
per-sample run directories, appends only output overrides, records command
metadata, and writes lightweight summaries. If the local environment cannot run
Verificarlo, it exits successfully with blocked evidence instead of claiming MCA
results.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_CASE = ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg"
DEFAULT_OUT = ROOT / "experiments" / "week13" / "mhd_verificarlo_smoke"
DEFAULT_IMAGE = "verificarlo/verificarlo"
EXPERIMENT = "week13-mhd-verificarlo-smoke"
SAMPLE_MAX_ATTEMPTS = 3

sys.path.insert(0, str(ROOT / "scripts" / "regression"))
from _mhd_harness import git_commit, replace_or_append_cfg, sha256_file  # noqa: E402


@dataclass(frozen=True)
class ProbeRecord:
    name: str
    command: list[str]
    returncode: int | None
    stdout: str
    stderr: str
    supported: bool
    runner: str | None = None


def clean_text(text: str | bytes | None) -> str:
    if text is None:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    return "".join(ch if ch in "\n\r\t" or ord(ch) >= 32 else " " for ch in str(text))


def json_sanitise(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: json_sanitise(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_sanitise(v) for v in value]
    if isinstance(value, tuple):
        return [json_sanitise(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def make_probe_record(
    name: str,
    command: list[str],
    *,
    returncode: int | None,
    stdout: str,
    stderr: str,
    supported: bool,
    runner: str | None = None,
) -> dict[str, Any]:
    record = ProbeRecord(
        name=name,
        command=list(command),
        returncode=returncode,
        stdout=clean_text(stdout),
        stderr=clean_text(stderr),
        supported=bool(supported),
        runner=runner,
    )
    return {
        "name": record.name,
        "command": record.command,
        "returncode": record.returncode,
        "stdout": record.stdout,
        "stderr": record.stderr,
        "supported": record.supported,
        "runner": record.runner,
    }


def run_command(command: list[str], *, cwd: pathlib.Path = ROOT, env: dict[str, str] | None = None,
                timeout: int = 120) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
        return {
            "command": list(command),
            "returncode": result.returncode,
            "stdout": clean_text(result.stdout),
            "stderr": clean_text(result.stderr),
        }
    except FileNotFoundError as exc:
        return {"command": list(command), "returncode": 127, "stdout": "", "stderr": clean_text(str(exc))}
    except subprocess.TimeoutExpired as exc:
        return {
            "command": list(command),
            "returncode": 124,
            "stdout": clean_text(exc.stdout),
            "stderr": clean_text(exc.stderr) + f"\nTimeoutExpired: {exc}",
        }


def docker_probe_command(image: str, repo: pathlib.Path = ROOT) -> list[str]:
    return [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{repo}:/workdir",
        "-w",
        "/workdir",
        image,
        "bash",
        "-lc",
        "verificarlo-c++ --version && cmake --version",
    ]


def wsl_probe_command() -> list[str]:
    return ["wsl", "bash", "-lc", "verificarlo-c++ --version && cmake --version"]


def native_probe_command() -> list[str]:
    return ["verificarlo-c++", "--version"]


def probe_runners(image: str) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    for name, command, runner in (
        ("native", native_probe_command(), "native"),
        ("wsl", wsl_probe_command(), "wsl"),
        ("docker", docker_probe_command(image), "docker"),
    ):
        result = run_command(command, timeout=45)
        probes.append(
            make_probe_record(
                name,
                command,
                returncode=result["returncode"],
                stdout=result["stdout"],
                stderr=result["stderr"],
                supported=result["returncode"] == 0,
                runner=runner if result["returncode"] == 0 else None,
            )
        )
    return probes


def choose_runner(probes: list[dict[str, Any]]) -> str | None:
    supported = {probe.get("runner") for probe in probes if probe.get("supported")}
    for runner in ("docker", "native", "wsl"):
        if runner in supported:
            return runner
    return None


def make_sample_cfg(source_text: str, grid_path: pathlib.Path | str,
                    solver: str | None = None) -> str:
    text = source_text
    if solver:
        text = replace_or_append_cfg(text, "riemann", solver)
    text = replace_or_append_cfg(text, "output_format", "binary")
    text = replace_or_append_cfg(text, "output_file", str(grid_path))
    return text


def make_blocked_summary_md(status: str, probes: list[dict[str, Any]], reason: str) -> str:
    lines = [
        "# Week 13 MHD Verificarlo Smoke",
        "",
        f"Status: `{status}`",
        "",
        reason,
        "",
        "no Verificarlo MCA result was produced; no MCA evidence was generated.",
        "",
        "## Runner probes",
        "",
        "| runner | supported | return code | stderr |",
        "|---|---|---:|---|",
    ]
    for probe in probes:
        stderr = " ".join(str(probe.get("stderr", "")).split())[:240]
        lines.append(
            f"| {probe.get('name')} | {probe.get('supported')} | "
            f"{probe.get('returncode')} | `{stderr}` |"
        )
    lines.append("")
    return "\n".join(lines)


def make_probe_summary_md(status: str, probes: list[dict[str, Any]], runner: str | None) -> str:
    reason = (
        f"Supported runner selected for sample mode: `{runner}`."
        if runner else
        "No supported Verificarlo runner was found."
    )
    return make_blocked_summary_md(status, probes, reason)


def write_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(json_sanitise(payload), indent=2, allow_nan=False) + "\n", encoding="utf-8")


def base_environment(args: argparse.Namespace, probes: list[dict[str, Any]], runner: str | None) -> dict[str, Any]:
    return {
        "experiment": EXPERIMENT,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": git_commit(),
        "platform": platform.platform(),
        "python": sys.version,
        "case": str(args.case),
        "case_sha256": sha256_file(args.case) if args.case.is_file() else None,
        "output_root": str(args.out),
        "samples": args.samples,
        "precision": args.precision,
        "solver": getattr(args, "solver", "hll"),
        "image": args.image,
        "probe_only": args.probe_only,
        "selected_runner": runner,
        "probes": probes,
    }


def write_probe_outputs(args: argparse.Namespace, probes: list[dict[str, Any]], status: str,
                        runner: str | None, reason: str) -> None:
    args.out.mkdir(parents=True, exist_ok=True)
    environment = base_environment(args, probes, runner)
    environment["status"] = status
    write_json(args.out / "environment.json", environment)
    summary = {
        "experiment": EXPERIMENT,
        "status": status,
        "reason": reason,
        "selected_runner": runner,
        "mca_samples_produced": 0,
        "mca_evidence_generated": False,
        "environment_json": str(args.out / "environment.json"),
        "probes": probes,
    }
    write_json(args.out / "summary.json", summary)
    if status == "blocked_environment":
        md = make_blocked_summary_md(status, probes, reason)
    else:
        md = make_probe_summary_md(status, probes, runner)
    (args.out / "summary.md").write_text(md, encoding="utf-8")


def docker_repo_mount(repo: pathlib.Path = ROOT) -> str:
    return f"{repo}:/workdir"


def rel_to_root(path: pathlib.Path) -> pathlib.Path:
    try:
        return path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return path


def runner_path(runner: str, path: pathlib.Path) -> str:
    if runner == "docker":
        rel = rel_to_root(path)
        return "/workdir" if str(rel) == "." else f"/workdir/{rel.as_posix()}"
    if runner == "wsl":
        return wsl_path(path) if path.is_absolute() else path.as_posix()
    return str(path)


def docker_command(image: str, shell_script: str) -> list[str]:
    return ["docker", "run", "--rm", "-v", docker_repo_mount(), "-w", "/workdir", image, "bash", "-lc", shell_script]


def native_build_command(build_dir: pathlib.Path) -> list[str]:
    return [
        "cmake",
        "-S",
        ".",
        "-B",
        str(build_dir),
        "-G",
        "Ninja",
        "-DCMAKE_CXX_COMPILER=verificarlo-c++",
        "-DFLOAT_PRECISION=double",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DENABLE_OPENMP=OFF",
    ]


def native_build_target_command(build_dir: pathlib.Path) -> list[str]:
    return ["cmake", "--build", str(build_dir), "--target", "hrsc_mhd"]


def wsl_path(path: pathlib.Path) -> str:
    drive = path.drive.rstrip(":").lower()
    rest = path.as_posix().split(":", 1)[-1].lstrip("/")
    return f"/mnt/{drive}/{rest}"


def build_commands_for_runner(runner: str, image: str, build_dir: pathlib.Path) -> list[list[str]]:
    if runner == "docker":
        build_dir_arg = runner_path(runner, build_dir)
        build = (
            f"cmake -S . -B {build_dir_arg} -G Ninja "
            "-DCMAKE_CXX_COMPILER=verificarlo-c++ -DFLOAT_PRECISION=double "
            "-DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=OFF && "
            f"cmake --build {build_dir_arg} --target hrsc_mhd"
        )
        return [docker_command(image, build)]
    if runner == "wsl":
        repo = wsl_path(ROOT)
        build_dir_arg = rel_to_root(build_dir).as_posix()
        build = (
            f"cd {repo} && cmake -S . -B {build_dir_arg} -G Ninja "
            "-DCMAKE_CXX_COMPILER=verificarlo-c++ -DFLOAT_PRECISION=double "
            "-DCMAKE_BUILD_TYPE=Release -DENABLE_OPENMP=OFF && "
            f"cmake --build {build_dir_arg} --target hrsc_mhd"
        )
        return [["wsl", "bash", "-lc", build]]
    return [native_build_command(build_dir), native_build_target_command(build_dir)]


def sample_command_for_runner(runner: str, image: str, build_dir: pathlib.Path,
                              cfg_path: pathlib.Path, precision: int) -> list[str]:
    binary = build_dir / ("hrsc_mhd.exe" if runner == "native" and platform.system().lower().startswith("win") else "hrsc_mhd")
    # Verificarlo 2.x interflop backends take precision as a VFC_BACKENDS
    # argument; the legacy VFC_MCA_PRECISION_BINARY64 env var is silently
    # ignored (same gotcha as VFC_BACKENDS_SEED; see noise_floor_run.sh). Inline
    # --precision-binary64 so the p24 surrogate actually lowers binary64
    # precision instead of silently running at the backend default (=53), which
    # is what made p24 and p53 collapse to the same machine-eps noise floor.
    vfc_backends = f"libinterflop_mca.so --mode=mca --precision-binary64={precision}"
    env_bits = (
        f"VFC_BACKENDS='{vfc_backends}' "
        "VFC_BACKENDS_SILENT_LOAD=True "
    )
    if runner == "docker":
        script = f"{env_bits}{runner_path(runner, binary)} {runner_path(runner, cfg_path)}"
        return docker_command(image, script)
    if runner == "wsl":
        repo = wsl_path(ROOT)
        script = f"cd {repo} && {env_bits}{runner_path(runner, binary)} {runner_path(runner, cfg_path)}"
        return ["wsl", "bash", "-lc", script]
    if platform.system().lower().startswith("win"):
        script = (
            f"$env:VFC_BACKENDS='{vfc_backends}'; "
            "$env:VFC_BACKENDS_SILENT_LOAD='True'; "
            f"& '{binary}' '{cfg_path}'"
        )
        return ["powershell", "-NoProfile", "-Command", script]
    return [
        "env",
        f"VFC_BACKENDS={vfc_backends}",
        "VFC_BACKENDS_SILENT_LOAD=True",
        str(binary),
        str(cfg_path),
    ]


def write_command_log(run_dir: pathlib.Path, label: str, result: dict[str, Any]) -> None:
    (run_dir / f"{label}_stdout.txt").write_text(result.get("stdout", ""), encoding="utf-8", errors="replace")
    (run_dir / f"{label}_stderr.txt").write_text(result.get("stderr", ""), encoding="utf-8", errors="replace")


def read_grid_metrics(grid_path: pathlib.Path) -> dict[str, Any]:
    if not grid_path.is_file():
        return {"grid_status": "missing", "rho_min": None, "rho_max": None, "rho_mean": None}
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        from io_helper import read_binary  # noqa: WPS433

        _, arr = read_binary(grid_path)
        rho = arr[..., 0]
        return {
            "grid_status": "read",
            "rho_min": float(rho.min()),
            "rho_max": float(rho.max()),
            "rho_mean": float(rho.mean()),
        }
    except Exception as exc:  # pragma: no cover - depends on real generated grids.
        return {
            "grid_status": f"unreadable: {type(exc).__name__}: {exc}",
            "rho_min": None,
            "rho_max": None,
            "rho_mean": None,
        }


def run_samples(args: argparse.Namespace, probes: list[dict[str, Any]], runner: str) -> tuple[str, list[dict[str, Any]], str]:
    build_dir = args.out / "build-vfc-p53"
    runs_dir = args.out / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    build_results = []
    for index, command in enumerate(build_commands_for_runner(runner, args.image, build_dir), start=1):
        result = run_command(command, timeout=600)
        build_results.append(result)
        write_command_log(args.out, f"build_{index}", result)
        if result["returncode"] != 0:
            return "blocked_run", [], f"Verificarlo build failed for runner `{runner}` at build command {index}."

    source_text = args.case.read_text(encoding="utf-8")
    sample_rows: list[dict[str, Any]] = []
    for i in range(1, args.samples + 1):
        sample_name = f"sample_{i:02d}"
        run_dir = runs_dir / sample_name
        run_dir.mkdir(parents=True, exist_ok=True)
        grid_path = run_dir / "grid.bin"
        cfg_path = run_dir / "config.cfg"
        for attempt in range(1, SAMPLE_MAX_ATTEMPTS + 1):
            if grid_path.exists():
                grid_path.unlink()
            cfg_text = make_sample_cfg(
                source_text,
                runner_path(runner, grid_path),
                solver=getattr(args, "solver", None),
            )
            cfg_path.write_text(cfg_text, encoding="utf-8")
            command = sample_command_for_runner(runner, args.image, build_dir, cfg_path, args.precision)
            t0 = time.perf_counter()
            result = run_command(command, timeout=300)
            elapsed = time.perf_counter() - t0
            stdout_path = run_dir / "stdout.txt"
            stderr_path = run_dir / "stderr.txt"
            stdout_path.write_text(result.get("stdout", ""), encoding="utf-8", errors="replace")
            stderr_path.write_text(result.get("stderr", ""), encoding="utf-8", errors="replace")
            (run_dir / f"attempt_{attempt:02d}_stdout.txt").write_text(
                result.get("stdout", ""), encoding="utf-8", errors="replace")
            (run_dir / f"attempt_{attempt:02d}_stderr.txt").write_text(
                result.get("stderr", ""), encoding="utf-8", errors="replace")
            metrics = read_grid_metrics(grid_path)
            row = {
                "sample": sample_name,
                "attempt": attempt,
                "max_attempts": SAMPLE_MAX_ATTEMPTS,
                "returncode": result["returncode"],
                "elapsed_wall_s": elapsed,
                "config": str(cfg_path),
                "output_binary": str(grid_path),
                "stdout": str(stdout_path),
                "stderr": str(stderr_path),
                "command": command,
                "runner": runner,
                "precision": args.precision,
            }
            row.update(metrics)
            metadata = {
                "experiment": EXPERIMENT,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "git_commit": git_commit(),
                "runner": runner,
                "precision": args.precision,
                "solver": getattr(args, "solver", "hll"),
                "sample": sample_name,
                "attempt": attempt,
                "max_attempts": SAMPLE_MAX_ATTEMPTS,
                "source_config": str(args.case),
                "source_config_sha256": sha256_file(args.case),
                "run_config": str(cfg_path),
                "run_config_text": cfg_text,
                "command": command,
                "returncode": result["returncode"],
                "elapsed_wall_s": elapsed,
                "output_binary": str(grid_path),
                "stdout": str(stdout_path),
                "stderr": str(stderr_path),
                "grid_metrics": metrics,
            }
            write_json(run_dir / "metadata.json", metadata)
            if result["returncode"] == 0 and metrics["grid_status"] == "read":
                sample_rows.append(row)
                break
        else:
            return (
                "blocked_run",
                sample_rows,
                f"Sample `{sample_name}` failed before producing a readable MCA grid "
                f"after {SAMPLE_MAX_ATTEMPTS} attempts.",
            )

    return "completed", sample_rows, f"Produced {len(sample_rows)} Verificarlo MCA sample grids with runner `{runner}`."


def summarise_samples(sample_rows: list[dict[str, Any]]) -> dict[str, Any]:
    means = [row.get("rho_mean") for row in sample_rows if isinstance(row.get("rho_mean"), (int, float))]
    if not means:
        return {"samples": len(sample_rows), "rho_mean_min": None, "rho_mean_max": None, "rho_mean_spread": None}
    return {
        "samples": len(sample_rows),
        "rho_mean_min": min(means),
        "rho_mean_max": max(means),
        "rho_mean_spread": max(means) - min(means),
    }


def write_sample_outputs(args: argparse.Namespace, probes: list[dict[str, Any]], runner: str,
                         status: str, sample_rows: list[dict[str, Any]], reason: str) -> None:
    environment = base_environment(args, probes, runner)
    environment["status"] = status
    write_json(args.out / "environment.json", environment)
    scalar_summary = summarise_samples(sample_rows)
    summary = {
        "experiment": EXPERIMENT,
        "status": status,
        "reason": reason,
        "selected_runner": runner,
        "mca_samples_produced": len([row for row in sample_rows if row.get("grid_status") == "read"]),
        "mca_evidence_generated": status == "completed",
        "environment_json": str(args.out / "environment.json"),
        "scalar_summary": scalar_summary,
        "samples": sample_rows,
        "probes": probes,
    }
    write_json(args.out / "summary.json", summary)
    if status != "completed":
        md = make_blocked_summary_md(status, probes, reason)
    else:
        lines = [
            "# Week 13 MHD Verificarlo Smoke",
            "",
            "Status: `completed`",
            "",
            reason,
            "",
            f"- runner: `{runner}`",
            f"- samples: {scalar_summary['samples']}",
            f"- rho_mean_spread: {scalar_summary['rho_mean_spread']}",
            "",
            "## Samples",
            "",
            "| sample | rc | grid_status | rho_min | rho_max | rho_mean |",
            "|---|---:|---|---:|---:|---:|",
        ]
        for row in sample_rows:
            lines.append(
                f"| {row['sample']} | {row['returncode']} | {row['grid_status']} | "
                f"{row.get('rho_min')} | {row.get('rho_max')} | {row.get('rho_mean')} |"
            )
        lines.extend([
            "",
            "Generated artifacts include `environment.json`, `summary.json`, per-sample "
            "`config.cfg`, logs, and `metadata.json`. Binary grids are transient.",
            "",
        ])
        md = "\n".join(lines)
    (args.out / "summary.md").write_text(md, encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", type=pathlib.Path, default=DEFAULT_CASE)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--precision", type=int, default=53)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--image", default=DEFAULT_IMAGE)
    parser.add_argument("--solver", choices=("hll", "hlld"), default="hll")
    parser.add_argument("--probe-only", action="store_true")
    return parser.parse_args(argv)


def normalise_args(args: argparse.Namespace) -> argparse.Namespace:
    args.case = args.case if args.case.is_absolute() else ROOT / args.case
    args.out = args.out if args.out.is_absolute() else ROOT / args.out
    return args


def main(argv: list[str] | None = None) -> int:
    args = normalise_args(parse_args(argv))
    args.out.mkdir(parents=True, exist_ok=True)
    probes = probe_runners(args.image)
    runner = choose_runner(probes)
    if runner is None:
        reason = "No supported native, WSL, or Docker Verificarlo runner was found."
        write_probe_outputs(args, probes, "blocked_environment", None, reason)
        print(reason)
        print(args.out / "summary.md")
        return 0

    if args.probe_only:
        reason = f"Probe found supported runner `{runner}`; sample mode was not requested."
        write_probe_outputs(args, probes, "runnable_environment", runner, reason)
        print(reason)
        print(args.out / "summary.md")
        return 0

    status, sample_rows, reason = run_samples(args, probes, runner)
    write_sample_outputs(args, probes, runner, status, sample_rows, reason)
    print(reason)
    print(args.out / "summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
