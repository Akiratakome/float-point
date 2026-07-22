from __future__ import annotations

import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
MHD_CASE_DIRS = {
    "brio_wu_1d",
    "kelvin_helmholtz_2d",
    "mhd_divb_clean",
    "orszag_tang_2d",
}


def test_all_euler_case_configs_pin_solver_after_default_change() -> None:
    cfgs = sorted(
        cfg
        for cfg in (REPO_ROOT / "tests" / "cases").rglob("*.cfg")
        if cfg.relative_to(REPO_ROOT / "tests" / "cases").parts[0] not in MHD_CASE_DIRS
    )
    missing = []
    for cfg in cfgs:
        text = cfg.read_text(encoding="utf-8")
        if not any(
            line.strip().startswith("solver")
            and "=" in line
            and not line.strip().startswith("#")
            for line in text.splitlines()
        ):
            missing.append(str(cfg.relative_to(REPO_ROOT)))

    assert missing == []


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
    assert metadata["schema"] == {"name": "hrsc.run-record", "version": 1}
    assert metadata["status"] == "success"
    assert set(metadata["provenance"]["git"]) == {"commit", "dirty"}


def test_run_matrix_dry_run_serialises_shared_runner_record(tmp_path: Path) -> None:
    from scripts import run_matrix

    cfg = tmp_path / "case.cfg"
    cfg.write_text("test = sod\n", encoding="utf-8")
    run = run_matrix.normalise_run(
        {"name": "dry", "binary": "build-double/hrsc", "config": str(cfg)},
        output_root=tmp_path / "out",
    )

    metadata = run_matrix.run_one(run, experiment="pytest", dry_run=True)

    assert metadata["status"] == "success"
    assert metadata["completion"] == {"reported": False}
    assert metadata["timing"]["total_s"] is None
    assert metadata["timing"]["elapsed_wall_s"] >= 0.0
    assert metadata["stdout"] == str(run.run_dir / "stdout.txt")
    assert metadata["stderr"] == str(run.run_dir / "stderr.txt")


def test_run_matrix_applies_extra_cfg_overrides(tmp_path: Path) -> None:
    from scripts import run_matrix

    cfg = tmp_path / "case.cfg"
    cfg.write_text(
        "test = sod\n"
        "solver = hllc\n"
        "output_format = table\n",
        encoding="utf-8",
    )
    raw_run = {
        "name": "sod-gpu",
        "binary": "build-cuda-double-strict/hrsc",
        "config": str(cfg),
        "extra_cfg": {
            "device": "gpu",
            "solver": "rusanov",
            "output_format": "binary",
            "output_file": "stale/path.bin",
        },
        "output_file": "grid.bin",
    }

    run = run_matrix.normalise_run(raw_run, output_root=tmp_path / "out")
    generated_cfg = run_matrix.materialise_run_config(run)
    text = generated_cfg.read_text(encoding="utf-8")

    assert "device = gpu\n" in text
    assert "solver = rusanov\n" in text
    assert "output_format = binary\n" in text
    assert "output_file = " + str(run.raw_output) in text
    assert cfg.read_text(encoding="utf-8").endswith("output_format = table\n")


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


def test_a4_metric_clis_accept_precision_label() -> None:
    from scripts.metrics import losos_metric, snr_metric

    snr_args = snr_metric._parse_args(
        [
            "--root", "experiments/week4/2d_vfc_cluster",
            "--reference", "experiments/week4/metrics/u_ref_200_blockavg.npz",
            "--out-dir", "experiments/week4/metrics",
            "--precision-label", "p24-real-float",
        ]
    )
    losos_args = losos_metric._parse_args(
        [
            "--root", "experiments/week4/2d_vfc_cluster",
            "--reference", "experiments/week4/metrics/u_ref_200_blockavg.npz",
            "--out-dir", "experiments/week4/metrics",
            "--precision-label", "p24-real-float",
        ]
    )

    assert snr_args.precision_label == "p24-real-float"
    assert losos_args.precision_label == "p24-real-float"


def test_verificarlo_2d_runner_accepts_precision_bits() -> None:
    script = (REPO_ROOT / "scripts" / "verificarlo" / "verificarlo_run_2d.sh").read_text(encoding="utf-8")

    assert "--precision" in script
    assert "PRECISION" in script
    assert "--precision-binary64=${PRECISION}" in script
    assert 'BUILD_DIR="build-vfc-p${PRECISION}-omp${ENABLE_OPENMP}"' in script


def test_verificarlo_2d_runner_disables_openmp() -> None:
    script = (REPO_ROOT / "scripts" / "verificarlo" / "verificarlo_run_2d.sh").read_text(encoding="utf-8")

    assert 'ENABLE_OPENMP="OFF"' in script


def test_verificarlo_2d_runner_accepts_openmp_override() -> None:
    script = (REPO_ROOT / "scripts" / "verificarlo" / "verificarlo_run_2d.sh").read_text(encoding="utf-8")

    assert "--openmp" in script
    assert "ENABLE_OPENMP" in script
    assert "-DENABLE_OPENMP=${ENABLE_OPENMP}" in script


def test_verificarlo_2d_runner_sets_thread_env_only_without_openmp() -> None:
    script = (REPO_ROOT / "scripts" / "verificarlo" / "verificarlo_run_2d.sh").read_text(encoding="utf-8")

    assert 'if [[ "$ENABLE_OPENMP" == "OFF" ]]' in script
    assert "export OMP_NUM_THREADS=1" in script


def test_verificarlo_2d_runner_accepts_mca_mode() -> None:
    script = (REPO_ROOT / "scripts" / "verificarlo" / "verificarlo_run_2d.sh").read_text(encoding="utf-8")

    assert "--mca-mode" in script
    assert "MCA_MODE" in script
    assert "--mode=${MCA_MODE}" in script


def test_verificarlo_2d_runner_uses_portable_seed_range() -> None:
    script = (REPO_ROOT / "scripts" / "verificarlo" / "verificarlo_run_2d.sh").read_text(encoding="utf-8")

    assert "0x000000007FFFFFFF" in script


def test_verificarlo_2d_runner_uses_single_seed_source() -> None:
    script = (REPO_ROOT / "scripts" / "verificarlo" / "verificarlo_run_2d.sh").read_text(encoding="utf-8")

    assert "export VFC_BACKENDS=" in script
    assert "VERIFICARLO_MCA_SEED" not in script
    assert "VFC_BACKEND_SEED" not in script


def test_tradeoff_summary_table_discovers_p53_and_float_rows(tmp_path: Path) -> None:
    from scripts.figures import tradeoff_summary_table

    snr_csv = tmp_path / "snr.csv"
    losos_csv = tmp_path / "losos.csv"
    sreq_csv = tmp_path / "sreq.csv"

    snr_csv.write_text(
        "solver,precision,variable,sigma_fp_l1\n"
        "hllc,p53,rho,1e-11\n"
        "hllc,p24-real-float,rho,1e-6\n"
        "rusanov,p53,rho,2e-11\n"
        "rusanov,p24-real-float,rho,2e-6\n",
        encoding="utf-8",
    )
    losos_csv.write_text(
        "solver,precision,variable,s_worst_q05\n"
        "hllc,p53,rho,1.5\n"
        "hllc,p24-real-float,rho,0.8\n"
        "rusanov,p53,rho,1.2\n"
        "rusanov,p24-real-float,rho,0.7\n",
        encoding="utf-8",
    )
    sreq_csv.write_text(
        "solver,variable,mu_trunc_l1,s_req\n"
        "hllc,rho,277.0,3.13\n"
        "rusanov,rho,418.0,2.95\n",
        encoding="utf-8",
    )

    rows = tradeoff_summary_table.build_rows(
        tradeoff_summary_table._read_csv(snr_csv),
        tradeoff_summary_table._read_csv(losos_csv),
        tradeoff_summary_table._read_csv(sreq_csv),
    )
    markdown = tradeoff_summary_table._format_markdown(rows, N=200)

    assert len(rows) == 4
    assert "| HLLC    | p24-real-float" in markdown
    assert "| RUSANOV | p24-real-float" in markdown


def test_missing_run_matrix_fields_raise_clear_error(tmp_path: Path) -> None:
    from scripts import run_matrix

    with pytest.raises(ValueError, match="missing required field 'config'"):
        run_matrix.normalise_run(
            {"name": "bad", "binary": "build-double/hrsc"},
            output_root=tmp_path,
        )
