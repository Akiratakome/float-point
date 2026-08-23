import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHAPTER = ROOT / "report2/phd-thesis-template-2.4/Chapter5/chapter5.tex"
MCA_TABLE = ROOT / "report2/phd-thesis-template-2.4/Chapter5/chapter5_mca_table.tex"
MCA_STATUS_TABLE = ROOT / "report2/phd-thesis-template-2.4/Appendix1/chapter5_mca_status_table.tex"
FIG_DIR = ROOT / "report2/phd-thesis-template-2.4/Figs/report2"
BUILD_SUMMARY = ROOT / "experiments/week20/brio_wu_build_semantics/summary.json"
OUTLINE = ROOT / "report2/planning/manuscript_outline.md"
WRITING_PLAN = ROOT / "report2/planning/chapter5_writing_plan.md"
SCOPE_MATRIX = ROOT / "report2/planning/chapter5_result_scope_matrix.md"


def _approximate_words(text: str) -> int:
    text = re.sub(r"%.*", " ", text)
    text = re.sub(r"\\[A-Za-z@]+\*?(\[[^\]]*\])?", " ", text)
    text = re.sub(r"[{}$&_^~\\]", " ", text)
    return len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", text))


def test_chapter5_has_planned_structure_assets_and_budget():
    chapter = CHAPTER.read_text(encoding="utf-8")
    table = MCA_TABLE.read_text(encoding="utf-8")
    assert chapter.count("\\section{") == 6
    assert chapter.count("\\subsection{") == 9
    assert chapter.count("\\begin{figure}") == 7
    assert "\\input{Chapter5/chapter5_mca_table}" in chapter
    assert 2800 <= _approximate_words(chapter + "\n" + table) <= 2950
    for name in (
        "ch5_cross_system_sensitivity.pdf",
        "ch5_kh_timing.pdf",
        "ch5_hardware_reproducibility.pdf",
        "ch5_precision_refinement_context.pdf",
        "ch5_temporal_discrepancy.pdf",
        "ch5_build_semantics.pdf",
        "ch5_kh_cfl.png",
    ):
        assert (FIG_DIR / name).is_file()


def test_chapter5_retains_required_fact_and_claim_boundaries():
    chapter = CHAPTER.read_text(encoding="utf-8")
    normalised = " ".join(chapter.split())
    table = MCA_TABLE.read_text(encoding="utf-8")
    status_table = MCA_STATUS_TABLE.read_text(encoding="utf-8")
    assert "$4.21\\times10^{-16}$" in chapter
    assert "$1.311\\times10^{-6}$" in chapter
    assert "$2.608\\times10^{-6}$" in chapter
    assert "MSVC~19.51" in chapter
    assert "All groups took 1148 steps" in normalised
    assert "2.76\\times10^{-2}" in chapter
    assert "5.031\\times10^{-2}" in chapter
    assert "$-0.04223$" in chapter
    assert "Virtual p24 and p53 are not IEEE fp32 and fp64" in table
    assert "rather than an instability" in normalised
    assert "differing only in the declared axis" in normalised
    assert "\\subsection{Effective build-semantics sensitivity}" in chapter
    assert "\\subsection{CPU timing: HLL versus HLLD}" in chapter
    assert "round-off scale" not in chapter
    assert "Positive log bars show discrepancy, not accuracy" in normalised
    assert "\\citep{denisEtAl2016verificarlo}" in chapter
    for status in ("matched", "reduced", "toolchain", "validation"):
        assert status in status_table
    assert "2.12" in table and "2.46" in table


def test_chapter5_captions_and_causal_boundaries_match_plotted_statistics():
    chapter = CHAPTER.read_text(encoding="utf-8")
    normalised = " ".join(chapter.split())
    table = MCA_TABLE.read_text(encoding="utf-8")
    assert "O2-default fp32 versus fp64 (precision)" in chapter
    assert "mean-relative $L_1$ and absolute $L_\\infty$" not in chapter
    assert "Median, IQR and all $n=5$ CPU/GPU wall-time ratios" in normalised
    assert "overhead dominated" not in chapter
    assert "preregistered expectation" not in chapter
    assert "does not isolate the mechanism" in normalised
    assert "statistics are not\nequivalent" in table
    assert "p53+p24" not in table


def test_chapter5_build_semantics_values_are_bound_to_gated_summary():
    chapter = CHAPTER.read_text(encoding="utf-8")
    summary = json.loads(BUILD_SUMMARY.read_text(encoding="utf-8"))
    assert summary["gate"]["pass"] is True
    by_key = {
        (row["solver"], row["precision"], row["axis"]): row["rho_linf"]
        for row in summary["comparisons"]
    }
    expected = {
        ("hll", "double", "fast_math"): "$1.887\\times10^{-15}$",
        ("hll", "float", "fast_math"): "$1.311\\times10^{-6}$",
        ("hlld", "double", "fast_math"): "$4.413\\times10^{-15}$",
        ("hlld", "float", "fast_math"): "$1.729\\times10^{-6}$",
        ("hlld", "double", "branch_rule"): "$3.886\\times10^{-15}$",
        ("hlld", "float", "branch_rule"): "$2.608\\times10^{-6}$",
    }
    for key, rendered in expected.items():
        assert rendered in chapter
        mantissa, exponent = f"{by_key[key]:.3e}".split("e")
        assert rendered == f"${mantissa}\\times10^{{{int(exponent)}}}$"
    assert all(
        by_key[(solver, precision, "optimisation")] == 0.0
        for solver in ("hll", "hlld")
        for precision in ("double", "float")
    )


def test_chapter5_planning_assets_match_completed_direct_experiment_and_layout():
    chapter = CHAPTER.read_text(encoding="utf-8")
    outline = OUTLINE.read_text(encoding="utf-8")
    plan = WRITING_PLAN.read_text(encoding="utf-8")
    matrix = SCOPE_MATRIX.read_text(encoding="utf-8")
    assert "Week-20 direct packet" in plan
    assert "五图一表" in plan
    assert "Figure 5.5：Temporal discrepancy" in plan
    assert "completed-pending-student-signoff" in plan
    assert "独立拆轴仍为 provisional appendix context" not in plan
    assert "report-grade direct output sensitivity" in matrix
    assert "`/Ox` 对 `/O2`" in matrix
    assert "Brio--Wu direct build semantics" in outline
    assert "binary32 unit roundoff" in chapter
