#!/usr/bin/env python3
"""OpenMP thread-count axis on the Euler path, which does carry work sharing.

The ideal-MHD sweeps contain no work-sharing directives, so a thread-count
request cannot reach the arithmetic there and the resulting null is a statement
about the code rather than about threading. The Euler solver is different: its
x- and y-sweeps and its conservative update are wrapped in
`#pragma omp parallel for`, and the CFL scan is an explicit
`reduction(max:...)` over the whole grid. Running the thread axis there tests
the question the MHD path cannot.

Two comparisons are made for each precision:

  * serial build against the one-thread OpenMP build, isolating the effect of
    enabling the directives at all;
  * 2, 4 and 8 threads against one thread of the same OpenMP binary, isolating
    the effect of the decomposition.

Wall times are recorded so that a null arithmetic result can be shown to come
from an execution that actually used the threads, rather than from threads that
were never created.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import statistics
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from scripts.regression._mhd_harness import (  # noqa: E402
    ROOT,
    git_commit,
    read_binary,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)
from scripts.regression.mhd_gpu_hardware_axis import max_ulp_distance  # noqa: E402

CFG = ROOT / "tests" / "cases" / "liska_wendroff_2d" / "config3_n200.cfg"
DEFAULT_OUT = ROOT / "experiments" / "week21" / "euler_openmp_thread_axis"
EXPERIMENT = "week21-euler-openmp-thread-axis"
THREADS = (1, 2, 4, 8)
REPEATS = 3
BINS = {
    ("double", "omp"): ROOT / "build-double-omp" / "hrsc",
    ("float", "omp"): ROOT / "build-float-omp" / "hrsc",
    ("double", "serial"): ROOT / "build-double" / "hrsc",
    ("float", "serial"): ROOT / "build-float" / "hrsc",
}
IMPLEMENTATION_SOURCES = (
    ROOT / "src" / "euler" / "euler_solver.cpp",
    ROOT / "src" / "main.cpp",
    pathlib.Path(__file__).resolve(),
)


def one_run(label: str, binary: pathlib.Path, out: pathlib.Path, commit: str,
            binary_sha: str, threads: int | None) -> tuple[np.ndarray, float, int]:
    run_dir = out / "runs" / label
    out_bin = run_dir / "grid.bin"
    text = CFG.read_text(encoding="utf-8")
    text = replace_or_append_cfg(text, "output_format", "binary")
    text = replace_or_append_cfg(text, "output_file", str(out_bin).replace("\\", "/"))
    previous = os.environ.get("OMP_NUM_THREADS")
    if threads is not None:
        os.environ["OMP_NUM_THREADS"] = str(threads)
    try:
        run_case(label, text, run_dir, binary, CFG, commit, binary_sha,
                 output_bin=out_bin, experiment=EXPERIMENT)
    finally:
        if previous is None:
            os.environ.pop("OMP_NUM_THREADS", None)
        else:
            os.environ["OMP_NUM_THREADS"] = previous
    meta = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    _, arr = read_binary(out_bin)
    out_bin.unlink(missing_ok=True)
    steps = (meta.get("completion") or {}).get("steps")
    return np.ascontiguousarray(arr), float(meta["elapsed_wall_s"]), steps


def timed(label: str, binary: pathlib.Path, out: pathlib.Path, commit: str,
          binary_sha: str, threads: int | None,
          repeats: int) -> tuple[np.ndarray, list[float], int]:
    """First execution is a warm-up and its time is discarded; state is kept."""
    state, _, steps = one_run(f"{label}-warmup", binary, out, commit, binary_sha, threads)
    times = []
    for k in range(repeats):
        again, elapsed, _ = one_run(f"{label}-r{k}", binary, out, commit, binary_sha, threads)
        if not np.array_equal(again, state):
            raise RuntimeError(f"{label}: repeat {k} was not reproducible within the run")
        times.append(elapsed)
    return state, times, steps


def compare(reference: np.ndarray, candidate: np.ndarray) -> dict:
    if reference.dtype != candidate.dtype or reference.shape != candidate.shape:
        raise ValueError("mismatched saved states")
    diff = np.abs(candidate.astype(np.float64) - reference.astype(np.float64))
    return {
        "ulp_max": max_ulp_distance(reference, candidate),
        "linf_abs": float(diff.max(initial=0.0)),
        "bitwise_identical": bool(np.array_equal(reference, candidate)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    ap.add_argument("--threads", type=int, nargs="*", default=list(THREADS))
    ap.add_argument("--repeats", type=int, default=REPEATS)
    args = ap.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    commit = git_commit()

    groups = []
    for precision in ("double", "float"):
        omp = resolve_binary(BINS[(precision, "omp")])
        serial = resolve_binary(BINS[(precision, "serial")])
        omp_sha, serial_sha = sha256_file(omp), sha256_file(serial)

        serial_state, serial_times, steps = timed(
            f"{precision}-serial", serial, out, commit, serial_sha, None, args.repeats)

        rows, reference = [], None
        for threads in sorted(args.threads):
            state, times, steps_t = timed(
                f"{precision}-omp-t{threads}", omp, out, commit, omp_sha,
                threads, args.repeats)
            if reference is None:
                reference = state
            row = {
                "threads": threads,
                "steps": steps_t,
                "median_wall_s": statistics.median(times),
                "wall_times_s": times,
                **compare(reference, state),
            }
            rows.append(row)
        base = rows[0]["median_wall_s"]
        for row in rows:
            row["speedup_over_one_thread"] = base / row["median_wall_s"]

        groups.append({
            "precision": precision,
            "case": "lw_config3",
            "grid": "200x200",
            "solver": "hllc",
            "steps": steps,
            "omp_binary": str(omp), "omp_binary_sha256": omp_sha,
            "serial_binary": str(serial), "serial_binary_sha256": serial_sha,
            "serial_median_wall_s": statistics.median(serial_times),
            "serial_vs_one_thread": compare(serial_state, reference),
            "rows": rows,
        })

    payload = {
        "experiment": EXPERIMENT,
        "scope": ("Euler HLLC MUSCL-Hancock, Liska-Wendroff configuration 3 at "
                  "200^2. The Euler sweeps carry omp parallel for and the CFL "
                  "scan an explicit reduction(max:...)."),
        "git_commit": commit,
        "repeats_after_warmup": args.repeats,
        "source_config": str(CFG.relative_to(ROOT)),
        "source_config_sha256": sha256_file(CFG),
        "implementation_sources": {
            str(p.relative_to(ROOT)): sha256_file(p) for p in IMPLEMENTATION_SOURCES
        },
        "groups": groups,
        "all_thread_counts_bitwise_identical": all(
            r["bitwise_identical"] for g in groups for r in g["rows"]),
        "serial_matches_one_thread": all(
            g["serial_vs_one_thread"]["bitwise_identical"] for g in groups),
        "claim_boundary": [
            "One workstation, one compiler, one case and grid.",
            "A null here bounds this scheme's reduction structure, not OpenMP in general.",
            "Wall times are subprocess times on a shared desktop, not a scaling study.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    for g in groups:
        print(f"\n[{g['precision']}] {g['case']} {g['grid']} steps={g['steps']}  "
              f"serial={g['serial_median_wall_s']:.2f}s  "
              f"serial==1thread: {g['serial_vs_one_thread']['bitwise_identical']}")
        for r in g["rows"]:
            print(f"   threads={r['threads']}  median={r['median_wall_s']:6.2f}s  "
                  f"speedup={r['speedup_over_one_thread']:.2f}x  "
                  f"ULPmax={r['ulp_max']}  Linf={r['linf_abs']:.3e}")
    print(f"\nall thread counts bitwise identical: "
          f"{payload['all_thread_counts_bitwise_identical']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
