from __future__ import annotations

from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts._compat_wrapper import exec_archived as _exec_archived

_exec_archived("report1/figures/gen_a2_s2_figures.py", __file__, globals())
