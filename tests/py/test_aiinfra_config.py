from __future__ import annotations

import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write(tmp_path: Path, **overrides: object) -> Path:
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
    return path


def test_valid_config_round_trips(tmp_path: Path) -> None:
    from scripts.aiinfra import config

    loaded = config.load_workload_config(_write(tmp_path))

    assert loaded.workload == "determinism"
    assert loaded.batch_sizes == (1, 8)
    assert loaded.decode == "greedy"


@pytest.mark.parametrize(
    ("overrides", "expected"),
    (
        ({"decode": "sampling"}, "decode"),
        ({"repeats": 0}, "repeats"),
        ({"batch_sizes": []}, "batch_sizes"),
        ({"batch_sizes": [0]}, "batch_sizes"),
        ({"max_new_tokens": -1}, "max_new_tokens"),
        ({"prompt": ""}, "prompt"),
        ({"dtype": []}, "dtype"),
        ({"decode": []}, "decode"),
        ({"schema": {"name": "aiinfra.workload-config", "version": 2}}, "schema"),
    ),
)
def test_invalid_configs_fail_closed(
    tmp_path: Path, overrides: dict[str, object], expected: str
) -> None:
    from scripts.aiinfra import config

    with pytest.raises(ValueError, match=expected):
        config.load_workload_config(_write(tmp_path, **overrides))


def test_unknown_field_is_rejected(tmp_path: Path) -> None:
    from scripts.aiinfra import config

    with pytest.raises(ValueError, match="unexpected"):
        config.load_workload_config(_write(tmp_path, surprise=1))


@pytest.mark.parametrize("constant", ("NaN", "Infinity", "-Infinity"))
def test_non_standard_json_constants_are_rejected(tmp_path: Path, constant: str) -> None:
    """Do not allow non-finite values to enter an otherwise extensible options map."""
    from scripts.aiinfra import config

    path = _write(tmp_path)
    document = path.read_text(encoding="utf-8").replace(
        '"options": {}', f'"options": {{"poison": {constant}}}'
    )
    path.write_text(document, encoding="utf-8")

    with pytest.raises(ValueError, match="non-standard JSON constant"):
        config.load_workload_config(path)


def test_committed_model_pins_load_and_resolve(tmp_path: Path) -> None:
    from scripts.aiinfra import config

    pins = config.load_model_pins(REPO_ROOT / "configs" / "aiinfra" / "models.json")
    resolved = config.resolve_model(config.load_workload_config(_write(tmp_path)), pins)

    assert set(resolved) == {"id", "revision", "dtype"}
    assert resolved["id"] == "fake/tiny"
    assert resolved["dtype"] == "float32"


def test_unknown_model_key_fails_closed(tmp_path: Path) -> None:
    from scripts.aiinfra import config

    pins = config.load_model_pins(REPO_ROOT / "configs" / "aiinfra" / "models.json")
    loaded = config.load_workload_config(_write(tmp_path, model="not-pinned"))

    with pytest.raises(ValueError, match="not-pinned"):
        config.resolve_model(loaded, pins)
