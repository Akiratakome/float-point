#!/usr/bin/env python3
"""Reproduce the Lecoanet et al. smooth KH initial condition and linear growth.

The solver is ideal MHD with B=0, so this packet exercises the inviscid
hydrodynamic limit. It reproduces the published unstratified initial condition
and evaluates the k=2*pi transverse-velocity mode during the linear stage. It
does not claim the nonlinear Re=1e5 reference solution because the application
does not implement the paper's explicit viscosity, thermal diffusion, or dye.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import platform
import sys
from typing import Any

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
CFG = ROOT / "tests" / "cases" / "kelvin_helmholtz_lecoanet_2d" / "lecoanet_unstratified.cfg"
DEFAULT_BINARY = ROOT / "build-double" / "hrsc_mhd.exe"
DEFAULT_OUT = ROOT / "experiments" / "week19" / "lecoanet_kh_linear_reproduction"
EXPERIMENT = "week19-lecoanet-kh-linear-reproduction"
TIMES = (0.25, 0.50, 0.75, 1.00)
EXPECTED_GROWTH_RATE = 3.227
SIGMA = 0.2
FIT_START_TIME = 0.25
IMPLEMENTATION_SOURCES = (
    ROOT / "src" / "mhd" / "mhd_config.hpp",
    ROOT / "src" / "mhd" / "mhd_solver.hpp",
    ROOT / "src" / "mhd" / "mhd_solver.cpp",
    ROOT / "src" / "mhd_main.cpp",
    pathlib.Path(__file__).resolve(),
)

sys.path.insert(0, str(ROOT / "scripts" / "regression"))
from _mhd_harness import (  # noqa: E402
    git_commit,
    read_binary,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)


def lecoanet_mode_amplitude(vy: np.ndarray, x: np.ndarray, y: np.ndarray) -> float:
    """Grid analogue of Tricco (2019), equations (25)--(28)."""
    if vy.shape != (y.size, x.size):
        raise ValueError(f"vy shape {vy.shape} does not match y/x sizes {(y.size, x.size)}")
    yy = y[:, None]
    reflected_distance = np.where(yy < 1.0, np.abs(yy - 0.5), np.abs((2.0 - yy) - 0.5))
    weight = np.exp(-reflected_distance / (SIGMA * SIGMA))
    phase = 2.0 * math.pi * x[None, :]
    denominator = float(np.broadcast_to(weight, vy.shape).sum())
    s_component = float((vy * np.sin(phase) * weight).sum() / denominator)
    c_component = float((vy * np.cos(phase) * weight).sum() / denominator)
    return 2.0 * math.hypot(s_component, c_component)


def analytic_initial_vy(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    dy1 = y[:, None] - 0.5
    dy2 = y[:, None] - 1.5
    return 0.01 * np.sin(2.0 * math.pi * x[None, :]) * (
        np.exp(-(dy1 * dy1) / (SIGMA * SIGMA))
        + np.exp(-(dy2 * dy2) / (SIGMA * SIGMA))
    )


def fit_growth_rate(rows: list[dict[str, Any]]) -> tuple[float, float]:
    times = np.asarray([float(row["time"]) for row in rows], dtype=np.float64)
    amplitudes = np.asarray([float(row["mode_amplitude"]) for row in rows], dtype=np.float64)
    if times.size < 2 or np.any(amplitudes <= 0.0):
        raise ValueError("at least two positive mode amplitudes are required")
    slope, intercept = np.polyfit(times, np.log(amplitudes), 1)
    fitted = slope * times + intercept
    residual = np.log(amplitudes) - fitted
    ss_res = float(np.sum(residual * residual))
    centred = np.log(amplitudes) - float(np.log(amplitudes).mean())
    ss_tot = float(np.sum(centred * centred))
    r2 = 1.0 if ss_tot == 0.0 and ss_res == 0.0 else 1.0 - ss_res / ss_tot
    return float(slope), float(r2)


def _cfg_text(output: pathlib.Path, t_end: float, nx: int, ny: int) -> str:
    text = CFG.read_text(encoding="utf-8")
    for key, value in (
        ("nx", nx),
        ("ny", ny),
        ("t_end", f"{t_end:.8g}"),
        ("output_format", "binary"),
        ("output_file", output.as_posix()),
    ):
        text = replace_or_append_cfg(text, key, str(value))
    return text


def _measure_grid(path: pathlib.Path, steps: int) -> dict[str, Any]:
    header, arr = read_binary(path)
    rho = arr[..., 0].astype(np.float64)
    momentum = arr[..., 1:4].astype(np.float64)
    magnetic = arr[..., 4:7].astype(np.float64)
    vy = momentum[..., 1] / rho
    kinetic = 0.5 * np.sum(momentum * momentum, axis=-1) / rho
    magnetic_energy = 0.5 * np.sum(magnetic * magnetic, axis=-1)
    pressure = (5.0 / 3.0 - 1.0) * (arr[..., 7].astype(np.float64) - kinetic - magnetic_energy)
    positive_state = bool(
        np.isfinite(arr).all() and np.all(rho > 0.0) and np.all(pressure > 0.0)
    )
    x = (np.arange(header.nx, dtype=np.float64) + 0.5) * float(header.dx)
    y = (np.arange(header.ny, dtype=np.float64) + 0.5) * float(header.dy)
    return {
        "time": float(header.t),
        "steps": int(steps),
        "mode_amplitude": lecoanet_mode_amplitude(vy, x, y),
        "rho_min": float(rho.min()),
        "rho_max": float(rho.max()),
        "finite_positive_state": positive_state,
    }


def _plot(
    rows: list[dict[str, Any]], out: pathlib.Path, growth_rate: float,
    fit_start_time: float,
) -> list[str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    times = np.asarray([float(row["time"]) for row in rows])
    amplitudes = np.asarray([float(row["mode_amplitude"]) for row in rows])
    fit_mask = times >= fit_start_time
    fit_times = times[fit_mask]
    fit_amplitudes = amplitudes[fit_mask]
    intercept = float(np.log(fit_amplitudes).mean() - growth_rate * fit_times.mean())
    fit = np.exp(intercept + growth_rate * fit_times)
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    ax.semilogy(times, amplitudes, "o-", label="HRSC measured")
    ax.semilogy(fit_times, fit, "--", label=f"fit t>={fit_start_time:g}: gamma={growth_rate:.3f}")
    ax.set_xlabel("time")
    ax.set_ylabel("k=2pi mode amplitude")
    ax.set_title("Lecoanet KH early linear-growth reproduction")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    paths = []
    for suffix in ("png", "pdf"):
        path = out / "figures" / f"lecoanet_kh_mode_growth.{suffix}"
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=180 if suffix == "png" else None)
        paths.append(path.relative_to(ROOT).as_posix())
    plt.close(fig)
    return paths


def _write_summary(out: pathlib.Path, rows: list[dict[str, Any]], payload: dict[str, Any]) -> None:
    with (out / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    gate = payload["gate"]
    lines = [
        "# Lecoanet KH Linear-Reproduction Packet",
        "",
        "This packet reproduces the smooth unstratified initial condition from "
        "Lecoanet et al. (2016) on `[0,1] x [0,2]` and measures the early "
        "`k=2*pi` transverse-velocity mode using the Tricco (2019) convolution.",
        "",
        "It is an **initial-condition and early linear-growth reproduction**, not "
        "a reproduction of the nonlinear `Re=1e5` reference: the current solver "
        "does not include explicit viscosity, thermal diffusion, or passive dye.",
        "",
        f"- Grid: `{payload['grid']['nx']} x {payload['grid']['ny']}`; HLL FP64, periodic.",
        f"- Fitted growth rate: `{payload['growth_rate']:.6f}`; literature linear value: "
        f"`{payload['expected_growth_rate']:.3f}`; relative difference: "
        f"`{payload['growth_rate_relative_difference']:.3%}`.",
        f"- Fit window: `t >= {payload['fit_window']['start']:.2f}`; the earlier "
        "seed-adjustment transient is retained but excluded from the exponential fit.",
        f"- Log-linear fit R2: `{payload['fit_r2']:.6f}`.",
        f"- Gate: `{gate['pass']}` (strictly increasing positive mode in the declared "
        "fit window, finite positive state, positive finite fit with R2 >= 0.98).",
        "",
        "| time | steps | mode amplitude | rho min | rho max |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['time']:.3f} | {row['steps']} | {row['mode_amplitude']:.8e} | "
            f"{row['rho_min']:.8e} | {row['rho_max']:.8e} |"
        )
    lines.extend([
        "",
        "Sources: Lecoanet et al. (2016), DOI `10.1093/mnras/stv2564`; "
        "Tricco (2019), DOI `10.1093/mnras/stz2042`.",
        "",
    ])
    (out / "summary.md").write_text("\n".join(lines), encoding="utf-8")


def reproduce(args: argparse.Namespace) -> dict[str, Any]:
    out = args.out if args.out.is_absolute() else ROOT / args.out
    binary = resolve_binary(args.binary if args.binary.is_absolute() else ROOT / args.binary)
    out.mkdir(parents=True, exist_ok=True)
    commit = git_commit()
    binary_hash = sha256_file(binary)
    times = (0.25, 0.50) if args.smoke else TIMES
    nx, ny = (64, 128) if args.smoke else (args.nx, 2 * args.nx)
    rows: list[dict[str, Any]] = []
    run_metadata: list[str] = []

    x = (np.arange(nx, dtype=np.float64) + 0.5) / nx
    y = (np.arange(ny, dtype=np.float64) + 0.5) * (2.0 / ny)
    rows.append({
        "time": 0.0,
        "steps": 0,
        "mode_amplitude": lecoanet_mode_amplitude(analytic_initial_vy(x, y), x, y),
        "rho_min": 1.0,
        "rho_max": 1.0,
        "finite_positive_state": True,
    })

    for t_end in times:
        label = f"t{int(round(100 * t_end)):03d}"
        run_dir = out / "runs" / label
        grid = run_dir / "grid.bin"
        if grid.exists():
            grid.unlink()
        text = _cfg_text(grid, t_end, nx, ny)
        _, metadata, _ = run_case(
            label,
            text,
            run_dir,
            binary,
            CFG,
            commit,
            binary_hash,
            output_bin=grid,
            experiment=EXPERIMENT,
        )
        diagnostics = metadata.get("stderr_diagnostics") or {}
        if "steps" not in diagnostics:
            raise RuntimeError(f"run {label} did not report a step count")
        row = _measure_grid(grid, int(diagnostics["steps"]))
        rows.append(row)
        run_metadata.append(pathlib.Path(metadata["run_config"]).parent.joinpath("metadata.json").relative_to(ROOT).as_posix())
        if not args.keep_grids:
            grid.unlink()

    fit_rows = [row for row in rows if float(row["time"]) >= FIT_START_TIME]
    growth_rate, fit_r2 = fit_growth_rate(fit_rows)
    increasing = all(
        fit_rows[index]["mode_amplitude"] > fit_rows[index - 1]["mode_amplitude"]
        for index in range(1, len(fit_rows))
    )
    initial_transient = rows[1]["mode_amplitude"] < rows[0]["mode_amplitude"]
    finite_positive = all(bool(row["finite_positive_state"]) for row in rows)
    gate_pass = bool(
        increasing and finite_positive and math.isfinite(growth_rate)
        and growth_rate > 0.0 and fit_r2 >= 0.98
    )
    figures = _plot(rows, out, growth_rate, FIT_START_TIME)
    payload = {
        "schema": {"name": "hrsc.experiment-summary", "version": 1},
        "experiment": EXPERIMENT,
        "scope": "Lecoanet unstratified IC and early linear growth only",
        "mode": "smoke" if args.smoke else "reproduction",
        "git_commit": commit,
        "binary": str(binary),
        "binary_sha256": binary_hash,
        "source_config": CFG.relative_to(ROOT).as_posix(),
        "source_config_sha256": sha256_file(CFG),
        "implementation_sources": {
            path.relative_to(ROOT).as_posix(): sha256_file(path)
            for path in IMPLEMENTATION_SOURCES
        },
        "analysis_environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
        "grid": {"nx": nx, "ny": ny},
        "growth_rate": growth_rate,
        "expected_growth_rate": EXPECTED_GROWTH_RATE,
        "growth_rate_relative_difference": abs(growth_rate - EXPECTED_GROWTH_RATE) / EXPECTED_GROWTH_RATE,
        "fit_r2": fit_r2,
        "fit_window": {
            "start": FIT_START_TIME,
            "end": float(fit_rows[-1]["time"]),
            "initial_seed_adjustment_transient_observed": initial_transient,
        },
        "rows": rows,
        "gate": {
            "pass": gate_pass,
            "mode_amplitude_strictly_increasing_in_fit_window": increasing,
            "finite_positive_state": finite_positive,
            "fit_r2_minimum": 0.98,
        },
        "figures": figures,
        "run_metadata": run_metadata,
        "claim_boundary": [
            "No nonlinear Re=1e5 reference-solution claim.",
            "No explicit-viscosity, thermal-diffusion, or passive-dye claim.",
            "The literature growth rate is a diagnostic comparison, not the pass threshold.",
        ],
    }
    _write_summary(out, rows, payload)
    if not gate_pass:
        raise RuntimeError(f"reproduction gate failed: {payload['gate']}")
    return payload


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=pathlib.Path, default=DEFAULT_BINARY)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--nx", type=int, default=128)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--keep-grids", action="store_true")
    args = parser.parse_args(argv)
    if args.nx < 16:
        parser.error("--nx must be at least 16")
    return args


def main(argv: list[str] | None = None) -> int:
    payload = reproduce(_parse_args(argv))
    print((pathlib.Path(payload["source_config"])).as_posix())
    print(f"growth_rate={payload['growth_rate']:.6f} fit_r2={payload['fit_r2']:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
