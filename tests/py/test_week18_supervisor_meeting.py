from __future__ import annotations

import re
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ENGLISH = ROOT / "docs" / "week18" / "week18-supervisor-meeting-EN.md"
CHINESE = ROOT / "docs" / "week18" / "week18-supervisor-meeting-ZH.md"
METHODS_EN = ROOT / "docs" / "week18" / "week18-metrics-methods-EN.md"
METHODS_ZH = ROOT / "docs" / "week18" / "week18-metrics-methods-ZH.md"


def test_bilingual_reports_follow_week14_content_form():
    english = ENGLISH.read_text(encoding="utf-8")
    chinese = CHINESE.read_text(encoding="utf-8")

    for heading in (
        "## One-line summary",
        "## What we actually did",
        "## The figures: how to read them, what they show",
        "## What we can tell the supervisor (and what we won't)",
        "## Next steps",
        "## References",
    ):
        assert heading in english
    for heading in (
        "## 一句话总结",
        "## 我们实际完成的工作",
        "## 图应该如何阅读、它们说明了什么",
        "## 可以向导师说明什么（以及不能说明什么）",
        "## 下一步",
        "## 参考文献",
    ):
        assert heading in chinese


def test_bilingual_reports_preserve_full_kh_mca_boundary():
    for path in (ENGLISH, CHINESE):
        text = path.read_text(encoding="utf-8")
        assert "256^2" in text
        assert "t=1.0" in text
        assert "N=30" in text
        assert "unclaimed" in text.lower() or "不作结论" in text


def test_reports_share_figure_order_and_headline_values():
    english = ENGLISH.read_text(encoding="utf-8")
    chinese = CHINESE.read_text(encoding="utf-8")
    figure_names = (
        "fig_w17_axis_synthesis.png",
        "hardware_repeats.png",
        "thread_repro.png",
        "kh_cfl.png",
        "fig_w16_kh_precision_mca_boundary.png",
        "temporal_divergence.png",
        "fig_w17_gates_and_boundaries.png",
        "csc_mca_precision_triangulation.png",
        "csc_mca_cost_feasibility.png",
        "kh_solver_precision_timing.png",
    )

    assert [english.index(name) for name in figure_names] == sorted(
        english.index(name) for name in figure_names
    )
    assert [chinese.index(name) for name in figure_names] == sorted(
        chinese.index(name) for name in figure_names
    )
    for value in ("6.17", "5.92", "4.68e-6", "7.20e-6", "30.615", "0.0293", "34.484", "29.196", "39.542", "34.254", "1.181", "1.154"):
        assert value in english
        assert value in chinese


def test_report_figure_paths_exist():
    for document in (ENGLISH, CHINESE):
        text = document.read_text(encoding="utf-8")
        paths = re.findall(r"`((?:experiments|docs)/[^`]+\.png)`", text)
        assert len(paths) >= 7
        for relative in paths:
            assert (ROOT / relative).is_file(), relative


def test_reports_name_machine_readable_authorities():
    for document in (ENGLISH, CHINESE):
        text = document.read_text(encoding="utf-8")
        assert "experiments/week18/supplemental/hardware_repeats/summary.json" in text
        assert "experiments/week18/supplemental/thread_repro/summary.json" in text
        assert "experiments/week18/supplemental/kh_cfl/summary.json" in text
        assert "experiments/week18/kh_solver_timing/summary.json" in text
        assert "docs/experiment_logs/report2_evidence_map.md" in text


def test_headline_numbers_are_formatted_from_week18_summaries():
    hardware = json.loads(
        (
            ROOT
            / "experiments/week18/supplemental/hardware_repeats/summary.json"
        ).read_text(encoding="utf-8")
    )
    cfl = json.loads(
        (
            ROOT / "experiments/week18/supplemental/kh_cfl/summary.json"
        ).read_text(encoding="utf-8")
    )
    hardware_groups = {
        (row["case"], row["precision"]): row for row in hardware["groups"]
    }
    hll = [
        row["Linf_rho_fp32_vs_fp64"]
        for row in cfl["groups"]
        if row["solver"] == "hll"
    ]
    hlld = [
        row["Linf_rho_fp32_vs_fp64"]
        for row in cfl["groups"]
        if row["solver"] == "hlld"
    ]
    expected = (
        f"{hardware_groups[('orszag_tang_2d', 'double')]['speedup_median']:.2f}",
        f"{hardware_groups[('orszag_tang_2d', 'float')]['speedup_median']:.2f}",
        f"{max(hll):.2e}".replace("e-0", "e-"),
        f"{max(hlld):.2e}".replace("e-0", "e-"),
    )

    for document in (ENGLISH, CHINESE):
        text = document.read_text(encoding="utf-8")
        for value in expected:
            assert value in text


def test_reports_include_csc_native_smoke_and_matched_local_boundary():
    for document in (ENGLISH, CHINESE):
        text = document.read_text(encoding="utf-8")
        assert "csc_mca_precision_triangulation.png" in text
        assert "csc_mca_cost_feasibility.png" in text
        assert "experiments/week18/csc_findings_synthesis/summary.json" in text
        assert "N=4" in text
        assert "2.71e8" in text
        assert "4.24e8" in text
        assert "0.20" in text
        assert "2.18" in text
        assert "existing Apptainer job runs full" not in text

def test_metric_method_appendices_define_formula_rationale_and_boundaries():
    required = (
        "L_{1,mean}",
        "L_\\infty",
        "ULP",
        "spread_q",
        "SNR_q",
        "IQR",
        "divB_max",
        "Gate pass",
    )
    for document in (METHODS_EN, METHODS_ZH):
        text = document.read_text(encoding="utf-8")
        for token in required:
            assert token in text
        assert "mhd_fields.py" in text
        assert "error_norms.hpp" in text


def test_kh_timing_report_numbers_match_machine_readable_summary():
    payload = json.loads(
        (ROOT / "experiments/week18/kh_solver_timing/summary.json").read_text(
            encoding="utf-8"
        )
    )
    groups = {(row["solver"], row["precision"]): row for row in payload["groups"]}
    expected = [
        f"{groups[(solver, precision)]['wall_time_median_s']:.3f}"
        for solver in ("hll", "hlld")
        for precision in ("double", "float")
    ]
    expected += [
        f"{payload['comparisons']['fp32_speedup']['hll']:.3f}",
        f"{payload['comparisons']['fp32_speedup']['hlld']:.3f}",
    ]
    for document in (ENGLISH, CHINESE):
        text = document.read_text(encoding="utf-8")
        for value in expected:
            assert value in text

def test_reports_include_current_problem_impact_and_decision_section():
    english = ENGLISH.read_text(encoding="utf-8")
    chinese = CHINESE.read_text(encoding="utf-8")

    assert "## Current problems, impact, and decisions" in english
    assert "## 当前问题、影响与处理决定" in chinese
    for token in (
        "256^2",
        "N=30",
        "N=4",
        "417",
        "mca_int",
        "CFL 0.4",
        "and 0.2",
        "sum*dx",
        "Linf",
        "negative result",
    ):
        assert token in english
    for token in (
        "256^2",
        "N=30",
        "N=4",
        "417",
        "mca_int",
        "CFL 0.4",
        "和 0.2",
        "sum*dx",
        "Linf",
        "负结果",
    ):
        assert token in chinese