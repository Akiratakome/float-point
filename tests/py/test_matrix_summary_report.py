from __future__ import annotations

import csv
import os
import json
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_binary(path: Path, cons: np.ndarray, dx: float, dy: float, t: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ny, nx, nvars = cons.shape
    header = struct.pack(
        "<4siiiiddd20s",
        b"HRSC",
        nx,
        ny,
        nvars,
        cons.dtype.itemsize,
        t,
        dx,
        dy,
        b"\x00" * 20,
    )
    assert len(header) == 64
    with open(path, "wb") as f:
        f.write(header)
        f.write(cons.tobytes(order="C"))


def _write_run(
    root: Path,
    name: str,
    precision: str,
    build: str,
    payload: np.ndarray,
    total_s: float,
    *,
    dx: float = 0.25,
    dy: float = 1.0,
    t: float = 0.2,
    raw_output_text: str | None = None,
) -> dict[str, object]:
    run_dir = root / "runs" / name
    raw_output = run_dir / "grid.bin"
    raw_output_meta = str(raw_output) if raw_output_text is None else raw_output_text
    metadata = {
        "experiment": "synthetic",
        "name": name,
        "precision": precision,
        "build": build,
        "source_config": "tests/cases/toro_1d/sod.cfg",
        "run_config": str(run_dir / "config.cfg"),
        "raw_output": raw_output_meta,
        "timing": {"total_s": total_s},
        "returncode": 0,
    }
    _write_binary(raw_output, payload, dx=dx, dy=dy, t=t)
    (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return metadata


def _synthetic_matrix(tmp_path: Path) -> Path:
    root = tmp_path / "matrix"
    nx = 32
    base = np.zeros((1, nx, 4), dtype=np.float64)
    x = np.arange(nx, dtype=np.float64)
    base[..., 0] = 1.0 + 0.01 * x
    base[..., 1] = 0.5
    base[..., 2] = 0.0
    base[..., 3] = 2.5
    perturbed = base.copy()
    perturbed[..., 0] += 0.25
    perturbed[..., 3] -= 0.125

    run_a = _write_run(
        root,
        "sod-cpu-double-o2-ieee-leq",
        "double",
        "cpu-double-o2-ieee-leq",
        base,
        total_s=1.25,
    )
    run_b = _write_run(
        root,
        "sod-cpu-float-o2-ieee-leq",
        "float",
        "cpu-float-o2-ieee-leq",
        perturbed.astype(np.float32),
        total_s=2.5,
    )
    matrix_summary = {
        "experiment": "synthetic",
        "output_root": str(root),
        "run_count": 2,
        "runs": [run_a, run_b],
    }
    path = root / "matrix_summary.json"
    path.write_text(json.dumps(matrix_summary, indent=2) + "\n", encoding="utf-8")
    return path


def _run_report(matrix_summary: Path, *extra_args: str, cwd: Path = REPO_ROOT) -> dict[str, object]:
    subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "regression" / "matrix_summary_report.py"),
            str(matrix_summary),
            *extra_args,
        ],
        check=True,
        cwd=cwd,
    )
    resolved_matrix = matrix_summary if matrix_summary.is_absolute() else (cwd / matrix_summary).resolve()
    prefix = Path(extra_args[extra_args.index("--out") + 1]) if "--out" in extra_args else resolved_matrix.parent / "summary"
    return json.loads(prefix.with_suffix(".json").read_text(encoding="utf-8"))


def test_cli_reports_implicit_precision_pairs_and_scalars(tmp_path: Path) -> None:
    matrix_summary = _synthetic_matrix(tmp_path)

    summary = _run_report(matrix_summary, "--pair-by", "precision")

    for suffix in (".csv", ".json", ".md"):
        assert (matrix_summary.parent / f"summary{suffix}").is_file()
    assert summary["run_count"] == 2
    assert summary["pair_count"] == 1

    runs = {row["name"]: row for row in summary["runs"]}
    run_a = runs["sod-cpu-double-o2-ieee-leq"]
    assert run_a["nx"] == 32
    assert run_a["ny"] == 1
    assert run_a["t_end"] == pytest.approx(0.2)
    assert run_a["total_s"] == pytest.approx(1.25)
    assert run_a["integrals"]["rho"] == pytest.approx(float(np.sum(1.0 + 0.01 * np.arange(32)) * 0.25))
    assert run_a["integral_min"] == pytest.approx(0.0)
    assert run_a["integral_max"] == pytest.approx(20.0)

    pair = summary["pairs"][0]
    assert pair["left"] == "sod-cpu-double-o2-ieee-leq"
    assert pair["right"] == "sod-cpu-float-o2-ieee-leq"
    assert pair["pair_label"] == "sod-cpu-o2-ieee-leq"
    expected_l1 = (32 * 0.25 + 32 * 0.125) / (32 * 4)
    assert pair["l1"] == pytest.approx(expected_l1)
    assert pair["linf"] == pytest.approx(0.25)
    assert pair["ulp_max"] is None

    with open(matrix_summary.parent / "summary.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert any(row["row_type"] == "pair" and row["pair_label"] == "sod-cpu-o2-ieee-leq" for row in rows)


def test_cli_reports_explicit_pair_label(tmp_path: Path) -> None:
    matrix_summary = _synthetic_matrix(tmp_path)
    out_prefix = tmp_path / "explicit" / "axis_summary"

    summary = _run_report(
        matrix_summary,
        "--pair-by",
        "none",
        "--pair",
        "sod-cpu-double-o2-ieee-leq",
        "sod-cpu-float-o2-ieee-leq",
        "--pair-label",
        "synthetic_axis",
        "--out",
        str(out_prefix),
    )

    assert out_prefix.with_suffix(".csv").is_file()
    assert out_prefix.with_suffix(".json").is_file()
    assert out_prefix.with_suffix(".md").is_file()
    assert summary["pair_count"] == 1
    assert summary["pairs"][0]["pair_label"] == "synthetic_axis"


def test_cli_reports_zero_denominator_ratios_as_not_applicable(tmp_path: Path) -> None:
    root = tmp_path / "matrix"
    zero = np.zeros((1, 32, 4), dtype=np.float64)
    run_a = _write_run(root, "zero-a-double", "double", "cpu-a", zero, total_s=1.0)
    run_b = _write_run(root, "zero-b-double", "double", "cpu-b", zero, total_s=1.0)
    reference = tmp_path / "reference.bin"
    _write_binary(reference, zero, dx=0.25, dy=1.0, t=0.2)
    matrix_summary = {
        "experiment": "synthetic-zero",
        "output_root": str(root),
        "run_count": 2,
        "runs": [run_a, run_b],
    }
    matrix_summary_path = root / "matrix_summary.json"
    matrix_summary_path.write_text(json.dumps(matrix_summary, indent=2) + "\n", encoding="utf-8")

    summary = _run_report(
        matrix_summary_path,
        "--pair-by",
        "none",
        "--pair",
        "zero-a-double",
        "zero-b-double",
        "--pair-label",
        "zero_axis",
        "--reference",
        str(reference),
    )

    pair = summary["pairs"][0]
    assert pair["l1"] == pytest.approx(0.0)
    assert pair["linf"] == pytest.approx(0.0)
    assert pair["philip_ratio"] is None
    assert pair["ulp_max"] is None

    with open(matrix_summary_path.parent / "summary.csv", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    pair_row = next(row for row in rows if row["row_type"] == "pair")
    assert pair_row["philip_ratio"] == "n/a"
    assert pair_row["ulp_max"] == "n/a"


def test_cli_allows_one_explicit_pair_label_for_multiple_pairs(tmp_path: Path) -> None:
    root = tmp_path / "matrix"
    payload = np.ones((1, 32, 4), dtype=np.float64)
    run_a = _write_run(root, "axis-a", "double", "cpu-a", payload, total_s=1.0)
    run_b = _write_run(root, "axis-b", "double", "cpu-b", payload + 1.0, total_s=1.0)
    run_c = _write_run(root, "axis-c", "double", "cpu-c", payload + 2.0, total_s=1.0)
    run_d = _write_run(root, "axis-d", "double", "cpu-d", payload + 3.0, total_s=1.0)
    matrix_summary_path = root / "matrix_summary.json"
    matrix_summary_path.write_text(
        json.dumps(
            {
                "experiment": "synthetic-axis",
                "output_root": str(root),
                "run_count": 4,
                "runs": [run_a, run_b, run_c, run_d],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    summary = _run_report(
        matrix_summary_path,
        "--pair-by",
        "none",
        "--pair",
        "axis-a",
        "axis-b",
        "--pair",
        "axis-c",
        "axis-d",
        "--pair-label",
        "compiler_axis",
    )

    assert summary["pair_count"] == 2
    assert [pair["pair_label"] for pair in summary["pairs"]] == ["compiler_axis", "compiler_axis"]


def test_cli_rejects_pair_header_time_or_spacing_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "matrix"
    payload = np.ones((1, 32, 4), dtype=np.float64)
    run_a = _write_run(root, "header-a", "double", "cpu-a", payload, total_s=1.0, t=0.2)
    run_b = _write_run(root, "header-b", "double", "cpu-b", payload, total_s=1.0, t=0.25)
    matrix_summary_path = root / "matrix_summary.json"
    matrix_summary_path.write_text(
        json.dumps({"experiment": "headers", "output_root": str(root), "run_count": 2, "runs": [run_a, run_b]}) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "regression" / "matrix_summary_report.py"),
            str(matrix_summary_path),
            "--pair-by",
            "none",
            "--pair",
            "header-a",
            "header-b",
            "--pair-label",
            "bad_header",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "Header mismatch" in result.stderr
    assert "t" in result.stderr


def test_cli_allows_float_double_header_roundoff(tmp_path: Path) -> None:
    root = tmp_path / "matrix"
    payload = np.ones((1, 32, 4), dtype=np.float64)
    run_a = _write_run(root, "roundoff-double", "double", "cpu-a", payload, total_s=1.0, dx=0.005)
    run_b = _write_run(
        root,
        "roundoff-float",
        "float",
        "cpu-b",
        (payload + 0.25).astype(np.float32),
        total_s=1.0,
        dx=float(np.float32(0.005)),
    )
    matrix_summary_path = root / "matrix_summary.json"
    matrix_summary_path.write_text(
        json.dumps({"experiment": "roundoff", "output_root": str(root), "run_count": 2, "runs": [run_a, run_b]})
        + "\n",
        encoding="utf-8",
    )

    summary = _run_report(matrix_summary_path, "--pair-by", "precision")

    assert summary["pair_count"] == 1
    assert summary["pairs"][0]["l1"] == pytest.approx(0.25)


def test_cli_rejects_reference_header_time_or_spacing_mismatch(tmp_path: Path) -> None:
    root = tmp_path / "matrix"
    payload = np.ones((1, 32, 4), dtype=np.float64)
    run_a = _write_run(root, "ref-a", "double", "cpu-a", payload, total_s=1.0)
    run_b = _write_run(root, "ref-b", "double", "cpu-b", payload + 1.0, total_s=1.0)
    reference = tmp_path / "reference.bin"
    _write_binary(reference, payload, dx=0.5, dy=1.0, t=0.2)
    matrix_summary_path = root / "matrix_summary.json"
    matrix_summary_path.write_text(
        json.dumps({"experiment": "reference", "output_root": str(root), "run_count": 2, "runs": [run_a, run_b]}) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "regression" / "matrix_summary_report.py"),
            str(matrix_summary_path),
            "--pair-by",
            "none",
            "--pair",
            "ref-a",
            "ref-b",
            "--pair-label",
            "bad_reference",
            "--reference",
            str(reference),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "Reference header mismatch" in result.stderr
    assert "dx" in result.stderr


def test_cli_resolves_relative_matrix_paths_from_matrix_root_not_cwd(tmp_path: Path) -> None:
    matrix_dir = tmp_path / "case"
    output_root = matrix_dir / "matrix_out"
    payload = np.ones((1, 32, 4), dtype=np.float64)
    run_a = _write_run(
        output_root,
        "rel-double",
        "double",
        "cpu-a",
        payload,
        total_s=1.0,
        raw_output_text="grid.bin",
    )
    run_b = _write_run(
        output_root,
        "rel-float",
        "float",
        "cpu-b",
        (payload + 0.5).astype(np.float32),
        total_s=1.0,
        raw_output_text="grid.bin",
    )
    matrix_summary_path = matrix_dir / "matrix_summary.json"
    matrix_dir.mkdir(parents=True, exist_ok=True)
    matrix_summary_path.write_text(
        json.dumps(
            {
                "experiment": "relative",
                "output_root": "matrix_out",
                "run_count": 2,
                "runs": [
                    {"name": run_a["name"]},
                    {"name": run_b["name"]},
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    other_cwd = tmp_path / "other_cwd"
    other_cwd.mkdir()
    relative_matrix = Path(os.path.relpath(matrix_summary_path, other_cwd))

    summary = _run_report(relative_matrix, "--pair-by", "precision", cwd=other_cwd)

    assert summary["run_count"] == 2
    assert summary["pair_count"] == 1
    assert (matrix_summary_path.parent / "summary.json").is_file()


def test_cli_resolves_canonical_run_matrix_relative_paths_from_different_cwd(tmp_path: Path) -> None:
    launch_root = tmp_path / "launch"
    output_root = launch_root / "exp" / "out"
    payload = np.ones((1, 32, 4), dtype=np.float64)
    run_a = _write_run(
        output_root,
        "canon-double",
        "double",
        "cpu-a",
        payload,
        total_s=1.0,
        raw_output_text=str(Path("exp") / "out" / "runs" / "canon-double" / "grid.bin"),
    )
    run_b = _write_run(
        output_root,
        "canon-float",
        "float",
        "cpu-b",
        (payload + 0.25).astype(np.float32),
        total_s=1.0,
        raw_output_text=str(Path("exp") / "out" / "runs" / "canon-float" / "grid.bin"),
    )
    matrix_summary_path = output_root / "matrix_summary.json"
    matrix_summary_path.write_text(
        json.dumps(
            {
                "experiment": "canonical-relative",
                "output_root": str(Path("exp") / "out"),
                "run_count": 2,
                "runs": [
                    {
                        "name": run_a["name"],
                        "run_config": str(Path("exp") / "out" / "runs" / "canon-double" / "config.cfg"),
                        "raw_output": run_a["raw_output"],
                    },
                    {
                        "name": run_b["name"],
                        "run_config": str(Path("exp") / "out" / "runs" / "canon-float" / "config.cfg"),
                        "raw_output": run_b["raw_output"],
                    },
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    other_cwd = tmp_path / "other_cwd"
    other_cwd.mkdir()
    relative_matrix = Path(os.path.relpath(matrix_summary_path, other_cwd))

    summary = _run_report(relative_matrix, "--pair-by", "precision", cwd=other_cwd)

    assert summary["run_count"] == 2
    assert summary["pair_count"] == 1
    assert summary["runs"][0]["nx"] == 32


def test_load_runs_rejects_failed_canonical_metadata(tmp_path: Path) -> None:
    from scripts.regression import matrix_summary_report

    root = tmp_path / "matrix"
    run_dir = root / "runs" / "failed"
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text(
        json.dumps(
            {
                "schema": {"name": "hrsc.run-record", "version": 1},
                "name": "failed",
                "status": "failed",
                "failure": {"category": "numerical_failure", "message": "nan"},
                "returncode": 1,
            }
        ),
        encoding="utf-8",
    )
    matrix_path = root / "matrix_summary.json"
    matrix_path.write_text(
        json.dumps({"output_root": str(root), "runs": [{"name": "failed"}]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="numerical_failure"):
        matrix_summary_report._load_runs(matrix_path)


def test_load_runs_rejects_success_metadata_with_nonzero_returncode(
    tmp_path: Path,
) -> None:
    from scripts.regression import matrix_summary_report

    root = tmp_path / "matrix"
    run_dir = root / "runs" / "nonzero"
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text(
        json.dumps(
            {
                "schema": {"name": "hrsc.run-record", "version": 1},
                "name": "nonzero",
                "status": "success",
                "returncode": 3,
            }
        ),
        encoding="utf-8",
    )
    matrix_path = root / "matrix_summary.json"
    matrix_path.write_text(
        json.dumps({"output_root": str(root), "runs": [{"name": "nonzero"}]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="failed"):
        matrix_summary_report._load_runs(matrix_path)


def test_load_runs_reads_legacy_output_binary_alias(tmp_path: Path) -> None:
    from scripts.regression import matrix_summary_report

    root = tmp_path / "matrix"
    run_dir = root / "runs" / "legacy"
    output = run_dir / "grid.bin"
    payload = np.ones((1, 4, 4), dtype=np.float64)
    _write_binary(output, payload, dx=0.25, dy=1.0, t=0.2)
    (run_dir / "metadata.json").write_text(
        json.dumps(
            {"name": "legacy", "returncode": 0, "output_binary": str(output)}
        ),
        encoding="utf-8",
    )
    matrix_path = root / "matrix_summary.json"
    matrix_path.write_text(
        json.dumps({"output_root": str(root), "runs": [{"name": "legacy"}]}),
        encoding="utf-8",
    )

    runs = matrix_summary_report._load_runs(matrix_path)

    assert runs[0].grid is not None
    assert runs[0].grid.shape == (1, 4, 4)


def test_scalar_only_import_does_not_require_phase_metric_module() -> None:
    code = f"""
import importlib.abc
import importlib.util
import pathlib
import sys

class BlockPhase(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if fullname == "phase_error_metrics":
            raise ImportError("phase blocked")
        return None

sys.meta_path.insert(0, BlockPhase())
script = pathlib.Path({str(REPO_ROOT / "scripts" / "regression" / "matrix_summary_report.py")!r})
spec = importlib.util.spec_from_file_location("matrix_summary_report_lazy_test", script)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
"""
    result = subprocess.run([sys.executable, "-c", code], text=True, capture_output=True)

    assert result.returncode == 0, result.stderr
