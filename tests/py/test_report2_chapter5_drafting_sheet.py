from scripts.regression import report2_chapter5_drafting_sheet as sheet


def test_drafting_sheet_is_source_gated_and_status_aware():
    payload = sheet.build()
    assert payload["gate"]["pass"]
    assert len(payload["facts"]) >= 40
    assert len(payload["mca_status"]) == 16
    assert {row["status"] for row in payload["mca_status"]} == {
        "report-grade", "provisional-reduced-scope", "reduced-scope-provenance",
        "validation", "blocked"
    }
    assert any(row["task"] == "5.8" and row["status"] == "negative-result" for row in payload["facts"])
    assert any(row["metric"] == "complete_same_grid_precision_cells" and row["value"] == 12
               for row in payload["facts"])
    build_rows = [row for row in payload["facts"] if row["task"] == "5.4"]
    assert len(build_rows) == 24
    assert all(row["status"] == "report-grade" and "MSVC 19.51.36248.0" in row["scope"]
               for row in build_rows)
    assert sum(row["metric"] == "rho_linf_optimisation" and row["value"] == 0.0
               for row in build_rows) == 4
    pair_rows = [row for row in payload["facts"] if row["subject"] == "Orszag--Tang HLLD 512"]
    assert pair_rows and all("steps=3277" in row["scope"] for row in pair_rows)
