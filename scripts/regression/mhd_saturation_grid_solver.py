#!/usr/bin/env python3
"""Long-horizon fp32-fp64 discrepancy for Kelvin-Helmholtz across grid and solver.

Report 2 measures the temporal saturation of the precision discrepancy only at
128^2 with the globally clamped HLL flux, while the refinement result shows the
same domain-mean level rising steeply with resolution.  The two therefore sit on
disjoint configurations and cannot be composed.  This runner closes that gap by
repeating the identical series -- same case, same stopping times, same analyser
and same tolerances as ``mhd_temporal_divergence.py`` -- on:

  kh_n256_hll_cfl04   256^2, HLL,  CFL 0.4  : grid axis against the 128^2 series
  kh_n128_hlld_cfl02  128^2, HLLD, CFL 0.2  : solver axis, least dissipative path
  kh_n128_hll_cfl02   128^2, HLL,  CFL 0.2  : matched-step control for the above
  kh_n256_hlld_cfl02  256^2, HLLD, CFL 0.2  : both axes at once (optional)

It is kept separate from ``mhd_temporal_divergence.py`` so that the frozen
Report 2 evidence for that experiment is not perturbed.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any, Mapping, Sequence

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "metrics", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

from _mhd_harness import (  # noqa: E402
    git_commit,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)
from scripts.metrics.drift_timeseries import analyse_pair  # noqa: E402

EXPERIMENT = "week22-mhd-saturation-grid-solver"
DEFAULT_OUT = ROOT / "experiments" / "week22" / "mhd_saturation_grid_solver"
KH_CFG = ROOT / "tests" / "cases" / "kelvin_helmholtz_2d" / "kh.cfg"

BINARY_PATHS = {
    "double": ROOT / "build-matrix" / "cpu-double-O2-ieee-leq" / "hrsc_mhd",
    "float": ROOT / "build-matrix" / "cpu-float-O2-ieee-leq" / "hrsc_mhd",
}

# t_start/t_end_max/n_slices reproduce the 128^2 HLL series of
# mhd_temporal_divergence.py exactly, so the stopping times are shared.
_COMMON = {
    "cfg": KH_CFG,
    "t_start": 0.2,
    "t_end_max": 3.0,
    "n_slices": 20,
    "fit_window": [0.2, 3.0],
}
CASES: dict[str, dict[str, Any]] = {
    "kh_n256_hll_cfl04": {**_COMMON, "nx": 256, "ny": 256, "solver": "hll", "cfl": 0.4},
    "kh_n128_hlld_cfl02": {**_COMMON, "nx": 128, "ny": 128, "solver": "hlld", "cfl": 0.2},
    "kh_n128_hll_cfl02": {**_COMMON, "nx": 128, "ny": 128, "solver": "hll", "cfl": 0.2},
    "kh_n256_hlld_cfl02": {**_COMMON, "nx": 256, "ny": 256, "solver": "hlld", "cfl": 0.2},
}


def slice_plan(case: str, smoke: bool = False, n_slices: int | None = None) -> list[float]:
    spec = CASES[case]
    count = 3 if smoke else int(n_slices or spec["n_slices"])
    return np.linspace(float(spec["t_start"]), float(spec["t_end_max"]), count).tolist()


def case_gamma(cfg_text: str) -> float:
    for line in cfg_text.splitlines():
        content = line.split("#", 1)[0].strip()
        if content and "=" in content:
            key, value = (part.strip() for part in content.split("=", 1))
            if key == "gamma":
                return float(value)
    return 5.0 / 3.0


def build_cfg(
    base_text: str,
    *,
    nx: int,
    ny: int,
    cfl: float,
    t_end: float,
    solver: str,
    output_file: pathlib.Path,
) -> str:
    text = base_text
    for key, value in (
        ("nx", str(nx)),
        ("ny", str(ny)),
        ("cfl", f"{cfl:.17g}"),
        ("t_end", f"{t_end:.17g}"),
        ("riemann", solver),
        ("output_format", "binary"),
        ("output_file", output_file.as_posix()),
    ):
        text = replace_or_append_cfg(text, key, value)
    return text


def run_series(
    case: str,
    out_dir: pathlib.Path,
    binaries: Mapping[str, pathlib.Path],
    *,
    smoke: bool = False,
    keep_grids: bool = False,
    n_slices: int | None = None,
) -> dict[str, Any]:
    spec = CASES[case]
    source_cfg = pathlib.Path(spec["cfg"])
    base_text = source_cfg.read_text(encoding="utf-8")
    gamma = case_gamma(base_text)
    commit = git_commit()
    grids: dict[str, list[pathlib.Path]] = {"double": [], "float": []}
    runs: list[dict[str, Any]] = []
    for precision in ("double", "float"):
        binary = pathlib.Path(binaries[precision])
        sha = sha256_file(binary) if binary.is_file() else "test-double"
        for index, target in enumerate(slice_plan(case, smoke=smoke, n_slices=n_slices)):
            run_dir = pathlib.Path(out_dir) / "runs" / case / precision / f"slice_{index:02d}"
            grid = run_dir / "grid.bin"
            cfg_text = build_cfg(
                base_text,
                nx=int(spec["nx"]),
                ny=int(spec["ny"]),
                cfl=float(spec["cfl"]),
                t_end=target,
                solver=str(spec["solver"]),
                output_file=grid,
            )
            _, meta, _ = run_case(
                f"{case}-{precision}-{index:02d}",
                cfg_text,
                run_dir,
                binary,
                source_cfg,
                commit,
                sha,
                output_bin=grid,
                experiment=EXPERIMENT,
            )
            grids[precision].append(grid)
            runs.append(meta)
    entry = {
        "case": case,
        "pair": "fp32-vs-fp64",
        "variable": "rho",
        "gamma": gamma,
        "a": list(grids["double"]),
        "b": list(grids["float"]),
        "time_tolerance": 2.0e-3,
        "spatial_tolerance": 1.0e-5,
        "notes": [
            "Descriptive discrepancy series; the fitted exponent is not a growth law.",
        ],
    }
    record = analyse_pair(entry, fit_window=spec["fit_window"])
    record["grid"] = f"{int(spec['nx'])}x{int(spec['ny'])}"
    record["solver"] = str(spec["solver"])
    record["cfl"] = float(spec["cfl"])
    if not keep_grids:
        for grid in grids["double"] + grids["float"]:
            if grid.is_file():
                grid.unlink()
    return {"record": record, "runs": runs}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=sorted(CASES) + ["all"], default="all")
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--keep-grids", action="store_true")
    parser.add_argument(
        "--n-slices",
        type=int,
        default=None,
        help="override the stopping-time count; the window is unchanged",
    )
    args = parser.parse_args(argv)

    selected = sorted(CASES) if args.case == "all" else [args.case]
    out = args.out if args.out.is_absolute() else ROOT / args.out
    if args.case != "all":
        out = out.with_name(f"{out.name}_{args.case}")
    if args.smoke:
        out = out.with_name(f"{out.name}_smoke")
    out.mkdir(parents=True, exist_ok=True)

    binaries = {p: resolve_binary(path) for p, path in BINARY_PATHS.items()}
    records: list[dict[str, Any]] = []
    runs: list[dict[str, Any]] = []
    for case in selected:
        result = run_series(
            case,
            out,
            binaries,
            smoke=args.smoke,
            keep_grids=args.keep_grids,
            n_slices=args.n_slices,
        )
        records.append(result["record"])
        runs.extend(result["runs"])

    summary = {
        "experiment": EXPERIMENT,
        "mode": "smoke" if args.smoke else "diagnostic",
        "selected_cases": selected,
        "git_commit": git_commit(),
        "analysis_generator": {
            "path": "scripts/regression/mhd_saturation_grid_solver.py",
            "sha256": sha256_file(pathlib.Path(__file__)),
        },
        "case_spec": {
            case: {
                k: (str(v) if isinstance(v, pathlib.Path) else v)
                for k, v in CASES[case].items()
            }
            for case in selected
        },
        "records": records,
        "runs": runs,
        "runs_successful": all(r.get("returncode") == 0 for r in runs),
    }
    (out / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    for record in records:
        print(
            f"{record['case']}: n={len(record['times'])} "
            f"l1[0]={record['l1'][0]:.4e} l1[-1]={record['l1'][-1]:.4e} "
            f"ratio={record['l1'][-1] / record['l1'][0]:.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
