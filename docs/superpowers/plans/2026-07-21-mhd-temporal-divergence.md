# MHD Temporal Divergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce report-grade fp32-versus-fp64 temporal-divergence evidence and Lyapunov-like growth fits for Brio-Wu 1D and Orszag-Tang 2D without changing the C++ solver.

**Architecture:** A Python regression driver generates cfg slices with increasing `t_end`, runs the canonical CPU O2/IEEE/leq float and double MHD binaries, and delegates grid-pair measurement and exponential fitting to `scripts.metrics.drift_timeseries`. The driver writes provenance-rich JSON/CSV/Markdown summaries and one paper-style figure, then removes transient grids unless explicitly asked to keep them.

**Tech Stack:** Python 3.11, pytest, NumPy, matplotlib, the existing `_mhd_harness.py`, `drift_timeseries.py`, and `build-matrix` CPU binaries.

## Global Constraints

- Do not change MHD solver numerics, existing cfg defaults, or binary output formats.
- Use only `cpu-double-O2-ieee-leq` and `cpu-float-O2-ieee-leq`, with HLL.
- Cases are Brio-Wu 1D at native `nx=800` and Orszag-Tang 2D at `128^2`.
- Fit `log(error) = lambda*t + c`; describe lambda as Lyapunov-like, never as a formal maximal Lyapunov exponent.
- Preserve generated cfgs, stdout, stderr, metadata, binary hashes, and git commit.
- Delete transient `.bin` grids after successful measurement unless `--keep-grids` is passed.
- Use the project test interpreter: `C:\Users\tangy\miniconda3\envs\floatpoint\python.exe`.

---

## File Map

- Create `scripts/regression/mhd_temporal_divergence.py`: configuration, run orchestration, aggregation, gates, plotting, and CLI.
- Extend `tests/py/test_mhd_temporal_divergence.py`: pure helper, fake-run integration, schema, cleanup, and CLI tests. The existing untracked four-test seed is retained.
- Modify `scripts/regression/README.md`: command and evidence contract.
- Modify `docs/INDEX.md`: register the completed temporal-divergence data product.
- Create evidence under `experiments/week15/mhd_temporal_divergence/`: `summary.{json,csv,md}`, `figures/temporal_divergence.png`, and per-run metadata/logs; do not commit `.bin` files.

### Task 1: Slice and cfg helpers

**Files:**
- Create: `scripts/regression/mhd_temporal_divergence.py`
- Test: `tests/py/test_mhd_temporal_divergence.py`

**Interfaces:**
- Produces: `CASES`, `DEFAULT_GAMMA`, `slice_plan(case_name, smoke=False)`, `case_gamma(cfg_text)`, `temporal_cfg(...)`, and `pair_entry(...)`.
- Consumes: `replace_or_append_cfg` from `scripts/regression/_mhd_harness.py`.

- [ ] **Step 1: Run the existing seed tests and verify the module is missing**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_mhd_temporal_divergence.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'mhd_temporal_divergence'`.

- [ ] **Step 2: Create the driver constants and pure helpers**

Create `scripts/regression/mhd_temporal_divergence.py` with these public interfaces:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
from typing import Any, Callable, Mapping, Sequence

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "metrics", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

from _mhd_harness import replace_or_append_cfg

DEFAULT_GAMMA = 5.0 / 3.0
DEFAULT_OUT = ROOT / "experiments" / "week15" / "mhd_temporal_divergence"
CASES = {
    "brio_wu_1d": {
        "cfg": ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg",
        "nx": 800,
        "ny": 1,
        "t_start": 0.01,
        "t_end_max": 0.1,
        "n_slices": 15,
        "fit_window": [0.01, 0.1],
    },
    "orszag_tang_2d": {
        "cfg": ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg",
        "nx": 128,
        "ny": 128,
        "t_start": 0.05,
        "t_end_max": 1.0,
        "n_slices": 25,
        "fit_window": [0.1, 0.5],
    },
}


def slice_plan(case_name: str, smoke: bool = False) -> list[float]:
    spec = CASES[case_name]
    count = 3 if smoke else int(spec["n_slices"])
    return np.linspace(float(spec["t_start"]), float(spec["t_end_max"]), count).tolist()


def case_gamma(cfg_text: str) -> float:
    for line in cfg_text.splitlines():
        content = line.split("#", 1)[0].strip()
        if content and "=" in content:
            key, value = (part.strip() for part in content.split("=", 1))
            if key == "gamma":
                return float(value)
    return DEFAULT_GAMMA


def temporal_cfg(
    base_text: str,
    *,
    nx: int,
    ny: int,
    t_end: float,
    solver: str,
    output_file: pathlib.Path,
) -> str:
    text = base_text
    for key, value in (
        ("nx", str(nx)),
        ("ny", str(ny)),
        ("t_end", f"{t_end:.17g}"),
        ("riemann", solver),
        ("output_format", "binary"),
        ("output_file", output_file.as_posix()),
    ):
        text = replace_or_append_cfg(text, key, value)
    return text


def pair_entry(
    case_name: str,
    *,
    gamma: float,
    double_grids: Sequence[pathlib.Path],
    float_grids: Sequence[pathlib.Path],
) -> dict[str, Any]:
    return {
        "case": case_name,
        "pair": "fp32-vs-fp64",
        "variable": "rho",
        "gamma": gamma,
        "a": list(double_grids),
        "b": list(float_grids),
        "time_tolerance": 2.0e-3,
        "spatial_tolerance": 1.0e-5,
        "notes": ["Lyapunov-like precision-perturbation growth rate; not a formal maximal exponent."],
    }
```

- [ ] **Step 3: Run the helper tests**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_mhd_temporal_divergence.py -q
```

Expected: the four seed tests pass.

- [ ] **Step 4: Commit the pure helper slice**

```powershell
git add -- scripts/regression/mhd_temporal_divergence.py tests/py/test_mhd_temporal_divergence.py
git commit -m "feat(analysis): add MHD temporal slice configuration"
```

### Task 2: Run orchestration, provenance, and cleanup

**Files:**
- Modify: `scripts/regression/mhd_temporal_divergence.py`
- Modify: `tests/py/test_mhd_temporal_divergence.py`

**Interfaces:**
- Consumes: `run_case`, `resolve_binary`, `sha256_file`, and `git_commit` from `_mhd_harness.py`; `analyse_pair` from `scripts.metrics.drift_timeseries`.
- Produces: `resolve_binaries() -> dict[str, Path]` and `run_case_series(case_name, out_dir, binaries, *, smoke=False, keep_grids=False, runner=run_case, analyser=analyse_pair) -> dict`.

- [ ] **Step 1: Add a failing fake-run integration test**

Append a test that records generated cfgs, creates placeholder grids, injects a fake analyser, and verifies cleanup only occurs after successful analysis:

```python
def test_run_case_series_records_both_precisions_and_cleans_grids(tmp_path):
    calls = []

    def fake_runner(label, cfg_text, run_dir, bin_path, source_cfg, commit, sha, **kwargs):
        grid = Path(kwargs["output_bin"])
        grid.parent.mkdir(parents=True, exist_ok=True)
        grid.write_bytes(b"grid")
        calls.append((label, cfg_text, Path(bin_path), grid))
        return None, {
            "returncode": 0,
            "elapsed_wall_s": 0.01,
            "stderr_diagnostics": {"steps": 1, "divB_max": 0.0},
        }, ""

    def fake_analyser(entry, fit_window):
        assert len(entry["a"]) == len(entry["b"]) == 3
        return {
            "case": entry["case"], "pair": entry["pair"], "variable": "rho",
            "times": [0.01, 0.055, 0.1], "l1": [1e-8, 2e-8, 3e-8],
            "linf": [2e-8, 4e-8, 6e-8], "lambda_l1": 1.0,
            "lambda_linf": 1.0, "fit_l1": {"slope": 1.0, "intercept": -18.0},
            "fit_linf": {"slope": 1.0, "intercept": -17.0},
            "fit_window": fit_window, "notes": entry["notes"], "samples": [],
        }

    result = td.run_case_series(
        "brio_wu_1d", tmp_path,
        {"double": tmp_path / "double.exe", "float": tmp_path / "float.exe"},
        smoke=True, runner=fake_runner, analyser=fake_analyser,
    )
    assert len(calls) == 6
    assert result["record"]["lambda_l1"] == 1.0
    assert not list(tmp_path.rglob("*.bin"))
```

- [ ] **Step 2: Run the integration test and verify failure**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_mhd_temporal_divergence.py::test_run_case_series_records_both_precisions_and_cleans_grids -q
```

Expected: FAIL because `run_case_series` is not defined.

- [ ] **Step 3: Implement binary resolution and case-series orchestration**

Add imports from `_mhd_harness` and `drift_timeseries`, constants for the two binaries, and this orchestration shape:

```python
from _mhd_harness import git_commit, resolve_binary, run_case, sha256_file
from scripts.metrics.drift_timeseries import analyse_pair

BINARY_PATHS = {
    "double": ROOT / "build-matrix" / "cpu-double-O2-ieee-leq" / "hrsc_mhd",
    "float": ROOT / "build-matrix" / "cpu-float-O2-ieee-leq" / "hrsc_mhd",
}


def resolve_binaries() -> dict[str, pathlib.Path]:
    return {precision: resolve_binary(path) for precision, path in BINARY_PATHS.items()}


def run_case_series(
    case_name: str,
    out_dir: pathlib.Path,
    binaries: Mapping[str, pathlib.Path],
    *,
    smoke: bool = False,
    keep_grids: bool = False,
    runner: Callable[..., Any] = run_case,
    analyser: Callable[..., dict[str, Any]] = analyse_pair,
) -> dict[str, Any]:
    spec = CASES[case_name]
    source_cfg = pathlib.Path(spec["cfg"])
    base_text = source_cfg.read_text(encoding="utf-8")
    gamma = case_gamma(base_text)
    commit = git_commit()
    grids: dict[str, list[pathlib.Path]] = {"double": [], "float": []}
    runs: list[dict[str, Any]] = []
    for precision in ("double", "float"):
        binary = pathlib.Path(binaries[precision])
        sha = sha256_file(binary) if binary.is_file() else "test-double"
        for index, target in enumerate(slice_plan(case_name, smoke=smoke)):
            run_dir = pathlib.Path(out_dir) / "runs" / case_name / precision / f"slice_{index:02d}"
            grid = run_dir / "grid.bin"
            cfg_text = temporal_cfg(
                base_text, nx=int(spec["nx"]), ny=int(spec["ny"]),
                t_end=target, solver="hll", output_file=grid,
            )
            _, meta, _ = runner(
                f"{case_name}-{precision}-{index:02d}", cfg_text, run_dir,
                binary, source_cfg, commit, sha, output_bin=grid,
                experiment="week15-mhd-temporal-divergence",
            )
            grids[precision].append(grid)
            runs.append(meta)
    entry = pair_entry(
        case_name, gamma=gamma,
        double_grids=grids["double"], float_grids=grids["float"],
    )
    record = analyser(entry, fit_window=spec["fit_window"])
    if not keep_grids:
        for grid in grids["double"] + grids["float"]:
            if grid.is_file():
                grid.unlink()
    return {"record": record, "runs": runs}
```

Do not put cleanup in a `finally` block: a failed measurement keeps grids for diagnosis.

- [ ] **Step 4: Run all temporal driver tests**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_mhd_temporal_divergence.py -q
```

Expected: all tests pass and the fake run leaves metadata directories but no `.bin` grids.

- [ ] **Step 5: Commit orchestration**

```powershell
git add -- scripts/regression/mhd_temporal_divergence.py tests/py/test_mhd_temporal_divergence.py
git commit -m "feat(analysis): orchestrate MHD temporal divergence runs"
```

### Task 3: Gates, summaries, and figure

**Files:**
- Modify: `scripts/regression/mhd_temporal_divergence.py`
- Modify: `tests/py/test_mhd_temporal_divergence.py`

**Interfaces:**
- Consumes: records returned by `run_case_series`.
- Produces: `evaluate_gates(records)`, `write_outputs(out_dir, records, runs)`, and `plot_records(out_dir, records)`.

- [ ] **Step 1: Add failing gate and output-schema tests**

Add `import json` and `import math` at the top of the test module, then append:

```python
def _record(case, lam, scale=1.0):
    return {
        "case": case, "pair": "fp32-vs-fp64", "variable": "rho",
        "times": [0.1, 0.2, 0.3], "l1": [scale, 2*scale, 4*scale],
        "linf": [2*scale, 4*scale, 8*scale], "lambda_l1": lam,
        "lambda_linf": lam, "fit_l1": {"slope": lam, "intercept": math.log(scale)},
        "fit_linf": {"slope": lam, "intercept": math.log(2*scale)},
        "fit_window": [0.1, 0.3], "notes": [], "samples": [],
    }


def test_outputs_are_strict_json_and_register_figure(tmp_path):
    records = [_record("brio_wu_1d", 0.1), _record("orszag_tang_2d", 2.0, 1e-6)]
    paths = td.write_outputs(tmp_path, records, runs=[])
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["gates"]["pass"] is True
    assert payload["gates"]["orszag_tang_positive_lambda"] is True
    assert payload["interpretation"]["formal_maximal_lyapunov"] is False
    assert paths["figure"].is_file()
```

- [ ] **Step 2: Run the schema test and verify failure**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_mhd_temporal_divergence.py::test_outputs_are_strict_json_and_register_figure -q
```

Expected: FAIL because `write_outputs` is not defined.

- [ ] **Step 3: Implement strict gates, summary files, and plotting**

Implement the following behavior:

```python
def evaluate_gates(records: Sequence[dict[str, Any]]) -> dict[str, Any]:
    by_case = {record["case"]: record for record in records}
    finite_nonnegative = all(
        math.isfinite(float(value)) and float(value) >= 0.0
        for record in records for key in ("l1", "linf") for value in record[key]
    )
    ot_lambda = by_case.get("orszag_tang_2d", {}).get("lambda_l1")
    ot_positive = ot_lambda is not None and math.isfinite(float(ot_lambda)) and float(ot_lambda) > 0.0
    complete = set(by_case) == set(CASES)
    return {
        "pass": bool(complete and finite_nonnegative and ot_positive),
        "cases_complete": complete,
        "all_drift_finite_nonnegative": finite_nonnegative,
        "orszag_tang_positive_lambda": ot_positive,
    }


def plot_records(out_dir: pathlib.Path, records: Sequence[dict[str, Any]]) -> pathlib.Path:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure = pathlib.Path(out_dir) / "figures" / "temporal_divergence.png"
    figure.parent.mkdir(parents=True, exist_ok=True)
    with plt.rc_context({
        "font.family": "serif", "font.size": 9,
        "axes.grid": True, "grid.alpha": 0.25,
        "figure.dpi": 120, "savefig.dpi": 300,
    }):
        fig, ax = plt.subplots(figsize=(6.6, 3.8), constrained_layout=True)
        for record in records:
            times = np.asarray(record["times"], dtype=np.float64)
            l1 = np.asarray(record["l1"], dtype=np.float64)
            label = str(record["case"]).replace("_", " ")
            line, = ax.plot(times, np.log10(l1), marker="o", ms=3, lw=1.2, label=label)
            fit = record["fit_l1"]
            window = record["fit_window"]
            if fit["slope"] is not None and window is not None:
                fit_t = np.linspace(float(window[0]), float(window[1]), 100)
                fit_log10 = (float(fit["slope"]) * fit_t + float(fit["intercept"])) / math.log(10.0)
                ax.plot(fit_t, fit_log10, ls="--", lw=1.0, color=line.get_color())
                ax.text(
                    fit_t[-1], fit_log10[-1], f"lambda={float(fit['slope']):.3g}",
                    color=line.get_color(), fontsize=8, ha="right", va="bottom",
                )
        ax.set_xlabel("time")
        ax.set_ylabel("log10 L1 density drift")
        ax.legend(frameon=False)
        fig.savefig(figure)
        plt.close(fig)
    return figure


def write_outputs(
    out_dir: pathlib.Path,
    records: Sequence[dict[str, Any]],
    runs: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    gates = evaluate_gates(records)
    figure = plot_records(out, records)
    payload = {
        "experiment": "week15-mhd-temporal-divergence",
        "git_commit": git_commit(),
        "gates": gates,
        "records": list(records),
        "runs": list(runs),
        "figure": figure.relative_to(out).as_posix(),
        "interpretation": {
            "formal_maximal_lyapunov": False,
            "statement": "lambda is a Lyapunov-like growth rate of an fp32-vs-fp64 perturbation.",
        },
    }
    json_path = out / "summary.json"
    csv_path = out / "summary.csv"
    md_path = out / "summary.md"
    json_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        columns = ("case", "pair", "variable", "time", "l1", "linf", "lambda_l1", "lambda_linf")
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in records:
            for time_value, l1, linf in zip(record["times"], record["l1"], record["linf"]):
                writer.writerow({
                    "case": record["case"], "pair": record["pair"],
                    "variable": record["variable"], "time": time_value,
                    "l1": l1, "linf": linf,
                    "lambda_l1": record["lambda_l1"],
                    "lambda_linf": record["lambda_linf"],
                })

    def fmt_lambda(value: Any) -> str:
        return "n/a" if value is None else f"{float(value):.6g}"

    lines = [
        "# MHD Temporal Divergence", "",
        "| case | samples | lambda L1 | lambda Linf | fit window |",
        "|---|---:|---:|---:|---|",
    ]
    for record in records:
        lines.append(
            f"| {record['case']} | {len(record['times'])} | {fmt_lambda(record['lambda_l1'])} | "
            f"{fmt_lambda(record['lambda_linf'])} | {record['fit_window']} |"
        )
    lines.extend([
        "", f"- Gate pass: {gates['pass']}",
        f"- Figure: `{payload['figure']}`", "",
        "The fitted lambda is a Lyapunov-like engineering growth rate of an "
        "fp32-vs-fp64 perturbation, not a formal maximal Lyapunov exponent.", "",
    ])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "json": json_path, "csv": csv_path, "markdown": md_path,
        "figure": figure, "payload": payload,
    }
```

- [ ] **Step 4: Run the focused and related metric tests**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_mhd_temporal_divergence.py tests\py\test_drift_timeseries.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit summaries and plotting**

```powershell
git add -- scripts/regression/mhd_temporal_divergence.py tests/py/test_mhd_temporal_divergence.py
git commit -m "feat(analysis): report MHD Lyapunov-like drift fits"
```

### Task 4: CLI, real evidence, and registration

**Files:**
- Modify: `scripts/regression/mhd_temporal_divergence.py`
- Modify: `tests/py/test_mhd_temporal_divergence.py`
- Modify: `scripts/regression/README.md`
- Modify: `docs/INDEX.md`
- Create: `experiments/week15/mhd_temporal_divergence/summary.json`
- Create: `experiments/week15/mhd_temporal_divergence/summary.csv`
- Create: `experiments/week15/mhd_temporal_divergence/summary.md`
- Create: `experiments/week15/mhd_temporal_divergence/figures/temporal_divergence.png`

**Interfaces:**
- Consumes: `resolve_binaries`, `run_case_series`, and `write_outputs`.
- Produces: CLI options `--out`, `--case {all,brio_wu_1d,orszag_tang_2d}`, `--smoke`, and `--keep-grids`.

- [ ] **Step 1: Add a failing CLI-default test**

```python
def test_parse_args_defaults_to_all_full_runs():
    args = td.parse_args([])
    assert args.out == td.DEFAULT_OUT
    assert args.case == "all"
    assert args.smoke is False
    assert args.keep_grids is False
```

- [ ] **Step 2: Run the CLI test and verify failure**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_mhd_temporal_divergence.py::test_parse_args_defaults_to_all_full_runs -q
```

Expected: FAIL because `parse_args` is not defined.

- [ ] **Step 3: Implement CLI and main**

```python
def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    parser.add_argument("--case", choices=("all", *CASES), default="all")
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--keep-grids", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    out = args.out if args.out.is_absolute() else ROOT / args.out
    binaries = resolve_binaries()
    names = list(CASES) if args.case == "all" else [args.case]
    records, runs = [], []
    for name in names:
        result = run_case_series(
            name, out, binaries, smoke=args.smoke, keep_grids=args.keep_grids,
        )
        records.append(result["record"])
        runs.extend(result["runs"])
    paths = write_outputs(out, records, runs)
    print(paths["markdown"])
    return 0 if paths["payload"]["gates"]["pass"] else 1
```

When `--case` selects only one case, `evaluate_gates` must report `cases_complete=false`; `--smoke` is therefore a diagnostic command and may return 1 until both cases are present. For the evidence command, always use the default `--case all`.

- [ ] **Step 4: Run all unit tests for the driver**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_mhd_temporal_divergence.py tests\py\test_drift_timeseries.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Ensure the two canonical binaries exist**

Run:

```powershell
Test-Path 'build-matrix\cpu-double-O2-ieee-leq\hrsc_mhd.exe'
Test-Path 'build-matrix\cpu-float-O2-ieee-leq\hrsc_mhd.exe'
```

Expected: both print `True`. If either is absent, build only the missing variants through the established matrix builder before continuing.

Build command for either or both missing variants:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -c "from scripts.build_matrix import BuildVariant; from scripts.regression.mhd_precision_pilot import build_variant; [build_variant(BuildVariant(p, 'O2', False, False)) for p in ('double', 'float')]"
```

Expected: each call returns a path ending in `build-matrix/cpu-<precision>-O2-ieee-leq/hrsc_mhd.exe`.

- [ ] **Step 6: Run the real smoke**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\regression\mhd_temporal_divergence.py --smoke --out experiments\week15\mhd_temporal_divergence_smoke
```

Expected: six slices per case pair complete, strict JSON is written, and no `.bin` remains. Inspect the series before selecting the fixed full-run fit window; change the window only if the observed growth phase lies outside the design value, and record the reason in the summary.

- [ ] **Step 7: Run the full evidence command**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" scripts\regression\mhd_temporal_divergence.py
```

Expected: Brio-Wu has 15 paired samples, Orszag-Tang has 25 paired samples, `gates.pass=true`, the OT L1 lambda is positive, and the figure exists.

- [ ] **Step 8: Audit evidence structure**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -c "import json,pathlib; p=pathlib.Path('experiments/week15/mhd_temporal_divergence'); d=json.loads((p/'summary.json').read_text()); assert d['gates']['pass']; assert {r['case']:len(r['times']) for r in d['records']} == {'brio_wu_1d':15,'orszag_tang_2d':25}; assert (p/'figures/temporal_divergence.png').is_file(); assert not list(p.rglob('*.bin')); print('temporal evidence audit passed')"
```

Expected: `temporal evidence audit passed`.

- [ ] **Step 9: Register the command and evidence**

Add to `scripts/regression/README.md`:

```markdown
- `mhd_temporal_divergence.py`: runs fp32-vs-fp64 HLL time slices for Brio-Wu
  1D and Orszag-Tang 2D, fits Lyapunov-like density-drift growth rates, and
  writes `experiments/week15/mhd_temporal_divergence/summary.{json,csv,md}`
  plus `figures/temporal_divergence.png`. Use `--smoke` before the full run.
```

Add a data-product row to `docs/INDEX.md` naming both cases, sample counts,
the fp32/fp64 pair, and the interpretation boundary.

- [ ] **Step 10: Run final verification**

Run:

```powershell
& "C:\Users\tangy\miniconda3\envs\floatpoint\python.exe" -m pytest tests\py\test_mhd_temporal_divergence.py tests\py\test_drift_timeseries.py tests\py\test_mhd_orszag_tang_precision_smoke.py tests\py\test_mhd_precision_sampling.py -q
git diff --check
```

Expected: all selected tests pass and `git diff --check` prints no errors.

- [ ] **Step 11: Commit code, docs, and bounded evidence without grids**

```powershell
git add -- scripts/regression/mhd_temporal_divergence.py tests/py/test_mhd_temporal_divergence.py scripts/regression/README.md docs/INDEX.md
git add -f -- experiments/week15/mhd_temporal_divergence/summary.json experiments/week15/mhd_temporal_divergence/summary.csv experiments/week15/mhd_temporal_divergence/summary.md experiments/week15/mhd_temporal_divergence/figures/temporal_divergence.png
git commit -m "feat(analysis): add report-grade MHD temporal divergence evidence"
```

Verify staged content contains no `.bin` before committing:

```powershell
git diff --cached --name-only | Select-String -Pattern '\.bin$'
```

Expected: no output.

## Next Plan

After this plan passes, execute `docs/superpowers/plans/2026-07-09-gpu-mhd-hll.md`. The hardware-axis packet, Kelvin-Helmholtz precision packet, and 512^2 consolidation receive separate plans after the GPU gate and KH 512^2 prerequisite expose their actual tolerances and runtime costs.
