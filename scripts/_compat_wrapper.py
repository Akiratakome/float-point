from __future__ import annotations

from pathlib import Path
from typing import MutableMapping


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "docs" / "INDEX.md").is_file() and (candidate / "scripts").is_dir():
            return candidate
    raise RuntimeError(f"Could not find repository root from {start}")


def exec_archived(relative_archive_path: str, old_file: str, namespace: MutableMapping[str, object]) -> None:
    old_path = Path(old_file).resolve()
    repo_root = _find_repo_root(old_path)
    archive_path = repo_root / "scripts" / "provenance" / relative_archive_path
    if not archive_path.is_file():
        raise FileNotFoundError(f"Archived script not found: {archive_path}")

    source = archive_path.read_text(encoding="utf-8")
    namespace["__file__"] = str(old_path)
    namespace["__cached__"] = None
    namespace["_ARCHIVED_SOURCE"] = str(archive_path)
    code = compile(source, str(archive_path), "exec")
    exec(code, namespace)
