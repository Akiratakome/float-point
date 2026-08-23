import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
THESIS = ROOT / "report2" / "phd-thesis-template-2.4"


def _manuscript_text() -> str:
    paths = [
        THESIS / "Abstract" / "abstract.tex",
        *(THESIS / f"Chapter{i}" / f"chapter{i}.tex" for i in range(1, 8)),
        THESIS / "Appendix1" / "appendix1.tex",
    ]
    return "\n".join(path.read_text(encoding="utf-8") for path in paths)


def test_report2_has_reviewed_bibliography_records_and_uses_every_key():
    bibliography = (THESIS / "References" / "references.bib").read_text(
        encoding="utf-8"
    )
    keys = set(re.findall(r"^@[A-Za-z]+\{([^,]+),", bibliography, re.MULTILINE))
    assert len(keys) == 38
    assert {
        "toro2009riemann",
        "liskaWendroff2003comparison",
        "vanLeer1979muscl",
        "orszagTang1979",
        "oberkampfRoy2010vv",
        "microsoftMsvcFp2021",
        "triccoPrice2012divb",
        "torrilhon2003pseudo",
    } <= keys

    cited = set()
    for group in re.findall(r"\\cite[pt]?\{([^}]+)\}", _manuscript_text()):
        cited.update(key.strip() for key in group.split(","))
    assert cited == keys


def test_report2_visual_inventory_meets_full_review_expansion():
    main = _manuscript_text()
    included_tables = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            THESIS / "Chapter4" / "chapter4_cpu_gpu_table.tex",
            THESIS / "Chapter5" / "chapter5_mca_table.tex",
            THESIS / "Appendix1" / "chapter5_mca_status_table.tex",
            THESIS / "Appendix1" / "evidence_map_table.tex",
        )
    )
    assert main.count("\\begin{figure}") == 15
    assert (main + included_tables).count("\\begin{table}") == 9

    supplementary = (
        "ch4_brio_wu_profiles.png",
        "ch4_orszag_tang_morphology.png",
        "ch4_orszag_tang_solver_comparison.png",
        "ch4_kelvin_helmholtz_morphology.png",
        "ch5_build_semantics.pdf",
        "ch5_kh_cfl.png",
    )
    figure_dir = THESIS / "Figs" / "report2"
    for name in supplementary:
        assert (figure_dir / name).is_file()
