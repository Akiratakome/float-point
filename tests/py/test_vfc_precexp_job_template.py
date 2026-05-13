from pathlib import Path


def test_vfc_precexp_job_template_records_logs_and_does_not_edit_cfg() -> None:
    text = Path("scripts/cluster/slurm/vfc_precexp_rerun.sh").read_text(encoding="utf-8")
    assert "set -euo pipefail" in text
    assert "vfc_precexp" in text
    assert "logs/environment.txt" in text
    assert "scripts/exrun" in text
    assert "scripts/excmp" in text
    assert "tests/cases/toro_1d/sod.cfg" in text
    assert "cp " in text or "Copy-Item" not in text
    assert "sed -i" not in text
