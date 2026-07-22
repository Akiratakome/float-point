import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
EVIDENCE_MAP = DOCS / "experiment_logs" / "report2_evidence_map.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_evidence_inventory(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    header_index = next(
        index
        for index, line in enumerate(lines)
        if line.startswith("| Evidence | Status |")
    )
    headers = [cell.strip() for cell in lines[header_index].strip("|").split("|")]
    rows = []
    for line in lines[header_index + 2 :]:
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        assert len(cells) == len(headers), line
        rows.append(dict(zip(headers, cells, strict=True)))
    return rows


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


def test_evidence_inventory_binds_status_provenance_and_retention_contract():
    inventory = parse_evidence_inventory(read(EVIDENCE_MAP))
    required_columns = {
        "Evidence",
        "Status",
        "Authority and facts",
        "Supported claim",
        "Excluded claims",
        "Supersedes",
        "Provenance",
        "Retention",
    }
    assert set(inventory[0]) == required_columns

    expected_statuses = {
        "Week 12 Brio-Wu 1D": "`validation`",
        "Week 12 2D invariance/GLM": "`validation`",
        "Week 13 HLLD divB follow-up": "`validation`",
        "Week 13 OT morphology": "`morphology-only`",
        "Week 13 KH morphology": "`morphology-only`",
        "Week 14 HLL MCA": "`invalid`",
        "Week 14 pilots/smokes": "`superseded`",
        "Week 15 Brio-Wu HLL": "`provisional`",
        "Week 15 Brio-Wu HLLD": "`provisional`",
        "Week 15 OT HLL": "`provisional`",
        "Week 15 OT HLLD": "`provisional`",
        "Temporal divergence": "`negative-result`",
        "GPU HLL MHD": "`deferred`",
        "CPU/GPU hardware axis": "`deferred`",
        "KH report-grade precision": "`deferred`",
        "OT/KH 512^2 consolidation": "`deferred`",
    }
    by_evidence = {row["Evidence"]: row for row in inventory}
    assert set(by_evidence) == set(expected_statuses)
    for evidence, expected_status in expected_statuses.items():
        row = by_evidence[evidence]
        assert row["Status"] == expected_status
        for column in required_columns - {"Evidence", "Status"}:
            assert row[column], f"{evidence}: empty {column}"

    for evidence in (
        "Week 15 Brio-Wu HLL",
        "Week 15 Brio-Wu HLLD",
        "Week 15 OT HLL",
        "Week 15 OT HLLD",
    ):
        assert "N=30" in by_evidence[evidence]["Authority and facts"]

    inventory_text = "\n".join(
        " | ".join(row.values()) for row in inventory
    )
    assert not re.search(r"\b\d+\s+(?:tracked\s+)?files?\b", inventory_text, re.I)


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


def test_current_harness_and_manifest_routing_is_explicit():
    harness = read(DOCS / "HARNESS.md")
    scripts = read(ROOT / "scripts" / "README.md")
    index = read(DOCS / "INDEX.md")
    retention = read(DOCS / "experiment_logs" / "experiments_retention.md")
    cleanup = DOCS / "experiment_logs" / "experiment_cleanup_candidates.md"

    assert '{"name": "hrsc.run-record", "version": 1}' in harness
    for alias in ("raw_output", "output_binary", "elapsed_wall_s", "timing.total_s"):
        assert alias in harness
    assert "completion gate" in harness
    assert "completion.reported=true" in harness
    assert "completion.reported=false" in harness
    assert "effective math mode" in harness
    assert "Euler / GPU" in harness
    assert "MHD / GPU" in harness
    for lifecycle in ("canonical", "provenance", "superseded", "invalid", "generated"):
        assert f"`{lifecycle}`" in harness
        assert f"`{lifecycle}`" in retention
    assert "13 promoted Report 2 lifecycle manifests" in harness
    assert "13 promoted Report 2 manifests" in retention
    assert "scripts/harness/" in scripts
    assert "audit_experiments.py" in scripts
    assert "experiment_cleanup_candidates.md" in index
    assert cleanup.is_file()
