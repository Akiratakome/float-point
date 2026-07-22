from __future__ import annotations

import shutil
from collections.abc import Mapping
from pathlib import Path


def replace_or_append_cfg(text: str, key: str, value: str) -> str:
    out: list[str] = []
    replaced = False
    for line in text.splitlines():
        if line.strip().startswith("#") or "=" not in line:
            out.append(line)
            continue
        if line.split("=", 1)[0].strip() != key:
            out.append(line)
            continue
        comment_at = line.find("#")
        suffix = ""
        if comment_at >= 0:
            before = line[:comment_at]
            suffix = before[len(before.rstrip()):] + line[comment_at:]
        out.append(f"{key} = {value}{suffix}")
        replaced = True
    if not replaced:
        out.append(f"{key} = {value}")
    return "\n".join(out) + "\n"


def materialise_config(
    source: Path, target: Path, overrides: Mapping[str, str]
) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    if overrides:
        text = target.read_text(encoding="utf-8")
        for key, value in overrides.items():
            text = replace_or_append_cfg(text, str(key), str(value))
        target.write_text(text, encoding="utf-8")
    return target
