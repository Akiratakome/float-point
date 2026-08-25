"""A CPU-only, torch-free backend that exercises every harness path deterministically."""

from __future__ import annotations

import hashlib
import time
from collections.abc import Mapping
from typing import Any

from scripts.aiinfra.backends.base import (
    GenerationRequest,
    GenerationResult,
    WorkloadFailure,
)


VERSION = "1"
NONDETERMINISM_MODES = {"none", "batch", "repeat"}
FAULTS = {"none", "resource_exhausted", "unsupported_capability"}
# One synthetic token is eight hex characters of a SHA-256 stream; the count is the
# only thing max_new_tokens controls here, so output length tracks the request.
TOKEN_HEX_WIDTH = 8


class FakeBackend:
    """Generates reproducible pseudo-text without loading any model weights."""

    def __init__(self, *, model: Mapping[str, str], options: Mapping[str, Any]) -> None:
        self._model = dict(model)
        self._mode = str(options.get("nondeterminism", "none"))
        if self._mode not in NONDETERMINISM_MODES:
            raise WorkloadFailure(
                "configuration_error",
                f"fake backend nondeterminism must be one of {sorted(NONDETERMINISM_MODES)}",
            )
        self._fault = str(options.get("fault", "none"))
        if self._fault not in FAULTS:
            raise WorkloadFailure(
                "configuration_error", f"fake backend fault must be one of {sorted(FAULTS)}"
            )
        self._call_index = 0

    def describe(self) -> dict[str, str]:
        return {
            "name": "fake",
            "version": VERSION,
            "requested_path": f"fake:{self._mode}",
            "effective_path": f"fake:{self._mode}",
        }

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if self._fault == "resource_exhausted":
            raise WorkloadFailure(
                "resource_exhausted",
                f"fake backend refused batch_size={request.batch_size}",
            )
        if self._fault == "unsupported_capability":
            raise WorkloadFailure(
                "unsupported_capability",
                f"fake backend does not implement dtype={request.dtype}",
            )

        started = time.perf_counter()
        parts = [self._model.get("id", ""), request.prompt, str(request.seed), request.dtype]
        if self._mode == "batch":
            parts.append(f"batch={request.batch_size}")
        if self._mode == "repeat":
            parts.append(f"call={self._call_index}")
        seed_material = "|".join(parts).encode("utf-8")

        text = self._stream(seed_material, request.max_new_tokens)
        self._call_index += 1
        return GenerationResult(
            texts=tuple([text] * request.batch_size),
            logits=None,
            latency_s=time.perf_counter() - started,
        )

    @staticmethod
    def _stream(seed_material: bytes, token_count: int) -> str:
        tokens = []
        digest = hashlib.sha256(seed_material).digest()
        while len(tokens) < token_count:
            digest = hashlib.sha256(digest).digest()
            chunk = digest.hex()
            tokens.extend(
                chunk[index : index + TOKEN_HEX_WIDTH]
                for index in range(0, len(chunk), TOKEN_HEX_WIDTH)
            )
        return " ".join(tokens[:token_count])
