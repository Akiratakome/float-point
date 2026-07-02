import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "regression"))

import mhd_literature_validation as lit


def _cell(rho, vx, By, p, gamma):
    energy = p / (gamma - 1.0) + 0.5 * rho * vx * vx + 0.5 * By * By
    return [rho, rho * vx, 0.0, 0.0, 0.0, By, 0.0, energy, 0.0]


def _summary():
    return {
        "experiment": "week14-mhd-precision-pilot",
        "case": "brio_wu_1d",
        "solver": "hll",
        "reference": "cpu-double-O2-ieee-leq",
        "git_commit": "abc123",
        "gates": {
            "G0": {
                "pass": True,
                "all_finite": True,
                "anchor_reproduced": True,
                "schema_valid": True,
                "mca_representable": True,
            }
        },
        "deterministic": [
            {
                "variant": "cpu-double-O2-ieee-leq",
                "steps": 759,
                "divB_max": 4.441e-14,
                "finite": True,
                "is_reference": True,
            }
        ],
        "mca": {
            "p53": {"status": "completed", "n": 8, "runner": "docker"},
            "p24": {"status": "completed", "n": 8, "runner": "docker"},
        },
    }


def test_supervisor_payload_requires_docker_mca():
    payload = lit.supervisor_payload(_summary())

    assert payload["g0_pass"] is True
    assert payload["reference_steps"] == 759
    assert payload["mca"]["p53"]["runner"] == "docker"
    assert payload["mca"]["p24"]["status"] == "completed"


def test_supervisor_payload_rejects_skipped_mca():
    summary = _summary()
    summary["mca"]["p24"] = {"status": "blocked_environment", "n": 0, "runner": None}

    with pytest.raises(ValueError, match="Docker Verificarlo MCA"):
        lit.supervisor_payload(summary)


def test_profile_fields_extracts_brio_wu_primitive_fields():
    gamma = 2.0
    arr = np.array(
        [[_cell(1.0, 0.1, 1.0, 1.0, gamma), _cell(0.125, 0.0, -1.0, 0.1, gamma)]],
        dtype=np.float64,
    )
    profile = lit.profile_fields(arr, gamma=gamma, dx=0.5, xmin=0.0)

    assert np.allclose(profile["x"], [0.25, 0.75])
    assert np.allclose(profile["rho"], [1.0, 0.125])
    assert np.allclose(profile["vx"], [0.1, 0.0])
    assert np.allclose(profile["By"], [1.0, -1.0])
    assert np.allclose(profile["p"], [1.0, 0.1])


def test_render_markdown_keeps_verificarlo_as_required_evidence():
    md = lit.render_markdown(lit.supervisor_payload(_summary()))

    assert "Docker Verificarlo MCA" in md
    assert "--skip-mca" not in md
    assert "Brio & Wu (1988)" in md
    assert "Claim boundary" in md
