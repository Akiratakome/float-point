from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
EVIDENCE_MAP = DOCS / "experiment_logs" / "report2_evidence_map.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_report2_evidence_map_has_required_status_and_assets():
    text = read(EVIDENCE_MAP)
    for status in (
        "report-grade",
        "provisional",
        "validation",
        "morphology-only",
        "negative-result",
        "invalid",
        "superseded",
        "deferred",
    ):
        assert f"`{status}`" in text

    required_paths = (
        "experiments/week12/brio_wu_1d/summary.md",
        "experiments/week12/mhd_2d/divb_clean/summary.md",
        "experiments/week13/hlld_divb_followup/summary.md",
        "experiments/week13/orszag_tang/paper_summary.md",
        "experiments/week13/kelvin_helmholtz/paper_summary.md",
        "experiments/week15/brio_wu_precision_pilot_p1/summary.md",
        "experiments/week15/brio_wu_precision_pilot_hlld_p1/summary.md",
        "experiments/week15/orszag_tang_precision_smoke/headline256_p1/summary.md",
        "experiments/week15/orszag_tang_precision_smoke_hlld/headline256_p1/summary.md",
        "experiments/week15/mhd_temporal_divergence/summary.md",
    )
    for relative in required_paths:
        assert relative in text
        assert (ROOT / relative).is_file()


def test_week14_to_week16_have_canonical_navigation():
    index = read(DOCS / "INDEX.md")
    for week in (14, 15, 16):
        plan = DOCS / f"week{week}" / f"week{week}-plan.md"
        summary = DOCS / f"week{week}" / f"week{week}-summary.md"
        assert plan.is_file()
        assert summary.is_file()
        assert f"week{week}/week{week}-plan.md" in index
        assert f"week{week}/week{week}-summary.md" in index

    assert "report2_evidence_map.md" in index
    assert "**Active branch**" not in index


def test_dated_meeting_material_is_not_current_status():
    snapshots = (
        DOCS / "week13" / "week13-supervisor-meeting.md",
        DOCS / "week13" / "week13-supervisor-meeting-EN.md",
        DOCS / "week14" / "week14-supervisor-meeting.md",
        DOCS / "week14" / "week14-supervisor-meeting-EN.md",
        DOCS / "week15" / "week15-supervisor-meeting.md",
        DOCS / "week15" / "week15-supervisor-meeting-EN.md",
        DOCS / "week15" / "week15-supervisor-report.md",
    )
    for path in snapshots:
        text = read(path).lower()
        assert "historical snapshot" in text
        assert "report2_evidence_map.md" in text


def test_temporal_claim_is_bounded():
    text = read(EVIDENCE_MAP)
    assert "planned OT > Brio-Wu contrast was not observed" in text
    assert "formal maximal Lyapunov exponent" in text
    assert "not claimed" in text
