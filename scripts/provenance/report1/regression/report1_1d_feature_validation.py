#!/usr/bin/env python3
"""Derived 1D feature-validation metrics for Report 1.

This script reads existing final 1D grids and compares density features against
the analytic Riemann solution. It does not run the solver or modify raw grids.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
import sys
from typing import Iterable

import numpy as np

_SCRIPTS_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SCRIPTS_ROOT))
from io_helper import cons_to_prim, read_binary  # noqa: E402


@dataclass(frozen=True)
class TestConfig:
    name: str
    title: str
    t_end: float
    x0: float
    gamma: float
    rhoL: float
    uL: float
    pL: float
    rhoR: float
    uR: float
    pR: float
    xmin: float = 0.0
    xmax: float = 1.0


@dataclass(frozen=True)
class ShockFeature:
    side: str
    speed: float
    position: float


@dataclass(frozen=True)
class WaveDescription:
    side: str
    kind: str
    speed: float | None = None
    position: float | None = None
    head_speed: float | None = None
    tail_speed: float | None = None
    head_position: float | None = None
    tail_position: float | None = None


@dataclass(frozen=True)
class RiemannFeatures:
    p_star: float
    u_star: float
    contact_position: float
    left: WaveDescription
    right: WaveDescription
    shocks: tuple[ShockFeature, ...]


@dataclass(frozen=True)
class LocatedFeature:
    position: float
    abs_error: float
    gradient_value: float
    gradient_index: int
    window_radius: float
    window_lower: float
    window_upper: float


TESTS: dict[str, TestConfig] = {
    "sod": TestConfig(
        name="sod",
        title="Sod shock tube",
        t_end=0.25,
        x0=0.5,
        gamma=1.4,
        rhoL=1.0,
        uL=0.0,
        pL=1.0,
        rhoR=0.125,
        uR=0.0,
        pR=0.1,
    ),
    "toro3": TestConfig(
        name="toro3",
        title="Toro test 3 blast wave",
        t_end=0.012,
        x0=0.5,
        gamma=1.4,
        rhoL=1.0,
        uL=0.0,
        pL=1000.0,
        rhoR=1.0,
        uR=0.0,
        pR=0.01,
    ),
    "toro5": TestConfig(
        name="toro5",
        title="Toro test 5 slow moving contact",
        t_end=0.035,
        x0=0.5,
        gamma=1.4,
        rhoL=5.99924,
        uL=19.5975,
        pL=460.894,
        rhoR=5.99242,
        uR=-6.19633,
        pR=46.0950,
    ),
}

PRECISIONS = ("double", "float")


def _f(p: float, rho_k: float, p_k: float, gamma: float) -> float:
    gm1, gp1 = gamma - 1.0, gamma + 1.0
    a = 2.0 / (gp1 * rho_k)
    b = gm1 / gp1 * p_k
    if p > p_k:
        return (p - p_k) * np.sqrt(a / (p + b))
    a_k = np.sqrt(gamma * p_k / rho_k)
    return 2.0 * a_k / gm1 * ((p / p_k) ** (gm1 / (2.0 * gamma)) - 1.0)


def _df(p: float, rho_k: float, p_k: float, gamma: float) -> float:
    gm1, gp1 = gamma - 1.0, gamma + 1.0
    a = 2.0 / (gp1 * rho_k)
    b = gm1 / gp1 * p_k
    if p > p_k:
        return np.sqrt(a / (p + b)) * (1.0 - (p - p_k) / (2.0 * (p + b)))
    a_k = np.sqrt(gamma * p_k / rho_k)
    return 1.0 / (rho_k * a_k) * (p / p_k) ** (-(gp1) / (2.0 * gamma))


def _solve_pstar(
    gamma: float,
    rho_l: float,
    u_l: float,
    p_l: float,
    a_l: float,
    rho_r: float,
    u_r: float,
    p_r: float,
    a_r: float,
    tol: float = 1e-12,
) -> float:
    p = 0.5 * (p_l + p_r) - 0.125 * (u_r - u_l) * (rho_l + rho_r) * (a_l + a_r)
    p = max(float(p), 1e-15)
    for _ in range(200):
        f_l = _f(p, rho_l, p_l, gamma)
        f_r = _f(p, rho_r, p_r, gamma)
        df_l = _df(p, rho_l, p_l, gamma)
        df_r = _df(p, rho_r, p_r, gamma)
        dp = -(f_l + f_r + u_r - u_l) / (df_l + df_r)
        p_new = max(p + dp, 1e-15)
        if abs(p_new - p) < tol * 0.5 * (p_new + p):
            return float(p_new)
        p = p_new
    return float(p)


def solve_riemann_features(cfg: TestConfig) -> RiemannFeatures:
    """Return exact star state and shock/contact feature positions."""
    gamma = cfg.gamma
    gm1, gp1 = gamma - 1.0, gamma + 1.0
    a_l = float(np.sqrt(gamma * cfg.pL / cfg.rhoL))
    a_r = float(np.sqrt(gamma * cfg.pR / cfg.rhoR))
    p_star = _solve_pstar(
        gamma,
        cfg.rhoL,
        cfg.uL,
        cfg.pL,
        a_l,
        cfg.rhoR,
        cfg.uR,
        cfg.pR,
        a_r,
    )
    u_star = 0.5 * (cfg.uL + cfg.uR) + 0.5 * (
        _f(p_star, cfg.rhoR, cfg.pR, gamma) - _f(p_star, cfg.rhoL, cfg.pL, gamma)
    )
    contact_position = cfg.x0 + u_star * cfg.t_end
    shocks: list[ShockFeature] = []

    if p_star > cfg.pL:
        speed_l = cfg.uL - a_l * np.sqrt(
            gp1 / (2.0 * gamma) * p_star / cfg.pL + gm1 / (2.0 * gamma)
        )
        left = WaveDescription(
            side="left",
            kind="shock",
            speed=float(speed_l),
            position=float(cfg.x0 + speed_l * cfg.t_end),
        )
        shocks.append(ShockFeature("left", float(speed_l), float(left.position)))
    else:
        a_star_l = a_l * (p_star / cfg.pL) ** (gm1 / (2.0 * gamma))
        head_l = cfg.uL - a_l
        tail_l = u_star - a_star_l
        left = WaveDescription(
            side="left",
            kind="rarefaction",
            head_speed=float(head_l),
            tail_speed=float(tail_l),
            head_position=float(cfg.x0 + head_l * cfg.t_end),
            tail_position=float(cfg.x0 + tail_l * cfg.t_end),
        )

    if p_star > cfg.pR:
        speed_r = cfg.uR + a_r * np.sqrt(
            gp1 / (2.0 * gamma) * p_star / cfg.pR + gm1 / (2.0 * gamma)
        )
        right = WaveDescription(
            side="right",
            kind="shock",
            speed=float(speed_r),
            position=float(cfg.x0 + speed_r * cfg.t_end),
        )
        shocks.append(ShockFeature("right", float(speed_r), float(right.position)))
    else:
        a_star_r = a_r * (p_star / cfg.pR) ** (gm1 / (2.0 * gamma))
        head_r = cfg.uR + a_r
        tail_r = u_star + a_star_r
        right = WaveDescription(
            side="right",
            kind="rarefaction",
            head_speed=float(head_r),
            tail_speed=float(tail_r),
            head_position=float(cfg.x0 + head_r * cfg.t_end),
            tail_position=float(cfg.x0 + tail_r * cfg.t_end),
        )

    return RiemannFeatures(
        p_star=float(p_star),
        u_star=float(u_star),
        contact_position=float(contact_position),
        left=left,
        right=right,
        shocks=tuple(shocks),
    )


def exact_riemann_density_velocity_pressure(
    x: np.ndarray,
    cfg: TestConfig,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Sample the exact Riemann solution using the verify_toro formulas."""
    if cfg.t_end <= 0.0:
        raise ValueError("t_end must be positive")
    gamma = cfg.gamma
    gm1, gp1 = gamma - 1.0, gamma + 1.0
    a_l = float(np.sqrt(gamma * cfg.pL / cfg.rhoL))
    a_r = float(np.sqrt(gamma * cfg.pR / cfg.rhoR))
    features = solve_riemann_features(cfg)
    p_star, u_star = features.p_star, features.u_star

    if p_star > cfg.pL:
        rho_star_l = cfg.rhoL * (
            (p_star / cfg.pL + gm1 / gp1) / (gm1 / gp1 * p_star / cfg.pL + 1.0)
        )
        s_l = features.left.speed
    else:
        rho_star_l = cfg.rhoL * (p_star / cfg.pL) ** (1.0 / gamma)
        a_star_l = a_l * (p_star / cfg.pL) ** (gm1 / (2.0 * gamma))
        s_hl = cfg.uL - a_l
        s_tl = u_star - a_star_l
        s_l = None

    if p_star > cfg.pR:
        rho_star_r = cfg.rhoR * (
            (p_star / cfg.pR + gm1 / gp1) / (gm1 / gp1 * p_star / cfg.pR + 1.0)
        )
        s_r = features.right.speed
    else:
        rho_star_r = cfg.rhoR * (p_star / cfg.pR) ** (1.0 / gamma)
        a_star_r = a_r * (p_star / cfg.pR) ** (gm1 / (2.0 * gamma))
        s_hr = cfg.uR + a_r
        s_tr = u_star + a_star_r
        s_r = None

    rho = np.empty_like(x, dtype=np.float64)
    u = np.empty_like(x, dtype=np.float64)
    p = np.empty_like(x, dtype=np.float64)

    for i, xi in enumerate(x):
        s = float((xi - cfg.x0) / cfg.t_end)
        if s <= u_star:
            if p_star > cfg.pL:
                if s <= float(s_l):
                    rho[i], u[i], p[i] = cfg.rhoL, cfg.uL, cfg.pL
                else:
                    rho[i], u[i], p[i] = rho_star_l, u_star, p_star
            else:
                if s <= s_hl:
                    rho[i], u[i], p[i] = cfg.rhoL, cfg.uL, cfg.pL
                elif s <= s_tl:
                    ratio = 2.0 / gp1 + gm1 / (gp1 * a_l) * (cfg.uL - s)
                    rho[i] = cfg.rhoL * ratio ** (2.0 / gm1)
                    u[i] = 2.0 / gp1 * (a_l + gm1 / 2.0 * cfg.uL + s)
                    p[i] = cfg.pL * ratio ** (2.0 * gamma / gm1)
                else:
                    rho[i], u[i], p[i] = rho_star_l, u_star, p_star
        else:
            if p_star > cfg.pR:
                if s <= float(s_r):
                    rho[i], u[i], p[i] = rho_star_r, u_star, p_star
                else:
                    rho[i], u[i], p[i] = cfg.rhoR, cfg.uR, cfg.pR
            else:
                if s <= s_tr:
                    rho[i], u[i], p[i] = rho_star_r, u_star, p_star
                elif s <= s_hr:
                    ratio = 2.0 / gp1 - gm1 / (gp1 * a_r) * (cfg.uR - s)
                    rho[i] = cfg.rhoR * ratio ** (2.0 / gm1)
                    u[i] = 2.0 / gp1 * (-a_r + gm1 / 2.0 * cfg.uR + s)
                    p[i] = cfg.pR * ratio ** (2.0 * gamma / gm1)
                else:
                    rho[i], u[i], p[i] = cfg.rhoR, cfg.uR, cfg.pR
    return rho, u, p


def locate_feature_by_gradient(
    x: np.ndarray,
    values: np.ndarray,
    exact_position: float,
    dx: float,
    domain_length: float,
    min_window_cells: int = 8,
    window_fraction: float = 0.05,
    blocker_positions: Iterable[float] | None = None,
) -> LocatedFeature:
    """Locate a feature by the strongest adjacent-cell gradient near it."""
    if x.ndim != 1 or values.ndim != 1 or x.shape != values.shape:
        raise ValueError("x and values must be one-dimensional arrays with matching shape")
    if x.size < 2:
        raise ValueError("at least two cells are required to locate a feature")

    base_radius = max(float(min_window_cells) * dx, window_fraction * domain_length)
    window_radius = base_radius
    if blocker_positions is not None:
        distances = [
            abs(float(pos) - exact_position)
            for pos in blocker_positions
            if np.isfinite(pos) and abs(float(pos) - exact_position) > 0.0
        ]
        if distances:
            isolation_radius = 0.45 * min(distances)
            min_radius = float(min_window_cells) * dx
            window_radius = max(min_radius, min(base_radius, isolation_radius))
    lower = exact_position - window_radius
    upper = exact_position + window_radius
    edge_midpoints = 0.5 * (x[:-1] + x[1:])
    gradients = np.abs(np.diff(values)) / dx
    in_window = (edge_midpoints >= lower) & (edge_midpoints <= upper)
    if not np.any(in_window):
        raise ValueError(
            f"no cell-edge midpoints within search window [{lower}, {upper}]"
        )

    candidate_indices = np.flatnonzero(in_window)
    best_local = int(np.argmax(gradients[candidate_indices]))
    best_idx = int(candidate_indices[best_local])
    position = float(edge_midpoints[best_idx])
    return LocatedFeature(
        position=position,
        abs_error=float(abs(position - exact_position)),
        gradient_value=float(gradients[best_idx]),
        gradient_index=best_idx,
        window_radius=float(window_radius),
        window_lower=float(lower),
        window_upper=float(upper),
    )


def discontinuity_band_mask(
    x: np.ndarray,
    feature_positions: Iterable[float],
    band_cells: int,
    dx: float,
) -> np.ndarray:
    """Mask cells within band_cells*dx of exact contact/shock positions."""
    radius = float(band_cells) * dx
    mask = np.zeros_like(x, dtype=bool)
    for pos in feature_positions:
        if np.isfinite(pos):
            mask |= np.abs(x - float(pos)) <= radius
    return mask


def _read_primitive_1d(path: Path, gamma: float) -> tuple[object, np.ndarray, np.ndarray]:
    header, cons = read_binary(path)
    if header.ny != 1:
        raise ValueError(f"{path}: expected 1D binary with ny=1, got ny={header.ny}")
    prim = cons_to_prim(cons.astype(np.float64), gamma)
    return header, cons, prim[0]


def analyse_case(
    cfg: TestConfig,
    precision: str,
    path: Path,
    band_cells: int,
    min_window_cells: int,
    window_fraction: float,
) -> dict[str, object]:
    header, _cons, prim = _read_primitive_1d(path, cfg.gamma)
    nx = int(header.nx)
    dx = float(header.dx)
    domain_length = cfg.xmax - cfg.xmin
    x = cfg.xmin + (np.arange(nx, dtype=np.float64) + 0.5) * dx
    rho_num = prim[:, 0]
    p_num = prim[:, 3]
    rho_exact, _u_exact, _p_exact = exact_riemann_density_velocity_pressure(x, cfg)
    features = solve_riemann_features(cfg)

    contact_loc = locate_feature_by_gradient(
        x,
        rho_num,
        features.contact_position,
        dx,
        domain_length,
        min_window_cells=min_window_cells,
        window_fraction=window_fraction,
        blocker_positions=[shock.position for shock in features.shocks],
    )

    shock_rows = []
    for shock in features.shocks:
        shock_loc = locate_feature_by_gradient(
            x,
            p_num,
            shock.position,
            dx,
            domain_length,
            min_window_cells=min_window_cells,
            window_fraction=window_fraction,
        )
        shock_rows.append(
            {
                "side": shock.side,
                "speed": shock.speed,
                "exact_x": shock.position,
                "numerical_x": shock_loc.position,
                "abs_error": shock_loc.abs_error,
                "gradient_value": shock_loc.gradient_value,
                "gradient_index": shock_loc.gradient_index,
                "search_window": {
                    "radius": shock_loc.window_radius,
                    "lower": shock_loc.window_lower,
                    "upper": shock_loc.window_upper,
                },
            }
        )

    band_positions = [features.contact_position] + [shock.position for shock in features.shocks]
    band = discontinuity_band_mask(x, band_positions, band_cells=band_cells, dx=dx)
    rho_abs_diff = np.abs(rho_num - rho_exact)
    band_l1 = float(np.sum(rho_abs_diff[band]) * dx)
    smooth_l1 = float(np.sum(rho_abs_diff[~band]) * dx)
    max_shock_error = (
        max(float(row["abs_error"]) for row in shock_rows) if shock_rows else 0.0
    )

    return {
        "test": cfg.name,
        "title": cfg.title,
        "precision": precision,
        "source_path": str(path),
        "N": nx,
        "t": float(header.t),
        "t_expected": cfg.t_end,
        "dx": dx,
        "band_cells": int(band_cells),
        "search": {
            "min_window_cells": int(min_window_cells),
            "window_fraction": float(window_fraction),
            "rule": (
                "max(abs(diff(values))/dx) on adjacent-cell midpoint in the "
                "exact-position window; contact windows are bounded away from "
                "exact shock positions if another discontinuity is closer than "
                "the default window"
            ),
        },
        "p_star": features.p_star,
        "u_star": features.u_star,
        "waves": {
            "left": asdict(features.left),
            "right": asdict(features.right),
        },
        "contact": {
            "exact_x": features.contact_position,
            "numerical_x": contact_loc.position,
            "abs_error": contact_loc.abs_error,
            "gradient_value": contact_loc.gradient_value,
            "gradient_index": contact_loc.gradient_index,
            "search_window": {
                "radius": contact_loc.window_radius,
                "lower": contact_loc.window_lower,
                "upper": contact_loc.window_upper,
            },
        },
        "shocks": shock_rows,
        "max_shock_abs_error": max_shock_error,
        "smooth_rho_l1": smooth_l1,
        "discontinuity_band_rho_l1": band_l1,
        "discontinuity_band_fraction": float(np.mean(band)),
    }


def _join_float(values: Iterable[float]) -> str:
    vals = list(values)
    return ";".join(f"{float(v):.12e}" for v in vals) if vals else ""


def _write_outputs(output_dir: Path, rows: list[dict[str, object]], input_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "summary.csv"
    json_path = output_dir / "summary.json"
    md_path = output_dir / "summary.md"

    columns = [
        "test",
        "precision",
        "N",
        "t",
        "dx",
        "band_cells",
        "search_window_radius",
        "contact_exact_x",
        "contact_numerical_x",
        "contact_abs_error",
        "shock_count",
        "shock_exact_xs",
        "shock_numerical_xs",
        "shock_abs_errors",
        "max_shock_abs_error",
        "smooth_rho_l1",
        "discontinuity_band_rho_l1",
        "discontinuity_band_fraction",
        "p_star",
        "u_star",
        "source_path",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            contact = row["contact"]
            shocks = row["shocks"]
            writer.writerow(
                {
                    "test": row["test"],
                    "precision": row["precision"],
                    "N": row["N"],
                    "t": row["t"],
                    "dx": row["dx"],
                    "band_cells": row["band_cells"],
                    "search_window_radius": contact["search_window"]["radius"],
                    "contact_exact_x": contact["exact_x"],
                    "contact_numerical_x": contact["numerical_x"],
                    "contact_abs_error": contact["abs_error"],
                    "shock_count": len(shocks),
                    "shock_exact_xs": _join_float(s["exact_x"] for s in shocks),
                    "shock_numerical_xs": _join_float(s["numerical_x"] for s in shocks),
                    "shock_abs_errors": _join_float(s["abs_error"] for s in shocks),
                    "max_shock_abs_error": row["max_shock_abs_error"],
                    "smooth_rho_l1": row["smooth_rho_l1"],
                    "discontinuity_band_rho_l1": row["discontinuity_band_rho_l1"],
                    "discontinuity_band_fraction": row["discontinuity_band_fraction"],
                    "p_star": row["p_star"],
                    "u_star": row["u_star"],
                    "source_path": row["source_path"],
                }
            )

    summary = {
        "mode": "report1_1d_feature_validation",
        "input_dir": str(input_dir),
        "rows": rows,
        "outputs": {
            "csv": str(csv_path),
            "json": str(json_path),
            "markdown": str(md_path),
        },
    }
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Report 1 1D Feature Validation",
        "",
        "Derived from existing final grids; the solver is not rerun.",
        "",
        "| test | precision | contact_abs_error | max_shock_abs_error | smooth_rho_l1 | discontinuity_band_rho_l1 | band_fraction |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        md_lines.append(
            f"| {row['test']} | {row['precision']} | "
            f"{row['contact']['abs_error']:.6e} | "
            f"{row['max_shock_abs_error']:.6e} | "
            f"{row['smooth_rho_l1']:.6e} | "
            f"{row['discontinuity_band_rho_l1']:.6e} | "
            f"{row['discontinuity_band_fraction']:.6e} |"
        )
    md_lines.extend(
        [
            "",
            "Band definition: cells within `band_cells*dx` of exact contact and shock positions only; rarefaction fans are excluded.",
            "Feature-location rule: strongest adjacent-cell gradient inside the exact-position search window.",
            "If an exact shock lies inside a contact's default search window, the contact window is deterministically narrowed before locating the density gradient.",
        ]
    )
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")


def build_summary(
    input_dir: Path,
    output_dir: Path,
    band_cells: int = 6,
    min_window_cells: int = 8,
    window_fraction: float = 0.05,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for test_name, cfg in TESTS.items():
        for precision in PRECISIONS:
            path = input_dir / f"{test_name}_{precision}_grid.bin"
            if not path.is_file():
                raise FileNotFoundError(f"Missing required grid: {path}")
            rows.append(
                analyse_case(
                    cfg,
                    precision,
                    path,
                    band_cells=band_cells,
                    min_window_cells=min_window_cells,
                    window_fraction=window_fraction,
                )
            )
    _write_outputs(output_dir, rows, input_dir)
    return rows


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build derived 1D feature-validation evidence for Report 1."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("experiments/week4/float_regression/1d"),
        help="Directory containing existing final 1D *_grid.bin files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("experiments/report1/evidence/1d_feature_validation"),
        help="Directory for summary.csv, summary.json, and summary.md.",
    )
    parser.add_argument("--band-cells", type=int, default=6)
    parser.add_argument("--min-window-cells", type=int, default=8)
    parser.add_argument("--window-fraction", type=float, default=0.05)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    rows = build_summary(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        band_cells=args.band_cells,
        min_window_cells=args.min_window_cells,
        window_fraction=args.window_fraction,
    )
    print(
        json.dumps(
            {
                "output_dir": str(args.output_dir),
                "rows": len(rows),
                "summary_csv": str(args.output_dir / "summary.csv"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
