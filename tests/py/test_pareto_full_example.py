from __future__ import annotations

import csv
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parents[2] / "scripts" / "figures"))

from pareto_full_example import main  # noqa: E402


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
            "precision_label": "p24-real-float",
            "sigma_fp_l1": "0.029555220848920056",
            "s_worst_q05": "1.542167573490249",
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

    assert len(written) == 3
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
