import json
import subprocess
import sys
from pathlib import Path

from scripts.regression.report2_synthesis import SOURCE_SUMMARIES, build_synthesis


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "regression" / "report2_synthesis.py"


def test_source_summaries_are_tracked_and_exist():
    assert "hardware_axis" in SOURCE_SUMMARIES
    assert "temporal_divergence" in SOURCE_SUMMARIES
    assert "kh_hll_precision" in SOURCE_SUMMARIES
    for relative_path in SOURCE_SUMMARIES.values():
        assert (ROOT / relative_path).is_file(), relative_path


def test_build_synthesis_preserves_week16_claim_boundaries():
    data = build_synthesis(ROOT)
    assert data["schema"] == {"name": "hrsc.report2-synthesis", "version": 1}
    assert data["gates"]["synthesis_complete"] is True
    assert data["claim_boundaries"]["kh_mca"] == "blocked_environment"
    assert data["claim_boundaries"]["asymptotic_convergence"] is False
    assert data["claim_boundaries"]["formal_lyapunov_exponent"] is False
    assert data["claim_boundaries"]["hll_gpu_scope"] == [
        "brio_wu_1d",
        "orszag_tang_2d",
    ]


def test_axis_ranking_is_bounded_and_uses_available_evidence():
    data = build_synthesis(ROOT)
    axes = {entry["axis"]: entry for entry in data["axis_ranking"]}
    assert axes["precision"]["rank"] == 1
    assert axes["hardware"]["bounded_result"] == "bit_exact_for_covered_hll_cases"
    assert axes["hardware"]["covered_rows"] == 4
    assert axes["implementation_variant"]["status"] == "small_or_zero_in_available_packets"
    assert axes["compiler_flags"]["status"] == "bounded_cpu_deterministic_variation"


def test_cli_writes_json_csv_markdown_and_figures(tmp_path: Path):
    output = tmp_path / "synthesis"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--output-dir", str(output)],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    assert "summary.json" in result.stdout
    assert (output / "summary.json").is_file()
    assert (output / "summary.csv").is_file()
    assert (output / "summary.md").is_file()
    assert (output / "figures" / "axis_ranking.png").is_file()
    assert (output / "figures" / "temporal_divergence.png").is_file()
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["gates"]["synthesis_complete"] is True


def test_week17_docs_point_to_synthesis_packet():
    assert (ROOT / "docs/week17/week17-plan.md").is_file()
    assert (ROOT / "docs/week17/week17-summary.md").is_file()
    index = (ROOT / "docs/INDEX.md").read_text(encoding="utf-8")
    assert "week17/week17-plan.md" in index
    assert "week17/week17-summary.md" in index
    assert "experiments/week17/report2_synthesis/summary.md" in index
    harness = (ROOT / "docs/HARNESS.md").read_text(encoding="utf-8")
    assert "MHD / GPU | supported as bounded HLL correctness path" in harness
    evidence = (ROOT / "docs/experiment_logs/report2_evidence_map.md").read_text(
        encoding="utf-8"
    )
    assert "Week 17 Report 2 synthesis" in evidence
    assert "experiments/week17/report2_synthesis/summary.md" in evidence
