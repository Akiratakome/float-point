#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def aggregate(summary_paths: list[Path], output: Path) -> dict[str, Any]:
    summaries: list[dict[str, Any]] = []
    for path in summary_paths:
        summaries.append(
            {
                "source": str(path),
                "payload": json.loads(path.read_text(encoding="utf-8")),
            }
        )
    combined = {
        "summary_count": len(summaries),
        "summaries": summaries,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")
    return combined


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Combine harness summary JSON files.")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("summaries", nargs="+", type=Path)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    aggregate(args.summaries, args.output)


if __name__ == "__main__":
    main()
