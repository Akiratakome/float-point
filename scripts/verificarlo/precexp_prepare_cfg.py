from __future__ import annotations

import argparse
from pathlib import Path


def replace_or_append_cfg_line(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or "=" not in line:
            out.append(line)
            continue
        lhs = line.split("=", 1)[0].strip()
        if lhs == key:
            out.append(f"{key} = {value}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{key} = {value}")
    return "\n".join(out) + "\n"


def materialise_cfg(source: Path, target: Path, grid: Path) -> None:
    text = source.read_text(encoding="utf-8")
    text = replace_or_append_cfg_line(text, "output_format", "binary")
    text = replace_or_append_cfg_line(text, "output_file", str(grid))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--grid", type=Path, required=True)
    args = parser.parse_args()
    materialise_cfg(args.source, args.output, args.grid)


if __name__ == "__main__":
    main()
