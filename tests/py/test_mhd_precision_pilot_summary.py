import sys
import json
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "regression"))

from mhd_precision_pilot_core import (
    REFERENCE, ANCHOR_STEPS, ANCHOR_DIVB_MAX,
    MCA_FIELD_KEYS, SUMMARY_CSV_COLUMNS,
    gate_g0, gate_g1, gate_g2, ordering_flags, assemble_summary,
    blocked_mca_block, schema_valid,
)


def _row(variant, precision, opt, fastmath, riemann, *, steps, divb, linf_rho,
         finite=True, is_ref=False):
    return {
        "variant": variant, "precision": precision, "opt": opt,
        "fastmath": fastmath, "riemann": riemann, "finite": finite, "rc": 0,
        "steps": steps, "divB_max": divb, "walltime_s": 0.01,
        "is_reference": is_ref,
        "L1_rho": 0.0 if is_ref else 0.01, "L2_rho": 0.0 if is_ref else 0.02,
        "Linf_rho": 0.0 if is_ref else linf_rho,
        "L1_By": 0.0, "L2_By": 0.0, "Linf_By": 0.0,
        "L1_p": 0.0, "L2_p": 0.0, "Linf_p": 0.0,
        "L1_vx": 0.0, "L2_vx": 0.0, "Linf_vx": 0.0,
    }


def _reference_row():
    return _row(REFERENCE, "double", "O2", False, "leq",
                steps=ANCHOR_STEPS, divb=ANCHOR_DIVB_MAX, linf_rho=0.0, is_ref=True)


def _blocked_mca():
    return {"p53": blocked_mca_block("blocked_environment", "no runner"),
            "p24": blocked_mca_block("blocked_environment", "no runner")}


def _completed_mca_block(**overrides):
    block = {
        "status": "completed", "n": 30,
        "mca_evidence_generated": True,
    }
    block.update({key: 1e-16 for key in MCA_FIELD_KEYS})
    block.update(overrides)
    return block


def test_g0_passes_on_anchor_and_finite_and_blocked_mca():
    rows = [_reference_row()]
    g0 = gate_g0(rows, _blocked_mca())
    assert g0["pass"] is True
    assert g0["anchor_reproduced"] is True
    assert g0["mca_representable"] is True
    assert g0["schema_valid"] is True


def test_schema_valid_rejects_missing_row_key():
    rows = [_reference_row()]
    bad = dict(rows[0]); bad.pop("Linf_By")
    assert schema_valid([bad], _blocked_mca()) is False
    assert gate_g0([bad], _blocked_mca())["pass"] is False


def test_schema_valid_rejects_missing_required_non_linf_row_key():
    rows = [_reference_row()]
    bad = dict(rows[0]); bad.pop("walltime_s")
    assert schema_valid([bad], _blocked_mca()) is False


def test_schema_valid_rejects_nonfinite_deterministic_metric():
    row = _reference_row()
    row["L1_rho"] = float("nan")
    assert schema_valid([row], _blocked_mca()) is False
    assert gate_g0([row], _blocked_mca())["pass"] is False


def test_schema_valid_rejects_nonzero_row_rc():
    row = _row("cpu-float-O2-ieee-leq", "float", "O2", False, "leq",
               steps=ANCHOR_STEPS, divb=ANCHOR_DIVB_MAX, linf_rho=0.0)
    row["rc"] = 1
    rows = [_reference_row(), row]
    assert schema_valid(rows, _blocked_mca()) is False
    assert gate_g0(rows, _blocked_mca())["pass"] is False


def test_schema_valid_rejects_non_bool_row_flags():
    finite_row = _row("cpu-float-O2-ieee-leq", "float", "O2", False, "leq",
                     steps=ANCHOR_STEPS, divb=ANCHOR_DIVB_MAX, linf_rho=0.0)
    finite_row["finite"] = "false"
    assert schema_valid([_reference_row(), finite_row], _blocked_mca()) is False
    assert gate_g0([_reference_row(), finite_row], _blocked_mca())["pass"] is False

    fastmath_row = _row("cpu-float-O2-fastmath-leq", "float", "O2", True, "leq",
                       steps=ANCHOR_STEPS, divb=ANCHOR_DIVB_MAX, linf_rho=0.0)
    fastmath_row["fastmath"] = "False"
    assert schema_valid([_reference_row(), fastmath_row], _blocked_mca()) is False
    assert gate_g0([_reference_row(), fastmath_row], _blocked_mca())["pass"] is False


def test_schema_valid_rejects_empty_mca():
    rows = [_reference_row()]
    assert schema_valid(rows, {}) is False
    assert gate_g0(rows, {})["pass"] is False


def test_g0_fails_when_reference_anchor_wrong():
    rows = [_row(REFERENCE, "double", "O2", False, "leq",
                 steps=700, divb=ANCHOR_DIVB_MAX, linf_rho=0.0, is_ref=True)]
    assert gate_g0(rows, _blocked_mca())["pass"] is False


def test_g0_requires_reference_variant_not_only_is_reference():
    rows = [_row("cpu-double-O2-ieee-strict", "double", "O2", False, "strict",
                 steps=ANCHOR_STEPS, divb=ANCHOR_DIVB_MAX, linf_rho=0.0, is_ref=True)]
    assert gate_g0(rows, _blocked_mca())["pass"] is False


def test_blocked_mca_block_contains_all_field_keys_with_none():
    block = blocked_mca_block("blocked_environment", "no runner")
    assert set(MCA_FIELD_KEYS) == {
        "spread_rho", "spread_By", "spread_p", "spread_vx",
        "snr_rho", "snr_By", "snr_p", "rho_mean_spread",
    }
    for key in MCA_FIELD_KEYS:
        assert block[key] is None
    assert block["status"] == "blocked_environment"
    assert block["reason"] == "no runner"
    assert block["n"] == 0
    assert block["mca_evidence_generated"] is False


def test_schema_valid_accepts_blocked_run():
    mca = {"p53": blocked_mca_block("blocked_run", "sample failed"),
           "p24": blocked_mca_block("blocked_run", "sample failed")}
    assert schema_valid([_reference_row()], mca) is True
    assert gate_g0([_reference_row()], mca)["mca_representable"] is True


def test_schema_valid_rejects_nonfinite_completed_mca():
    mca = {"p53": _completed_mca_block(spread_rho=float("nan")),
           "p24": _completed_mca_block()}
    assert schema_valid([_reference_row()], mca) is False
    assert gate_g0([_reference_row()], mca)["pass"] is False


def test_schema_valid_rejects_nonfinite_blocked_mca_metric():
    mca = _blocked_mca()
    mca["p53"]["spread_rho"] = float("nan")
    assert schema_valid([_reference_row()], mca) is False
    assert gate_g0([_reference_row()], mca)["pass"] is False


def test_g2_pending_before_depth_then_evaluated():
    assert gate_g2(_blocked_mca())["status"] == "pending_depth"
    completed = {"p53": _completed_mca_block(n=30, spread_rho=1e-16,
                                             spread_By=1e-16, spread_p=1e-16),
                 "p24": _completed_mca_block(n=30, spread_rho=1e-7,
                                             spread_By=1e-7, spread_p=1e-7)}
    g2 = gate_g2(completed)
    assert g2["status"] == "evaluated"
    assert g2["p24_float_scale"] is True


def test_g2_does_not_claim_p24_float_scale_for_incomplete_low_depth_block():
    mca = {"p53": blocked_mca_block("blocked_environment", "no runner"),
           "p24": {"status": "completed", "n": 1}}
    assert gate_g2(mca)["p24_float_scale"] is False


def test_g2_does_not_evaluate_malformed_completed_block():
    mca = {"p53": blocked_mca_block("blocked_environment", "no runner"),
           "p24": {"status": "completed", "n": 1}}
    g2 = gate_g2(mca)
    assert g2["p24_float_scale"] is False
    assert "p24" not in g2["completed_blocks"]
    assert g2["status"] == "pending_depth"


def test_g2_claims_p24_float_scale_for_schema_complete_float_scale_spread():
    mca = {"p53": blocked_mca_block("blocked_environment", "no runner"),
           "p24": _completed_mca_block(n=30, spread_rho=1e-7,
                                       spread_By=1e-7, spread_p=1e-7)}
    assert gate_g2(mca)["p24_float_scale"] is True


def test_g2_does_not_claim_p24_float_scale_for_tiny_spread():
    mca = {"p53": blocked_mca_block("blocked_environment", "no runner"),
           "p24": _completed_mca_block(n=30, spread_rho=1e-16,
                                       spread_By=1e-16, spread_p=1e-16)}
    assert gate_g2(mca)["p24_float_scale"] is False


def test_g1_reports_finite_and_anchor_status():
    g1 = gate_g1([_reference_row()])
    assert g1["all_finite"] is True
    assert g1["anchor_ok"] is True
    assert g1["ordering_flags"] == []


def test_g1_rejects_malformed_or_failed_rows():
    bad_ref = _reference_row()
    bad_ref["rc"] = 1
    assert gate_g1([bad_ref])["pass"] is False

    malformed_fastmath = _row("cpu-float-O3-fastmath-leq", "float", "O3", True, "leq",
                             steps=760, divb=1e-6, linf_rho=0.2)
    malformed_fastmath["fastmath"] = "False"
    rows = [
        _reference_row(),
        _row("cpu-float-O3-ieee-leq", "float", "O3", False, "leq",
             steps=760, divb=1e-6, linf_rho=0.5),
        malformed_fastmath,
    ]
    g1 = gate_g1(rows)
    assert g1["pass"] is False
    assert g1["ordering_flags"] == []


def test_ordering_flags_detects_fastmath_inversion():
    rows = [
        _reference_row(),
        _row("cpu-float-O3-ieee-leq", "float", "O3", False, "leq", steps=760, divb=1e-6, linf_rho=0.5),
        _row("cpu-float-O3-fastmath-leq", "float", "O3", True, "leq", steps=760, divb=1e-6, linf_rho=0.2),
    ]
    flags = ordering_flags(rows)
    assert len(flags) == 1
    assert flags[0]["axis"] == "fastmath"
    assert gate_g1(rows)["pass"] is True


def test_assemble_summary_shape_and_claims():
    rows = [_reference_row()]
    summary = assemble_summary(rows, _blocked_mca(), git_commit="deadbeef")
    assert summary["reference"] == REFERENCE
    assert summary["case"] == "brio_wu_1d" and summary["solver"] == "hll"
    assert summary["gates"]["G0"]["pass"] is True
    assert summary["gates"]["G2"]["status"] == "pending_depth"
    assert set(summary["claims"]) == {"morphology", "self_reference", "precision_noise"}
    assert summary["mca"]["p53"]["status"] == "blocked_environment"


def test_write_summaries_emits_three_files(tmp_path):
    from mhd_precision_pilot_core import (
        assemble_summary, write_summaries, REFERENCE, ANCHOR_STEPS,
        ANCHOR_DIVB_MAX, blocked_mca_block, SUMMARY_CSV_COLUMNS,
    )
    rows = [{
        "variant": REFERENCE, "precision": "double", "opt": "O2",
        "fastmath": False, "riemann": "leq", "finite": True, "rc": 0,
        "steps": ANCHOR_STEPS, "divB_max": ANCHOR_DIVB_MAX, "walltime_s": 0.01,
        "is_reference": True,
        "L1_rho": 0.0, "L2_rho": 0.0, "Linf_rho": 0.0,
        "L1_By": 0.0, "L2_By": 0.0, "Linf_By": 0.0,
        "L1_p": 0.0, "L2_p": 0.0, "Linf_p": 0.0,
        "L1_vx": 0.0, "L2_vx": 0.0, "Linf_vx": 0.0,
    }]
    mca = {"p53": blocked_mca_block("blocked_environment", "no runner"),
           "p24": blocked_mca_block("blocked_environment", "no runner")}
    summary = assemble_summary(rows, mca, git_commit="deadbeef")
    write_summaries(summary, tmp_path)
    loaded = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert loaded == summary

    csv_text = (tmp_path / "summary.csv").read_text(encoding="utf-8")
    csv_lines = csv_text.splitlines()
    assert csv_lines[0] == ",".join(SUMMARY_CSV_COLUMNS)
    csv_rows = list(csv.DictReader(csv_lines))
    assert len(csv_rows) == 1
    assert csv_rows[0]["variant"] == REFERENCE
    assert csv_rows[0]["precision"] == "double"
    assert csv_rows[0]["is_reference"] == "True"

    md = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "## G0" in md
    assert "## Deterministic variants" in md
    assert "## MCA" in md
    assert "## Ordering flags" in md
    assert "## Claim buckets" in md
    assert REFERENCE in md


def test_write_summaries_escapes_markdown_table_cells(tmp_path):
    from mhd_precision_pilot_core import assemble_summary, write_summaries

    rows = [
        _reference_row(),
        _row("bad|name", "float", "O2", False, "leq",
             steps=ANCHOR_STEPS, divb=ANCHOR_DIVB_MAX, linf_rho=0.01),
    ]
    mca = _blocked_mca()
    mca["p53"]["reason"] = "a|b\nc"
    summary = assemble_summary(rows, mca, git_commit="deadbeef")
    write_summaries(summary, tmp_path)

    md = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert "bad\\|name" in md
    assert "a\\|b c" in md
    assert "a|b\nc" not in md
