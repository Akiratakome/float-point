import pathlib
import sys
from types import SimpleNamespace


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from scripts.verificarlo.mhd_verificarlo_smoke import (
    ProbeRecord,
    apptainer_command,
    apptainer_probe_command,
    make_blocked_summary_md,
    make_probe_record,
    make_sample_cfg,
    sample_command_for_runner,
)
import scripts.verificarlo.mhd_verificarlo_smoke as smoke


def _joined(command: list[str]) -> str:
    return " ".join(command)


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


def test_make_sample_cfg_can_override_mhd_riemann_solver():
    source = "test = brio_wu\n"

    out = make_sample_cfg(source, "runs/sample_01/grid.bin", solver="hlld")

    assert "riemann = hlld\n" in out
    assert "output_format = binary\n" in out


def test_parse_args_accepts_hlld_solver():
    args = smoke.parse_args(["--solver", "hlld"])

    assert args.solver == "hlld"


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


def test_sample_command_passes_mca_precision_as_backend_arg_docker():
    # Verificarlo 2.x interflop backends read precision from a VFC_BACKENDS
    # argument; the legacy VFC_MCA_PRECISION_BINARY64 env var is silently
    # ignored (same class of gotcha as VFC_BACKENDS_SEED). If precision is not
    # inlined into VFC_BACKENDS, both p24 and p53 run at the backend default
    # (=53), which is the Week-14 p24-never-separates bug.
    cmd = sample_command_for_runner(
        "docker", "img", pathlib.Path("build-vfc"), pathlib.Path("config.cfg"), 24
    )
    text = _joined(cmd)

    assert "--precision-binary64=24" in text
    assert "VFC_MCA_PRECISION_BINARY64" not in text


def test_sample_command_precision_tracks_argument_docker():
    text = _joined(
        sample_command_for_runner(
            "docker", "img", pathlib.Path("build-vfc"), pathlib.Path("config.cfg"), 53
        )
    )

    assert "--precision-binary64=53" in text
    assert "VFC_MCA_PRECISION_BINARY64" not in text


def test_apptainer_probe_uses_sif_without_docker():
    cmd = apptainer_probe_command("verificarlo-cmake.sif")
    text = _joined(cmd)

    assert cmd[:2] == ["apptainer", "exec"]
    assert "verificarlo-cmake.sif" in cmd
    assert "docker" not in text.lower()
    assert "verificarlo-c++ --version" in text
    assert "cmake --version" in text


def test_apptainer_command_binds_repo_to_workdir():
    cmd = apptainer_command("verificarlo-cmake.sif", "echo ok")
    text = _joined(cmd)

    assert cmd[:2] == ["apptainer", "exec"]
    assert "--bind" in cmd
    assert ":/workdir" in text
    assert "--pwd /workdir" in text
    assert "docker" not in text.lower()


def test_sample_command_passes_mca_precision_as_backend_arg_apptainer():
    text = _joined(
        sample_command_for_runner(
            "apptainer", "verificarlo-cmake.sif", pathlib.Path("build-vfc"), pathlib.Path("config.cfg"), 24
        )
    )

    assert "apptainer exec" in text
    assert "--precision-binary64=24" in text
    assert "/workdir/build-vfc/hrsc_mhd" in text
    assert "/workdir/config.cfg" in text
    assert "docker" not in text.lower()
    assert "VFC_MCA_PRECISION_BINARY64" not in text


def test_sample_command_passes_mca_precision_as_backend_arg_wsl():
    text = _joined(
        sample_command_for_runner(
            "wsl", "img", pathlib.Path("build-vfc"), pathlib.Path("config.cfg"), 24
        )
    )

    assert "--precision-binary64=24" in text
    assert "VFC_MCA_PRECISION_BINARY64" not in text


def test_run_samples_retries_failed_mca_sample(tmp_path, monkeypatch):
    case = tmp_path / "brio_wu.cfg"
    case.write_text("test = brio_wu\n", encoding="utf-8")
    args = SimpleNamespace(out=tmp_path, case=case, samples=1, image="vfc", precision=24)
    commands = []
    metric_calls = 0

    monkeypatch.setattr(smoke, "build_commands_for_runner", lambda runner, image, build_dir: [["build"]])
    monkeypatch.setattr(smoke, "sample_command_for_runner", lambda *parts: ["sample"])

    def fake_run_command(command, **kwargs):
        commands.append(command)
        if command == ["build"]:
            return {"returncode": 0, "stdout": "", "stderr": ""}
        if commands.count(["sample"]) == 1:
            return {"returncode": 2, "stdout": "", "stderr": "did not advance time"}
        return {"returncode": 0, "stdout": "", "stderr": ""}

    def fake_grid_metrics(path):
        nonlocal metric_calls
        metric_calls += 1
        if metric_calls == 1:
            return {"grid_status": "missing", "rho_min": None, "rho_max": None, "rho_mean": None}
        return {"grid_status": "read", "rho_min": 1.0, "rho_max": 1.0, "rho_mean": 1.0}

    monkeypatch.setattr(smoke, "run_command", fake_run_command)
    monkeypatch.setattr(smoke, "read_grid_metrics", fake_grid_metrics)
    monkeypatch.setattr(smoke, "git_commit", lambda: "sha")
    monkeypatch.setattr(smoke, "sha256_file", lambda path: "hash")

    status, rows, reason = smoke.run_samples(args, [], "docker")

    assert status == "completed"
    assert len(rows) == 1
    assert rows[0]["attempt"] == 2
    assert commands.count(["sample"]) == 2
    assert "Produced 1 Verificarlo MCA sample grids" in reason


def test_run_samples_jobs_runs_samples_concurrently_in_order(tmp_path, monkeypatch):
    import threading
    import time as _time

    case = tmp_path / "brio_wu.cfg"
    case.write_text("test = brio_wu\n", encoding="utf-8")
    args = SimpleNamespace(out=tmp_path, case=case, samples=6, image="vfc", precision=53, jobs=3)

    monkeypatch.setattr(smoke, "build_commands_for_runner", lambda runner, image, build_dir: [["build"]])
    monkeypatch.setattr(smoke, "sample_command_for_runner", lambda *parts: ["sample"])

    lock = threading.Lock()
    active = 0
    peak = 0

    def fake_run_command(command, **kwargs):
        nonlocal active, peak
        if command == ["build"]:
            return {"returncode": 0, "stdout": "", "stderr": ""}
        with lock:
            active += 1
            peak = max(peak, active)
        _time.sleep(0.05)
        with lock:
            active -= 1
        return {"returncode": 0, "stdout": "", "stderr": ""}

    monkeypatch.setattr(smoke, "run_command", fake_run_command)
    monkeypatch.setattr(
        smoke, "read_grid_metrics",
        lambda path: {"grid_status": "read", "rho_min": 1.0, "rho_max": 1.0, "rho_mean": 1.0})
    monkeypatch.setattr(smoke, "git_commit", lambda: "sha")
    monkeypatch.setattr(smoke, "sha256_file", lambda path: "hash")

    status, rows, reason = smoke.run_samples(args, [], "docker")

    assert status == "completed"
    assert len(rows) == 6
    # Rows are returned in deterministic sample order regardless of completion order.
    assert [row["sample"] for row in rows] == [f"sample_{i:02d}" for i in range(1, 7)]
    # jobs=3 means at least two containers were genuinely in flight at once.
    assert peak > 1
    assert "Produced 6 Verificarlo MCA sample grids" in reason


def test_run_samples_jobs_reports_blocked_run_when_a_sample_fails(tmp_path, monkeypatch):
    case = tmp_path / "brio_wu.cfg"
    case.write_text("test = brio_wu\n", encoding="utf-8")
    args = SimpleNamespace(out=tmp_path, case=case, samples=4, image="vfc", precision=53, jobs=4)

    monkeypatch.setattr(smoke, "build_commands_for_runner", lambda runner, image, build_dir: [["build"]])
    monkeypatch.setattr(smoke, "sample_command_for_runner", lambda *parts: ["sample"])

    def fake_run_command(command, **kwargs):
        return {"returncode": 0, "stdout": "", "stderr": ""}

    # sample_03 never produces a readable grid; the others always do.
    def fake_grid_metrics(path):
        if "sample_03" in str(path):
            return {"grid_status": "missing", "rho_min": None, "rho_max": None, "rho_mean": None}
        return {"grid_status": "read", "rho_min": 1.0, "rho_max": 1.0, "rho_mean": 1.0}

    monkeypatch.setattr(smoke, "run_command", fake_run_command)
    monkeypatch.setattr(smoke, "read_grid_metrics", fake_grid_metrics)
    monkeypatch.setattr(smoke, "git_commit", lambda: "sha")
    monkeypatch.setattr(smoke, "sha256_file", lambda path: "hash")

    status, rows, reason = smoke.run_samples(args, [], "docker")

    assert status == "blocked_run"
    assert "sample_03" in reason
    # The three healthy samples are still reported as produced rows.
    assert {row["sample"] for row in rows} == {"sample_01", "sample_02", "sample_04"}
