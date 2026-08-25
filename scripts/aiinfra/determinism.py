"""Repeat-sampled determinism measurement: unique output count and reproduction rate."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

import numpy as np

from scripts.aiinfra.backends.base import Backend, GenerationRequest, WorkloadFailure
from scripts.aiinfra.config import WorkloadConfig
from scripts.harness.contracts import FailureCategory


# One discarded warm-up call per cell, matching experiments/week18/kh_solver_timing
# ("warmups_per_group": 1). Its latency and its digest are both dropped: a cold-start
# difference belongs to the loading path, not to inference nondeterminism.
WARMUP_CALLS = 1


def digest_output(text: str) -> str:
    """Digest of the measured sequence. The unit is one batch position, not the batch."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _median_iqr(values: list[float]) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    return (
        float(np.median(array)),
        float(np.percentile(array, 75) - np.percentile(array, 25)),
    )


def measure_cells(backend: Backend, config: WorkloadConfig) -> list[dict[str, Any]]:
    """One cell per batch size; each cell repeats the same request `config.repeats` times.

    The measured unit is batch position 0, so batch size is the only variable that moves
    between cells. Both the unique-output count (the headline statistic) and the
    reproduction rate (the fallback when the phenomenon is intermittent) are reported.
    Each cell discards WARMUP_CALLS leading calls before counting.
    """
    cells: list[dict[str, Any]] = []
    for batch_size in config.batch_sizes:
        digests: list[str] = []
        latencies: list[float] = []
        request = GenerationRequest(
            prompt=config.prompt,
            batch_size=batch_size,
            max_new_tokens=config.max_new_tokens,
            seed=config.seed,
            dtype=config.dtype,
        )
        try:
            for _warmup in range(WARMUP_CALLS):
                backend.generate(request)
            for _repeat in range(config.repeats):
                result = backend.generate(request)
                digests.append(digest_output(result.texts[0]))
                latencies.append(result.latency_s)
        except WorkloadFailure:
            raise
        except Exception as exc:
            raise WorkloadFailure(
                FailureCategory.INFRASTRUCTURE.value,
                f"backend failed for batch_size={batch_size}: {exc}",
            ) from exc
        median, iqr = _median_iqr(latencies)
        modal_count = Counter(digests).most_common(1)[0][1]
        cells.append(
            {
                "cell_id": f"batch_size={batch_size}",
                "axes": {"batch_size": batch_size},
                "repeats": config.repeats,
                "unique_output_count": len(set(digests)),
                "reproduction_rate": modal_count / config.repeats,
                "output_digests": digests,
                "latency_median_s": median,
                "latency_iqr_s": iqr,
            }
        )
    return cells
