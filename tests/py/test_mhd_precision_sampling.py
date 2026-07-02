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
