#!/usr/bin/env python3
"""Resolution ladder for the Lecoanet KH linear growth rate.

mhd_lecoanet_kh_reproduction.py measures the k=2*pi mode growth rate on one
grid. A single grid cannot distinguish an under-resolved shear layer from an
incorrect implementation: both show a growth rate below the published linear
value. This driver repeats the measurement over a refinement ladder so the
deficit can be attributed, or not, to resolution.

The per-grid acceptance gate of the underlying packet is deliberately not
enforced here. A coarse grid is expected to fail it, and that failure is the
measurement.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
DRIVER = ROOT / "scripts" / "regression" / "mhd_lecoanet_kh_reproduction.py"
DEFAULT_OUT = ROOT / "experiments" / "week21" / "lecoanet_kh_resolution_ladder"
EXPERIMENT = "week21-lecoanet-kh-growth-ladder"
GRIDS = (64, 128, 256, 512)
PUBLISHED_RATE = 3.227  # Berlok & Pfrommer (2019), smooth-IC linear theory


def run_rung(nx: int, out: pathlib.Path) -> dict:
    rung_dir = out / f"nx{nx}"
    summary = rung_dir / "summary.json"
    proc = subprocess.run(
        [sys.executable, str(DRIVER), "--nx", str(nx), "--out", str(rung_dir)],
        cwd=str(ROOT), capture_output=True, text=True)
    if not summary.exists():
        raise RuntimeError(f"nx={nx} produced no summary\n{proc.stderr[-2000:]}")
    payload = json.loads(summary.read_text(encoding="utf-8"))
    return {
        "nx": payload["grid"]["nx"],
        "ny": payload["grid"]["ny"],
        "growth_rate": payload["growth_rate"],
        "fit_r2": payload["fit_r2"],
        "relative_deficit": (PUBLISHED_RATE - payload["growth_rate"]) / PUBLISHED_RATE,
        "packet_gate_pass": payload["gate"]["pass"],
        "cells_across_layer": payload["grid"]["ny"] * 0.2 / 2.0,
        "summary": str(summary.relative_to(ROOT)),
    }


def plot(rows: list[dict], out: pathlib.Path) -> list[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5.6, 3.8), constrained_layout=True)
    n = [r["nx"] for r in rows]
    g = [r["growth_rate"] for r in rows]
    ax.semilogx(n, g, color="#0072B2", marker="o", linewidth=1.4, markersize=5,
                label="measured", zorder=3)
    ax.axhline(PUBLISHED_RATE, color="#B00020", linestyle="--", linewidth=1.1,
               label=f"linear theory ({PUBLISHED_RATE:g})", zorder=2)
    for r in rows:
        ax.annotate(f"{r['growth_rate']:.2f}", xy=(r["nx"], r["growth_rate"]),
                    xytext=(0, -13), textcoords="offset points",
                    ha="center", fontsize=8, color="#0072B2")
    ax.set_xlabel(r"Transverse resolution $N_x$ (grid is $N_x\times 2N_x$)")
    ax.set_ylabel(r"Fitted growth rate of the $k=2\pi$ mode")
    ax.set_xticks(n)
    ax.set_xticklabels([str(v) for v in n])
    ax.set_xticks([], minor=True)
    ax.set_ylim(0.0, 1.15 * PUBLISHED_RATE)
    ax.grid(True, which="major", color="#D9DEE5", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(fontsize=8, loc="lower right")
    paths = []
    (out / "figures").mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "pdf"):
        p = out / "figures" / f"lecoanet_kh_growth_ladder.{suffix}"
        fig.savefig(p, dpi=320)
        paths.append(str(p.relative_to(ROOT)))
    plt.close(fig)
    return paths


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=pathlib.Path, default=DEFAULT_OUT)
    ap.add_argument("--grids", type=int, nargs="*", default=list(GRIDS))
    args = ap.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    rows = [run_rung(nx, out) for nx in sorted(args.grids)]
    figures = plot(rows, out)
    payload = {
        "experiment": EXPERIMENT,
        "scope": ("Linear-stage growth rate of the k=2pi mode on the Lecoanet "
                  "smooth unstratified initial condition with B=0, so the solver "
                  "runs in its inviscid hydrodynamic limit."),
        "published_rate": PUBLISHED_RATE,
        "published_rate_source": "Berlok & Pfrommer (2019), 10.1093/mnras/stz379",
        "rows": rows,
        "monotone_towards_published": all(
            b["growth_rate"] > a["growth_rate"] for a, b in zip(rows, rows[1:])),
        "figures": figures,
        "claim_boundary": [
            "Inviscid hydrodynamic limit only; no magnetic field and no explicit viscosity.",
            "Bounds the solver's linear-stage behaviour, not the magnetised KH case.",
            "The published value is a comparison target, not an acceptance threshold.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    for r in rows:
        print(f"nx={r['nx']:4d} ({r['nx']}x{r['ny']})  rate={r['growth_rate']:.4f}  "
              f"R2={r['fit_r2']:.4f}  deficit={r['relative_deficit']:+.1%}  "
              f"gate={r['packet_gate_pass']}")
    print(f"monotone towards {PUBLISHED_RATE}: {payload['monotone_towards_published']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
