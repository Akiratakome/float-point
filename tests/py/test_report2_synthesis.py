import json
import subprocess
import sys
from pathlib import Path

import scripts.regression.report2_synthesis as synthesis
from scripts.regression.report2_synthesis import SOURCE_SUMMARIES, build_synthesis


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "regression" / "report2_synthesis.py"


def test_source_summaries_are_tracked_and_exist():
    assert "hardware_axis" in SOURCE_SUMMARIES
    assert "temporal_divergence" in SOURCE_SUMMARIES
    assert "kh_hll_precision" in SOURCE_SUMMARIES
    for relative_path in SOURCE_SUMMARIES.values():
        assert (ROOT / relative_path).is_file(), relative_path


def test_git_commit_falls_back_to_unknown_without_git_metadata(monkeypatch, tmp_path):
    def raise_missing_git(*args, **kwargs):
        raise subprocess.CalledProcessError(128, ["git", "rev-parse", "HEAD"])

    monkeypatch.setattr(synthesis.subprocess, "run", raise_missing_git)

    assert synthesis._git_commit(tmp_path) == "unknown"


def test_build_synthesis_preserves_week16_claim_boundaries():
    data = build_synthesis(ROOT)
    assert data["schema"] == {"name": "hrsc.report2-synthesis", "version": 1}
    assert data["gates"]["synthesis_complete"] is True
    assert data["claim_boundaries"]["kh_mca"] in {
        "blocked_environment",
        "completed",
    }
    assert data["claim_boundaries"]["asymptotic_convergence"] is False
    assert data["claim_boundaries"]["formal_lyapunov_exponent"] is False
    assert data["claim_boundaries"]["hll_gpu_scope"] == [
        "brio_wu_1d",
        "orszag_tang_2d",
    ]


def test_build_synthesis_promotes_kh_mca_when_both_solvers_completed(monkeypatch):
    def fake_load_summary(root, key):
        if key in {"kh_hll_precision", "kh_hlld_precision"}:
            return {
                "gates": {
                    "mca": {"status": "completed", "pass": True},
                    "report_grade": {"pass": True},
                }
            }
        if key == "hardware_axis":
            return {
                "gate": {"pass": True},
                "rows": [
                    {"case": "brio_wu_1d", "ulp_max": 0, "speedup_cpu_over_gpu": 0.5},
                    {"case": "brio_wu_1d", "ulp_max": 0, "speedup_cpu_over_gpu": 0.5},
                    {"case": "orszag_tang_2d", "ulp_max": 0, "speedup_cpu_over_gpu": 5.0},
                    {"case": "orszag_tang_2d", "ulp_max": 0, "speedup_cpu_over_gpu": 6.0},
                ],
            }
        if key == "ot_kh_512":
            return {
                "gates": {"all_512_gates_pass": True},
                "records": [
                    {
                        "case": "orszag_tang_2d",
                        "L1_rho": 0.1,
                        "Linf_rho": 0.2,
                        "divB_max": 1.0,
                        "gate_pass": True,
                    }
                ],
            }
        if key == "temporal_divergence":
            return {
                "gates": {"pass": True},
                "interpretation": {"observed_planned_contrast": False},
                "records": [
                    {
                        "case": "brio_wu_1d",
                        "samples": [1, 2],
                        "fit_window": [0.01, 0.1],
                        "lambda_l1": 10.0,
                        "lambda_linf": 1.0,
                    },
                    {
                        "case": "orszag_tang_2d",
                        "samples": [1, 2],
                        "fit_window": [0.1, 0.5],
                        "lambda_l1": 0.1,
                        "lambda_linf": -0.1,
                    },
                ],
            }
        return {}

    import scripts.regression.report2_synthesis as synthesis

    monkeypatch.setattr(synthesis, "load_summary", fake_load_summary)

    data = synthesis.build_synthesis(ROOT)

    assert data["gates"]["kh_mca_completed"] is True
    assert data["gates"]["kh_mca_block_recorded"] is False
    assert data["claim_boundaries"]["kh_mca"] == "completed"


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
