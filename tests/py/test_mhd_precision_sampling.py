import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "verificarlo"))

import mhd_precision_sampling as sampler


def test_blocked_environment_is_valid_outcome(tmp_path, monkeypatch):
    out_dir = tmp_path / "p53"
    probes = []

    monkeypatch.setattr(sampler, "choose_runner", lambda found_probes: None)
    monkeypatch.setattr(sampler, "probe_runners", lambda image: probes)
    monkeypatch.setattr(
        sampler,
        "base_environment",
        lambda args, found_probes, runner: {
            "experiment": sampler.WEEK14_MCA_EXPERIMENT,
            "selected_runner": runner,
            "probes": found_probes,
            "precision": args.precision,
        },
    )

    block = sampler.sample_precision(out_dir, precision=53, samples=8,
                                     image="verificarlo/verificarlo")
    assert block["status"] == "blocked_environment"
    assert block["n"] == 0
    assert block["mca_evidence_generated"] is False
    assert "spread_rho" in block and block["spread_rho"] is None
    assert "spread_vx" in block and block["spread_vx"] is None
    assert "snr_p" in block and block["snr_p"] is None
    environment = json.loads((out_dir / "environment.json").read_text(encoding="utf-8"))
    assert environment["status"] == "blocked_environment"
    assert environment["experiment"] == "week14-mhd-mca"
    assert environment["solver"] == "hll"


def test_default_hlld_sampler_output_dir_is_separate():
    assert sampler.resolve_output_dir(None, "hll") == sampler.DEFAULT_OUT
    assert (
        sampler.resolve_output_dir(None, "hlld")
        == sampler.DEFAULT_OUT.parent.with_name("mhd_precision_pilot_hlld") / "mca"
    )
    custom = Path("experiments/week14/custom_mca")
    assert sampler.resolve_output_dir(custom, "hlld") == sampler.ROOT / custom


def test_blocked_run_writes_week14_environment_and_restores_experiment(tmp_path, monkeypatch):
    out_dir = tmp_path / "p53"
    original_experiment = sampler.smoke.EXPERIMENT

    monkeypatch.setattr(sampler, "probe_runners", lambda image: [{"supported": True, "runner": "docker"}])
    monkeypatch.setattr(sampler, "choose_runner", lambda probes: "docker")
    monkeypatch.setattr(sampler, "run_samples", lambda args, probes, runner: ("blocked_run", [], "sample failed"))
    monkeypatch.setattr(
        sampler,
        "base_environment",
        lambda args, probes, runner: {
            "experiment": sampler.smoke.EXPERIMENT,
            "selected_runner": runner,
        },
    )

    block = sampler.sample_precision(out_dir, precision=53, samples=8, image="verificarlo/verificarlo")

    assert block["status"] == "blocked_run"
    environment_path = out_dir / "environment.json"
    assert environment_path.exists()
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    assert environment["experiment"] == "week14-mhd-mca"
    assert environment["status"] == "blocked_run"
    assert sampler.smoke.EXPERIMENT == original_experiment


def test_completed_writes_week14_environment_and_restores_experiment(tmp_path, monkeypatch):
    out_dir = tmp_path / "p53"
    original_experiment = sampler.smoke.EXPERIMENT
    metrics = {
        "spread_rho": 1.0e-16,
        "spread_By": 2.0e-16,
        "spread_p": 3.0e-16,
        "spread_vx": 4.0e-16,
        "snr_rho": 10.0,
        "snr_By": 11.0,
        "snr_p": 12.0,
        "rho_mean_spread": 5.0e-16,
    }

    monkeypatch.setattr(sampler, "probe_runners", lambda image: [{"supported": True, "runner": "docker"}])
    monkeypatch.setattr(sampler, "choose_runner", lambda probes: "docker")
    monkeypatch.setattr(
        sampler,
        "run_samples",
        lambda args, probes, runner: (
            "completed",
            [{"sample": "sample_01"}, {"sample": "sample_02"}],
            "ok",
        ),
    )
    monkeypatch.setattr(
        sampler,
        "base_environment",
        lambda args, probes, runner: {
            "experiment": sampler.smoke.EXPERIMENT,
            "selected_runner": runner,
        },
    )
    monkeypatch.setattr(sampler, "stack_samples", lambda sample_root: (None, object(), ["a", "b"]))
    monkeypatch.setattr(sampler, "mca_field_spread", lambda samples, gamma: metrics)

    block = sampler.sample_precision(out_dir, precision=53, samples=8, image="verificarlo/verificarlo")

    assert block["status"] == "completed"
    assert block["n"] == 2
    assert block["runner"] == "docker"
    assert block["mca_evidence_generated"] is True
    assert block["spread_vx"] == metrics["spread_vx"]
    assert block["snr_p"] == metrics["snr_p"]
    environment = json.loads((out_dir / "environment.json").read_text(encoding="utf-8"))
    assert environment["status"] == "completed"
    assert environment["experiment"] == "week14-mhd-mca"
    assert sampler.smoke.EXPERIMENT == original_experiment


def test_sample_precision_passes_solver_to_smoke_runner(tmp_path, monkeypatch):
    out_dir = tmp_path / "p53"
    seen = {}

    monkeypatch.setattr(sampler, "probe_runners", lambda image: [{"supported": True, "runner": "docker"}])
    monkeypatch.setattr(sampler, "choose_runner", lambda probes: "docker")

    def fake_run_samples(args, probes, runner):
        seen["solver"] = args.solver
        return "blocked_run", [], "stopped before sampling"

    monkeypatch.setattr(sampler, "run_samples", fake_run_samples)
    monkeypatch.setattr(
        sampler,
        "base_environment",
        lambda args, probes, runner: {
            "experiment": sampler.smoke.EXPERIMENT,
            "selected_runner": runner,
            "solver": args.solver,
        },
    )

    block = sampler.sample_precision(
        out_dir,
        precision=53,
        samples=8,
        image="verificarlo/verificarlo",
        solver="hlld",
    )

    assert seen["solver"] == "hlld"
    assert block["status"] == "blocked_run"
    environment = json.loads((out_dir / "environment.json").read_text(encoding="utf-8"))
    assert environment["solver"] == "hlld"


def test_sample_precision_accepts_explicit_case_and_experiment(monkeypatch, tmp_path):
    case = tmp_path / "ot.cfg"
    case.write_text("test = orszag_tang\ngamma = 1.6666666666666667\n", encoding="utf-8")
    seen = {}

    monkeypatch.setattr(sampler, "probe_runners", lambda image: [{"runner": "docker", "supported": True}])
    monkeypatch.setattr(sampler, "choose_runner", lambda probes: "docker")

    def fake_run(args, probes, runner, experiment=sampler.WEEK14_MCA_EXPERIMENT):
        seen["case"] = args.case
        seen["experiment"] = experiment
        return "blocked_run", [], "stop before aggregation", {"status": "blocked_run"}

    monkeypatch.setattr(sampler, "_run_with_experiment_label", fake_run)

    block = sampler.sample_precision(
        tmp_path / "mca",
        precision=53,
        samples=1,
        image="img",
        solver="hlld",
        case=case,
        experiment="week15-mhd-mca",
    )

    assert seen["case"] == case
    assert seen["experiment"] == "week15-mhd-mca"
    assert block["status"] == "blocked_run"


def test_sample_args_threads_jobs_default_one():
    ns = sampler._sample_args(Path("."), 53, 4, "img", "hll")
    assert ns.jobs == 1
    ns5 = sampler._sample_args(Path("."), 53, 4, "img", "hll", jobs=5)
    assert ns5.jobs == 5


def test_sample_args_threads_timeout_and_backend():
    ns = sampler._sample_args(
        Path("."), 24, 4, "img", "hll", sample_timeout_s=14400,
        backend_lib="libinterflop_mca.so",
    )
    assert ns.sample_timeout_s == 14400
    assert ns.backend_lib == "libinterflop_mca.so"


def test_parse_args_accepts_jobs():
    assert sampler.parse_args(["--jobs", "7"]).jobs == 7
    assert sampler.parse_args([]).jobs == 1


def test_parse_args_accepts_split_precision_and_merge_options():
    args = sampler.parse_args([
        "--precisions", "24", "--merge-only",
        "--sample-timeout-s", "14400", "--backend-lib", "custom.so",
    ])
    assert args.precisions == "24"
    assert args.merge_only is True
    assert args.sample_timeout_s == 14400
    assert args.backend_lib == "custom.so"


def test_parse_precisions_normalises_labels_and_rejects_unknown():
    assert sampler._parse_precisions("p53,24,p53") == [53, 24]
    try:
        sampler._parse_precisions("16")
    except ValueError as exc:
        assert "unsupported precision" in str(exc)
    else:
        raise AssertionError("unsupported precision was accepted")


def test_merge_partials_requires_both_precision_blocks(tmp_path):
    common = {
        "experiment": "kh-mca", "case": "kh.cfg", "samples": 30,
        "solver": "hll",
    }
    (tmp_path / "summary_p53.json").write_text(
        json.dumps({**common, "mca": {"p53": {"status": "completed"}}}),
        encoding="utf-8",
    )
    (tmp_path / "summary_p24.json").write_text(
        json.dumps({**common, "mca": {"p24": {"status": "completed"}}}),
        encoding="utf-8",
    )

    target = sampler.merge_partials(tmp_path)
    merged = json.loads(target.read_text(encoding="utf-8"))
    assert set(merged["mca"]) == {"p53", "p24"}
    assert merged["solver"] == "hll"
