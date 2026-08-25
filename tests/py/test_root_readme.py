from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "README.md"


def _readme() -> str:
    return README.read_text(encoding="utf-8")


def _summary(path: str) -> dict:
    return json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))


def _measured_result_bullets(text: str) -> list[str]:
    section = text.split("## Three measured results\n\n", maxsplit=1)[1].split(
        "\n## ", maxsplit=1
    )[0]
    bullets = re.findall(r"(?ms)^- (.*?)(?=^- |\Z)", section)
    return [re.sub(r"\s+", " ", bullet).strip() for bullet in bullets]


def test_readme_exists_and_links_the_three_entry_points() -> None:
    text = _readme()

    for link in ("docs/INDEX.md", "docs/HARNESS.md", "docs/aiinfra/PLAN.md"):
        assert link in text, f"root README must link {link}"


def test_readme_locks_all_presented_fma_results_to_the_summary() -> None:
    """Catch a README claim that diverges from the FMA evidence packet."""
    text = _readme()
    first_result, second_result, _ = _measured_result_bullets(text)
    fma = _summary("experiments/week20/gpu_fma_contraction/summary.json")
    off_rows = [row for row in fma["rows"] if row["fma_contraction"] == "off"]
    on_rows = {
        (row["case"], row["precision"]): row
        for row in fma["rows"]
        if row["fma_contraction"] == "on"
    }

    assert len(off_rows) == 4
    assert all(row["ulp_max"] == 0 for row in off_rows)
    assert all(row["bitwise_identical"] for row in off_rows)
    assert {row["nvcc_flag"] for row in off_rows} == {"--fmad=false"}
    for expected in (
        "--fmad=false",
        f"all {len(off_rows)} measured CPU/GPU pairs",
        "bit-identical",
        f"ulp_max = {max(row['ulp_max'] for row in off_rows)}",
    ):
        assert expected in first_result

    ot = on_rows[("orszag_tang_2d", "float")]
    brio = on_rows[("brio_wu_1d", "float")]
    assert ot["nvcc_flag"] == brio["nvcc_flag"] == "--fmad=true"
    for expected in ("--fmad=true", "fp32", "L-infinity"):
        assert expected in second_result
    assert re.search(
        rf"`?{ot['rho_linf_abs']:.3e}`? for Orszag--Tang", second_result
    )
    assert re.search(
        rf"`?{brio['rho_linf_abs']:.3e}`? for Brio--Wu", second_result
    )


def test_readme_locks_all_presented_openmp_results_to_the_summary() -> None:
    """Catch a README thread or speed-up value that differs from the summary."""
    text = _readme()
    _, _, third_result = _measured_result_bullets(text)
    omp = _summary("experiments/week21/euler_openmp_thread_axis/summary.json")
    fp64 = next(group for group in omp["groups"] if group["precision"] == "double")
    rows = fp64["rows"]
    thread_counts = [row["threads"] for row in rows]
    eight_thread = next(row for row in rows if row["threads"] == max(thread_counts))

    assert omp["all_thread_counts_bitwise_identical"]
    assert all(row["ulp_max"] == 0 and row["bitwise_identical"] for row in rows)
    assert thread_counts == [1, 2, 4, 8]
    for expected in (
        "1, 2, 4, and 8 threads",
        "bit-identical",
        "fp64",
        f"{max(thread_counts)}-thread row reaches",
    ):
        assert expected in third_result
    assert re.search(
        rf"`?{eight_thread['speedup_over_one_thread']:.2f}x`? over one thread",
        third_result,
    )


def test_readme_uses_one_tracked_figure_with_matching_alt_text() -> None:
    text = _readme()
    images = re.findall(r"!\[([^]]+)\]\(([^)]+\.png)\)", text)

    assert images == [
        (
            "Matched CPU/GPU timing repeats and density L-infinity discrepancy after relaxing device math",
            "experiments/week18/report2_publication_figures/fig_hardware_reproducibility.png",
        )
    ]
    tracked = subprocess.run(
        ["git", "ls-files", "--", images[0][1]],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    assert tracked == [images[0][1]]


def test_readme_does_not_repeat_the_unsupported_precision_comparison() -> None:
    """No committed summary supports a comparison with halving working precision."""
    assert not re.search(r"halv\w*\s+the\s+working\s+precision", _readme(), re.IGNORECASE)


def test_readme_states_the_distributed_scope_honestly() -> None:
    text = _readme().lower()

    assert "no multi-node gpu" in text
    assert "intra-node" in text


def test_readme_does_not_link_retired_directories() -> None:
    text = _readme()

    for retired in ("docs/superpowers/", "report1/", "report2/", "docs/week"):
        assert retired not in text, f"root README must not link retired path {retired}"
