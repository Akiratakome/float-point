from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image, ImageDraw


PRECISION_ORDER = {
    "p8": 8,
    "p16": 16,
    "p24-real-float": 24,
    "p32": 32,
    "p53": 53,
}
EXPLORATORY_PRECISIONS = {"p8", "p16", "p32"}


def _read_metric_rows(metric_root: Path, filename: str) -> pd.DataFrame:
    frames = []
    for csv_path in sorted(metric_root.glob(f"p*/{filename}")):
        df = pd.read_csv(csv_path)
        frames.append(df[df["variable"] == "rho"].copy())
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_summary(metric_root: Path, pareto_csv: Path) -> pd.DataFrame:
    losos = _read_metric_rows(metric_root, "losos_scalars.csv")
    snr = _read_metric_rows(metric_root, "snr_scalars.csv")
    pareto = pd.read_csv(pareto_csv).rename(columns={"precision_label": "precision"})

    if losos.empty:
        losos = pd.DataFrame(
            columns=[
                "solver",
                "precision",
                "variable",
                "s_reliability_q05",
                "s_accuracy_q05",
                "n_samples",
            ]
        )
    if snr.empty:
        snr = pd.DataFrame(columns=["solver", "precision", "variable", "sigma_fp_l1"])

    merged = pareto.merge(
        losos[
            [
                "solver",
                "precision",
                "variable",
                "s_reliability_q05",
                "s_accuracy_q05",
                "n_samples",
            ]
        ],
        on=["solver", "precision"],
        how="left",
    )
    snr_cols = snr[["solver", "precision", "sigma_fp_l1"]].rename(
        columns={"sigma_fp_l1": "sigma_fp_l1_snr"}
    )
    merged = merged.merge(snr_cols, on=["solver", "precision"], how="left")
    merged["sigma_fp_l1"] = merged["sigma_fp_l1"].combine_first(
        merged["sigma_fp_l1_snr"]
    )
    merged = merged.drop(columns=["sigma_fp_l1_snr"])
    merged["variable"] = merged["variable"].fillna("rho")
    merged.loc[
        merged["precision"].isin(["p24-real-float", "p53"]) & merged["n_samples"].isna(),
        "n_samples",
    ] = 30
    merged["precision_order"] = merged["precision"].map(PRECISION_ORDER)
    merged["sample_status"] = merged["precision"].apply(
        lambda p: "exploratory" if p in EXPLORATORY_PRECISIONS else "production"
    )
    merged = merged.sort_values(["solver", "precision_order"]).reset_index(drop=True)
    return merged


def count_precision_samples(sweep_root: Path) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for grid in sweep_root.glob("*/*/*/grid.bin"):
        precision = grid.parts[-4]
        solver = grid.parts[-3]
        counts.setdefault(precision, {})
        counts[precision][solver] = counts[precision].get(solver, 0) + 1
    return counts


def _analysed_count(counts: dict[str, dict[str, int]], precision: str) -> int:
    solver_counts = counts.get(precision, {})
    if not solver_counts:
        return 0
    return min(solver_counts.get("hllc", 0), solver_counts.get("rusanov", 0))


def write_audit(counts: dict[str, dict[str, int]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for precision in ["p8", "p16", "p32"]:
        analysed = _analysed_count(counts, precision)
        rows.append(
            {
                "precision": precision,
                "hllc_samples": analysed,
                "rusanov_samples": analysed,
                "status": "exploratory; common subset"
                if precision == "p8"
                else "exploratory",
            }
        )
    rows.extend(
        [
            {
                "precision": "p24-real-float",
                "hllc_samples": 30,
                "rusanov_samples": 30,
                "status": "Week 4/Athena metric source",
            },
            {
                "precision": "p53",
                "hllc_samples": 30,
                "rusanov_samples": 30,
                "status": "Week 4/Athena metric source",
            },
        ]
    )
    (out_dir / "audit.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    lines = [
        "# Verificarlo Report 1 Refresh Audit",
        "",
        "| precision | HLLC samples | Rusanov samples | status |",
        "|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['precision']} | {row['hllc_samples']} | "
            f"{row['rusanov_samples']} | {row['status']} |"
        )
    lines.extend(
        [
            "",
            "The refreshed Report 1 figures annotate sample counts. "
            "Do not present p8/p16/p32 as 30-sample production statistics.",
            "",
            "For p8, the raw checkout has an extra Rusanov grid, but the analysed "
            "common subset used by the metrics and figures is n=2 per solver.",
        ]
    )
    (out_dir / "audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(summary: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_dir / "summary.csv", index=False)
    (out_dir / "summary.json").write_text(
        json.dumps(summary.to_dict(orient="records"), indent=2),
        encoding="utf-8",
    )
    write_summary_md(summary, out_dir / "summary.md")


def write_summary_md(summary: pd.DataFrame, out_path: Path) -> None:
    lines = [
        "# Verificarlo Report 1 Refresh Summary",
        "",
        "Purpose: normalized Report 1 precision-sweep table after the 1600^2 reference refresh.",
        "",
        "| solver | precision | samples | sigma_fp_l1 | s_worst_q05 | s_req | precision_margin | regime |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in summary.to_dict(orient="records"):
        samples = "" if pd.isna(row.get("n_samples")) else int(row["n_samples"])
        lines.append(
            f"| {row['solver']} | {row['precision']} | {samples} | "
            f"{row['sigma_fp_l1']:.6g} | {row['s_worst_q05']:.6g} | "
            f"{row['s_req']:.6g} | {row['precision_margin']:.6g} | "
            f"{row['regime']} |"
        )
    lines.extend(
        [
            "",
            "p8/p16/p32 rows are exploratory virtual-precision rows with small sample counts.",
            "Use `precision_margin = s_worst_q05 - s_req` as the precision-adequacy wording.",
        ]
    )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _x_positions(group: pd.DataFrame) -> list[int]:
    return list(range(len(group)))


def _annotate_samples(ax, group: pd.DataFrame, x_values: list[int]) -> None:
    y_values = group["s_worst_q05"].tolist()
    for _, row in group.iterrows():
        if not pd.isna(row.get("n_samples")):
            idx = group.index.get_loc(row.name)
            ax.annotate(
                f"n={int(row['n_samples'])}",
                (x_values[idx], y_values[idx]),
                textcoords="offset points",
                xytext=(0, 7),
                ha="center",
                fontsize=7,
            )


def plot_precision_sweep(summary: pd.DataFrame, out_path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for solver, group in summary.groupby("solver"):
        group = group.sort_values("precision_order")
        x_values = _x_positions(group)
        axes[0].plot(x_values, group["s_worst_q05"], marker="o", label=solver)
        axes[1].plot(
            x_values, group["precision_margin"], marker="o", label=solver
        )
        for ax in axes:
            ax.set_xticks(x_values, group["precision"].tolist())
        _annotate_samples(axes[0], group, x_values)
    axes[0].set_ylabel("s_worst_q05 (rho)")
    axes[1].set_ylabel("s_worst_q05 - s_req")
    axes[1].axhline(0.0, color="black", linewidth=0.8, alpha=0.55)
    for ax in axes:
        ax.set_xlabel("precision")
        ax.grid(True, alpha=0.3)
        ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def plot_sigma_fp(summary: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.8))
    for solver, group in summary.groupby("solver"):
        group = group.sort_values("precision_order")
        x_values = _x_positions(group)
        ax.plot(x_values, group["sigma_fp_l1"], marker="o", label=solver)
        ax.set_xticks(x_values, group["precision"].tolist())
    ax.set_yscale("log")
    ax.set_xlabel("precision")
    ax.set_ylabel("sigma_fp_l1 (rho)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def plot_accuracy_noise_tradeoff(summary: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    for solver, group in summary.groupby("solver"):
        ax.scatter(group["sigma_fp_l1"], group["s_worst_q05"], label=solver)
        for _, row in group.iterrows():
            suffix = "" if pd.isna(row.get("n_samples")) else f" n={int(row['n_samples'])}"
            ax.annotate(
                f"{row['precision']}{suffix}",
                (row["sigma_fp_l1"], row["s_worst_q05"]),
                textcoords="offset points",
                xytext=(5, 4),
                fontsize=7,
            )
    ax.set_xscale("log")
    ax.set_xlabel("sigma_fp_l1 (rho)")
    ax.set_ylabel("s_worst_q05 (rho)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def _heatmap_sample_label(precision: str) -> str:
    if precision == "p8":
        return "exploratory; analysed common subset n=2 per solver"
    if precision in {"p16", "p32"}:
        return "exploratory; n=3 per solver"
    return "sample count recorded in summary.csv"


def _copy_with_banner(src: Path, dst: Path, precision: str) -> None:
    image = Image.open(src).convert("RGB")
    banner_height = 56
    canvas = Image.new("RGB", (image.width, image.height + banner_height), "white")
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (16, 12),
        f"{precision} source heatmap ({_heatmap_sample_label(precision)})",
        fill="black",
    )
    draw.text(
        (16, 32),
        "Copied from Week 7 metric output; s_accuracy=16 is a display cap, not proof of 16 true digits.",
        fill="black",
    )
    canvas.paste(image, (0, banner_height))
    canvas.save(dst)


def copy_source_heatmaps(metric_root: Path, out_dir: Path) -> None:
    heatmap_dir = out_dir / "figures" / "source_heatmaps"
    heatmap_dir.mkdir(parents=True, exist_ok=True)
    for precision in ["p8", "p16", "p32"]:
        for name in [
            "losos_accuracy_heatmap.png",
            "losos_reliability_heatmap.png",
            "losos_worst_heatmap.png",
            "sigma_fp_heatmap.png",
        ]:
            src = metric_root / precision / name
            if src.exists():
                dst = heatmap_dir / f"{precision}_{name}"
                _copy_with_banner(src, dst, precision)


def copy_pareto_figure(src: Path, out_dir: Path) -> None:
    if src.exists():
        fig_dir = out_dir / "figures"
        fig_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, fig_dir / "pareto_precision_adequacy_twopanel.png")


def write_sample_count_table(summary: pd.DataFrame, out_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.8, 2.8))
    ax.axis("off")
    table_df = summary[["solver", "precision", "n_samples", "sample_status"]].copy()
    table_df["n_samples"] = table_df["n_samples"].fillna("").astype(str)
    table = ax.table(
        cellText=table_df.values,
        colLabels=["solver", "precision", "samples", "status"],
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1, 1.25)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=160)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--metric-root", type=Path, default=Path("experiments/week7/metrics")
    )
    parser.add_argument(
        "--pareto-csv",
        type=Path,
        default=Path("experiments/week7/pareto_full/pareto_lw3_full.csv"),
    )
    parser.add_argument(
        "--sweep-root",
        type=Path,
        default=Path("experiments/week7/2d_vfc_precision_sweep"),
    )
    parser.add_argument(
        "--pareto-figure",
        type=Path,
        default=Path("experiments/week7/pareto_full/pareto_lw3_full_twopanel.png"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("experiments/week7/verificarlo_report1_refresh"),
    )
    args = parser.parse_args()

    summary = build_summary(args.metric_root, args.pareto_csv)
    write_outputs(summary, args.out_dir)
    write_audit(count_precision_samples(args.sweep_root), args.out_dir)

    fig_dir = args.out_dir / "figures"
    plot_precision_sweep(summary, fig_dir / "precision_sweep_losos_rho.png")
    plot_sigma_fp(summary, fig_dir / "precision_sweep_sigma_fp_rho.png")
    plot_accuracy_noise_tradeoff(
        summary, fig_dir / "hllc_rusanov_accuracy_noise_tradeoff.png"
    )
    write_sample_count_table(summary, fig_dir / "sample_count_badge_table.png")
    copy_source_heatmaps(args.metric_root, args.out_dir)
    copy_pareto_figure(args.pareto_figure, args.out_dir)


if __name__ == "__main__":
    main()
