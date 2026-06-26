#!/usr/bin/env python3
"""Generate HLL-vs-HLLD diagnostic figures for the deferred HLLD decision.

This script consumes the existing Week 13 Orszag-Tang solver-comparison binary
grids when they are present. If either grid is missing, it reruns the existing
solver comparison driver, then derives diagnostic-only PNG figures with the
stdlib PNG helpers from ``mhd_paper_figures.py``.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments" / "week13" / "solver_compare"
FIGURES = OUT / "figures"
HLL_BIN = OUT / "ot_256_hll.bin"
HLLD_BIN = OUT / "ot_256_hlld.bin"
SUMMARY = OUT / "summary.md"
WEEK13_SUMMARY = ROOT / "docs" / "week13" / "week13-summary.md"

RHO, MX, MY, MZ, BX, BY, BZ, E, PSI = range(9)


def ensure_solver_compare_outputs() -> None:
    """Use existing solver-comparison grids or regenerate them with the driver."""
    if HLL_BIN.is_file() and HLLD_BIN.is_file():
        return
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "regression" / "mhd_solver_compare_2d.py")],
        cwd=str(ROOT),
        check=True,
    )
    missing = [str(path) for path in (HLL_BIN, HLLD_BIN) if not path.is_file()]
    if missing:
        raise FileNotFoundError("solver comparison did not produce: " + ", ".join(missing))


def periodic_divb(arr, dx: float, dy: float):
    """Central-difference div(B) using periodic x/y boundaries."""
    import numpy as np

    bx = arr[..., BX].astype(np.float64)
    by = arr[..., BY].astype(np.float64)
    d_bx_dx = (np.roll(bx, -1, axis=1) - np.roll(bx, 1, axis=1)) / (2.0 * dx)
    d_by_dy = (np.roll(by, -1, axis=0) - np.roll(by, 1, axis=0)) / (2.0 * dy)
    return d_bx_dx + d_by_dy


def check_compatible_headers(h_hll, h_hlld) -> None:
    lhs = (
        h_hll.nx,
        h_hll.ny,
        h_hll.nvars,
        h_hll.precision_tag,
        h_hll.t,
        h_hll.dx,
        h_hll.dy,
    )
    rhs = (
        h_hlld.nx,
        h_hlld.ny,
        h_hlld.nvars,
        h_hlld.precision_tag,
        h_hlld.t,
        h_hlld.dx,
        h_hlld.dy,
    )
    if lhs != rhs:
        raise ValueError(f"HLL/HLLD grid headers differ: {lhs} vs {rhs}")
    if h_hll.nvars < 9:
        raise ValueError(f"expected 9-variable MHD grid, got {h_hll.nvars}")


def write_figures():
    import numpy as np

    sys.path.insert(0, str(ROOT / "scripts"))
    sys.path.insert(0, str(ROOT / "scripts" / "regression"))
    from io_helper import read_binary
    from mhd_paper_figures import plot_heatmap_panels

    ensure_solver_compare_outputs()
    h_hll, a_hll = read_binary(HLL_BIN)
    h_hlld, a_hlld = read_binary(HLLD_BIN)
    check_compatible_headers(h_hll, h_hlld)

    rho_hll = a_hll[..., RHO].astype(np.float64)
    rho_hlld = a_hlld[..., RHO].astype(np.float64)
    rho_diff = rho_hlld - rho_hll

    rho_min = float(min(np.nanmin(rho_hll), np.nanmin(rho_hlld)))
    rho_max = float(max(np.nanmax(rho_hll), np.nanmax(rho_hlld)))
    diff_abs = float(np.nanmax(np.abs(rho_diff)))

    divb_hll = periodic_divb(a_hll, float(h_hll.dx), float(h_hll.dy))
    divb_hlld = periodic_divb(a_hlld, float(h_hlld.dx), float(h_hlld.dy))
    abs_divb_hll = np.abs(divb_hll)
    abs_divb_hlld = np.abs(divb_hlld)
    log_floor = 1.0e-300
    divb_log_min = float(
        min(
            np.nanmin(np.log10(np.maximum(abs_divb_hll, log_floor))),
            np.nanmin(np.log10(np.maximum(abs_divb_hlld, log_floor))),
        )
    )
    divb_log_max = float(
        max(
            np.nanmax(np.log10(np.maximum(abs_divb_hll, log_floor))),
            np.nanmax(np.log10(np.maximum(abs_divb_hlld, log_floor))),
        )
    )

    FIGURES.mkdir(parents=True, exist_ok=True)
    rho_path = plot_heatmap_panels(
        FIGURES / "rho_hll_hlld_diff.png",
        [
            {"title": "hll rho", "field": rho_hll, "vmin": rho_min, "vmax": rho_max},
            {"title": "hlld rho", "field": rho_hlld, "vmin": rho_min, "vmax": rho_max},
            {"title": "hlld-hll rho", "field": rho_diff, "vmin": -diff_abs, "vmax": diff_abs},
        ],
        columns=3,
        panel_size=430,
    )
    divb_path = plot_heatmap_panels(
        FIGURES / "divb_hll_hlld.png",
        [
            {
                "title": "hll abs divB",
                "field": abs_divb_hll,
                "vmin": divb_log_min,
                "vmax": divb_log_max,
                "log10": True,
            },
            {
                "title": "hlld abs divB",
                "field": abs_divb_hlld,
                "vmin": divb_log_min,
                "vmax": divb_log_max,
                "log10": True,
            },
        ],
        columns=2,
        panel_size=520,
    )

    metrics = {
        "rho_l1_hlld_minus_hll": float(np.mean(np.abs(rho_diff))),
        "rho_linf_hlld_minus_hll": float(np.max(np.abs(rho_diff))),
        "divb_abs_mean_hll": float(np.mean(abs_divb_hll)),
        "divb_abs_mean_hlld": float(np.mean(abs_divb_hlld)),
        "divb_abs_max_hll": float(np.max(abs_divb_hll)),
        "divb_abs_max_hlld": float(np.max(abs_divb_hlld)),
        "nx": int(h_hll.nx),
        "ny": int(h_hll.ny),
        "time": float(h_hll.t),
        "dx": float(h_hll.dx),
        "dy": float(h_hll.dy),
    }
    return rho_path, divb_path, metrics


def replace_section(text: str, heading: str, section: str) -> str:
    lines = text.rstrip().splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == heading:
            start = i
            break
    if start is None:
        return text.rstrip() + "\n\n" + section.rstrip() + "\n"

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            end = j
            break
    new_lines = lines[:start] + section.rstrip().splitlines() + lines[end:]
    return "\n".join(new_lines).rstrip() + "\n"


def write_figures_readme(metrics: dict[str, float]) -> pathlib.Path:
    readme = FIGURES / "README.md"
    text = f"""# HLLD Diagnostic Figures

These PNGs are diagnostic figures for the Week 13 deferred-HLLD decision. They
support inspection of the HLL-vs-HLLD Orszag-Tang comparison, but they are not
production validation and do not adopt HLLD for subsequent precision-study
runs.

Inputs:

- `../ot_256_hll.bin`
- `../ot_256_hlld.bin`

Figures:

- `rho_hll_hlld_diff.png`: HLL density, HLLD density, and HLLD-HLL density.
- `divb_hll_hlld.png`: log10-scaled abs(divB) for HLL and HLLD.

Derived with periodic central differences from Bx/By using the binary header
spacing (`dx={metrics["dx"]:.8g}`, `dy={metrics["dy"]:.8g}`) to match the
Orszag-Tang periodic cfg.

Diagnostic values:

| metric | value |
|---|---:|
| grid | {metrics["nx"]}x{metrics["ny"]} |
| t | {metrics["time"]:.6g} |
| L1(rho) HLLD-HLL | {metrics["rho_l1_hlld_minus_hll"]:.3e} |
| Linf(rho) HLLD-HLL | {metrics["rho_linf_hlld_minus_hll"]:.3e} |
| mean abs(divB) HLL | {metrics["divb_abs_mean_hll"]:.3e} |
| mean abs(divB) HLLD | {metrics["divb_abs_mean_hlld"]:.3e} |
| max abs(divB) HLL | {metrics["divb_abs_max_hll"]:.3e} |
| max abs(divB) HLLD | {metrics["divb_abs_max_hlld"]:.3e} |
"""
    readme.write_text(text, encoding="utf-8")
    return readme


def update_solver_summary() -> None:
    decision = """## Decision

- [ ] HLLD validated and adopted for remaining MHD work, OR
- [x] HLLD deferred; HLL remains the production solver (fallback per overall.md).

Rationale: HLLD remains finite on the Week 13 Orszag-Tang solver comparison,
but it produces a substantially larger divB maximum than the HLL candidate in
the current GLM configuration. Keep HLL as the production solver for subsequent
MHD precision-study runs until a follow-up HLLD+divB-control pass is validated.
"""
    section = """## Diagnostic figures

- `figures/rho_hll_hlld_diff.png`
- `figures/divb_hll_hlld.png`

These figures support the deferred-HLLD decision; they are not production
validation.
"""
    text = SUMMARY.read_text(encoding="utf-8")
    text = replace_section(text, "## Decision", decision)
    text = replace_section(text, "## Diagnostic figures", section)
    text = text.replace(
        "validated.\n## Diagnostic figures",
        "validated.\n\n## Diagnostic figures",
    )
    SUMMARY.write_text(text, encoding="utf-8")


def update_week13_summary() -> None:
    text = WEEK13_SUMMARY.read_text(encoding="utf-8")
    bullet = (
        "- HLLD diagnostic figures:\n"
        "  [figures/README.md](../../experiments/week13/solver_compare/figures/README.md)"
    )
    if "solver_compare/figures/README.md" in text:
        return
    marker = (
        "- Solver comparison summary:\n"
        "  [summary.md](../../experiments/week13/solver_compare/summary.md)"
    )
    if marker in text:
        text = text.replace(marker, marker + "\n" + bullet)
    else:
        text = text.rstrip() + "\n" + bullet + "\n"
    WEEK13_SUMMARY.write_text(text, encoding="utf-8")


def main() -> None:
    rho_path, divb_path, metrics = write_figures()
    write_figures_readme(metrics)
    update_solver_summary()
    update_week13_summary()
    print(f"wrote {rho_path.relative_to(ROOT)}")
    print(f"wrote {divb_path.relative_to(ROOT)}")
    for key in (
        "rho_l1_hlld_minus_hll",
        "rho_linf_hlld_minus_hll",
        "divb_abs_max_hll",
        "divb_abs_max_hlld",
    ):
        print(f"{key}={metrics[key]:.6e}")


if __name__ == "__main__":
    main()
