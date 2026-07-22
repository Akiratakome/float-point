import json
import subprocess
import sys
from pathlib import Path

from scripts.audit_experiments import find_nested_build_roots, tracked_experiment_paths


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "scripts" / "audit_experiments.py"
EXPECTED_ROOTS = {
    Path("experiments/week14/mhd_precision_pilot_hlld/mca/p24/build-vfc-p53"),
    Path("experiments/week14/mhd_precision_pilot_hlld/mca/p53/build-vfc-p53"),
}


def run_audit(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(AUDIT), *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )


def test_known_week14_nested_builds_are_reported_without_deletion():
    tracked = tracked_experiment_paths(ROOT)
    groups = find_nested_build_roots(tracked)
    assert set(groups) == EXPECTED_ROOTS
    assert sum(len(files) for files in groups.values()) == 36
    assert all(
        (ROOT / path).exists()
        for files in groups.values()
        for path in files
    )
    assert all(
        path.as_posix() == str(path).replace("\\", "/")
        for path in groups
        for path in [path, *groups[path]]
    )


def test_nested_build_results_are_sorted_and_marker_driven(tmp_path: Path):
    paths = [
        Path("experiments/z/build-ninja/z.txt"),
        Path("experiments/z/build-ninja/CMakeCache.txt"),
        Path("experiments/a/build-vfc-p53/CMakeFiles/rules.ninja"),
        Path("experiments/a/build-vfc-p53/result.bin"),
        Path("experiments/a/build-vfc-p53/.ninja_deps"),
    ]
    groups = find_nested_build_roots(reversed(paths))
    assert list(groups) == [
        Path("experiments/a/build-vfc-p53"),
        Path("experiments/z/build-ninja"),
    ]
    assert groups[Path("experiments/a/build-vfc-p53")] == [
        Path("experiments/a/build-vfc-p53/.ninja_deps"),
        Path("experiments/a/build-vfc-p53/CMakeFiles/rules.ninja"),
        Path("experiments/a/build-vfc-p53/result.bin"),
    ]


def test_markdown_cli_reports_candidates_without_mutating_files(tmp_path: Path):
    before = sorted(path.as_posix() for path in ROOT.rglob("*"))
    result = run_audit("--format", "markdown")
    after = sorted(path.as_posix() for path in ROOT.rglob("*"))
    assert before == after
    assert "reference audit required" in result.stdout
    assert "no deletion performed" in result.stdout
    for root in EXPECTED_ROOTS:
        assert root.as_posix() in result.stdout
    assert "Total tracked candidate files: 36" in result.stdout
    groups = find_nested_build_roots(tracked_experiment_paths(ROOT))
    assert all(
        (ROOT / path).is_file()
        for files in groups.values()
        for path in files
    )


def test_json_cli_is_reproducible_and_reports_all_candidates(tmp_path: Path):
    output = tmp_path / "audit.json"
    first = run_audit("--format", "json", "--output", str(output))
    first_data = json.loads(output.read_text(encoding="utf-8"))
    second = run_audit("--format", "json")
    second_data = json.loads(second.stdout)
    assert first_data == second_data
    assert first_data["reference_audit"] == "reference audit required"
    assert first_data["deferred_action"] == "no deletion performed"
    assert [entry["root"] for entry in first_data["candidates"]] == sorted(
        root.as_posix() for root in EXPECTED_ROOTS
    )
    assert first_data["candidate_file_count"] == 36
    assert first_data["tracked_file_count"] >= 36
    assert first.returncode == 0


def test_cli_rejects_mutating_options():
    result = subprocess.run(
        [sys.executable, str(AUDIT), "--format", "markdown", "--delete"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )
    assert result.returncode != 0
    assert "unrecognized arguments" in result.stderr
