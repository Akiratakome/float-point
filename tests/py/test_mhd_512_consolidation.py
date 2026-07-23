import json
from pathlib import Path

from scripts.regression import mhd_512_consolidation as mod


def _summary(path: Path, l1: float, divb: float, gates: tuple[bool, bool, bool]) -> None:
    path.write_text(
        json.dumps(
            {
                "experiment": path.stem,
                "git_commit": "abc123",
                "results": {
                    "L1_rho": l1,
                    "L2_rho": l1 * 2,
                    "Linf_rho": l1 * 3,
                    "mass_rel": 0.0,
                    "divB_max_cr018": divb,
                    "gate_norms": gates[0],
                    "gate_mass": gates[1],
                    "gate_divb": gates[2],
                },
            }
        ),
        encoding="utf-8",
    )


def test_collect_case_preserves_gate_boundaries(tmp_path):
    summary = tmp_path / "summary.json"
    _summary(summary, 0.1, 0.2, (True, False, True))

    record = mod.collect_case("ot", summary)

    assert record["case"] == "ot"
    assert record["gate_pass"] is False
    assert record["gate_mass"] is False
    assert record["L1_rho"] == 0.1
    assert record["divB_max"] == 0.2


def test_write_outputs_records_no_asymptotic_claim(tmp_path):
    ot = tmp_path / "ot.json"
    kh = tmp_path / "kh.json"
    _summary(ot, 0.07, 3.7, (True, True, True))
    _summary(kh, 0.002, 0.0007, (True, True, True))

    payload = mod.write_outputs(
        tmp_path / "out",
        [mod.collect_case("orszag_tang", ot), mod.collect_case("kelvin_helmholtz", kh)],
    )

    assert payload["gates"]["all_512_gates_pass"] is True
    assert payload["gates"]["asymptotic_convergence_claim"] is False
    assert "do not establish asymptotic convergence" in (tmp_path / "out" / "summary.md").read_text(encoding="utf-8")
    assert (tmp_path / "out" / "summary.csv").is_file()
