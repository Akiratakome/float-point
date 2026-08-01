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


def parse_paper_importance(text: str) -> list[dict[str, str]]:
    lines = text.splitlines()
    header_index = next(
        index
        for index, line in enumerate(lines)
        if line.startswith("| Evidence | Paper importance |")
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
        "experiments/week16/cpu_gpu_hardware_axis/summary.md",
        "experiments/week16/kelvin_helmholtz_precision/validation/summary.md",
        "experiments/week16/kelvin_helmholtz_precision/hll_p1/summary.md",
        "experiments/week16/kelvin_helmholtz_precision/hlld_p1/summary.md",
        "experiments/week16/ot_kh_512_consolidation/summary.md",
        "experiments/week17/report2_synthesis/summary.md",
        "experiments/week18/euler_mhd_cross_system/summary.md",
        "experiments/week18/resolution_ladder/summary.md",
        "experiments/week18/precision_mca_gate/summary.md",
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
        "Week 15 Brio-Wu HLL": "`report-grade`",
        "Week 15 Brio-Wu HLLD": "`report-grade`",
        "Week 15 OT HLL": "`provisional`",
        "Week 15 OT HLLD": "`provisional`",
        "Temporal divergence": "`negative-result`",
        "GPU HLL MHD": "`validation`",
        "CPU/GPU hardware axis": "`report-grade`",
        "KH report-grade precision": "`provisional`",
        "OT/KH 512^2 consolidation": "`report-grade`",
        "Week 17 Report 2 synthesis": "`report-grade`",
        "Week 18 supplemental robustness": "`report-grade`",
        "CSC KH native MCA smoke": "`validation`",
        "KH solver/precision timing": "`report-grade`",
        "Week 18 Euler--MHD cross-system": "`report-grade`",
        "Week 20 Brio--Wu direct build semantics": "`report-grade`",
        "Week 18 MHD resolution ladder": "`report-grade`",
        "Week 18 precision/MCA scope gate": "`report-grade`",
        "Lecoanet KH linear reproduction": "`validation`",
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


def test_every_evidence_row_has_a_paper_importance_and_route():
    text = read(EVIDENCE_MAP)
    inventory = parse_evidence_inventory(text)
    importance = parse_paper_importance(text)
    inventory_names = {row["Evidence"] for row in inventory}
    by_evidence = {row["Evidence"]: row for row in importance}

    assert set(by_evidence) == inventory_names
    expected = {
        "Week 12 Brio-Wu 1D": "`P1`",
        "Week 12 2D invariance/GLM": "`P1`",
        "Week 13 HLLD divB follow-up": "`P1`",
        "Week 13 OT morphology": "`P2`",
        "Week 13 KH morphology": "`P2`",
        "Week 14 HLL MCA": "`X`",
        "Week 14 pilots/smokes": "`X`",
        "Week 15 Brio-Wu HLL": "`P1`",
        "Week 15 Brio-Wu HLLD": "`P1`",
        "Week 15 OT HLL": "`P2`",
        "Week 15 OT HLLD": "`P2`",
        "Temporal divergence": "`P0`",
        "GPU HLL MHD": "`P1`",
        "CPU/GPU hardware axis": "`P1`",
        "KH report-grade precision": "`P1`",
        "OT/KH 512^2 consolidation": "`P1`",
        "Week 17 Report 2 synthesis": "`P2`",
        "KH solver/precision timing": "`P1`",
        "CSC KH native MCA smoke": "`P1`",
        "Week 18 supplemental robustness": "`P0`",
        "Week 18 Euler--MHD cross-system": "`P0`",
        "Week 20 Brio--Wu direct build semantics": "`P1`",
        "Week 18 MHD resolution ladder": "`P0`",
        "Week 18 precision/MCA scope gate": "`P1`",
        "Lecoanet KH linear reproduction": "`P1`",
    }
    assert {name: row["Paper importance"] for name, row in by_evidence.items()} == expected
    for row in importance:
        assert row["Planned owner"]
        assert row["Manuscript use"]
        assert row["Figure decision"]

    assert "axis_ranking.png` is excluded" in text
    assert "report2_publication_figures/figure_manifest.json" in text


def test_week14_to_week17_have_canonical_navigation():
    index = read(DOCS / "INDEX.md")
    for week in (14, 15, 16, 17):
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


def test_architecture_matches_bounded_mhd_gpu_implementation():
    architecture = read(
        DOCS / "superpowers" / "specs" / "2026-07-22-project-architecture-convergence-design.md"
    )
    assert "CPU / bounded HLL GPU" in architecture
    assert "opt-in CUDA path only for `riemann=hll`" in architecture
    assert "HLLD-on-GPU is rejected" in architecture
    assert "currently supports only CPU" not in architecture
    assert (ROOT / "src" / "gpu" / "mhd_gpu_solver.cu").is_file()


def test_report2_submission_format_and_combined_wrapper_match_course_rules():
    report2 = ROOT / "report2"
    requirements = read(
        report2 / "requirements" / "submission_format_2026-07-28.md"
    )
    outline = read(report2 / "planning" / "manuscript_outline.md")
    combined = read(report2 / "submission" / "combined_submission.tex")
    checklist = read(report2 / "submission" / "release_checklist.md")
    thesis = read(report2 / "phd-thesis-template-2.4" / "thesis.tex")
    preamble = read(
        report2 / "phd-thesis-template-2.4" / "Preamble" / "preamble.tex"
    )

    for phrase in (
        "7,500 words",
        "tables, figure legends/captions, and appendices",
        "Excluded: bibliography",
        "Report 2 begins",
        "srs53@cam.ac.uk",
        "signed anti-plagiarism declaration",
    ):
        assert phrase.lower() in requirements.lower()
    for threshold in ("7,875", "7,876--8,250", "8,251--9,000", "9,001"):
        assert threshold in requirements

    assert "ReportOnePdf" in combined
    assert "ReportTwoPdf" in combined
    assert "REPORT 2 STARTS HERE" in combined
    assert combined.index("ReportOnePdf}") < combined.index("REPORT 2 STARTS HERE")
    assert combined.index("REPORT 2 STARTS HERE") < combined.rindex("ReportTwoPdf}")
    assert "standalone Report 2" in outline
    assert "Combined order is Report 1 -> Part II divider -> Report 2" in checklist
    assert thesis.index("\\maketitle") < thesis.index("Declaration/declaration")
    assert "\\onehalfspacing" in preamble


def test_signed_declaration_remains_an_external_release_input():
    report2 = ROOT / "report2"
    requirements = read(
        report2 / "requirements" / "submission_format_2026-07-28.md"
    )
    declaration = read(
        report2 / "phd-thesis-template-2.4" / "Declaration" / "declaration.tex"
    )
    assert "Do not fabricate a signature" in requirements
    assert "substantially my own work" in declaration
    assert "Signed:" not in declaration


def test_supervisor_schedule_is_reflected_in_report2_plan_and_release_gate():
    report2 = ROOT / "report2"
    schedule = read(report2 / "requirements" / "supervisor_schedule_2026-07.md")
    outline = read(report2 / "planning" / "manuscript_outline.md")
    status = read(report2 / "planning" / "drafting_status.md")
    checklist = read(report2 / "submission" / "release_checklist.md")

    for date in ("2026-07-27", "2026-07-31", "2026-08-07", "2026-08-12"):
        assert date in schedule
        assert date in outline
    assert "Past due" in schedule
    assert "past due" in outline
    assert "overdue external milestone" in status
    assert "Report 1" in schedule and "Report 2" in schedule
    assert "Reviewable Report 2 draft sent to Philip" in checklist
    assert "Final combined report" in checklist


def test_chapter4_plan_locks_report1_voice_and_skill_preflight():
    report2 = ROOT / "report2"
    plan = read(report2 / "planning" / "chapter4_writing_plan.md")
    skill_routing = read(report2 / "skills" / "README.md")
    writing_agent = read(report2 / "WRITING_AGENT.md")
    index = read(report2 / "INDEX.md")

    for relative in (
        "report1/phd-thesis-template-2.4/Chapter4/chapter4.tex",
        "report1/phd-thesis-template-2.4/Chapter5/chapter5.tex",
        "report1/phd-thesis-template-2.4/Chapter6/chapter6.tex",
        "report1/skills/scientific-writing-duke/SKILL.md",
        "report1/skills/academic-english-style/SKILL.md",
        "report1/skills/editing-academic-prose/SKILL.md",
        "report1/skills/avoiding-ai-flavor/SKILL.md",
    ):
        assert (ROOT / relative).is_file()

    for skill in (
        "scientific-writing-duke",
        "academic-english-style",
        "editing-academic-prose",
        "avoiding-ai-flavor",
    ):
        assert f"`{skill}`" in plan
        assert f"`{skill}`" in skill_routing

    assert "Report 1 Chapters 5 and 6" in skill_routing
    assert "Report 1 Chapters 5 and 6" in writing_agent
    assert "report1-context` 不得用于 C4" in plan
    assert "Do not load `report1-context`" in skill_routing
    assert "每一轮最多加载两个" in plan
    assert "drafting sheet" in plan
    assert "英式拼写" in plan
    assert "report2/skills/README.md" in index


def test_chapter4_draft_preserves_evidence_and_claim_boundaries():
    report2 = ROOT / "report2"
    chapter = read(
        report2 / "phd-thesis-template-2.4" / "Chapter4" / "chapter4.tex"
    )
    table = read(
        report2
        / "phd-thesis-template-2.4"
        / "Chapter4"
        / "chapter4_cpu_gpu_table.tex"
    )
    normalised = " ".join(chapter.split())

    assert "TODO" not in chapter
    assert chapter.count("\\section{") == 7
    assert "all 24 planned runs and all eight three-grid groups completed" in normalised
    assert "failed numerically" not in chapter
    assert "fitted rate of 2.193" not in chapter
    assert "32.0\\%" not in chapter
    assert "Precision separation with refinement" not in chapter
    assert "do not establish an asymptotic regime" in chapter
    assert "does not cover HLLD, Kelvin--Helmholtz, GPU MCA" in normalised
    assert "\\input{Chapter4/chapter4_cpu_gpu_table}" in chapter
    assert "speedup" not in table.lower()

    for asset in (
        "ch4_validation_refinement_glm.pdf",
        "ch4_resolution_precision.pdf",
    ):
        assert (
            report2 / "phd-thesis-template-2.4" / "Figs" / "report2" / asset
        ).is_file()

    assert not re.search(r"\bweek\d+\b|\bP[0-3]\b|\bG[01]\b", chapter)
