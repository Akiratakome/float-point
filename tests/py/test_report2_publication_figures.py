import json

from scripts.figures import report2_publication_figures as publication


def test_source_evidence_audit_passes_for_all_publication_figures():
    audit = publication.audit_sources(publication.load_data())
    assert audit
    assert all(audit.values())
    temporal = publication.load_data()["temporal"]
    assert temporal["gates"]["fit_quality_quantified"] is True


def test_publication_generator_writes_png_pdf_and_manifest(tmp_path):
    manifest = publication.generate(tmp_path)
    assert manifest["quality_gate"]["pass"] is True
    assert len(manifest["figures"]) == 7
    assert {row["importance"] for row in manifest["figures"]} == {"P0", "P1"}
    for row in manifest["figures"]:
        assert row["png_dimensions"][0] >= 1800
        assert row["png_dimensions"][1] >= 700
        assert len(row["png_sha256"]) == 64
        assert len(row["pdf_sha256"]) == 64
        assert set(row["source_sha256"]) == set(row["sources"])
        assert all(len(value) == 64 for value in row["source_sha256"].values())
    stored = json.loads((tmp_path / "figure_manifest.json").read_text(encoding="utf-8"))
    assert stored == manifest
    assert (tmp_path / "README.md").is_file()
