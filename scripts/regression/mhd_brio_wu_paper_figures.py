#!/usr/bin/env python3
"""Generate a paper-style Brio-Wu 1D MHD validation profile figure.

This script reads the Week 12 HLL Brio-Wu output when available. If the
800-cell binary is missing, it runs the existing double-precision hrsc_mhd
binary with a generated cfg that redirects output to the Week 12 experiment
directory and records the usual cfg/stdout/stderr/metadata artefacts.
"""

from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from io_helper import read_binary  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from _mhd_harness import (  # noqa: E402
    git_commit,
    replace_or_append_cfg,
    resolve_binary,
    run_case,
    sha256_file,
)
from mhd_paper_figures import mhd_primitive, plot_line_panels  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parents[2]
BASE_CFG = ROOT / "tests" / "cases" / "brio_wu_1d" / "brio_wu.cfg"
BASE_BIN = ROOT / "build-double" / "hrsc_mhd"
OUT = ROOT / "experiments" / "week12" / "brio_wu_1d"
RUN_DIR = OUT / "runs" / "bw_800_double"
BIN_800 = OUT / "bw_800.bin"
FIGURE = OUT / "figures" / "brio_wu_paper_profiles.png"
PAPER_SUMMARY = OUT / "paper_summary.md"
GAMMA = 2.0
SENTINEL_FALLBACK = "[mhd] t=0.100000 steps=759 divB_mean=3.339e-16 divB_max=4.441e-14"


def ensure_bw_800() -> pathlib.Path:
    """Return bw_800.bin, generating it only when it is absent."""
    if BIN_800.is_file():
        return BIN_800

    bin_path = resolve_binary(BASE_BIN)
    cfg_text = BASE_CFG.read_text(encoding="utf-8")
    cfg_text = replace_or_append_cfg(cfg_text, "nx", "800")
    cfg_text = replace_or_append_cfg(cfg_text, "output_format", "binary")
    cfg_text = replace_or_append_cfg(cfg_text, "output_file", str(BIN_800))
    run_case(
        "bw_800_double",
        cfg_text,
        RUN_DIR,
        bin_path,
        BASE_CFG,
        git_commit(),
        sha256_file(bin_path),
        output_bin=BIN_800,
        experiment="week12-brio-wu-paper-profiles",
    )
    return BIN_800


def read_profiles(path: pathlib.Path) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    header, arr = read_binary(path)
    if header.nvars != 9:
        raise ValueError(f"{path} is not a 9-variable MHD field (nvars={header.nvars})")
    if header.ny != 1:
        raise ValueError(f"{path} is not a 1D Brio-Wu field (ny={header.ny})")
    data = arr[0].astype(np.float64, copy=False)
    x = (np.arange(header.nx, dtype=np.float64) + 0.5) * float(header.dx)
    prim = mhd_primitive(data, GAMMA)
    return x, prim


def load_sentinel_line() -> str:
    metadata_path = RUN_DIR / "metadata.json"
    if metadata_path.is_file():
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            line = (metadata.get("stderr_diagnostics") or {}).get("line")
            if line:
                return str(line)
        except json.JSONDecodeError:
            pass
    summary_path = OUT / "summary.md"
    if summary_path.is_file():
        text = summary_path.read_text(encoding="utf-8", errors="replace")
        if "759" in text and "3.339e-16" in text and "4.441e-14" in text:
            return SENTINEL_FALLBACK
    return ""


def write_paper_summary(binary_path: pathlib.Path, figure_path: pathlib.Path, sentinel: str) -> pathlib.Path:
    lines = [
        "# Brio-Wu Paper-Style Validation Profiles",
        "",
        "Paper anchor: Brio & Wu 1988, DOI `10.1016/0021-9991(88)90120-9`.",
        "",
        "The figure `figures/brio_wu_paper_profiles.png` is generated from this "
        "repository's Week 12 HLL Brio-Wu output, not copied from the paper. It "
        "plots the 800-cell profiles for density `rho`, velocity `vx`, transverse "
        "magnetic field `By`, and pressure `p` at `t=0.1` with `gamma=2`.",
        "",
        "Self-reference convergence against the local N=8000 double run remains "
        "secondary engineering evidence. The paper-grounded validation claim is "
        "limited to qualitative Brio-Wu wave-structure agreement plus the local "
        "divergence sentinel.",
        "",
        "## Artefacts",
        "",
        f"- Binary input: `{binary_path.relative_to(ROOT).as_posix()}`",
        f"- Paper-style figure: `{figure_path.relative_to(ROOT).as_posix()}`",
        "- Existing self-reference summary: `experiments/week12/brio_wu_1d/summary.md`",
        "",
    ]
    if sentinel:
        lines.extend(["## Brio-Wu sentinel", "", f"`{sentinel}`", ""])
    PAPER_SUMMARY.write_text("\n".join(lines), encoding="utf-8")
    return PAPER_SUMMARY


def main() -> None:
    binary_path = ensure_bw_800()
    x, prim = read_profiles(binary_path)
    figure_path = plot_line_panels(
        FIGURE,
        x,
        [
            ("rho", prim["rho"]),
            ("vx", prim["vx"]),
            ("By", prim["By"]),
            ("p", prim["p"]),
        ],
    )
    summary_path = write_paper_summary(binary_path, figure_path, load_sentinel_line())
    print(f"wrote {figure_path.relative_to(ROOT)}")
    print(f"wrote {summary_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
