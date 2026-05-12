from pathlib import Path

import pandas as pd
from PIL import Image

from scripts.figures.verificarlo_report1_refresh import (
    build_summary,
    plot_precision_sweep,
)


def test_build_summary_keeps_sample_counts_and_margins(tmp_path: Path) -> None:
    metric_root = tmp_path / "metrics"
    pareto = tmp_path / "pareto.csv"
    metric_root.mkdir()
    for precision, samples in [("p8", 2), ("p16", 3)]:
        d = metric_root / precision
        d.mkdir()
        pd.DataFrame(
            [
                {
                    "solver": "hllc",
                    "precision": precision,
                    "variable": "rho",
                    "s_worst_q05": 1.0,
                    "s_accuracy_q05": 1.1,
                    "s_reliability_q05": 1.2,
                    "n_samples": samples,
                }
            ]
        ).to_csv(d / "losos_scalars.csv", index=False)
        pd.DataFrame(
            [
                {
                    "solver": "hllc",
                    "precision": precision,
                    "variable": "rho",
                    "sigma_fp_l1": 10.0,
                    "n_samples": samples,
                }
            ]
        ).to_csv(d / "snr_scalars.csv", index=False)
    pd.DataFrame(
        [
            {
                "solver": "hllc",
                "precision_label": "p8",
                "sigma_fp_l1": 10.0,
                "s_worst_q05": 1.0,
                "s_req": 3.0,
                "precision_margin": -2.0,
                "regime": "precision-adequacy deficit",
            }
        ]
    ).to_csv(pareto, index=False)

    out = build_summary(metric_root, pareto)
    row = out[(out["solver"] == "hllc") & (out["precision"] == "p8")].iloc[0]
    assert row["n_samples"] == 2
    assert row["precision_margin"] == -2.0


def test_plot_precision_sweep_writes_png(tmp_path: Path) -> None:
    df = pd.DataFrame(
        [
            {
                "solver": "hllc",
                "precision": "p8",
                "precision_order": 8,
                "sigma_fp_l1": 10.0,
                "s_worst_q05": 1.0,
                "s_req": 3.0,
                "precision_margin": -2.0,
                "n_samples": 2,
            },
            {
                "solver": "hllc",
                "precision": "p16",
                "precision_order": 16,
                "sigma_fp_l1": 1.0,
                "s_worst_q05": 1.5,
                "s_req": 3.0,
                "precision_margin": -1.5,
                "n_samples": 3,
            },
        ]
    )
    out = tmp_path / "fig.png"
    plot_precision_sweep(df, out)
    im = Image.open(out)
    assert im.size[0] > 200
    assert im.size[1] > 150
