import json
from pathlib import Path

import pytest

from scripts.harness.experiment_manifest import load_valid_manifest, validate_manifest


ROOT = Path(__file__).resolve().parents[2]
MANIFESTS = (
    "experiments/week12/brio_wu_1d/manifest.json",
    "experiments/week12/mhd_2d/brio_wu_2d/manifest.json",
    "experiments/week12/mhd_2d/divb_clean/manifest.json",
    "experiments/week13/hlld_divb_followup/manifest.json",
    "experiments/week13/orszag_tang/manifest.json",
    "experiments/week13/kelvin_helmholtz/manifest.json",
    "experiments/week14/mhd_precision_pilot/manifest.json",
    "experiments/week14/mhd_precision_pilot_hlld/manifest.json",
    "experiments/week15/brio_wu_precision_pilot_p1/manifest.json",
    "experiments/week15/brio_wu_precision_pilot_hlld_p1/manifest.json",
    "experiments/week15/orszag_tang_precision_smoke/manifest.json",
    "experiments/week15/orszag_tang_precision_smoke_hlld/manifest.json",
    "experiments/week15/mhd_temporal_divergence/manifest.json",
)


def _write_valid_manifest(tmp_path: Path) -> Path:
    for relative_path in (
        "inputs/case.cfg",
        "tools/build.py",
        "tools/run.py",
        "tools/measure.py",
        "results/summary.json",
        "figures/result.png",
        "evidence/summary.md",
    ):
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("present\n", encoding="utf-8")

    manifest = {
        "schema": {"name": "hrsc.experiment-manifest", "version": 1},
        "id": "report2-test",
        "report": "report2",
        "lifecycle": "canonical",
        "purpose": "Validate a bounded test experiment.",
        "pipeline": {
            "config": ["inputs/case.cfg"],
            "build": ["tools/build.py"],
            "run": ["tools/run.py"],
            "measure": ["tools/measure.py"],
            "aggregate": ["results/summary.json"],
            "plot": ["figures/result.png"],
        },
        "evidence": ["evidence/summary.md"],
        "retention": {"keep": ["summary.*"], "transient": ["generated grids"]},
        "provenance": {"notes": "Tracked Git history is authoritative."},
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def test_report2_promoted_manifests_are_valid_and_evidence_exists() -> None:
    manifests = [load_valid_manifest(ROOT / path, ROOT) for path in MANIFESTS]
    assert {item["lifecycle"] for item in manifests} >= {
        "canonical",
        "superseded",
        "invalid",
    }


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        (lambda data: data.update(lifecycle="unknown"), "lifecycle"),
        (lambda data: data["pipeline"].pop("plot"), "pipeline.plot"),
        (lambda data: data.update(evidence=["evidence/missing.md"]), "evidence"),
        (lambda data: data.update(lifecycle="superseded"), "replacement"),
        (lambda data: data.update(lifecycle="invalid"), "exclusion_reason"),
        (lambda data: data["schema"].update(version=2), "schema.version"),
        (lambda data: data.update(evidence="evidence/summary.md"), "evidence"),
        (lambda data: data["pipeline"].update(config=["../outside.cfg"]), "pipeline.config"),
    ),
)
def test_invalid_manifests_return_clear_aggregated_errors(
    tmp_path: Path, mutation, expected: str
) -> None:
    path = _write_valid_manifest(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    mutation(data)
    path.write_text(json.dumps(data), encoding="utf-8")

    errors = validate_manifest(path, tmp_path)

    assert errors
    assert any(expected in error for error in errors)
    with pytest.raises(ValueError, match=expected):
        load_valid_manifest(path, tmp_path)


def test_superseded_manifest_requires_existing_safe_replacement(tmp_path: Path) -> None:
    path = _write_valid_manifest(tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["lifecycle"] = "superseded"
    data["replacement"] = "../replacement/manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    errors = validate_manifest(path, tmp_path)

    assert any("replacement" in error for error in errors)
