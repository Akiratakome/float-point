from __future__ import annotations

import builtins
import json

import pytest


def test_probe_returns_a_serialisable_mapping() -> None:
    from scripts.aiinfra import environment

    probe = environment.probe()

    assert set(probe) >= {
        "platform",
        "python",
        "container_digest",
        "torch",
        "vllm",
        "devices",
        "git",
    }
    json.dumps(probe)


def test_probe_never_raises_when_torch_is_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.aiinfra import environment

    real_import = builtins.__import__

    def fail_on_torch(name: str, *args: object, **kwargs: object) -> object:
        if name.split(".")[0] in {"torch", "vllm"}:
            raise ImportError(f"blocked {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fail_on_torch)

    probe = environment.probe()

    assert probe["torch"]["available"] is False
    assert probe["vllm"]["available"] is False
    assert "blocked" in probe["torch"]["reason"]


def test_probe_never_raises_when_git_provenance_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Catch a broken git command rather than failing an otherwise useful probe."""
    from scripts.aiinfra import environment

    def broken_git_provenance(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise RuntimeError("blocked git")

    monkeypatch.setattr(environment, "git_provenance", broken_git_provenance)

    probe = environment.probe()

    assert probe["git"] == {"error": "RuntimeError: blocked git"}


def test_container_digest_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    from scripts.aiinfra import environment

    monkeypatch.setenv("AIINFRA_CONTAINER_DIGEST", "sha256:deadbeef")

    assert environment.probe()["container_digest"] == "sha256:deadbeef"
