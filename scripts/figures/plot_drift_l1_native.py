#!/usr/bin/env python3
"""Re-render Fig 5.10 (O2 strict-IEEE vs Ofast+fast-math L1 drift) as a
native matplotlib vector PDF, using thesis-style fonts so the figure
labels match the surrounding body text.

Data source: experiments/week7/lyapunov_1d_full/summary.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _style import apply, PALETTE, save_pair  # noqa: E402

apply()

OUT = ROOT / "report1" / "phd-thesis-template-2.4" / "Figs" / "report1"
SUMMARY = ROOT / "experiments" / "week7" / "lyapunov_1d_full" / "summary.json"

PAIR_KEY = "strict_ieee_o2_vs_ofast_fastmath"
CASES = ["sod", "toro2", "toro3", "toro4", "toro5"]
CASE_DISPLAY = {"sod": "Sod", "toro2": "Toro2", "toro3": "Toro3",
                "toro4": "Toro4", "toro5": "Toro5"}
CASE_COLORS = {
    "sod":  "#1F4E79",
    "toro2": "#2A9D8F",
    "toro3": "#E76F51",
    "toro4": "#9B2226",
    "toro5": "#F4A261",
}


def main() -> None:
    payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    pairs = payload["pairs"] if isinstance(payload, dict) else payload
    selected = [p for p in pairs if p.get("pair") == PAIR_KEY
                and p.get("case") in CASES]

    fig, (ax_rho, ax_p) = plt.subplots(1, 2, figsize=(9.0, 3.8),
                                       constrained_layout=True, sharex=True)

    for ax, var in [(ax_rho, "rho"), (ax_p, "p")]:
        for case in CASES:
            rec = next((r for r in selected if r["case"] == case
                        and r["variable"] == var), None)
            if rec is None:
                continue
            times = [float(t) for t in rec["times"]]
            l1 = [float(v) for v in rec["l1"]]
            if not times or not l1:
                continue
            t_end = max(times) or 1.0
            x = [t / t_end for t in times]
            ax.plot(x, l1, marker="o", markersize=3.4, linewidth=1.3,
                    color=CASE_COLORS[case], label=CASE_DISPLAY[case])
        ax.set_yscale("log")
        ax.set_xlabel(r"normalised time $t/t_{\mathrm{end}}$", fontsize=13)
        ax.set_title("Density" if var == "rho" else "Pressure", fontsize=15)
        ax.tick_params(labelsize=12)
        ax.grid(True, which="both", linewidth=0.4, alpha=0.35)

    ax_rho.set_ylabel(r"$L_1$ drift", fontsize=13)
    ax_p.legend(loc="lower right", fontsize=11, title="Case", title_fontsize=12,
                frameon=True, framealpha=0.85, ncol=1)
    # Title removed from the figure on purpose: it is given as the slide caption
    # below the figure (supervisor request: enlarge / move title to caption).

    save_pair(fig, "drift_timeseries_l1_native", str(OUT))
    plt.close(fig)
    print(f"wrote {OUT}/drift_timeseries_l1_native.{{pdf,png}}")


if __name__ == "__main__":
    main()
