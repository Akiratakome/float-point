#!/usr/bin/env python3
"""Do implementation-axis differences grow with time?

The reported temporal study follows the fp32-fp64 precision axis only. The
project brief asks whether the difference between different *implementations*
of the same algorithm grows over time, which is the build and device axes. This
driver follows both at matched, independently executed stopping times:

  host  : /fp:fast against compiler-default math, same O2 optimisation level
  device: nvcc --fmad=true against --fmad=false, same host binary

Both in fp32 on Brio-Wu at N=800, where the two axes were largest, so the
series are directly comparable with the precision series at the same case,
grid, solver and CFL.
"""
from __future__ import annotations

import json
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "week21" / "implementation_temporal"
EXPERIMENT = "week21-implementation-temporal"

for path in (ROOT, ROOT / "scripts", ROOT / "scripts" / "regression"):
    sys.path.insert(0, str(path))

from io_helper import read_binary  # noqa: E402
from _mhd_harness import (  # noqa: E402
    git_commit,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)

CFG = ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg"
TIMES = tuple(round(0.01 + i * (0.09 / 14), 6) for i in range(15))
AXES = {
    "host_fastmath": {
        "device": "cpu",
        "baseline": ROOT / "build-matrix" / "cpu-float-O2-ieee-leq" / "hrsc_mhd",
        "variant": ROOT / "build-matrix" / "cpu-float-O2-fastmath-leq" / "hrsc_mhd",
        "label": "/fp:fast vs default math (fp32, CPU)",
    },
    "device_fmad": {
        "device": "gpu",
        "baseline": ROOT / "build-cuda-float" / "hrsc_mhd",
        "variant": ROOT / "build-cuda-fmad-float" / "hrsc_mhd",
        "label": "--fmad=true vs --fmad=false (fp32, GPU)",
    },
}
MEAN_RHO_BRIO = 0.5625  # domain-mean reference density, as used elsewhere
U32 = 2.0 ** -24


def run_slice(axis: str, arm: str, binary: pathlib.Path, device: str,
              t_end: float, commit: str) -> np.ndarray:
    name = f"{axis}-{arm}-t{t_end:.6f}".replace(".", "p")
    run_dir = OUT / "runs" / name
    run_dir.mkdir(parents=True, exist_ok=True)
    out_bin = run_dir / "grid.bin"
    text = CFG.read_text(encoding="utf-8")
    for key, value in (("nx", 800), ("riemann", "hll"), ("device", device),
                       ("cfl", 0.4), ("t_end", f"{t_end:.6f}"),
                       ("output_format", "binary"),
                       ("output_file", str(out_bin).replace("\\", "/"))):
        text = replace_or_append_cfg(text, key, str(value))
    resolved = resolve_binary(binary)
    run_case(name, text, run_dir, resolved, CFG, commit, sha256_file(resolved),
             output_bin=out_bin, experiment=EXPERIMENT)
    _header, data = read_binary(out_bin)
    return np.asarray(data, dtype=np.float64)[..., 0]


def fit(x: np.ndarray, log_y: np.ndarray) -> dict[str, float]:
    slope, intercept = np.polyfit(x, log_y, 1)
    resid = log_y - (intercept + slope * x)
    total = log_y - log_y.mean()
    return {
        "slope": float(slope), "intercept": float(intercept),
        "r2": float(1.0 - resid @ resid / (total @ total)) if total.any() else float("nan"),
        "rmse_log": float(np.sqrt(resid @ resid / resid.size)),
        "n_fit": int(resid.size),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    commit = git_commit()
    series = {}
    for axis, spec in AXES.items():
        rows = []
        for t_end in TIMES:
            a = run_slice(axis, "baseline", spec["baseline"], spec["device"], t_end, commit)
            b = run_slice(axis, "variant", spec["variant"], spec["device"], t_end, commit)
            d = np.abs(a - b)
            rows.append({
                "t": t_end,
                "l1_mean": float(d.mean()),
                "linf": float(d.max()),
                "l1_mean_over_u32": float(d.mean() / MEAN_RHO_BRIO / U32),
            })
            print(f"  {axis} t={t_end:.4f}: mean_L1={d.mean():.4e} Linf={d.max():.4e}")
        t = np.array([r["t"] for r in rows])
        positive = np.array([r["l1_mean"] > 0 for r in rows])
        e = np.array([r["l1_mean"] for r in rows])
        fits = {}
        if positive.sum() >= 3:
            fits["exponential"] = fit(t[positive], np.log(e[positive]))
            fits["power_law"] = fit(np.log(t[positive]), np.log(e[positive]))
        series[axis] = {"label": AXES[axis]["label"], "rows": rows, "fits": fits,
                        "n_positive": int(positive.sum())}

    figures = plot(series)
    payload = {
        "schema": {"name": "hrsc.week21-implementation-temporal", "version": 1},
        "experiment": EXPERIMENT, "git_commit": commit,
        "case": "brio_wu_1d", "nx": 800, "solver": "hll", "cfl": 0.4,
        "precision": "float", "times": list(TIMES),
        "series": series, "figures": figures,
        "claim_boundary": [
            "Each stopping time is an independently executed pair, not a checkpoint.",
            "Density only; one case, one grid, one toolchain.",
            "Differences are between two builds of the same algorithm, not errors.",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for path in (OUT / "runs").rglob("grid.bin"):
        path.unlink()
    for axis, s in series.items():
        if s["fits"]:
            print(f"{axis}: exp lam={s['fits']['exponential']['slope']:.3f} "
                  f"rms={s['fits']['exponential']['rmse_log']:.3f} | "
                  f"pow k={s['fits']['power_law']['slope']:.3f} "
                  f"rms={s['fits']['power_law']['rmse_log']:.3f}")
    print(f"\nwrote {OUT / 'summary.json'}")
    return 0


def plot(series) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6.0, 3.8), constrained_layout=True)
    colours = {"host_fastmath": "#D55E00", "device_fmad": "#7A5195"}
    for axis, s in series.items():
        t = [r["t"] for r in s["rows"]]
        e = [r["l1_mean"] for r in s["rows"]]
        k = s["fits"].get("power_law", {}).get("slope")
        label = s["label"] + (f"  ($k$={k:.2f})" if k is not None else "")
        ax.loglog(t, e, color=colours[axis], marker="o", markersize=4,
                  linewidth=1.3, label=label)
    ax.set_xlabel("Simulation time")
    ax.set_ylabel(r"Density mean $L_1$ between builds")
    ax.set_title("Implementation-axis differences in time (Brio--Wu, fp32)", loc="left",
                 fontsize=9.5)
    ax.grid(True, which="both", color="#D9DEE5", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(fontsize=8)
    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    paths = []
    for suffix in ("png", "pdf"):
        p = OUT / "figures" / f"implementation_temporal.{suffix}"
        fig.savefig(p, dpi=320)
        paths.append(str(p.relative_to(ROOT)))
    plt.close(fig)
    return paths


if __name__ == "__main__":
    raise SystemExit(main())
