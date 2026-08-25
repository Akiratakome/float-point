from __future__ import annotations

import json
from pathlib import Path

import pytest


def _config(tmp_path: Path, **overrides):
    from scripts.aiinfra import config

    document = {
        "schema": {"name": "aiinfra.workload-config", "version": 1},
        "workload": "determinism",
        "backend": "fake",
        "model": "fake-tiny",
        "dtype": "float32",
        "prompt": "hello",
        "max_new_tokens": 8,
        "repeats": 4,
        "batch_sizes": [1, 8],
        "seed": 0,
        "decode": "greedy",
        "options": {},
    }
    document.update(overrides)
    path = tmp_path / "workload.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return config.load_workload_config(path)


def _backend(loaded):
    from scripts.aiinfra.backends import base

    return base.get_backend(
        loaded.backend,
        model={"id": "fake/tiny", "revision": "builtin", "dtype": loaded.dtype},
        options=loaded.options,
    )


def test_deterministic_backend_gives_one_unique_output_per_cell(tmp_path: Path) -> None:
    from scripts.aiinfra import determinism

    loaded = _config(tmp_path)
    cells = determinism.measure_cells(_backend(loaded), loaded)

    assert [cell["cell_id"] for cell in cells] == ["batch_size=1", "batch_size=8"]
    assert all(cell["unique_output_count"] == 1 for cell in cells)
    assert all(cell["reproduction_rate"] == 1.0 for cell in cells)
    assert all(len(cell["output_digests"]) == 4 for cell in cells)


def test_batch_sensitive_backend_changes_the_output_across_batch_sizes(tmp_path: Path) -> None:
    from scripts.aiinfra import determinism

    loaded = _config(tmp_path, options={"nondeterminism": "batch"})
    cells = determinism.measure_cells(_backend(loaded), loaded)

    assert all(cell["unique_output_count"] == 1 for cell in cells)
    assert cells[0]["output_digests"][0] != cells[1]["output_digests"][0]


def test_repeat_sensitive_backend_reports_more_than_one_unique_output(tmp_path: Path) -> None:
    from scripts.aiinfra import determinism

    loaded = _config(tmp_path, options={"nondeterminism": "repeat"})
    cells = determinism.measure_cells(_backend(loaded), loaded)

    assert cells[0]["unique_output_count"] == 4
    assert cells[0]["reproduction_rate"] == 0.25


def test_warmup_output_is_excluded_from_repeat_measurements(tmp_path: Path) -> None:
    from scripts.aiinfra import determinism

    loaded = _config(tmp_path, repeats=1, batch_sizes=[1], options={"nondeterminism": "repeat"})
    backend = _backend(loaded)
    warmup_digest = determinism.digest_output(
        backend.generate(
            determinism.GenerationRequest(
                prompt=loaded.prompt,
                batch_size=1,
                max_new_tokens=loaded.max_new_tokens,
                seed=loaded.seed,
                dtype=loaded.dtype,
            )
        ).texts[0]
    )

    measured = determinism.measure_cells(_backend(loaded), loaded)[0]

    assert measured["output_digests"] != [warmup_digest]


def test_cells_satisfy_the_result_schema(tmp_path: Path) -> None:
    from scripts.aiinfra import determinism, result_schema

    loaded = _config(tmp_path)
    cells = determinism.measure_cells(_backend(loaded), loaded)
    assert all(set(cell) == result_schema.CELL_FIELDS for cell in cells)
    document = result_schema.build_workload_result(
        workload=loaded.workload,
        backend=_backend(loaded).describe(),
        model={"id": "fake/tiny", "revision": "builtin", "dtype": loaded.dtype},
        environment={"container_digest": "none"},
        cells=cells,
        completed=len(cells),
        expected=len(cells),
    )

    result_schema.validate_workload_result(document)


@pytest.mark.parametrize(
    ("fault", "category"),
    (("resource_exhausted", "resource_exhausted"), ("unsupported_capability", "unsupported_capability")),
)
def test_injected_faults_raise_a_categorised_workload_failure(
    tmp_path: Path, fault: str, category: str
) -> None:
    from scripts.aiinfra import determinism
    from scripts.aiinfra.backends import base

    loaded = _config(tmp_path, options={"fault": fault})
    with pytest.raises(base.WorkloadFailure) as excinfo:
        determinism.measure_cells(_backend(loaded), loaded)

    assert excinfo.value.category == category


def test_unknown_backend_is_an_unsupported_capability(tmp_path: Path) -> None:
    from scripts.aiinfra.backends import base

    loaded = _config(tmp_path, backend="does-not-exist")
    with pytest.raises(base.WorkloadFailure) as excinfo:
        _backend(loaded)

    assert excinfo.value.category == "unsupported_capability"


def test_uncategorised_backend_errors_fail_closed_as_infrastructure_failures(
    tmp_path: Path,
) -> None:
    from scripts.aiinfra import determinism
    from scripts.aiinfra.backends import base

    class ExplodingBackend:
        def generate(self, request: base.GenerationRequest) -> base.GenerationResult:
            raise RuntimeError("driver lost")

    with pytest.raises(base.WorkloadFailure) as excinfo:
        determinism.measure_cells(ExplodingBackend(), _config(tmp_path))

    assert excinfo.value.category == "infrastructure_error"


def test_backend_description_has_exact_schema_keys(tmp_path: Path) -> None:
    loaded = _config(tmp_path)

    assert set(_backend(loaded).describe()) == {
        "name",
        "version",
        "requested_path",
        "effective_path",
    }
