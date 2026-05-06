"""
plot_divergence_marker.py — HLLC vs Rusanov first-divergence marker.

Stage 1 (A2-S1): "visible" mode (presentation-level rel_tol).
Stage 2 (A2-S2): "noise_floor" mode (MCA p=53 per-cell envelope) and
                 "strict_fp" mode (ulp-calibrated fallback, degraded).
"""

from __future__ import annotations

import argparse
import os
import warnings
from pathlib import Path
from typing import Literal, Optional

import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Module-level constants — no magic numbers elsewhere
# ---------------------------------------------------------------------------
DEFAULT_SAFETY_SIGMA = 3.0       # 3-σ envelope around MCA noise floor
DEFAULT_K_GRAD = 1.0             # gradient-proportional tolerance component
DEFAULT_K_EPS_FALLBACK = 10.0   # ulp multiplier for strict_fp fallback
DEFAULT_VISIBLE_REL_TOL = 1e-3  # human-eye threshold, explicitly non-statistical
REQUIRED_PRECISION_BITS = 53    # .npz metadata contract for noise_floor mode
DEFAULT_LABEL_MIN_DISTANCE = 10  # min index spacing between text labels
DEFAULT_MAX_ONSET_LABELS = 4     # cap onset text labels per panel
DEFAULT_MAX_REJOIN_LABELS = 3    # cap rejoin text labels per panel

# Column mapping in 1D data files: x  rho  u  v  p
COLUMN_MAP = {"rho": 1, "u": 2, "v": 3, "p": 4}

# Map "variable" CLI string → key in noise-floor .npz
NOISE_FLOOR_KEY_MAP = {
    "rho": "rho_std",
    "u": "u_std",
    "v": "v_std",
    "p": "p_std",
}

Mode = Literal["noise_floor", "strict_fp", "visible"]
SourcePrecision = Literal["float32", "float64"]


# ---------------------------------------------------------------------------
# Shared tolerance helper — single source of truth for all three modes
# ---------------------------------------------------------------------------

def _tolerance(
    mode: Mode,
    a: np.ndarray,
    b: np.ndarray,
    *,
    noise_floor_a: Optional[np.ndarray] = None,
    noise_floor_b: Optional[np.ndarray] = None,
    safety: float = DEFAULT_SAFETY_SIGMA,
    k_grad: float = DEFAULT_K_GRAD,
    abs_floor_frac: Optional[float] = None,
    source_precision: SourcePrecision = "float64",
    k_eps: float = DEFAULT_K_EPS_FALLBACK,
    visible_rel_tol: float = DEFAULT_VISIBLE_REL_TOL,
) -> np.ndarray:
    """Return the pointwise tolerance array for the chosen mode.

    All three detection functions (`first_divergence_index`,
    `all_divergence_indices`, `divergence_segment_onsets`) delegate here so
    that the mode semantics live in exactly one place.
    """
    if mode == "visible":
        # Presentation-level: scale by local magnitude, no statistical meaning.
        return visible_rel_tol * np.maximum(np.abs(a), np.abs(b))

    if mode == "noise_floor":
        if noise_floor_a is None or noise_floor_b is None:
            raise ValueError(
                "mode='noise_floor' requires both noise_floor_a and noise_floor_b"
            )
        # Cell-wise 3-σ envelope over the two solvers' MCA std fields.
        noise = safety * np.maximum(noise_floor_a, noise_floor_b)
        # Symmetric gradient term soaks up 1-cell shock offset (big |∇|, no
        # real amplitude divergence).
        avg_grad = 0.5 * (np.abs(np.gradient(a)) + np.abs(np.gradient(b)))
        # Global safety: spike somewhere in the worst-case noise floor becomes
        # the per-cell abs floor everywhere, preventing spurious flags in cells
        # where the local std is near zero.
        if abs_floor_frac is not None:
            abs_floor = float(abs_floor_frac)
        else:
            abs_floor = safety * np.maximum(noise_floor_a, noise_floor_b).max()
        return noise + k_grad * avg_grad + abs_floor

    if mode == "strict_fp":
        # Fallback when no MCA data is available. We warn because the k_eps
        # multiplier is not calibrated against empirical noise — it is a rough
        # ulp-count guard, typically loose by 1-2 orders of magnitude for a
        # shock-capturing solver.
        warnings.warn(
            "mode='strict_fp' is a degraded fallback with uncalibrated "
            "thresholds; prefer mode='noise_floor' with MCA-sampled envelope.",
            stacklevel=3,
        )
        if source_precision == "float32":
            eps = np.finfo(np.float32).eps
        elif source_precision == "float64":
            eps = np.finfo(np.float64).eps
        else:
            raise ValueError(
                f"Unknown source_precision: {source_precision!r}; "
                "choose 'float32' or 'float64'."
            )
        ulp_term = k_eps * eps * np.maximum(np.abs(a), np.abs(b))
        grad_term = k_grad * 0.5 * (np.abs(np.gradient(a)) + np.abs(np.gradient(b)))
        return ulp_term + grad_term

    raise ValueError(
        f"Unknown mode: {mode!r}. Choose from 'visible', 'noise_floor', 'strict_fp'."
    )


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def first_divergence_index(
    a: np.ndarray,
    b: np.ndarray,
    mode: Mode = "noise_floor",
    # noise_floor mode:
    noise_floor_a: Optional[np.ndarray] = None,
    noise_floor_b: Optional[np.ndarray] = None,
    safety: float = DEFAULT_SAFETY_SIGMA,
    # shared:
    k_grad: float = DEFAULT_K_GRAD,
    abs_floor_frac: Optional[float] = None,
    # strict_fp fallback:
    source_precision: SourcePrecision = "float64",
    k_eps: float = DEFAULT_K_EPS_FALLBACK,
    # visible mode:
    visible_rel_tol: float = DEFAULT_VISIBLE_REL_TOL,
) -> Optional[int]:
    """Return the first index i where |a - b| exceeds the per-mode tolerance.

    Modes:
      "visible"     — rel_tol * max(|a|,|b|); presentation only.
      "noise_floor" — 3σ MCA envelope + k_grad·|∇avg| + abs_floor.
      "strict_fp"   — k_eps·eps·max(|a|,|b|) + k_grad·|∇avg|; degraded fallback.
    """
    tol = _tolerance(
        mode, a, b,
        noise_floor_a=noise_floor_a, noise_floor_b=noise_floor_b,
        safety=safety, k_grad=k_grad, abs_floor_frac=abs_floor_frac,
        source_precision=source_precision, k_eps=k_eps,
        visible_rel_tol=visible_rel_tol,
    )
    diff = np.abs(a - b)
    idx = np.where(diff > tol)[0]
    return int(idx[0]) if len(idx) else None


def all_divergence_indices(
    a: np.ndarray,
    b: np.ndarray,
    mode: Mode = "visible",
    noise_floor_a: Optional[np.ndarray] = None,
    noise_floor_b: Optional[np.ndarray] = None,
    safety: float = DEFAULT_SAFETY_SIGMA,
    k_grad: float = DEFAULT_K_GRAD,
    abs_floor_frac: Optional[float] = None,
    source_precision: SourcePrecision = "float64",
    k_eps: float = DEFAULT_K_EPS_FALLBACK,
    visible_rel_tol: float = DEFAULT_VISIBLE_REL_TOL,
) -> np.ndarray:
    """Return every index i where |a - b| exceeds the per-mode tolerance."""
    tol = _tolerance(
        mode, a, b,
        noise_floor_a=noise_floor_a, noise_floor_b=noise_floor_b,
        safety=safety, k_grad=k_grad, abs_floor_frac=abs_floor_frac,
        source_precision=source_precision, k_eps=k_eps,
        visible_rel_tol=visible_rel_tol,
    )
    diff = np.abs(a - b)
    return np.where(diff > tol)[0]


def divergence_segment_onsets(
    a: np.ndarray,
    b: np.ndarray,
    mode: Mode = "visible",
    noise_floor_a: Optional[np.ndarray] = None,
    noise_floor_b: Optional[np.ndarray] = None,
    safety: float = DEFAULT_SAFETY_SIGMA,
    k_grad: float = DEFAULT_K_GRAD,
    abs_floor_frac: Optional[float] = None,
    source_precision: SourcePrecision = "float64",
    k_eps: float = DEFAULT_K_EPS_FALLBACK,
    visible_rel_tol: float = DEFAULT_VISIBLE_REL_TOL,
) -> list[int]:
    """Return the onset index of each contiguous divergent segment.

    A "segment" is a maximal run of consecutive indices where |a - b| > tol.
    Onset = first index of each run. Keeps per-shock / per-contact entry
    points visible without cluttering the plot with one label per cell.
    """
    # Call _tolerance directly (peer to all_divergence_indices) so that the
    # strict_fp stacklevel=3 warning points to the user's call site rather
    # than to this function's internal hop through all_divergence_indices.
    tol = _tolerance(
        mode, a, b,
        noise_floor_a=noise_floor_a, noise_floor_b=noise_floor_b,
        safety=safety, k_grad=k_grad, abs_floor_frac=abs_floor_frac,
        source_precision=source_precision, k_eps=k_eps,
        visible_rel_tol=visible_rel_tol,
    )
    diff = np.abs(a - b)
    idx = np.where(diff > tol)[0]
    if len(idx) == 0:
        return []
    gaps = np.diff(idx) > 1
    onset_mask = np.concatenate(([True], gaps))
    return [int(i) for i in idx[onset_mask]]


def _filtered_divergence_segments(
    a: np.ndarray,
    b: np.ndarray,
    mode: Mode = "visible",
    noise_floor_a: Optional[np.ndarray] = None,
    noise_floor_b: Optional[np.ndarray] = None,
    safety: float = DEFAULT_SAFETY_SIGMA,
    k_grad: float = DEFAULT_K_GRAD,
    abs_floor_frac: Optional[float] = None,
    source_precision: SourcePrecision = "float64",
    k_eps: float = DEFAULT_K_EPS_FALLBACK,
    visible_rel_tol: float = DEFAULT_VISIBLE_REL_TOL,
    *,
    merge_gap: int = 1,
    min_segment_len: int = 1,
    min_onset_distance: int = 6,
) -> list[tuple[int, int, float]]:
    """Return de-cluttered divergent segments as (start, end, score).

    This is a stricter variant of raw segment extraction intended for
    supervisor-facing figures: it merges tiny gaps, drops tiny segments, and
    suppresses multiple nearby onsets in the same transition region.
    """
    tol = _tolerance(
        mode, a, b,
        noise_floor_a=noise_floor_a, noise_floor_b=noise_floor_b,
        safety=safety, k_grad=k_grad, abs_floor_frac=abs_floor_frac,
        source_precision=source_precision, k_eps=k_eps,
        visible_rel_tol=visible_rel_tol,
    )
    diff = np.abs(a - b)
    mask = diff > tol
    n = len(mask)
    if n == 0 or not np.any(mask):
        return []

    # 1) Merge small zero-gaps between two divergent runs.
    if merge_gap > 0:
        i = 0
        while i < n:
            if not mask[i]:
                z0 = i
                while i < n and not mask[i]:
                    i += 1
                z1 = i
                gap_len = z1 - z0
                if z0 > 0 and z1 < n and gap_len <= merge_gap:
                    mask[z0:z1] = True
            else:
                i += 1

    # 2) Build segments (start, end inclusive, score=max excess over tol).
    segments: list[tuple[int, int, float]] = []
    i = 0
    while i < n:
        if not mask[i]:
            i += 1
            continue
        s = i
        while i + 1 < n and mask[i + 1]:
            i += 1
        e = i
        seg_len = e - s + 1
        if seg_len >= min_segment_len:
            score = float(np.max(diff[s:e + 1] - tol[s:e + 1]))
            segments.append((s, e, score))
        i += 1

    if not segments:
        return []

    # 3) Non-maximum suppression in onset-index space.
    kept: list[tuple[int, float]] = []
    for s, _e, score in segments:
        if not kept:
            kept.append((s, score))
            continue
        prev_s, prev_score = kept[-1]
        if s - prev_s <= min_onset_distance:
            if score > prev_score:
                kept[-1] = (s, score)
        else:
            kept.append((s, score))
    kept_onsets = [int(s) for s, _score in kept]
    onset_set = set(kept_onsets)
    return [(s, e, score) for s, e, score in segments if s in onset_set]


def filtered_divergence_segment_onsets(
    a: np.ndarray,
    b: np.ndarray,
    mode: Mode = "visible",
    noise_floor_a: Optional[np.ndarray] = None,
    noise_floor_b: Optional[np.ndarray] = None,
    safety: float = DEFAULT_SAFETY_SIGMA,
    k_grad: float = DEFAULT_K_GRAD,
    abs_floor_frac: Optional[float] = None,
    source_precision: SourcePrecision = "float64",
    k_eps: float = DEFAULT_K_EPS_FALLBACK,
    visible_rel_tol: float = DEFAULT_VISIBLE_REL_TOL,
    *,
    merge_gap: int = 1,
    min_segment_len: int = 1,
    min_onset_distance: int = 6,
) -> list[int]:
    """Return de-cluttered divergence onsets for presentation plots."""
    seg = _filtered_divergence_segments(
        a, b,
        mode=mode,
        noise_floor_a=noise_floor_a,
        noise_floor_b=noise_floor_b,
        safety=safety,
        k_grad=k_grad,
        abs_floor_frac=abs_floor_frac,
        source_precision=source_precision,
        k_eps=k_eps,
        visible_rel_tol=visible_rel_tol,
        merge_gap=merge_gap,
        min_segment_len=min_segment_len,
        min_onset_distance=min_onset_distance,
    )
    return [int(s) for s, _e, _score in seg]


def filtered_divergence_segment_rejoins(
    a: np.ndarray,
    b: np.ndarray,
    mode: Mode = "visible",
    noise_floor_a: Optional[np.ndarray] = None,
    noise_floor_b: Optional[np.ndarray] = None,
    safety: float = DEFAULT_SAFETY_SIGMA,
    k_grad: float = DEFAULT_K_GRAD,
    abs_floor_frac: Optional[float] = None,
    source_precision: SourcePrecision = "float64",
    k_eps: float = DEFAULT_K_EPS_FALLBACK,
    visible_rel_tol: float = DEFAULT_VISIBLE_REL_TOL,
    *,
    merge_gap: int = 1,
    min_segment_len: int = 1,
    min_onset_distance: int = 6,
) -> list[int]:
    """Return de-cluttered rejoin indices where separated curves overlap again."""
    seg = _filtered_divergence_segments(
        a, b,
        mode=mode,
        noise_floor_a=noise_floor_a,
        noise_floor_b=noise_floor_b,
        safety=safety,
        k_grad=k_grad,
        abs_floor_frac=abs_floor_frac,
        source_precision=source_precision,
        k_eps=k_eps,
        visible_rel_tol=visible_rel_tol,
        merge_gap=merge_gap,
        min_segment_len=min_segment_len,
        min_onset_distance=min_onset_distance,
    )
    n = len(a)
    out: list[int] = []
    for _s, e, _score in seg:
        if e + 1 < n:
            out.append(int(e + 1))
    return out


# ---------------------------------------------------------------------------
# Noise-floor .npz loader
# ---------------------------------------------------------------------------

def load_noise_floor(npz_path: Path, variable: str) -> np.ndarray:
    """Load a per-cell MCA noise-floor std array for ``variable``.

    Parameters
    ----------
    npz_path : Path
        Output of ``scripts/metrics/compute_noise_floor.py``.
    variable : {"rho","u","v","p"}
        Which field's std to return.

    Raises
    ------
    KeyError : for unknown variable.
    ValueError : if the .npz metadata does not assert p=53 (plan §A2.1 contract).
    """
    if variable not in NOISE_FLOOR_KEY_MAP:
        raise KeyError(
            f"Unknown variable {variable!r}; choose from {sorted(NOISE_FLOOR_KEY_MAP)}"
        )
    key = NOISE_FLOOR_KEY_MAP[variable]
    with np.load(str(npz_path), allow_pickle=True) as data:
        # metadata is stored as a 0-D object array — unpack via .item().
        meta = data["metadata"].item()
        precision = meta.get("precision_bits")
        if precision != REQUIRED_PRECISION_BITS:
            raise ValueError(
                f"{npz_path}: metadata.precision_bits={precision!r}, "
                f"expected {REQUIRED_PRECISION_BITS} (MCA p=53 contract)."
            )
        return np.asarray(data[key])


# ---------------------------------------------------------------------------
# Single-panel plot helper
# ---------------------------------------------------------------------------

def plot_single_panel(
    ax: plt.Axes,
    x_a: np.ndarray,
    a: np.ndarray,
    x_b: np.ndarray,
    b: np.ndarray,
    label_a: str,
    label_b: str,
    variable: str,
    mode: Mode = "visible",
    visible_rel_tol: float = DEFAULT_VISIBLE_REL_TOL,
    # Stage-2 extensions (all optional for backward compat):
    noise_floor_a: Optional[np.ndarray] = None,
    noise_floor_b: Optional[np.ndarray] = None,
    safety: float = DEFAULT_SAFETY_SIGMA,
    k_grad: float = DEFAULT_K_GRAD,
    abs_floor_frac: Optional[float] = None,
    source_precision: SourcePrecision = "float64",
    k_eps: float = DEFAULT_K_EPS_FALLBACK,
    # Marker policy for readability:
    show_all_divergent_cells: bool = False,
    show_rejoin_points: bool = True,
    show_rejoin_labels: bool = True,
    onset_merge_gap: int = 1,
    onset_min_segment_len: int = 1,
    onset_min_distance: int = 6,
    label_min_distance: int = DEFAULT_LABEL_MIN_DISTANCE,
    max_onset_labels: int = DEFAULT_MAX_ONSET_LABELS,
    max_rejoin_labels: int = DEFAULT_MAX_REJOIN_LABELS,
    title: Optional[str] = None,
) -> Optional[int]:
    """Plot two solver lines and annotate the first-divergence index.

    Returns the first-divergence index (or None).
    """
    ax.plot(x_a, a, color="tab:blue", linewidth=1.5, label=label_a)
    ax.plot(x_b, b, color="tab:red", linewidth=1.5, linestyle="--", label=label_b)

    # Supervisor-facing default: only mark onset points where profiles clearly
    # move from overlapping to separated (de-cluttered by merge/NMS filters).
    detector_kwargs = dict(
        mode=mode,
        noise_floor_a=noise_floor_a, noise_floor_b=noise_floor_b,
        safety=safety, k_grad=k_grad, abs_floor_frac=abs_floor_frac,
        source_precision=source_precision, k_eps=k_eps,
        visible_rel_tol=visible_rel_tol,
    )
    all_idx = all_divergence_indices(a, b, **detector_kwargs)
    seg_onsets = filtered_divergence_segment_onsets(
        a, b,
        **detector_kwargs,
        merge_gap=onset_merge_gap,
        min_segment_len=onset_min_segment_len,
        min_onset_distance=onset_min_distance,
    )
    seg_rejoins = filtered_divergence_segment_rejoins(
        a, b,
        **detector_kwargs,
        merge_gap=onset_merge_gap,
        min_segment_len=onset_min_segment_len,
        min_onset_distance=onset_min_distance,
    )
    div_idx = int(all_idx[0]) if len(all_idx) else None

    if div_idx is not None:
        def _pick_label_indices(points: list[int], max_labels: int) -> list[int]:
            if not points or max_labels <= 0:
                return []
            picked: list[int] = []
            for p in points:
                if not picked or p - picked[-1] >= label_min_distance:
                    picked.append(p)
            if len(picked) <= max_labels:
                return picked
            slots = np.unique(np.linspace(0, len(picked) - 1, num=max_labels, dtype=int))
            return [picked[int(i)] for i in slots]

        span_x = float(x_a[-1] - x_a[0]) if len(x_a) > 1 else 1.0
        span_y = float(np.max(a) - np.min(a))
        if span_y <= 0.0:
            span_y = 1.0

        if show_all_divergent_cells:
            ax.plot(x_a[all_idx], a[all_idx], "x",
                    color="tab:red", markersize=6, markeredgewidth=1.2,
                    label=f"Divergent cells (n={len(all_idx)})")

        # Mark every kept onset point, but annotate only a sparse subset.
        onset_label_idx = set(_pick_label_indices(seg_onsets, max_onset_labels))
        for k, onset in enumerate(seg_onsets):
            xo = x_a[onset]
            yo = a[onset]
            ax.plot(xo, yo, "x",
                    color="darkred", markersize=11, markeredgewidth=2.2,
                    label="Divergence onset" if k == 0 else None)
            if onset in onset_label_idx:
                level = (k % 3) + 1
                ax.annotate(
                    f"i={onset}\nx={xo:.3f}",
                    xy=(xo, yo),
                    xytext=(xo + 0.02 * span_x, yo + 0.035 * level * span_y),
                    fontsize=7,
                    color="darkred",
                    arrowprops=dict(arrowstyle="->", color="darkred", lw=0.8),
                )

        if show_rejoin_points:
            rejoin_label_idx = set(_pick_label_indices(seg_rejoins, max_rejoin_labels))
            for k, rejoin in enumerate(seg_rejoins):
                xr = x_a[rejoin]
                yr = a[rejoin]
                ax.plot(
                    xr, yr, "o",
                    color="darkgreen", markersize=5, markeredgewidth=0.8,
                    label="Rejoin point" if k == 0 else None,
                )
                if show_rejoin_labels and rejoin in rejoin_label_idx:
                    level = (k % 3) + 1
                    ax.annotate(
                        f"i={rejoin}\nx={xr:.3f}",
                        xy=(xr, yr),
                        xytext=(xr - 0.02 * span_x, yr - 0.035 * level * span_y),
                        fontsize=7,
                        color="darkgreen",
                        arrowprops=dict(arrowstyle="->", color="darkgreen", lw=0.8),
                    )
    else:
        ax.text(
            0.98, 0.98,
            f"No divergence detected\nmode={mode}",
            transform=ax.transAxes,
            ha="right", va="top",
            fontsize=7, color="gray",
        )

    if title:
        ax.set_title(title, fontsize=9)
    ax.set_xlabel("x", fontsize=8)
    ax.set_ylabel(variable, fontsize=8)
    ax.legend(fontsize=7)
    ax.tick_params(labelsize=7)

    return div_idx


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _load_column(path: str, variable: str) -> tuple[np.ndarray, np.ndarray]:
    """Load (x, var) arrays from a data file."""
    data = np.loadtxt(path)
    # Defensive shape check: mirrors the pattern in compute_noise_floor.py so
    # a truncated or malformed data file fails with a clear message instead of
    # an IndexError deep inside the column indexing below.
    expected_cols = max(COLUMN_MAP.values()) + 1
    if data.ndim != 2 or data.shape[1] < expected_cols:
        raise ValueError(
            f"{path}: expected 2-D array with >= {expected_cols} columns "
            f"(x, rho, u, v, p), got shape {data.shape}"
        )
    x = data[:, 0]
    col = COLUMN_MAP[variable]
    var = data[:, col]
    return x, var


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Plot HLLC vs Rusanov with first-divergence marker."
    )
    p.add_argument("--input-a", required=True, metavar="PATH", help="Path to solver A data file.")
    p.add_argument("--label-a", default="A", metavar="STR", help="Label for solver A.")
    p.add_argument("--input-b", required=True, metavar="PATH", help="Path to solver B data file.")
    p.add_argument("--label-b", default="B", metavar="STR", help="Label for solver B.")
    p.add_argument("--variable", choices=list(COLUMN_MAP.keys()), default="rho",
                   help="Variable to plot (rho=col 1, u=col 2, v=col 3, p=col 4).")
    p.add_argument("--mode", choices=["visible", "noise_floor", "strict_fp"], default="noise_floor",
                   help="Divergence-detection mode (default: noise_floor).")
    p.add_argument("--visible-rel-tol", type=float, default=DEFAULT_VISIBLE_REL_TOL,
                   metavar="FLOAT", help="Relative tolerance for visible mode.")
    # Stage-2 noise_floor arguments
    p.add_argument("--noise-floor-a", default=None, metavar="PATH",
                   help="Path to solver-A noise_floor.npz (required for --mode noise_floor).")
    p.add_argument("--noise-floor-b", default=None, metavar="PATH",
                   help="Path to solver-B noise_floor.npz (required for --mode noise_floor).")
    p.add_argument("--safety", type=float, default=DEFAULT_SAFETY_SIGMA, metavar="FLOAT",
                   help="σ multiplier for noise_floor envelope (default 3.0).")
    p.add_argument("--k-grad", type=float, default=DEFAULT_K_GRAD, metavar="FLOAT",
                   help="Gradient-proportional tolerance coefficient (default 1.0).")
    p.add_argument("--abs-floor-frac", type=float, default=None, metavar="FLOAT",
                   help="Explicit absolute floor; default safety·max(max(nf_a),max(nf_b)).")
    # Stage-2 strict_fp arguments
    p.add_argument("--source-precision", choices=["float32", "float64"], default="float64",
                   help="Source precision for strict_fp mode (default float64).")
    p.add_argument("--k-eps", type=float, default=DEFAULT_K_EPS_FALLBACK, metavar="FLOAT",
                   help="ulp multiplier for strict_fp mode (default 10.0).")
    p.add_argument("--show-all-divergent-cells", action="store_true",
                   help="Also mark every divergent cell with small x (off by default).")
    p.add_argument("--hide-rejoin-points", action="store_true",
                   help="Hide points where curves rejoin (on by default).")
    p.add_argument("--hide-rejoin-labels", action="store_true",
                   help="Hide text labels for rejoin points (markers remain).")
    p.add_argument("--onset-merge-gap", type=int, default=1, metavar="INT",
                   help="Merge non-divergent gaps up to this many cells before onset detection.")
    p.add_argument("--onset-min-segment-len", type=int, default=1, metavar="INT",
                   help="Drop divergent segments shorter than this many cells.")
    p.add_argument("--onset-min-distance", type=int, default=6, metavar="INT",
                   help="Suppress nearby onset markers within this many cell indices.")
    p.add_argument("--label-min-distance", type=int, default=DEFAULT_LABEL_MIN_DISTANCE, metavar="INT",
                   help="Minimum index spacing between annotated labels.")
    p.add_argument("--max-onset-labels", type=int, default=DEFAULT_MAX_ONSET_LABELS, metavar="INT",
                   help="Maximum number of onset text labels per panel.")
    p.add_argument("--max-rejoin-labels", type=int, default=DEFAULT_MAX_REJOIN_LABELS, metavar="INT",
                   help="Maximum number of rejoin text labels per panel.")
    p.add_argument("--output", required=True, metavar="PATH", help="Output PNG path.")
    p.add_argument("--title", default=None, metavar="STR", help="Optional figure title.")
    return p


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    # Post-parse validation: noise_floor mode requires both .npz inputs.
    if args.mode == "noise_floor":
        if not args.noise_floor_a or not args.noise_floor_b:
            parser.error(
                "--mode noise_floor requires --noise-floor-a and --noise-floor-b"
            )

    x_a, a = _load_column(args.input_a, args.variable)
    x_b, b = _load_column(args.input_b, args.variable)

    # Load noise-floor arrays when in noise_floor mode.
    nf_a = nf_b = None
    if args.mode == "noise_floor":
        nf_a = load_noise_floor(Path(args.noise_floor_a), args.variable)
        nf_b = load_noise_floor(Path(args.noise_floor_b), args.variable)

    fig, ax = plt.subplots(figsize=(7, 4))
    div_idx = plot_single_panel(
        ax, x_a, a, x_b, b,
        label_a=args.label_a,
        label_b=args.label_b,
        variable=args.variable,
        mode=args.mode,
        visible_rel_tol=args.visible_rel_tol,
        noise_floor_a=nf_a,
        noise_floor_b=nf_b,
        safety=args.safety,
        k_grad=args.k_grad,
        abs_floor_frac=args.abs_floor_frac,
        source_precision=args.source_precision,
        k_eps=args.k_eps,
        show_all_divergent_cells=args.show_all_divergent_cells,
        show_rejoin_points=not args.hide_rejoin_points,
        show_rejoin_labels=not args.hide_rejoin_labels,
        onset_merge_gap=args.onset_merge_gap,
        onset_min_segment_len=args.onset_min_segment_len,
        onset_min_distance=args.onset_min_distance,
        label_min_distance=args.label_min_distance,
        max_onset_labels=args.max_onset_labels,
        max_rejoin_labels=args.max_rejoin_labels,
        title=args.title,
    )

    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    fig.savefig(args.output, dpi=150)
    plt.close(fig)

    if div_idx is not None:
        print(f"First divergence at index {div_idx}, x={x_a[div_idx]:.4f} (mode={args.mode})")
    else:
        print(f"No divergence detected (mode={args.mode})")


if __name__ == "__main__":
    main()
