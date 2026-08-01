import json
import math

from scripts.regression import mhd_resolution_pair_completion as completion
from scripts.regression import mhd_week18_resolution_ladder as ladder


def test_reference_semantics_match_retained_corrected_grid():
    result = completion.validate_reference_semantics()
    assert result["pass"] is True
    assert all(result["checks"].values())


def test_primary_resolution_summary_has_complete_precision_pairs():
    summary = json.loads(ladder.DEFAULT_OUT.joinpath("summary.json").read_text(encoding="utf-8"))
    assert summary["gate"]["precision_pair_metrics_complete"] is True
    assert summary["gate"]["precision_pair_cells_available"] == 12
    assert summary["precision_pair_completion"]["gate"]["pass"] is True
    rows = [
        row for row in summary["runs"]
        if row["case"] == "orszag_tang_2d"
        and row["solver"] == "hlld"
        and row["resolution"] == 512
    ]
    assert len(rows) == 2
    assert all(math.isfinite(row["rho_linf_fp32_vs_fp64"]) for row in rows)


def test_retained_pair_records_hashes_needed_for_safe_refresh():
    payload = json.loads(completion.DEFAULT_OUT.joinpath("summary.json").read_text(encoding="utf-8"))
    assert payload["provenance"]["float_grid_sha256"]
    assert payload["provenance"]["float_binary_sha256"]
    assert payload["float_run"]["status"] == "completed"


def test_retained_pair_separates_revalidation_from_failed_replay():
    revalidation = json.loads(completion.ARTIFACT_REVALIDATION.read_text(encoding="utf-8"))
    replay = json.loads(completion.REPLAY_ATTEMPT_METADATA.read_text(encoding="utf-8"))
    assert revalidation["status"] == "revalidated"
    assert all(revalidation["checks"].values())
    assert replay["status"] == "failed"
    assert replay["failure"]["category"] == "configuration_error"
    assert not completion.PAIR_RUN_METADATA.exists()
