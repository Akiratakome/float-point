from pathlib import Path

import json

from scripts.verificarlo.precexp_aggregate import (
    classify_component,
    parse_precision_rows,
    write_outputs,
)


def test_classify_component_maps_known_symbols() -> None:
    assert classify_component("hrsc::hllc_flux<double>") == "flux"
    assert classify_component("hrsc::pressure<double>") == "eos"
    assert classify_component("hrsc::minmod<double>") == "muscl"


def test_parse_precision_rows_accepts_csv_like_output(tmp_path: Path) -> None:
    raw = tmp_path / "vfc_precexp_stdout.txt"
    raw.write_text(
        "symbol,minimum_precision_bits,status\n"
        "hrsc::hllc_flux<double>,24,accepted\n"
        "hrsc::pressure<double>,40,accepted\n",
        encoding="utf-8",
    )

    rows = parse_precision_rows(
        raw,
        case="sod",
        solver="hllc",
        reference="reference/grid.bin",
    )

    assert rows[0]["component"] == "flux"
    assert rows[0]["minimum_precision_bits"] == 24
    assert rows[1]["component"] == "eos"


def test_parse_precision_rows_marks_non_csv_output_not_reported(tmp_path: Path) -> None:
    raw = tmp_path / "vfc_precexp_stdout.txt"
    raw.write_text("vfc_precexp: no precision table emitted\n", encoding="utf-8")

    rows = parse_precision_rows(raw, case="sod", solver="hllc", reference="reference/grid.bin")

    assert rows == [
        {
            "case": "sod",
            "solver": "hllc",
            "symbol": "",
            "component": "unknown",
            "minimum_precision_bits": "",
            "status": "not_reported",
            "criterion": "density_l1_relative_and_pressure_linf_relative",
            "reference": "reference/grid.bin",
            "notes": "Could not parse vfc_precexp output; inspect logs manually",
        }
    ]


def test_write_outputs_creates_csv_json_and_summary(tmp_path: Path) -> None:
    rows = [
        {
            "case": "sod",
            "solver": "hllc",
            "symbol": "hrsc::hllc_flux<double>",
            "component": "flux",
            "minimum_precision_bits": 24,
            "status": "accepted",
            "criterion": "density_l1_relative_and_pressure_linf_relative",
            "reference": "reference/grid.bin",
            "notes": "",
        },
        {
            "case": "sod",
            "solver": "hllc",
            "symbol": "hrsc::pressure<double>",
            "component": "eos",
            "minimum_precision_bits": 40,
            "status": "accepted",
            "criterion": "density_l1_relative_and_pressure_linf_relative",
            "reference": "reference/grid.bin",
            "notes": "",
        },
    ]

    write_outputs(rows, tmp_path)

    csv_text = (tmp_path / "function_precision.csv").read_text(encoding="utf-8")
    assert "symbol,component,minimum_precision_bits" in csv_text
    assert "hrsc::hllc_flux<double>,flux,24" in csv_text

    payload = json.loads((tmp_path / "function_precision.json").read_text(encoding="utf-8"))
    assert payload[1]["component"] == "eos"

    summary = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "| flux | 1 | 24 | 24 |" in summary
    assert "| eos | 1 | 40 | 40 |" in summary
