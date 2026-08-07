#!/usr/bin/env python3
"""Circularly polarised Alfven wave convergence: order verification for the MHD path.

The discontinuous and instability-driven benchmarks used elsewhere in Report 2
admit only self-refinement rates, because no exact field is available. The
circularly polarised Alfven wave (Toth 2000; Gardiner & Stone 2005) is an exact
nonlinear solution of ideal MHD at finite amplitude: |B| and the total pressure
stay uniform, so the wave translates without changing shape.

With rho=1, Bx=1 the Alfven speed is unity, so on the unit periodic domain the
exact state at t=1 is the initial condition translated through one wavelength,
i.e. the initial condition itself. The final-minus-analytic difference is
therefore true discretisation error, and the fitted slope is a genuine observed
order of accuracy rather than a self-refinement rate.

Runs each grid on every available (precision, device) build so the CPU and GPU
paths are order-verified, not merely compared with one another.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
from scripts.regression._mhd_harness import (  # noqa: E402
    BY,
    BZ,
    ROOT,
    git_commit,
    read_binary,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)

CFG = ROOT / "tests" / "cases" / "cp_alfven_1d" / "cp_alfven.cfg"
DEFAULT_OUT = ROOT / "experiments" / "week21" / "cp_alfven_convergence"
EXPERIMENT = "week21-cp-alfven-convergence"
GRIDS = (32, 64, 128, 256, 512)
AMPLITUDE = 0.1
BINS = {
    ("double", "cpu"): ROOT / "build-double" / "hrsc_mhd.exe",
    ("float", "cpu"): ROOT / "build-float" / "hrsc_mhd.exe",
    ("double", "gpu"): ROOT / "build-cuda" / "hrsc_mhd.exe",
    ("float", "gpu"): ROOT / "build-cuda-float" / "hrsc_mhd.exe",
}
IMPLEMENTATION_SOURCES = (
    ROOT / "src" / "mhd" / "mhd_solver.cpp",
    ROOT / "src" / "mhd" / "mhd_config.hpp",
    ROOT / "src" / "mhd_main.cpp",
    pathlib.Path(__file__).resolve(),
)


def analytic_transverse(nx: int) -> tuple[np.ndarray, np.ndarray]:
    """Exact By, Bz at cell centres; equal to the state at t=0 and at t=1."""
    x = (np.arange(nx, dtype=np.float64) + 0.5) / nx
    phase = 2.0 * math.pi * x
    return AMPLITUDE * np.sin(phase), AMPLITUDE * np.cos(phase)


def measure(path: pathlib.Path) -> dict[str, float]:
    header, arr = read_binary(path)
    by = np.asarray(arr[0, :, BY], dtype=np.float64)
    bz = np.asarray(arr[0, :, BZ], dtype=np.float64)
    by_ref, bz_ref = analytic_transverse(header.nx)
    dby, dbz = by - by_ref, bz - bz_ref
    # Transverse field error magnitude, so the two components enter once.
    mag = np.hypot(dby, dbz)
    return {
        "nx": int(header.nx),
        "l1": float(np.mean(mag)),
        "l2": float(np.sqrt(np.mean(mag**2))),
        "linf": float(np.max(mag)),
        "by_l1": float(np.mean(np.abs(dby))),
        "bz_l1": float(np.mean(np.abs(dbz))),
    }


def fit_order(rows: list[dict[str, float]], key: str) -> dict[str, float]:
    usable = [r for r in rows if r[key] > 0.0]
    if len(usable) < 2:
        return {"order": float("nan"), "r2": float("nan"), "n_fit": len(usable)}
    logn = np.log2([r["nx"] for r in usable])
    loge = np.log2([r[key] for r in usable])
    slope, intercept = np.polyfit(logn, loge, 1)
    resid = loge - (intercept + slope * logn)
    total = loge - loge.mean()
    r2 = 1.0 - float(resid @ resid) / float(total @ total) if total.any() else float("nan")
    return {"order": float(-slope), "r2": r2, "n_fit": len(usable)}


def pairwise_orders(rows: list[dict[str, float]], key: str) -> list[dict[str, float]]:
    out = []
    for a, b in zip(rows, rows[1:]):
        if a[key] > 0.0 and b[key] > 0.0:
            out.append({
                "coarse": a["nx"], "fine": b["nx"],
                "order": float(math.log2(a[key] / b[key]) / math.log2(b["nx"] / a["nx"])),
            })
    return out


def run_group(precision: str, device: str, out: pathlib.Path,
              commit: str, grids: tuple[int, ...]) -> dict | None:
    try:
        binary = resolve_binary(BINS[(precision, device)])
    except (FileNotFoundError, KeyError):
        return None
    binary_sha = sha256_file(binary)
    base = CFG.read_text(encoding="utf-8")
    rows: list[dict[str, float]] = []
    for nx in grids:
        label = f"cp_alfven-{precision}-{device}-n{nx}"
        run_dir = out / "runs" / label
        out_bin = run_dir / "grid.bin"
        text = replace_or_append_cfg(base, "nx", str(nx))
        text = replace_or_append_cfg(text, "device", device)
        text = replace_or_append_cfg(text, "riemann", "hll")
        text = replace_or_append_cfg(text, "output_format", "binary")
        text = replace_or_append_cfg(text, "output_file", str(out_bin).replace("\\", "/"))
        run_case(label, text, run_dir, binary, CFG, commit, binary_sha,
                 output_bin=out_bin, experiment=EXPERIMENT)
        row = measure(out_bin)
        meta = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
        row["steps"] = meta.get("stderr_diagnostics", {}).get("steps")
        row["divB_max"] = meta.get("stderr_diagnostics", {}).get("divB_max")
        rows.append(row)
    return {
        "precision": precision,
        "device": device,
        "binary": str(binary),
        "binary_sha256": binary_sha,
        "rows": rows,
        "fit_l1": fit_order(rows, "l1"),
        "fit_linf": fit_order(rows, "linf"),
        "pairwise_l1": pairwise_orders(rows, "l1"),
    }


def plot(groups: list[dict], out: pathlib.Path) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    styles = {
        ("double", "cpu"): ("#0072B2", "o", "fp64 CPU"),
        ("double", "gpu"): ("#D55E00", "s", "fp64 GPU"),
        ("float", "cpu"): ("#009E73", "^", "fp32 CPU"),
        ("float", "gpu"): ("#7A5195", "d", "fp32 GPU"),
    }
    fig, ax = plt.subplots(figsize=(5.6, 4.0), constrained_layout=True)
    for g in groups:
        colour, marker, label = styles[(g["precision"], g["device"])]
        n = [r["nx"] for r in g["rows"]]
        e = [r["l1"] for r in g["rows"]]
        ax.loglog(n, e, color=colour, marker=marker, linewidth=1.3, markersize=4.5,
                  label=f"{label} (p={g['fit_l1']['order']:.2f})")
    ref_n = np.array(GRIDS, dtype=float)
    anchor = groups[0]["rows"][0]["l1"] if groups else 1.0
    ax.loglog(ref_n, anchor * (ref_n / ref_n[0]) ** -2.0, color="#5F6368",
              linestyle="--", linewidth=1.0, label="second order")
    ax.set_xlabel("Grid cells $N$")
    ax.set_ylabel(r"Transverse field mean $L_1$ error")
    ax.set_title("Circularly polarised Alfven wave at $t=1$", loc="left")
    ax.set_xticks(list(ref_n))
    ax.set_xticklabels([str(int(v)) for v in ref_n])
    ax.set_xticks([], minor=True)
    ax.grid(True, which="major", color="#D9DEE5", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(fontsize=8)
    paths = []
    (out / "figures").mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "pdf"):
        p = out / "figures" / f"cp_alfven_convergence.{suffix}"
        fig.savefig(p, dpi=320)
        paths.append(str(p.relative_to(ROOT)))
    plt.close(fig)
    return paths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    ap.add_argument("--grids", type=int, nargs="*", default=list(GRIDS))
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    commit = git_commit()
    grids = tuple(sorted(args.grids))

    groups = []
    skipped = []
    for precision in ("double", "float"):
        for device in ("cpu", "gpu"):
            g = run_group(precision, device, out, commit, grids)
            if g is None:
                skipped.append(f"{precision}-{device}")
            else:
                groups.append(g)
    if not groups:
        raise SystemExit("no usable builds found")

    figures = plot(groups, out)
    fp64_cpu = next((g for g in groups if g["precision"] == "double"
                     and g["device"] == "cpu"), None)
    payload = {
        "experiment": EXPERIMENT,
        "scope": "Circularly polarised Alfven wave, exact solution, order verification only",
        "git_commit": commit,
        "grids": list(grids),
        "amplitude": AMPLITUDE,
        "implementation_sources": {
            str(p.relative_to(ROOT)): sha256_file(p) for p in IMPLEMENTATION_SOURCES
        },
        "source_config": str(CFG.relative_to(ROOT)),
        "source_config_sha256": sha256_file(CFG),
        "groups": groups,
        "skipped_builds": skipped,
        "figures": figures,
        "gate": {
            "all_groups_complete": all(
                len(g["rows"]) == len(grids) for g in groups),
            "fp64_cpu_order_in_band": bool(
                fp64_cpu is not None
                and 1.5 <= fp64_cpu["fit_l1"]["order"] <= 2.5),
        },
        "claim_boundary": [
            "Order verification for a smooth exact solution only.",
            "No claim transfers to the discontinuous or instability-driven cases.",
            "fp32 groups saturate at the rounding floor and are not order estimates there.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for g in groups:
        print(f"{g['precision']:6s} {g['device']:3s} "
              f"order(L1)={g['fit_l1']['order']:.3f} R2={g['fit_l1']['r2']:.4f}  "
              + "  ".join(f"N{r['nx']}={r['l1']:.3e}" for r in g["rows"]))
    if skipped:
        print("skipped (build absent):", ", ".join(skipped))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
