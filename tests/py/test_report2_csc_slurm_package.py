from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "scripts" / "cluster" / "report2_w16_w17_slurm"


def read(name: str) -> str:
    return (PACKAGE / name).read_text(encoding="utf-8")


def test_csc_slurm_package_has_no_docker_dependency():
    for rel in (
        "env.sh",
        "run_kh_full_mca.slurm",
        "run_kh_smoke_mca.slurm",
        "run_kh_packets_from_mca.slurm",
        "run_w17_synthesis_and_figures.slurm",
        "submit_w16_w17.sh",
        "make_bundle.sh",
    ):
        text = read(rel).lower()
        assert "docker" not in text
        assert "apptainer" in text or rel in {
            "run_kh_packets_from_mca.slurm",
            "run_w17_synthesis_and_figures.slurm",
            "submit_w16_w17.sh",
            "make_bundle.sh",
        }


def test_full_kh_mca_job_writes_csc_scoped_outputs():
    text = read("run_kh_full_mca.slurm")

    assert "#SBATCH --partition=csc-mphil" in text
    assert "#SBATCH --array=0-3" in text
    assert "#SBATCH --time=06:00:00" in text
    assert "tests/cases/kelvin_helmholtz_2d/kh.cfg" in text
    assert "experiments/week16/kelvin_helmholtz_precision/csc_mca/${SOLVER}" in text
    assert "SOLVERS=(hll hll hlld hlld)" in text
    assert "PRECS=(53 24 53 24)" in text
    assert "--samples \"${HRSC_KH_FULL_SAMPLES}\"" in text
    assert "--jobs \"${HRSC_MCA_JOBS}\"" in text
    assert "--solver \"${SOLVER}\"" in text
    assert "--precisions \"${PREC}\"" in text
    assert "--sample-timeout-s \"${HRSC_KH_SAMPLE_TIMEOUT_S}\"" in text
    assert "--backend-lib \"${HRSC_VFC_BACKEND_LIB}\"" in text


def test_smoke_kh_mca_job_uses_packaged_reduced_cfg():
    text = read("run_kh_smoke_mca.slurm")
    cfg = read("cfg/kh_64_t005.cfg")

    assert "scripts/cluster/report2_w16_w17_slurm/cfg/kh_64_t005.cfg" in text
    assert "experiments/week16/kelvin_helmholtz_precision/csc_mca_smoke/${SOLVER}" in text
    assert "#SBATCH --array=0-3" in text
    assert "--precisions \"${PREC}\"" in text
    assert "nx = 64" in cfg
    assert "ny = 64" in cfg
    assert "t_end = 0.05" in cfg


def test_packet_job_consumes_full_mca_summary_without_overwriting_local_packets():
    text = read("run_kh_packets_from_mca.slurm")

    assert "experiments/week16/kelvin_helmholtz_precision/csc_packets" in text
    assert 'MCA_DIR="experiments/week16/kelvin_helmholtz_precision/csc_mca/${SOLVER}"' in text
    assert 'MCA_SUMMARY="${MCA_DIR}/summary.json"' in text
    assert "--merge-only" in text
    assert "--mca-summary \"${MCA_SUMMARY}\"" in text
    assert "--phase p1" in text
    assert "hll_p1/summary" not in text

def test_bundle_script_is_scoped_and_excludes_transient_outputs():
    text = read("make_bundle.sh")

    assert "report2_w16_w17_csc_bundle.tar.gz" in text
    assert "CMakeLists.txt" in text
    assert "experiments/week15" in text
    assert "experiments/week16" in text
    assert "experiments/week17" in text
    assert "--exclude \"build-*\"" in text
    assert "--exclude \"build-matrix\"" in text
    assert "--exclude \"grid.bin\"" in text
    assert "mktemp" in text
    assert ".git" not in text


def test_week18_slurm_routes_gpu_and_cpu_suites_without_docker():
    gpu = read("run_week18_hardware_repeats.slurm")
    cpu = read("run_week18_cpu_robustness.slurm")

    assert "--gres=gpu:1" in gpu
    assert "mhd_week18_supplemental.py hardware" in gpu
    assert "mhd_week18_supplemental.py threads" in cpu
    assert "mhd_week18_supplemental.py cfl" in cpu
    assert "docker" not in (gpu + cpu).lower()


def test_week18_submit_includes_existing_full_kh_mca_job():
    submit = read("submit_week18.sh")

    assert "run_kh_full_mca.slurm" in submit
    assert "run_week18_hardware_repeats.slurm" in submit
    assert "run_week18_cpu_robustness.slurm" in submit
