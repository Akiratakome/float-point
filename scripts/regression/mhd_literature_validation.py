#!/usr/bin/env python3
"""Supervisor-facing Brio-Wu literature validation packet for Week 14.

This is a harness/reporting helper only. It does not alter solver numerics or
Week-14 summary schemas. The formal evidence path keeps Docker Verificarlo MCA
as required evidence; blocked or skipped MCA is rejected for this note.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASE = ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg"
DEFAULT_SUMMARY = ROOT / "experiments" / "week14" / "mhd_precision_pilot" / "summary.json"
DEFAULT_OUT = ROOT / "experiments" / "week14" / "mhd_precision_pilot" / "literature_validation"
DEFAULT_BINARY = ROOT / "build-matrix" / "cpu-double-O2-ieee-leq" / "hrsc_mhd.exe"
REFERENCE = "cpu-double-O2-ieee-leq"
EXPERIMENT = "week14-mhd-literature-validation"

for path in (
    ROOT,
    ROOT / "scripts",
    ROOT / "scripts" / "metrics",
    ROOT / "scripts" / "regression",
):
    sys.path.insert(0, str(path))

from io_helper import read_binary  # noqa: E402
from mhd_fields import mhd_primitive_fields  # noqa: E402
from _mhd_harness import (  # noqa: E402
    git_commit,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)

SOURCES = [
    {
        "label": "Brio & Wu (1988)",
        "url": "https://doi.org/10.1016/0021-9991(88)90120-9",
        "role": "classic one-dimensional ideal-MHD shock-tube benchmark",
    },
    {
        "label": "Athena code paper (Stone et al., 2008)",
        "url": "https://arxiv.org/abs/0804.0402",
        "role": "modern MHD code test-suite context for comparison claims",
    },
    {
        "label": "PLUTO code paper (Mignone et al., 2007)",
        "url": "https://arxiv.org/abs/astro-ph/0701854",
        "role": "Godunov shock-capturing benchmark context",
    },
    {
        "label": "Takahashi & Yamada (2012)",
        "url": "https://arxiv.org/abs/1210.5584",
        "role": "Brio-Wu Riemann-problem non-uniqueness caution",
    },
]


def supervisor_payload(summary: dict[str, Any]) -> dict[str, Any]:
    """Extract a claim-bounded supervisor summary from authoritative Week-14 JSON."""
    g0 = summary.get("gates", {}).get("G0", {})
    if g0.get("pass") is not True:
        raise ValueError("Week-14 G0 must pass before writing supervisor validation.")
    mca = summary.get("mca", {})
    for key in ("p53", "p24"):
        block = mca.get(key, {})
        if block.get("status") != "completed" or block.get("runner") != "docker":
            raise ValueError(f"{key} must have completed Docker Verificarlo MCA evidence.")
        if int(block.get("n", 0)) <= 0:
            raise ValueError(f"{key} Docker Verificarlo MCA sample count must be positive.")
    reference = _reference_row(summary)
    return {
        "experiment": summary.get("experiment"),
        "case": summary.get("case"),
        "solver": summary.get("solver"),
        "reference": summary.get("reference"),
        "git_commit": summary.get("git_commit"),
        "g0_pass": bool(g0.get("pass")),
        "reference_steps": int(reference.get("steps", 0)),
        "reference_divB_max": float(reference.get("divB_max", 0.0)),
        "reference_finite": bool(reference.get("finite")),
        "mca": {
            key: {
                "status": mca[key].get("status"),
                "n": int(mca[key].get("n", 0)),
                "runner": mca[key].get("runner"),
                "spread_rho": mca[key].get("spread_rho"),
                "spread_By": mca[key].get("spread_By"),
                "spread_p": mca[key].get("spread_p"),
            }
            for key in ("p53", "p24")
        },
        "sources": SOURCES,
    }


def profile_fields(arr: np.ndarray, *, gamma: float, dx: float, xmin: float) -> dict[str, np.ndarray]:
    """Return x and y-averaged primitive fields used in Brio-Wu profile plots."""
    prim = mhd_primitive_fields(arr.astype(np.float64, copy=False), gamma)
    nx = arr.shape[1]
    profile = {"x": xmin + (np.arange(nx, dtype=np.float64) + 0.5) * dx}
    for name in ("rho", "vx", "By", "p"):
        profile[name] = np.asarray(prim[name], dtype=np.float64).mean(axis=0)
    return profile


def render_markdown(payload: dict[str, Any]) -> str:
    """Render a short supervisor-facing validation note."""
    mca = payload["mca"]
    source_lines = "\n".join(
        f"- [{source['label']}]({source['url']}): {source['role']}."
        for source in payload["sources"]
    )
    return f"""# Week 14 Supervisor Validation Note

## What Was Validated

- Benchmark: Brio-Wu 1D ideal-MHD shock tube, following the classic Brio & Wu (1988) validation problem.
- Solver path: HLL, CPU only; HLLD remains deferred diagnostic work.
- Formal Week-14 gate: G0 pass = {payload['g0_pass']}.
- Reference row: `{payload['reference']}` with steps = {payload['reference_steps']} and divB_max = {payload['reference_divB_max']:.3e}.
- Docker Verificarlo MCA: p53 completed with n = {mca['p53']['n']}; p24 completed with n = {mca['p24']['n']}.

## Literature Comparison

The result should be presented as a benchmark-aligned validation, not as a new
exact-solution claim. Brio-Wu is a standard MHD shock-tube problem used to check
shock-capturing behavior. Athena and PLUTO provide the relevant code-validation
context: robust Godunov-type MHD methods are expected to capture the wave
pattern while differing in dissipation depending on the Riemann solver. The HLL
choice here is therefore framed as a robust production baseline, with sharper
HLLD-style comparisons left to later work.

## Claim boundary

- Supported now: finite Brio-Wu HLL execution, reproduced Week-14 reference
  anchor, bounded divB diagnostic, deterministic precision deltas, and Docker
  Verificarlo MCA noise evidence.
- Not claimed now: exact Riemann-solution agreement, HLLD superiority/production
  readiness, 2D MHD conclusions, GPU MHD conclusions, or P1/P2 scaling claims.

## Sources

{source_lines}
"""


def write_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), indent=2) + "\n", encoding="utf-8")


def plot_profile(profile: dict[str, np.ndarray], path: pathlib.Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [("rho", "Density"), ("vx", "Velocity x"), ("By", "Magnetic field y"), ("p", "Pressure")]
    fig, axes = plt.subplots(4, 1, figsize=(7.0, 8.0), sharex=True)
    for ax, (key, label) in zip(axes, fields):
        ax.plot(profile["x"], profile[key], color="#1f77b4", linewidth=1.3)
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.25)
    axes[-1].set_xlabel("x")
    fig.suptitle("Brio-Wu 1D HLL reference profile (Week 14)")
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.98))
    fig.savefig(path, dpi=180)
    plt.close(fig)


def run_reference(binary: pathlib.Path, out: pathlib.Path, *, keep_grid: bool) -> pathlib.Path:
    """Run the reference Brio-Wu case once and return the transient grid path."""
    run_dir = out / "reference_profile"
    grid = run_dir / "grid.bin"
    cfg_text = CASE.read_text(encoding="utf-8")
    cfg_text = replace_or_append_cfg(cfg_text, "output_format", "binary")
    cfg_text = replace_or_append_cfg(cfg_text, "output_file", str(grid))
    bin_path = resolve_binary(binary)
    run_case(
        REFERENCE,
        cfg_text,
        run_dir,
        bin_path,
        CASE,
        git_commit(),
        sha256_file(bin_path),
        output_bin=grid,
        experiment=EXPERIMENT,
    )
    if not keep_grid:
        # The caller reads the grid before cleanup through build_profile_packet.
        return grid
    return grid


def build_profile_packet(args: argparse.Namespace) -> dict[str, Any]:
    out = _resolve(args.out)
    summary = json.loads(_resolve(args.summary).read_text(encoding="utf-8"))
    payload = supervisor_payload(summary)
    grid = _resolve(args.grid) if args.grid is not None else run_reference(_resolve(args.binary), out, keep_grid=True)
    header, arr = read_binary(grid)
    gamma = _cfg_float(CASE, "gamma", 2.0)
    xmin = _cfg_float(CASE, "xmin", 0.0)
    profile = profile_fields(arr, gamma=gamma, dx=float(header.dx), xmin=xmin)
    figure = out / "brio_wu_reference_profile.png"
    plot_profile(profile, figure)
    payload["profile_figure"] = str(figure.relative_to(ROOT) if figure.is_relative_to(ROOT) else figure)
    payload["profile_grid_shape"] = [int(header.ny), int(header.nx), int(header.nvars)]
    payload["profile_time"] = float(header.t)
    write_json(out / "supervisor_validation.json", payload)
    (out / "supervisor_validation.md").write_text(render_markdown(payload), encoding="utf-8")
    if args.grid is None and not args.keep_grid and grid.is_file():
        grid.unlink()
    return payload


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    build_profile_packet(args)
    print(_resolve(args.out) / "supervisor_validation.md")
    return 0


def _reference_row(summary: dict[str, Any]) -> dict[str, Any]:
    for row in summary.get("deterministic", []):
        if row.get("variant") == REFERENCE or row.get("is_reference") is True:
            return row
    raise ValueError(f"summary does not contain reference row {REFERENCE}")


def _cfg_float(path: pathlib.Path, key: str, default: float) -> float:
    for line in path.read_text(encoding="utf-8").splitlines():
        content = line.split("#", 1)[0].strip()
        if not content or "=" not in content:
            continue
        lhs, rhs = [part.strip() for part in content.split("=", 1)]
        if lhs == key:
            return float(rhs)
    return default


def _jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _resolve(path: pathlib.Path) -> pathlib.Path:
    return path if path.is_absolute() else ROOT / path


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=pathlib.Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--binary", type=pathlib.Path, default=DEFAULT_BINARY)
    parser.add_argument("--grid", type=pathlib.Path)
    parser.add_argument("--keep-grid", action="store_true")
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
