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
    "experiments/week19/lecoanet_kh_linear_reproduction/manifest.json",
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


def _read_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_manifest(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_aiinfra_report_id_is_accepted(tmp_path: Path) -> None:
    path = _write_valid_manifest(tmp_path)
    data = _read_manifest(path)
    data["report"] = "aiinfra"
    data["id"] = "aiinfra-test"
    _write_manifest(path, data)

    assert validate_manifest(path, tmp_path) == []


def test_unknown_report_id_is_still_rejected(tmp_path: Path) -> None:
    path = _write_valid_manifest(tmp_path)
    data = _read_manifest(path)
    data["report"] = "report9"
    _write_manifest(path, data)

    assert any("report" in error for error in validate_manifest(path, tmp_path))


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


@pytest.mark.parametrize("field", ("pipeline.config", "evidence", "replacement"))
def test_referenced_paths_must_be_existing_regular_files(tmp_path: Path, field: str) -> None:
    path = _write_valid_manifest(tmp_path)
    data = _read_manifest(path)
    data["lifecycle"] = "superseded" if field == "replacement" else "canonical"
    if field == "pipeline.config":
        data["pipeline"]["config"] = ["inputs"]
    elif field == "evidence":
        data["evidence"] = ["evidence"]
    else:
        data["replacement"] = "inputs"
    _write_manifest(path, data)

    errors = validate_manifest(path, tmp_path)

    assert any(field in error and "regular file" in error for error in errors)


@pytest.mark.parametrize(
    "bad_path",
    (
        "/absolute.cfg",
        "../outside.cfg",
        r"C:relative.cfg",
        r"C:\\absolute.cfg",
        r"\\\\server\\share\\case.cfg",
        r"..\\outside.cfg",
    ),
)
def test_cross_platform_absolute_and_traversal_paths_are_rejected(
    tmp_path: Path, bad_path: str
) -> None:
    path = _write_valid_manifest(tmp_path)
    data = _read_manifest(path)
    data["pipeline"]["config"] = [bad_path]
    _write_manifest(path, data)

    errors = validate_manifest(path, tmp_path)

    assert any("pipeline.config" in error for error in errors)
    assert any("absolute" in error or "traversal" in error for error in errors)


@pytest.mark.parametrize("bad_path", ("inputs/\x00case.cfg", "inputs/\ncase.cfg"))
def test_control_characters_in_referenced_paths_return_diagnostics(
    tmp_path: Path, bad_path: str
) -> None:
    path = _write_valid_manifest(tmp_path)
    data = _read_manifest(path)
    data["pipeline"]["config"] = [bad_path]
    _write_manifest(path, data)

    errors = validate_manifest(path, tmp_path)

    assert any("pipeline.config" in error and "control" in error for error in errors)


def test_manifest_must_be_regular_file_inside_repo_root(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    outside_manifest = _write_valid_manifest(tmp_path / "outside")
    manifest_directory = repo_root / "manifest-directory"
    manifest_directory.mkdir()

    outside_errors = validate_manifest(outside_manifest, repo_root)
    directory_errors = validate_manifest(manifest_directory, repo_root)

    assert any("outside repo_root" in error for error in outside_errors)
    assert any("regular file" in error for error in directory_errors)


def test_symlink_escape_is_rejected(tmp_path: Path) -> None:
    path = _write_valid_manifest(tmp_path)
    outside = tmp_path.parent / "outside.cfg"
    outside.write_text("outside\n", encoding="utf-8")
    link = tmp_path / "inputs" / "escaped.cfg"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable on this platform: {exc}")
    data = _read_manifest(path)
    data["pipeline"]["config"] = ["inputs/escaped.cfg"]
    _write_manifest(path, data)

    errors = validate_manifest(path, tmp_path)

    assert any("pipeline.config" in error and "escapes" in error for error in errors)


@pytest.mark.parametrize("version", (True, 1.0))
def test_schema_version_must_be_non_bool_integer_one(tmp_path: Path, version: object) -> None:
    path = _write_valid_manifest(tmp_path)
    data = _read_manifest(path)
    data["schema"]["version"] = version
    _write_manifest(path, data)

    errors = validate_manifest(path, tmp_path)

    assert any("schema.version" in error for error in errors)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    (
        (lambda data: data["retention"].update(extra=[]), "retention has unknown fields"),
        (lambda data: data["retention"].update(keep="summary.*"), "retention.keep"),
        (lambda data: data["provenance"].update(extra="no"), "provenance has unknown fields"),
        (lambda data: data["provenance"].update(notes=[]), "provenance.notes"),
    ),
)
def test_retention_and_provenance_nested_schema_is_exact(
    tmp_path: Path, mutation, expected: str
) -> None:
    path = _write_valid_manifest(tmp_path)
    data = _read_manifest(path)
    mutation(data)
    _write_manifest(path, data)

    errors = validate_manifest(path, tmp_path)

    assert any(expected in error for error in errors)


def test_self_replacement_cycle_is_rejected(tmp_path: Path) -> None:
    path = _write_valid_manifest(tmp_path)
    data = _read_manifest(path)
    data["lifecycle"] = "superseded"
    data["replacement"] = "manifest.json"
    _write_manifest(path, data)

    errors = validate_manifest(path, tmp_path)

    assert any("replacement cycle" in error for error in errors)


def test_two_manifest_replacement_cycle_is_rejected(tmp_path: Path) -> None:
    path = _write_valid_manifest(tmp_path)
    replacement = _write_valid_manifest(tmp_path / "replacement")
    data = _read_manifest(path)
    data["lifecycle"] = "superseded"
    data["replacement"] = "replacement/manifest.json"
    _write_manifest(path, data)
    replacement_data = _read_manifest(replacement)
    replacement_data["lifecycle"] = "superseded"
    replacement_data["replacement"] = "manifest.json"
    _write_manifest(replacement, replacement_data)

    errors = validate_manifest(path, tmp_path)

    assert any("replacement cycle" in error for error in errors)


def test_recursively_valid_replacement_is_accepted(tmp_path: Path) -> None:
    path = _write_valid_manifest(tmp_path)
    _write_valid_manifest(tmp_path / "replacement")
    data = _read_manifest(path)
    data["lifecycle"] = "superseded"
    data["replacement"] = "replacement/manifest.json"
    _write_manifest(path, data)

    assert validate_manifest(path, tmp_path) == []


def test_validation_aggregates_independent_errors(tmp_path: Path) -> None:
    path = _write_valid_manifest(tmp_path)
    data = _read_manifest(path)
    data["schema"]["version"] = True
    data["lifecycle"] = "invalid"
    data["pipeline"].pop("plot")
    data["evidence"] = ["evidence/missing.md"]
    data["retention"].update(extra=[])
    _write_manifest(path, data)

    errors = validate_manifest(path, tmp_path)

    for expected in ("schema.version", "pipeline", "evidence", "retention", "exclusion_reason"):
        assert any(expected in error for error in errors)
