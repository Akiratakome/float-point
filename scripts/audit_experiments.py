"""Read-only discovery of tracked experiment build-directory candidates."""

from __future__ import annotations

import argparse
import datetime as _datetime
import json
import os
import subprocess
from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import Any


BUILD_MARKERS = frozenset({"CMakeCache.txt", "build.ninja", ".ninja_deps", "CMakeFiles"})


def _repo_relative(path: Path | str) -> Path:
    """Return a stable repository-relative path with POSIX separators."""

    value = path.as_posix() if isinstance(path, Path) else str(path).replace("\\", "/")
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"expected a repository-relative path: {path!r}")
    return Path(*relative.parts)


def tracked_experiment_paths(repo_root: Path) -> list[Path]:
    """List tracked files below ``experiments/`` without invoking a shell."""

    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "experiments"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    raw_paths = result.stdout.split(b"\0")
    paths = {
        _repo_relative(Path(os.fsdecode(raw_path)))
        for raw_path in raw_paths
        if raw_path
    }
    return sorted(paths, key=lambda path: path.as_posix())


def _build_root_candidates(path: Path) -> Iterable[Path]:
    parts = path.parts
    for index, name in enumerate(parts[:-1]):
        if name.lower().startswith("build"):
            yield Path(*parts[: index + 1])


def _has_build_marker(path: Path, root: Path) -> bool:
    relative_parts = path.parts[len(root.parts) :]
    return bool(relative_parts) and relative_parts[0] in BUILD_MARKERS


def find_nested_build_roots(paths: Iterable[Path]) -> dict[Path, list[Path]]:
    """Group tracked files below build-named roots that have build markers."""

    normalized = sorted({_repo_relative(path) for path in paths}, key=lambda path: path.as_posix())
    roots = {
        root
        for path in normalized
        for root in _build_root_candidates(path)
        if _has_build_marker(path, root)
    }
    grouped: dict[Path, list[Path]] = {}
    for path in normalized:
        for root in roots:
            if path.parts[: len(root.parts)] == root.parts:
                grouped.setdefault(root, []).append(path)

    return {
        root: sorted(files, key=lambda path: path.as_posix())
        for root, files in sorted(grouped.items(), key=lambda item: item[0].as_posix())
    }


def _audit_date() -> str:
    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if source_date_epoch is not None:
        return _datetime.datetime.fromtimestamp(
            int(source_date_epoch), tz=_datetime.timezone.utc
        ).date().isoformat()
    return _datetime.date.today().isoformat()


def build_report(repo_root: Path) -> dict[str, Any]:
    tracked = tracked_experiment_paths(repo_root)
    groups = find_nested_build_roots(tracked)
    candidates = [
        {"root": root.as_posix(), "files": [path.as_posix() for path in files]}
        for root, files in groups.items()
    ]
    return {
        "audit_date": _audit_date(),
        "root": ".",
        "tracked_file_count": len(tracked),
        "candidate_root_count": len(candidates),
        "candidate_file_count": sum(len(entry["files"]) for entry in candidates),
        "reference_audit": "reference audit required",
        "deferred_action": "no deletion performed",
        "candidates": candidates,
    }


def render_json(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Experiment Cleanup Candidates",
        "",
        f"- Audit date: `{report['audit_date']}`",
        f"- Root: `{report['root']}`",
        f"- Tracked experiment files: {report['tracked_file_count']}",
        f"- Candidate build roots: {report['candidate_root_count']}",
        f"- Total tracked candidate files: {report['candidate_file_count']}",
        "- Reference status: reference audit required",
        "- Deferred action: no deletion performed",
        "",
        "Candidates are reported for manual reference checking only. The audit is read-only and does not delete or move files.",
        "",
        "| Candidate root | Tracked files |",
        "|---|---:|",
    ]
    for candidate in report["candidates"]:
        lines.append(f"| `{candidate['root']}` | {len(candidate['files'])} |")
    lines.extend(["", "## Tracked Files", ""])
    for candidate in report["candidates"]:
        lines.append(f"### `{candidate['root']}`")
        lines.append("")
        lines.extend(f"- `{path}`" for path in candidate["files"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("json", "markdown"), required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    report = build_report(repo_root)
    rendered = render_json(report) if args.format == "json" else render_markdown(report)
    if args.output is None:
        print(rendered, end="")
    else:
        output = args.output if args.output.is_absolute() else repo_root / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
