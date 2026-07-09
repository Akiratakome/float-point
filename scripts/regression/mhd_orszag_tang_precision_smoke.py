#!/usr/bin/env python3
"""Week-15 Orszag-Tang precision-smoke helper layer."""

from __future__ import annotations

import argparse
import csv
import json
import math
import pathlib
import sys
from typing import Any, Sequence

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
CASE = ROOT / "tests" / "cases" / "orszag_tang_2d" / "orszag_tang.cfg"
DEFAULT_OUT = ROOT / "experiments" / "week15" / "orszag_tang_precision_smoke"
EXPERIMENT = "week15-mhd-orszag-tang-precision-smoke"
DEFAULT_GAMMA = 5.0 / 3.0
SUPPORTED_SOLVERS = ("hll", "hlld")
PROFILES = {
    "gate": {"subdir": "gate128", "nx": 128, "ny": 128, "t_end": 0.1},
    "headline": {"subdir": "headline256", "nx": 256, "ny": 256, "t_end": 0.5},
}
OT_ANCHORS = {
    ("hll", "gate"): (76, 1.173),
    ("hlld", "gate"): (76, 1.085),
    ("hll", "headline"): (806, 3.72),
    ("hlld", "headline"): (812, 24.45),
}
OT_ANCHOR_DIVB_RTOL = 0.05

for path in (
    ROOT,
    ROOT / "scripts",
    ROOT / "scripts" / "figures",
    ROOT / "scripts" / "metrics",
    ROOT / "scripts" / "regression",
    ROOT / "scripts" / "verificarlo",
):
    sys.path.insert(0, str(path))

from _mhd_harness import (  # noqa: E402
    git_commit,
    point_symmetry_residual,
    replace_or_append_cfg,
    run_case,
    sha256_file,
)
from io_helper import read_binary  # noqa: E402
from mhd_fields import field_norms, mhd_primitive_fields  # noqa: E402
from mhd_paper_figures import plot_heatmap_panels  # noqa: E402
from mhd_precision_pilot import (  # noqa: E402
    build_variant,
    ordered_variants_reference_first,
    select_variants,
)
from mhd_precision_pilot_core import REFERENCE, ordering_flags  # noqa: E402


ROW_COLUMNS = (
    "variant",
    "precision",
    "opt",
    "fastmath",
    "riemann",
    "solver",
    "profile",
    "case",
    "subdir",
    "nx",
    "ny",
    "t_end",
    "finite",
    "rc",
    "steps",
    "divB_mean",
    "divB_max",
    "walltime_s",
    "dx",
    "dy",
    "symmetry_residual_rho",
    "is_reference",
    "L1_rho",
    "L2_rho",
    "Linf_rho",
    "L1_By",
    "L2_By",
    "Linf_By",
    "L1_p",
    "L2_p",
    "Linf_p",
    "L1_vx",
    "L2_vx",
    "Linf_vx",
)


def _normalise_solver(solver: str) -> str:
    out = str(solver).lower()
    if out not in SUPPORTED_SOLVERS:
        raise ValueError(f"unsupported Orszag-Tang smoke solver: {solver}")
    return out


def _normalise_profile(profile: str) -> str:
    out = str(profile).lower()
    if out not in PROFILES:
        raise ValueError(f"unsupported Orszag-Tang smoke profile: {profile}")
    return out


def case_gamma(cfg_text: str) -> float:
    """Read ``gamma`` from key=value cfg text, defaulting to the OT value."""
    for line in cfg_text.splitlines():
        content = line.split("#", 1)[0].strip()
        if not content or "=" not in content:
            continue
        key, value = [part.strip() for part in content.split("=", 1)]
        if key == "gamma":
            return float(value)
    return DEFAULT_GAMMA


def plan_row(variant: Any, solver: str, profile: str) -> dict[str, Any]:
    """Return one deterministic run-plan row for an existing build variant."""
    solver = _normalise_solver(solver)
    profile = _normalise_profile(profile)
    spec = PROFILES[profile]
    return {
        "variant": variant.name,
        "precision": variant.precision,
        "opt": variant.opt_level,
        "fastmath": bool(variant.fast_math),
        "riemann": "strict" if variant.strict_riemann else "leq",
        "solver": solver,
        "profile": profile,
        "case": CASE.name,
        "subdir": spec["subdir"],
        "nx": int(spec["nx"]),
        "ny": int(spec["ny"]),
        "t_end": float(spec["t_end"]),
        "is_reference": variant.name == REFERENCE,
        "build_variant": variant,
    }


def deterministic_plan(
    solver: str = "hll", profile: str = "gate", variant_set: str = "p0"
) -> list[dict[str, Any]]:
    """Return deterministic smoke rows for the given variant tier ("p0"=8, "p1"=24), reference first."""
    solver = _normalise_solver(solver)
    profile = _normalise_profile(profile)
    variants = ordered_variants_reference_first(select_variants(variant_set))
    return [plan_row(variant, solver, profile) for variant in variants]


def orszag_tang_cfg(base_text: str, *, solver: str, profile: str, output_file: str | pathlib.Path) -> str:
    """Generate an OT smoke cfg by overriding only harness-controlled keys."""
    solver = _normalise_solver(solver)
    profile = _normalise_profile(profile)
    spec = PROFILES[profile]
    text = base_text
    for key, value in (
        ("nx", str(spec["nx"])),
        ("ny", str(spec["ny"])),
        ("t_end", f"{float(spec['t_end']):g}"),
        ("riemann", solver),
        ("output_format", "binary"),
        ("output_file", str(output_file)),
    ):
        text = replace_or_append_cfg(text, key, value)
    return text


def measure_pair(
    plan: dict[str, Any],
    arr: np.ndarray,
    ref_arr: np.ndarray,
    *,
    gamma: float,
    dx: float,
    dy: float,
    diagnostics: dict[str, Any],
    walltime_s: float,
) -> dict[str, Any]:
    """Measure one OT deterministic row against the same-grid reference."""
    candidate = np.asarray(arr, dtype=np.float64)
    reference = np.asarray(ref_arr, dtype=np.float64)
    finite = bool(np.isfinite(candidate).all() and np.isfinite(reference).all())
    norms = field_norms(candidate, reference, gamma, dx) if finite else _na_norms()
    if finite:
        rho = mhd_primitive_fields(candidate, gamma)["rho"]
        symmetry = point_symmetry_residual(rho)
    else:
        symmetry = 0.0

    row = {key: value for key, value in plan.items() if key != "build_variant"}
    row.update(
        {
            "finite": finite,
            "rc": int(diagnostics.get("rc", 0)),
            "steps": int(diagnostics.get("steps", 0)),
            "divB_mean": _finite_float(diagnostics.get("divB_mean", 0.0)),
            "divB_max": _finite_float(diagnostics.get("divB_max", 0.0)),
            "walltime_s": _finite_float(walltime_s),
            "dx": _finite_float(dx),
            "dy": _finite_float(dy),
            "symmetry_residual_rho": _finite_float(symmetry),
        }
    )
    row.update({key: None if value is None else _finite_float(value) for key, value in norms.items()})
    return row


def anchor_gate(rows: list[dict[str, Any]], solver: str, profile: str) -> dict[str, Any]:
    """Gate G0 anchor check for the reference deterministic OT row."""
    solver = _normalise_solver(solver)
    profile = _normalise_profile(profile)
    anchor_steps, anchor_divb = OT_ANCHORS[(solver, profile)]
    reference = next((row for row in rows if row.get("is_reference") is True), None)
    all_finite = bool(rows) and all(row.get("finite") is True for row in rows)
    steps = reference.get("steps") if reference else None
    divb = reference.get("divB_max") if reference else None
    steps_exact = steps == anchor_steps
    divb_within = _divb_within_rtol(divb, anchor_divb)
    passed = bool(reference) and all_finite and steps_exact and divb_within
    return {
        "pass": passed,
        "all_finite": all_finite,
        "reference_variant": reference.get("variant") if reference else None,
        "expected_steps": anchor_steps,
        "observed_steps": steps,
        "steps_exact": steps_exact,
        "expected_divB_max": anchor_divb,
        "observed_divB_max": divb,
        "divB_rtol": OT_ANCHOR_DIVB_RTOL,
        "divB_within_rtol": divb_within,
    }


def write_outputs(
    out_dir: str | pathlib.Path,
    rows: list[dict[str, Any]],
    *,
    solver: str,
    profile: str,
    git_commit: str,
    figures: list[str],
) -> dict[str, Any]:
    """Write JSON, CSV, and Markdown summaries for measured smoke rows."""
    solver = _normalise_solver(solver)
    profile = _normalise_profile(profile)
    out = pathlib.Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    safe_rows = _jsonable(rows)
    anchor = anchor_gate(safe_rows, solver, profile)
    payload = {
        "experiment": EXPERIMENT,
        "case": CASE.name,
        "solver": solver,
        "profile": profile,
        "git_commit": _jsonable(git_commit),
        "reference_variant": REFERENCE,
        "gates": {
            "G0": anchor,
            "G0_anchor": anchor,
            "G1": {"ordering_flags": ordering_flags(safe_rows)},
        },
        "rows": safe_rows,
        "figures": _jsonable(figures),
        "notes": {
            "mca": "Docker Verificarlo MCA evidence is required separately; this smoke only records deterministic rows.",
            "norms": "L1/L2 values are same-grid proxy norms because field_norms is reused with dx.",
        },
    }

    json_path = out / "summary.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, allow_nan=False)
        f.write("\n")

    csv_path = out / "summary.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ROW_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in safe_rows:
            writer.writerow(row)

    md_path = out / "summary.md"
    md_path.write_text(_render_markdown(payload), encoding="utf-8")

    payload["json"] = str(json_path)
    payload["csv"] = str(csv_path)
    payload["markdown"] = str(md_path)
    return payload


def write_figures(
    out_dir: str | pathlib.Path,
    arr: np.ndarray,
    ref_arr: np.ndarray,
    *,
    gamma: float,
    dx: float,
    dy: float,
) -> list[str]:
    """Write reference and drift heatmaps; return paths relative to ``out_dir``."""
    _ = (dx, dy)
    out = pathlib.Path(out_dir)
    figure_dir = out / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)
    candidate = np.asarray(arr, dtype=np.float64)
    reference = np.asarray(ref_arr, dtype=np.float64)
    ref_fields = mhd_primitive_fields(reference, gamma)
    cand_fields = mhd_primitive_fields(candidate, gamma)

    reference_path = figure_dir / "reference_fields.png"
    drift_path = figure_dir / "drift_fields.png"
    plot_heatmap_panels(
        reference_path,
        [
            {"title": "rho ref", "field": ref_fields["rho"]},
            {"title": "p ref", "field": ref_fields["p"]},
        ],
    )
    plot_heatmap_panels(
        drift_path,
        [
            {"title": "rho drift", "field": np.abs(cand_fields["rho"] - ref_fields["rho"]), "log10": True},
            {"title": "By drift", "field": np.abs(cand_fields["By"] - ref_fields["By"]), "log10": True},
        ],
    )
    return [
        str(reference_path.relative_to(out)).replace("\\", "/"),
        str(drift_path.relative_to(out)).replace("\\", "/"),
    ]


def _na_norms() -> dict[str, None]:
    return {
        f"{norm}_{field}": None
        for field in ("rho", "By", "p", "vx")
        for norm in ("L1", "L2", "Linf")
    }


def _finite_float(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"expected finite numeric value, got {value!r}")
    return number


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, np.generic):
        return _jsonable(value.item())
    if isinstance(value, np.ndarray):
        return _jsonable(value.tolist())
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"cannot serialise non-finite float {value!r}")
        return value
    return value


def _render_markdown(summary: dict[str, Any]) -> str:
    rows = summary.get("rows", [])
    gates = summary.get("gates", {})
    lines = [
        "# Orszag-Tang Precision Smoke Summary",
        "",
        f"- Experiment: {_md(summary.get('experiment'))}",
        f"- Case: {_md(summary.get('case'))}",
        f"- Solver: {_md(summary.get('solver'))}",
        f"- Profile: {_md(summary.get('profile'))}",
        f"- Reference: {_md(summary.get('reference_variant'))}",
        f"- Git commit: {_md(summary.get('git_commit'))}",
        "",
        "## Gate G0",
        "",
        f"- Pass: {_md(gates.get('G0', {}).get('pass'))}",
        f"- Steps exact: {_md(gates.get('G0', {}).get('steps_exact'))}",
        f"- divB tolerance: {_md(gates.get('G0', {}).get('divB_within_rtol'))}",
        "",
        "## Deterministic Rows",
        "",
        _markdown_table(
            (
                "variant",
                "finite",
                "steps",
                "divB_max",
                "Linf_By",
                "Linf_rho",
                "symmetry_residual_rho",
                "walltime_s",
            ),
            rows,
        ),
        "",
        "## Comparison Focus",
        "",
        "Use Linf(By) and Linf(rho) for deterministic comparison language. "
        "L1/L2 row values, where present, are same-grid proxy norms, not strict 2D area-integral norms.",
        "",
        "## Figures",
        "",
    ]
    figures = summary.get("figures", [])
    lines.extend(f"- {_md(figure)}" for figure in figures)
    if not figures:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## MCA Note",
            "",
            "Docker Verificarlo is required separately for MCA evidence; this helper only summarises deterministic smoke rows.",
            "",
        ]
    )
    return "\n".join(lines)


def _markdown_table(columns: tuple[str, ...], rows: list[dict[str, Any]]) -> str:
    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| " + " | ".join(_md(row.get(column)) for column in columns) + " |"
        for row in rows
    ]
    if not body:
        body = ["| " + " | ".join("" for _ in columns) + " |"]
    return "\n".join([header, divider, *body])


def _md(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def _divb_within_rtol(value: Any, anchor: float) -> bool:
    try:
        observed = _finite_float(value)
    except (TypeError, ValueError):
        return False
    if anchor == 0.0:
        return observed == 0.0
    return abs(observed - anchor) <= OT_ANCHOR_DIVB_RTOL * abs(anchor)


def run_deterministic(
    out_dir: str | pathlib.Path,
    *,
    solver: str = "hll",
    profile: str = "gate",
    variant_set: str = "p0",
    variants: Sequence[Any] | None = None,
    base_cfg_text: str | None = None,
    builder=build_variant,
    runner=run_case,
    reader=read_binary,
    keep_grids: bool = False,
) -> dict[str, Any]:
    solver = _normalise_solver(solver)
    profile = _normalise_profile(profile)
    out = pathlib.Path(out_dir)
    selected = select_variants(variant_set) if variants is None else list(variants)
    if not selected:
        raise ValueError("variants must not be empty")
    if not any(variant.name == REFERENCE for variant in selected):
        raise ValueError(f"selected variants must include reference variant {REFERENCE}")
    ordered = ordered_variants_reference_first(selected)
    source = base_cfg_text if base_cfg_text is not None else CASE.read_text(encoding="utf-8")
    gamma = case_gamma(source)
    commit = git_commit()
    staged: list[tuple[Any, dict[str, Any], pathlib.Path, pathlib.Path, Any, np.ndarray]] = []
    for variant in ordered:
        run_dir = out / "runs" / variant.name
        grid = run_dir / "grid.bin"
        cfg_text = orszag_tang_cfg(source, solver=solver, profile=profile, output_file=grid)
        binary = pathlib.Path(builder(variant))
        sha = sha256_file(binary) if binary.is_file() else "unknown"
        _, meta, _ = runner(
            variant.name,
            cfg_text,
            run_dir,
            binary,
            CASE,
            commit,
            sha,
            output_bin=grid,
            experiment=EXPERIMENT,
        )
        header, arr = reader(grid)
        staged.append((variant, meta, run_dir, grid, header, arr))
    ref_header, ref_arr = staged[0][4], staged[0][5]
    rows = []
    for variant, meta, run_dir, grid, header, arr in staged:
        diagnostics = dict(meta.get("stderr_diagnostics", {}))
        diagnostics.setdefault("rc", meta.get("returncode", meta.get("return_code", 0)))
        row = measure_pair(
            plan_row(variant, solver, profile),
            arr,
            ref_arr,
            gamma=gamma,
            dx=float(header.dx),
            dy=float(header.dy),
            diagnostics=diagnostics,
            walltime_s=float(meta.get("elapsed_wall_s", 0.0)),
        )
        row["is_reference"] = variant.name == REFERENCE
        row["run_dir"] = str(run_dir)
        row["metadata_path"] = str(run_dir / "metadata.json")
        rows.append(row)
        if not keep_grids and grid.is_file():
            grid.unlink()
    drift = next(
        (s for s in staged if s[0].precision == "float" and s[0].opt_level == "O2" and not s[0].strict_riemann),
        staged[-1],
    )
    figures = []
    if rows and rows[0]["finite"] and next((row["finite"] for row in rows if row["variant"] == drift[0].name), False):
        figures = write_figures(
            out, drift[5], ref_arr, gamma=gamma, dx=float(ref_header.dx), dy=float(ref_header.dy)
        )
    return write_outputs(out, rows, solver=solver, profile=profile, git_commit=commit, figures=figures)


def resolve_output_dir(path: pathlib.Path | None, solver: str) -> pathlib.Path:
    solver = _normalise_solver(solver)
    if path is None:
        if solver == "hll":
            return DEFAULT_OUT
        return DEFAULT_OUT.with_name(f"{DEFAULT_OUT.name}_{solver}")
    return path if path.is_absolute() else ROOT / path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=pathlib.Path, default=None)
    parser.add_argument("--solver", choices=SUPPORTED_SOLVERS, default="hll")
    parser.add_argument("--profile", choices=tuple(PROFILES), default="gate")
    parser.add_argument("--keep-grids", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    packet = resolve_output_dir(args.out, args.solver) / PROFILES[_normalise_profile(args.profile)]["subdir"]
    payload = run_deterministic(
        packet,
        solver=args.solver,
        profile=args.profile,
        keep_grids=args.keep_grids,
    )
    print(packet / "summary.md")
    return 0 if payload["gates"]["G0_anchor"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
