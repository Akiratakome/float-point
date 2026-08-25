"""Backend interface, failure type, and the registry the workload entry point uses."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from scripts.harness.contracts import FailureCategory


@dataclass(frozen=True)
class GenerationRequest:
    prompt: str
    batch_size: int
    max_new_tokens: int
    seed: int
    dtype: str


@dataclass(frozen=True)
class GenerationResult:
    texts: tuple[str, ...]
    logits: Any | None
    latency_s: float


class WorkloadFailure(Exception):
    """A failure that must reach the run record as a structured category."""

    def __init__(self, category: str, message: str) -> None:
        valid = {member.value for member in FailureCategory}
        if category not in valid:
            raise ValueError(f"unknown failure category: {category!r}")
        super().__init__(message)
        self.category = category


class Backend(Protocol):
    def describe(self) -> dict[str, str]: ...

    def generate(self, request: GenerationRequest) -> GenerationResult: ...


def get_backend(
    name: str, *, model: Mapping[str, str], options: Mapping[str, Any]
) -> Backend:
    """Construct a backend by name. Unknown names are a capability failure, not a crash."""
    if name == "fake":
        from scripts.aiinfra.backends.fake import FakeBackend

        return FakeBackend(model=model, options=options)
    if name == "torch_eager":
        from scripts.aiinfra.backends.torch_eager import TorchEagerBackend

        return TorchEagerBackend(model=model, options=options)
    if name == "vllm_offline":
        from scripts.aiinfra.backends.vllm_offline import VllmOfflineBackend

        return VllmOfflineBackend(model=model, options=options)
    raise WorkloadFailure(
        FailureCategory.UNSUPPORTED.value, f"no backend named {name!r}"
    )
