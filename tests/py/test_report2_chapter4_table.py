import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "figures" / "report2_chapter4_cpu_gpu_table.py"
SOURCE = ROOT / "experiments" / "week16" / "cpu_gpu_hardware_axis" / "summary.json"


def test_chapter4_cpu_gpu_table_is_generated_from_summary(tmp_path):
    output = tmp_path / "table.tex"
    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--source",
            str(SOURCE),
            "--output",
            str(output),
        ],
        check=True,
        cwd=ROOT,
    )

    text = output.read_text(encoding="utf-8")
    assert text.count("HLL saved state") == 4
    assert "Brio--Wu & fp64 & $800\\times1$ & 759/759 & 0 & 0" in text
    assert "Orszag--Tang & fp32 & $256^2$ & 806/806 & 0 & 0" in text
    assert "speedup" not in text.lower()
    assert "experiments/week16/cpu_gpu_hardware_axis/summary.json" in text
