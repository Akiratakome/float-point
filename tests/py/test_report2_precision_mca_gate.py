import json

from scripts.regression import report2_precision_mca_gate as gate


def test_config_parser_extracts_scope_and_ignores_comments():
    parsed = gate.parse_config("test=orszag_tang\nnx=64\nny=64\nt_end=0.05 # short\ncfl=0.4\nriemann=hll\n")
    assert parsed == {"test": "orszag_tang", "nx": 64, "ny": 64, "t_end": 0.05, "cfl": 0.4, "riemann": "hll"}


def test_scope_match_detects_resolution_or_time_change():
    base = {"test": "x", "nx": 64, "t_end": 0.05}
    assert gate.scopes_match(base, dict(base))
    assert not gate.scopes_match(base, {**base, "nx": 256})
    assert not gate.scopes_match(base, {**base, "t_end": 0.5})


def test_scope_normalization_makes_default_hll_explicit():
    assert gate.normalize_scope({"nx": 800}, "hll") == {"nx": 800, "riemann": "hll"}


def test_retained_packets_have_two_same_scope_promotions():
    summary = gate.build_summary()
    assert summary["gate"]["audit_pass"] is True
    assert summary["gate"]["full_matrix_promotion_pass"] is False
    assert summary["gate"]["report_grade_rows"] == 2
    promoted = {(row["case"], row["solver"]) for row in summary["rows"] if row["promotion_pass"]}
    assert promoted == {("brio_wu_1d", "hll"), ("brio_wu_1d", "hlld")}
    assert all(len(row["sources"]) >= 85 for row in summary["rows"])
    assert all(all(source["sha256"] for source in row["sources"]) for row in summary["rows"])
    assert all(row["deterministic"]["metadata_records"] == 24 for row in summary["rows"])
    assert all(row["mca"]["metadata_records"] == 60 for row in summary["rows"])
    assert all(row["checks"]["deterministic_metadata_scope_consistent"] for row in summary["rows"])
    assert all(row["checks"]["mca_metadata_scope_consistent"] for row in summary["rows"])


def test_generated_summary_preserves_ot_scope_boundary():
    summary = json.loads(gate.DEFAULT_OUT.joinpath("summary.json").read_text(encoding="utf-8"))
    ot = [row for row in summary["rows"] if row["case"] == "orszag_tang_2d"]
    assert len(ot) == 2
    assert all(row["status"] == "provisional-reduced-scope" for row in ot)
    assert all(row["deterministic_scope"]["nx"] == 256 for row in ot)
    assert all(row["mca_scope"]["nx"] == 64 for row in ot)
