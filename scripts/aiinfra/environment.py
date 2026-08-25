#!/usr/bin/env python3
"""Read-only environment probe. Installs nothing, downloads nothing, never raises."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.harness.runner import git_provenance


REPO_ROOT = Path(__file__).resolve().parents[2]
NVIDIA_SMI_TIMEOUT_S = 10.0


def _error(exc: BaseException) -> dict[str, str]:
    return {"error": f"{type(exc).__name__}: {exc}"}


def _safe_probe(component: Callable[[], Any]) -> Any:
    try:
        return component()
    except BaseException as exc:
        return _error(exc)


def _probe_module(name: str) -> dict[str, Any]:
    try:
        module = __import__(name)
    except BaseException as exc:
        return {"available": False, "reason": f"{type(exc).__name__}: {exc}"}
    return {"available": True, "version": str(getattr(module, "__version__", "unknown"))}


def _probe_torch() -> dict[str, Any]:
    probe = _probe_module("torch")
    if not probe["available"]:
        return probe
    try:
        import torch

        probe["cuda_version"] = str(torch.version.cuda)
        probe["cuda_available"] = bool(torch.cuda.is_available())
        probe["device_count"] = int(torch.cuda.device_count()) if probe["cuda_available"] else 0
    except BaseException as exc:
        probe["cuda_probe_error"] = f"{type(exc).__name__}: {exc}"
    return probe


def _probe_devices() -> list[dict[str, str]]:
    try:
        output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version,compute_cap",
                "--format=csv,noheader",
            ],
            text=True,
            timeout=NVIDIA_SMI_TIMEOUT_S,
            stderr=subprocess.DEVNULL,
        )
    except BaseException as exc:
        return [_error(exc)]

    devices = []
    for line in output.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) == 4:
            devices.append(
                {
                    "name": parts[0],
                    "memory_total": parts[1],
                    "driver_version": parts[2],
                    "compute_capability": parts[3],
                }
            )
    return devices


def _platform_probe() -> dict[str, str]:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
    }


def _python_probe() -> dict[str, str]:
    return {"version": platform.python_version(), "executable": sys.executable}


def _container_digest() -> str:
    return os.environ.get("AIINFRA_CONTAINER_DIGEST", "none")


def probe() -> dict[str, Any]:
    """Collect machine provenance for a run record; this function never raises."""
    return {
        "platform": _safe_probe(_platform_probe),
        "python": _safe_probe(_python_probe),
        "container_digest": _safe_probe(_container_digest),
        "torch": _safe_probe(_probe_torch),
        "vllm": _safe_probe(lambda: _probe_module("vllm")),
        "devices": _safe_probe(_probe_devices),
        "git": _safe_probe(lambda: git_provenance(REPO_ROOT)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the probe as JSON")
    args = parser.parse_args()
    document = probe()
    if args.json:
        json.dump(document, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        for key, value in sorted(document.items()):
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
