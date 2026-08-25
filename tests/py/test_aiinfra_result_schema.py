from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.harness.artifacts import ArtifactValidationError, validate_artifact


def _document() -> dict:
    from scripts.aiinfra import result_schema

    return result_schema.build_workload_result(
        workload="determinism",
        backend={"name": "fake", "version": "0", "requested_path": "fake", "effective_path": "fake"},
        model={"id": "fake/tiny", "revision": "0000000", "dtype": "float32"},
        environment={"container_digest": "none", "python": "3.12.10", "device": "cpu"},
        cells=[
            {
                "cell_id": "batch=1",
                "axes": {"batch_size": 1},
                "repeats": 4,
                "unique_output_count": 1,
                "reproduction_rate": 1.0,
                "output_digests": ["ab12", "ab12", "ab12", "ab12"],
                "latency_median_s": 0.01,
                "latency_iqr_s": 0.0,
            }
        ],
        completed=4,
        expected=4,
    )


def test_builder_produces_a_document_that_validates() -> None:
    from scripts.aiinfra import result_schema

    result_schema.validate_workload_result(_document())


def test_completed_below_expected_is_rejected() -> None:
    from scripts.aiinfra import result_schema

    document = _document()
    document["completion"]["completed"] = 3
    with pytest.raises(ValueError, match="completion"):
        result_schema.validate_workload_result(document)


def test_zero_completion_is_rejected_for_a_nonempty_result() -> None:
    """A result with measured cells cannot claim a zero-unit successful completion."""
    from scripts.aiinfra import result_schema

    document = _document()
    document["completion"] = {"completed": 0, "expected": 0}

    with pytest.raises(ValueError, match="completion"):
        result_schema.validate_workload_result(document)


def test_unexpected_top_level_field_is_rejected() -> None:
    from scripts.aiinfra import result_schema

    document = _document()
    document["surprise"] = 1
    with pytest.raises(ValueError, match="unexpected"):
        result_schema.validate_workload_result(document)


def test_unique_output_count_must_agree_with_the_digests() -> None:
    from scripts.aiinfra import result_schema

    document = _document()
    document["cells"][0]["output_digests"] = ["ab12", "cd34", "ef56", "gh78"]
    with pytest.raises(ValueError, match="unique_output_count"):
        result_schema.validate_workload_result(document)


def test_reproduction_rate_must_agree_with_the_modal_digest_frequency() -> None:
    """Two each of ``a`` and ``b`` reproduce at a hand-derived rate of 2 / 4."""
    from scripts.aiinfra import result_schema

    document = _document()
    document["cells"][0].update(
        {
            "output_digests": ["a", "a", "b", "b"],
            "unique_output_count": 2,
            "reproduction_rate": 1.0,
        }
    )

    with pytest.raises(ValueError, match="reproduction_rate"):
        result_schema.validate_workload_result(document)


def test_non_finite_latency_is_rejected() -> None:
    from scripts.aiinfra import result_schema

    document = _document()
    document["cells"][0]["latency_median_s"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        result_schema.validate_workload_result(document)


def test_non_string_digest_is_rejected_as_an_invalid_digest() -> None:
    from scripts.aiinfra import result_schema

    document = _document()
    document["cells"][0]["output_digests"] = [{}, {}, {}, {}]
    with pytest.raises(ValueError, match="output_digests"):
        result_schema.validate_workload_result(document)


def test_artifact_validator_accepts_a_valid_result_file(tmp_path: Path) -> None:
    path = tmp_path / "workload_result.json"
    path.write_text(json.dumps(_document()), encoding="utf-8")

    validate_artifact(path, "workload_result")


def test_artifact_validator_rejects_malformed_json(tmp_path: Path) -> None:
    path = tmp_path / "workload_result.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(ArtifactValidationError):
        validate_artifact(path, "workload_result")
