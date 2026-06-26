import pathlib
import sys


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from scripts.verificarlo.mhd_verificarlo_smoke import (
    ProbeRecord,
    make_blocked_summary_md,
    make_probe_record,
    make_sample_cfg,
)


def test_make_probe_record_has_structured_command_result_fields():
    record = make_probe_record(
        "native",
        ["verificarlo-c++", "--version"],
        returncode=127,
        stdout="",
        stderr="missing",
        supported=False,
    )

    assert record == {
        "name": "native",
        "command": ["verificarlo-c++", "--version"],
        "returncode": 127,
        "stdout": "",
        "stderr": "missing",
        "supported": False,
        "runner": None,
    }
    assert ProbeRecord.__name__ == "ProbeRecord"


def test_make_sample_cfg_appends_binary_output_keys_without_mutating_source():
    source = "test = brio_wu\nnx = 800\n"
    grid_path = pathlib.Path("runs") / "sample_01" / "grid.bin"

    out = make_sample_cfg(source, grid_path)

    assert source == "test = brio_wu\nnx = 800\n"
    assert out.endswith("\n")
    assert "output_format = binary\n" in out
    assert "output_file = runs\\sample_01\\grid.bin\n" in out or "output_file = runs/sample_01/grid.bin\n" in out


def test_make_sample_cfg_preserves_docker_posix_output_path():
    source = "test = brio_wu\n"

    out = make_sample_cfg(source, "/workdir/experiments/week13/sample_01/grid.bin")

    assert "output_file = /workdir/experiments/week13/sample_01/grid.bin\n" in out


def test_blocked_summary_explicitly_says_no_mca_result_was_produced():
    probes = [
        make_probe_record(
            "docker",
            ["docker", "run", "--rm", "verificarlo/verificarlo", "bash", "-lc", "verificarlo-c++ --version"],
            returncode=1,
            stdout="",
            stderr="permission denied",
            supported=False,
        )
    ]

    text = make_blocked_summary_md("blocked_environment", probes, "no supported runner")

    assert "blocked_environment" in text
    assert "no Verificarlo MCA result was produced" in text
    assert "no MCA evidence was generated" in text
    assert "permission denied" in text
