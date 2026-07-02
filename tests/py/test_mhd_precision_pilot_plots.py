import sys
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "figures"))
sys.path.insert(0, str(ROOT / "scripts" / "regression"))

from mhd_precision_pilot_core import (
    ANCHOR_DIVB_MAX,
    ANCHOR_STEPS,
    MCA_FIELD_KEYS,
    REFERENCE,
    assemble_summary,
    blocked_mca_block,
    schema_valid,
)


def _row(variant, precision, opt, fastmath, riemann, *, is_ref=False, linf_rho=0.0):
    return {
        "variant": variant,
        "precision": precision,
        "opt": opt,
        "fastmath": fastmath,
        "riemann": riemann,
        "finite": True,
        "rc": 0,
        "steps": ANCHOR_STEPS,
        "divB_max": ANCHOR_DIVB_MAX,
        "walltime_s": 0.01 if is_ref else 0.02,
        "is_reference": is_ref,
        "L1_rho": 0.0 if is_ref else 1.0e-4,
        "L2_rho": 0.0 if is_ref else 2.0e-4,
        "Linf_rho": 0.0 if is_ref else linf_rho,
        "L1_By": 0.0 if is_ref else 2.0e-4,
        "L2_By": 0.0 if is_ref else 3.0e-4,
        "Linf_By": 0.0 if is_ref else 4.0e-4,
        "L1_p": 0.0 if is_ref else 3.0e-4,
        "L2_p": 0.0 if is_ref else 4.0e-4,
        "Linf_p": 0.0 if is_ref else 5.0e-4,
        "L1_vx": 0.0 if is_ref else 4.0e-4,
        "L2_vx": 0.0 if is_ref else 5.0e-4,
        "Linf_vx": 0.0 if is_ref else 6.0e-4,
    }


def _completed_mca_block(scale):
    block = {
        "status": "completed",
        "reason": "ok",
        "n": 30,
        "runner": "local",
        "mca_evidence_generated": True,
    }
    block.update({key: scale for key in MCA_FIELD_KEYS})
    return block


def _summary():
    rows = [
        _row(REFERENCE, "double", "O2", False, "leq", is_ref=True),
        _row("cpu-float-O2-ieee-leq", "float", "O2", False, "leq", linf_rho=7.0e-4),
        _row("cpu-float-O2-fastmath-leq", "float", "O2", True, "leq", linf_rho=9.0e-4),
    ]
    mca = {
        "p53": _completed_mca_block(1.0e-16),
        "p24": _completed_mca_block(1.0e-7),
    }
    assert schema_valid(rows, mca) is True
    return assemble_summary(rows, mca, git_commit="deadbeef")


def _blocked_summary():
    rows = [_row(REFERENCE, "double", "O2", False, "leq", is_ref=True)]
    mca = {
        "p53": blocked_mca_block("blocked_environment", "no runner"),
        "p24": blocked_mca_block("blocked_run", "sample failed"),
    }
    assert schema_valid(rows, mca) is True
    return assemble_summary(rows, mca, git_commit="deadbeef")


def test_pilot_plot_functions_write_nonempty_pngs(tmp_path):
    from mhd_precision_pilot_plots import (
        plot_mca_noise_floor,
        plot_precision_variant_norms,
    )

    norms_path = tmp_path / "norms.png"
    mca_path = tmp_path / "mca.png"

    plot_precision_variant_norms(_summary(), norms_path)
    plot_mca_noise_floor(_summary(), mca_path)

    assert norms_path.stat().st_size > 0
    assert mca_path.stat().st_size > 0


def test_mca_noise_floor_handles_blocked_only_summary(tmp_path):
    from mhd_precision_pilot_plots import plot_mca_noise_floor

    path = tmp_path / "blocked-mca.png"
    plot_mca_noise_floor(_blocked_summary(), path)

    assert path.stat().st_size > 0


def test_mca_noise_floor_plots_only_completed_numeric_blocks(monkeypatch, tmp_path):
    import mhd_precision_pilot_plots

    summary = _blocked_summary()
    summary["mca"]["p24"] = _completed_mca_block(1.0e-7)
    observed = []

    def record_blocks(ax, names, blocks, keys):
        observed.append((tuple(names), tuple(block.get("status") for block in blocks), tuple(keys)))

    monkeypatch.setattr(mhd_precision_pilot_plots, "_plot_grouped_bars", record_blocks)
    mhd_precision_pilot_plots.plot_mca_noise_floor(summary, tmp_path / "mixed-mca.png")

    assert observed
    assert all(names == ("p24",) for names, _statuses, _keys in observed)
    assert all(statuses == ("completed",) for _names, statuses, _keys in observed)


def test_number_treats_nonfinite_as_missing():
    from mhd_precision_pilot_plots import _number

    assert _number(float("nan")) is None
    assert _number(float("inf")) is None
    assert _number(-float("inf")) is None
    assert math.isclose(_number(1.25), 1.25)
