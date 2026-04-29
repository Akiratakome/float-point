from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_build_all_matrix_names_are_stable() -> None:
    from scripts import build_matrix

    variants = build_matrix.generate_variants(
        precisions=("double", "float"),
        opt_levels=("O2", "Ofast"),
        fast_math_values=(False, True),
        strict_values=(False, True),
    )

    names = [v.name for v in variants]
    assert names == [
        "cpu-double-O2-ieee-leq",
        "cpu-double-O2-ieee-strict",
        "cpu-double-O2-fastmath-leq",
        "cpu-double-O2-fastmath-strict",
        "cpu-double-Ofast-ieee-leq",
        "cpu-double-Ofast-ieee-strict",
        "cpu-double-Ofast-fastmath-leq",
        "cpu-double-Ofast-fastmath-strict",
        "cpu-float-O2-ieee-leq",
        "cpu-float-O2-ieee-strict",
        "cpu-float-O2-fastmath-leq",
        "cpu-float-O2-fastmath-strict",
        "cpu-float-Ofast-ieee-leq",
        "cpu-float-Ofast-ieee-strict",
        "cpu-float-Ofast-fastmath-leq",
        "cpu-float-Ofast-fastmath-strict",
    ]


def test_build_all_variant_cmake_args_encode_fp_axes() -> None:
    from scripts import build_matrix

    variant = build_matrix.BuildVariant(
        precision="float",
        opt_level="O3",
        fast_math=True,
        strict_riemann=True,
    )

    args = variant.cmake_args()
    assert "-DFLOAT_PRECISION=float" in args
    assert "-DOPT_LEVEL=O3" in args
    assert "-DFAST_MATH=ON" in args
    assert "-DRIEMANN_STRICT_INEQUALITY=ON" in args


def test_run_matrix_writes_metadata_and_preserves_cfg(tmp_path: Path) -> None:
    from scripts import run_matrix

    cfg = tmp_path / "case.cfg"
    cfg.write_text(
        "test = sod\n"
        "nx = 4\n"
        "output_format = binary\n"
        "output_file = old/path.bin\n",
        encoding="utf-8",
    )
    matrix = {
        "experiment": "pytest",
        "runs": [
            {
                "name": "sod-double",
                "binary": "build-double/hrsc",
                "config": str(cfg),
                "precision": "double",
                "build": "cpu-double-O2-ieee-leq",
                "output_file": "grid.bin",
            }
        ],
    }

    run = run_matrix.normalise_run(matrix["runs"][0], output_root=tmp_path / "out")
    generated_cfg = run_matrix.materialise_run_config(run)

    assert cfg.read_text(encoding="utf-8").endswith("output_file = old/path.bin\n")
    assert "output_file = " + str(run.raw_output) in generated_cfg.read_text(encoding="utf-8")

    metadata = run_matrix.build_metadata(
        run,
        experiment=matrix["experiment"],
        command=["build-double/hrsc", str(generated_cfg)],
        git_commit="abc123",
        returncode=0,
    )
    assert metadata["experiment"] == "pytest"
    assert metadata["name"] == "sod-double"
    assert metadata["precision"] == "double"
    assert metadata["raw_output"] == str(run.raw_output)
    assert metadata["git_commit"] == "abc123"


def test_aggregate_metrics_combines_summary_jsons(tmp_path: Path) -> None:
    from scripts import aggregate_metrics

    first = tmp_path / "a" / "summary.json"
    second = tmp_path / "b" / "summary.json"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_text(json.dumps({"mode": "1d", "tests": {"sod": {"N_last": 800}}}), encoding="utf-8")
    second.write_text(json.dumps({"mode": "2d", "cases": {"double_200": {}}}), encoding="utf-8")

    output = tmp_path / "summary.json"
    aggregate_metrics.aggregate([first, second], output)

    combined = json.loads(output.read_text(encoding="utf-8"))
    assert combined["summary_count"] == 2
    assert combined["summaries"][0]["source"] == str(first)
    assert combined["summaries"][1]["payload"]["mode"] == "2d"


def test_missing_run_matrix_fields_raise_clear_error(tmp_path: Path) -> None:
    from scripts import run_matrix

    with pytest.raises(ValueError, match="missing required field 'config'"):
        run_matrix.normalise_run(
            {"name": "bad", "binary": "build-double/hrsc"},
            output_root=tmp_path,
        )
