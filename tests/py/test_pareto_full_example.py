from __future__ import annotations

import csv
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[2] / "scripts" / "figures"))

from pareto_full_example import build_rows_from_week4, main  # noqa: E402


def test_pareto_full_example_accepts_full_rows_and_writes_outputs(tmp_path: Path) -> None:
    input_csv = tmp_path / "input.csv"
    rows = [
        {
            "solver": "hllc",
            "precision_label": "p53",
            "sigma_fp_l1": "5.216e-11",
            "s_worst_q05": "1.5421710209890422",
            "s_req": "3.130448777972905",
            "regime": "precision-adequacy deficit",
        },
        {
            "solver": "hllc",
            "precision_label": "p32",
            "sigma_fp_l1": "2.100e-7",
            "s_worst_q05": "1.542170000000000",
            "s_req": "3.130448777972905",
            "regime": "precision-adequacy deficit",
        },
        {
            "solver": "hllc",
            "precision_label": "p24-real-float",
            "sigma_fp_l1": "0.029555220848920056",
            "s_worst_q05": "1.542167573490249",
            "s_req": "3.130448777972905",
            "regime": "precision-adequacy deficit",
        },
        {
            "solver": "hllc",
            "precision_label": "p16",
            "sigma_fp_l1": "0.42",
            "s_worst_q05": "1.531",
            "s_req": "3.130448777972905",
            "regime": "precision-adequacy deficit",
        },
        {
            "solver": "hllc",
            "precision_label": "p8",
            "sigma_fp_l1": "3.7",
            "s_worst_q05": "0.8",
            "s_req": "3.130448777972905",
            "regime": "precision-adequacy deficit",
        },
        {
            "solver": "rusanov",
            "precision_label": "p53",
            "sigma_fp_l1": "2.278e-11",
            "s_worst_q05": "1.230191183078682",
            "s_req": "2.952264234061909",
            "regime": "precision-adequacy deficit",
        },
    ]
    with input_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    output_dir = tmp_path / "out"

    main(["--input", str(input_csv), "--output", str(output_dir)])

    logx = output_dir / "pareto_lw3_full_logx.png"
    twopanel = output_dir / "pareto_lw3_full_twopanel.png"
    normalized = output_dir / "pareto_lw3_full.csv"
    summary = output_dir / "summary.md"

    assert logx.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert twopanel.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert summary.exists()

    with normalized.open(newline="") as f:
        written = list(csv.DictReader(f))

    assert len(written) == 6
    assert set(written[0]) == {
        "solver",
        "precision_label",
        "sigma_fp_l1",
        "s_worst_q05",
        "s_req",
        "precision_margin",
        "regime",
    }
    assert written[0]["precision_margin"] == "-1.588278"
    assert "precision-adequacy margin" in summary.read_text()
    assert "p8, p16, p24-real-float, p32, p53" in summary.read_text()


def test_week4_loader_reports_missing_requested_precision(tmp_path: Path) -> None:
    snr_csv = tmp_path / "snr.csv"
    losos_csv = tmp_path / "losos.csv"
    s_req_csv = tmp_path / "s_req.csv"

    with snr_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["solver", "precision", "variable", "sigma_fp_l1"])
        writer.writeheader()
        writer.writerow({"solver": "hllc", "precision": "p53", "variable": "rho", "sigma_fp_l1": "1e-12"})

    with losos_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["solver", "precision", "variable", "s_worst_q05"])
        writer.writeheader()
        writer.writerow({"solver": "hllc", "precision": "p53", "variable": "rho", "s_worst_q05": "3.0"})

    with s_req_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["solver", "variable", "s_req"])
        writer.writeheader()
        writer.writerow({"solver": "hllc", "variable": "rho", "s_req": "2.0"})

    try:
        build_rows_from_week4(snr_csv, losos_csv, s_req_csv, solvers=("hllc",), precisions=("p53", "p16"))
    except KeyError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected missing precision to raise KeyError")

    assert "p16" in message
    assert "missing requested Week 4 Pareto row" in message
