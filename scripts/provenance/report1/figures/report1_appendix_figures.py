"""Generate Report 1 appendix-only figures from existing evidence artifacts."""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.io_helper import read_binary  # noqa: E402


OUT = ROOT / "report1" / "phd-thesis-template-2.4" / "Figs" / "report1"


def save(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def density(path: Path) -> tuple[object, np.ndarray]:
    header, arr = read_binary(path)
    return header, arr[..., 0].astype(np.float64)


def plot_fp32_fp64_panel() -> None:
    runs = ROOT / "experiments" / "report1_fp32_fp64_time_drift" / "runs"
    cases = [
        ("Sod", "sod-cpu-double", "sod-cpu-float"),
        ("Toro3", "toro3-cpu-double", "toro3-cpu-float"),
        ("Toro5", "toro5-cpu-double", "toro5-cpu-float"),
        ("LW3", "lw3-n200-cpu-double", "lw3-n200-cpu-float"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(8.6, 5.8), constrained_layout=True)
    axes = axes.ravel()
    vmax_2d = None

    for ax, (title, dname, fname) in zip(axes, cases):
        h_d, rho_d = density(runs / dname / "grid.bin")
        _, rho_f = density(runs / fname / "grid.bin")
        diff = rho_f - rho_d

        if h_d.ny == 1:
            x = np.linspace(0.0, 1.0, h_d.nx, endpoint=False) + 0.5 / h_d.nx
            ax.plot(x, diff[0], lw=1.1, color="#235789")
            ax.axhline(0.0, lw=0.6, color="0.35")
            ax.set_xlabel("x")
            ax.set_ylabel("rho(fp32) - rho(fp64)")
            ax.ticklabel_format(axis="y", style="sci", scilimits=(-2, 2))
        else:
            vmax_2d = float(np.nanmax(np.abs(diff))) if vmax_2d is None else vmax_2d
            im = ax.imshow(
                diff,
                origin="lower",
                cmap="coolwarm",
                vmin=-vmax_2d,
                vmax=vmax_2d,
                interpolation="nearest",
            )
            fig.colorbar(im, ax=ax, shrink=0.82, label="rho(fp32) - rho(fp64)")
            ax.set_xlabel("i")
            ax.set_ylabel("j")
        ax.set_title(title)

    save(fig, "appendix_fp32_fp64_density_differences")


def read_trace(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def plot_toro2_branch_trace() -> None:
    base = ROOT / "experiments" / "report1_toro2_branch_trace" / "runs"
    leq = read_trace(base / "toro2_hllc_leq_trace" / "hllc_trace.csv")
    lt = read_trace(base / "toro2_hllc_lt_trace" / "hllc_trace.csv")

    def first_window(rows: list[dict[str, str]]) -> list[dict[str, str]]:
        return [
            r
            for r in rows
            if r["step"] == "0"
            and r["sweep"] == "x"
            and r["line"] == "0"
            and 95 <= int(r["face"]) <= 101
        ]

    leq_w = first_window(leq)
    lt_w = first_window(lt)
    faces = np.array([int(r["face"]) for r in leq_w])
    sstar = np.array(
        [
            [float(r["Sstar"]) for r in leq_w],
            [float(r["Sstar"]) for r in lt_w],
        ]
    )
    flux = np.array(
        [
            [float(r["flux_rho"]) for r in leq_w],
            [float(r["flux_rho"]) for r in lt_w],
        ]
    )
    branches = [[r["branch"] for r in leq_w], [r["branch"] for r in lt_w]]

    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(8.2, 4.8), constrained_layout=True)
    vmax = max(2.0, float(np.max(np.abs(sstar))))
    im = ax0.imshow(sstar, cmap="coolwarm", vmin=-vmax, vmax=vmax, aspect="auto")
    ax0.set_yticks([0, 1], labels=["<=", "<"])
    ax0.set_xticks(range(len(faces)), labels=faces)
    ax0.set_ylabel("branch rule")
    ax0.set_title("Toro2 first-step S* near centre interface")
    for i in range(2):
        for j in range(len(faces)):
            ax0.text(j, i, branches[i][j], ha="center", va="center", fontsize=7)
    fig.colorbar(im, ax=ax0, label="S*")

    width = 0.34
    x = np.arange(len(faces))
    ax1.bar(x - width / 2, flux[0], width, label="<=", color="#1f77b4")
    ax1.bar(x + width / 2, flux[1], width, label="<", color="#d62728")
    ax1.axhline(0.0, color="0.35", lw=0.7)
    ax1.set_xticks(x, labels=faces)
    ax1.set_xlabel("x-face index")
    ax1.set_ylabel("mass flux")
    ax1.legend(frameon=False, ncol=2)

    save(fig, "appendix_toro2_branch_trace")


def plot_runtime_bars() -> None:
    path = ROOT / "experiments" / "report1_runtime_minimatrix" / "timing_summary.csv"
    rows = []
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            if row["device"] in {"cpu", "gpu"}:
                rows.append(row)

    labels = [f"{r['case'].replace('_', ' ')}\n{r['precision']} {r['device']}" for r in rows]
    med = np.array([float(r["median_s"]) for r in rows])
    low = np.array([float(r["median_s"]) - float(r["min_s"]) for r in rows])
    high = np.array([float(r["max_s"]) - float(r["median_s"]) for r in rows])
    colors = ["#4c78a8" if r["device"] == "cpu" else "#f58518" for r in rows]

    fig, ax = plt.subplots(figsize=(9.0, 4.6), constrained_layout=True)
    x = np.arange(len(rows))
    ax.bar(x, med, color=colors, width=0.72)
    ax.errorbar(x, med, yerr=np.vstack([low, high]), fmt="none", ecolor="0.25", lw=0.8, capsize=2)
    ax.set_yscale("log")
    ax.set_ylabel("median runtime (s), log scale")
    ax.set_xticks(x, labels=labels, rotation=35, ha="right")
    ax.set_title("Strict-HLLC runtime mini-matrix")
    for device, color in [("CPU", "#4c78a8"), ("GPU", "#f58518")]:
        ax.bar([], [], color=color, label=device)
    ax.legend(frameon=False, ncol=2)

    save(fig, "appendix_runtime_minimatrix")


def plot_lw3_self_convergence() -> None:
    variables = ["rho", "u", "v", "p"]
    e400 = np.array([3.304289e-03, 4.718107e-03, 4.741893e-03, 3.349341e-03])
    e800 = np.array([2.392109e-03, 3.469584e-03, 3.430563e-03, 2.368599e-03])
    p_obs = np.log2(e400 / e800)

    fig, ax = plt.subplots(figsize=(7.8, 4.4), constrained_layout=True)
    x = np.array([400, 800])
    for var, y0, y1, p in zip(variables, e400, e800, p_obs):
        ax.plot(x, [y0, y1], marker="o", lw=1.5, label=f"{var}, p={p:.2f}")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(x, labels=["400 vs 800", "800 vs 1600"])
    ax.set_ylabel("L1 difference")
    ax.set_title("LW3 fp64 self-convergence against finer grids")
    ax.legend(frameon=False, ncol=2)
    ax.grid(True, which="both", lw=0.4, alpha=0.35)

    save(fig, "appendix_lw3_self_convergence")


def plot_vfc_toro_diagnostics() -> None:
    src = ROOT / "experiments" / "verificarlo" / "results"
    case = "toro3"
    panels = [
        ("overlay", "Overlay"),
        ("heatmap", "Heatmap"),
        ("noise_ratio", "Noise ratio"),
        ("error_budget", "Error budget"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(9.0, 7.0), constrained_layout=True)
    for ax, (suffix, title) in zip(axes.ravel(), panels):
        img = mpimg.imread(src / f"vfc_{case}_{suffix}.png")
        ax.imshow(img)
        ax.set_title(title, loc="left", fontsize=10)
        ax.axis("off")

    save(fig, "appendix_vfc_toro3_diagnostics")


def main() -> None:
    plot_fp32_fp64_panel()
    plot_toro2_branch_trace()
    plot_runtime_bars()
    plot_lw3_self_convergence()
    plot_vfc_toro_diagnostics()


if __name__ == "__main__":
    main()
