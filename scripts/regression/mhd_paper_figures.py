#!/usr/bin/env python3
"""Small NumPy + stdlib helpers for paper-facing MHD validation figures."""

from __future__ import annotations

import math
import pathlib
import struct
import zlib
from typing import Iterable, Sequence

import numpy as np

RHO, MX, MY, MZ, BX, BY, BZ, E, PSI = range(9)


def mhd_primitive(arr: np.ndarray, gamma: float) -> dict[str, np.ndarray]:
    """Convert conserved ideal-MHD variables to primitive fields."""
    rho = arr[..., RHO]
    vx = arr[..., MX] / rho
    vy = arr[..., MY] / rho
    vz = arr[..., MZ] / rho
    Bx = arr[..., BX]
    By = arr[..., BY]
    Bz = arr[..., BZ]
    energy = arr[..., E]
    kinetic = 0.5 * rho * (vx * vx + vy * vy + vz * vz)
    magnetic = 0.5 * (Bx * Bx + By * By + Bz * Bz)
    p = (gamma - 1.0) * (energy - kinetic - magnetic)
    return {
        "rho": rho,
        "vx": vx,
        "vy": vy,
        "vz": vz,
        "Bx": Bx,
        "By": By,
        "Bz": Bz,
        "p": p,
    }


def ensure_parent(path: str | pathlib.Path) -> pathlib.Path:
    out = pathlib.Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    return out


def save_png_rgb(path: str | pathlib.Path, image: np.ndarray) -> pathlib.Path:
    """Write a uint8 RGB PNG without third-party image libraries."""
    out = ensure_parent(path)
    arr = np.asarray(image, dtype=np.uint8)
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError(f"expected RGB image shape (height, width, 3), got {arr.shape}")
    height, width, _ = arr.shape

    def chunk(kind: bytes, data: bytes) -> bytes:
        payload = kind + data
        return struct.pack(">I", len(data)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF)

    rows = b"".join(b"\x00" + arr[y].tobytes() for y in range(height))
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(rows, level=6))
    png += chunk(b"IEND", b"")
    out.write_bytes(png)
    return out


_FONT = {
    " ": ("000", "000", "000", "000", "000", "000", "000"),
    "-": ("000", "000", "000", "111", "000", "000", "000"),
    ".": ("000", "000", "000", "000", "000", "110", "110"),
    "+": ("000", "010", "010", "111", "010", "010", "000"),
    "0": ("111", "101", "101", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "010", "010", "111"),
    "2": ("111", "001", "001", "111", "100", "100", "111"),
    "3": ("111", "001", "001", "111", "001", "001", "111"),
    "4": ("101", "101", "101", "111", "001", "001", "001"),
    "5": ("111", "100", "100", "111", "001", "001", "111"),
    "6": ("111", "100", "100", "111", "101", "101", "111"),
    "7": ("111", "001", "001", "010", "010", "010", "010"),
    "8": ("111", "101", "101", "111", "101", "101", "111"),
    "9": ("111", "101", "101", "111", "001", "001", "111"),
    "=": ("000", "111", "000", "111", "000", "000", "000"),
    "B": ("110", "101", "101", "110", "101", "101", "110"),
    "L": ("100", "100", "100", "100", "100", "100", "111"),
    "M": ("101", "111", "111", "101", "101", "101", "101"),
    "W": ("101", "101", "101", "101", "111", "111", "101"),
    "a": ("000", "000", "111", "001", "111", "101", "111"),
    "b": ("100", "100", "110", "101", "101", "101", "110"),
    "c": ("000", "000", "111", "100", "100", "100", "111"),
    "d": ("001", "001", "011", "101", "101", "101", "011"),
    "e": ("000", "000", "111", "101", "111", "100", "111"),
    "g": ("000", "000", "111", "101", "111", "001", "111"),
    "h": ("100", "100", "110", "101", "101", "101", "101"),
    "i": ("010", "000", "110", "010", "010", "010", "111"),
    "l": ("110", "010", "010", "010", "010", "010", "111"),
    "m": ("000", "000", "110", "111", "101", "101", "101"),
    "n": ("000", "000", "110", "101", "101", "101", "101"),
    "o": ("000", "000", "111", "101", "101", "101", "111"),
    "p": ("000", "000", "110", "101", "101", "110", "100"),
    "q": ("000", "000", "011", "101", "101", "011", "001"),
    "r": ("000", "000", "110", "101", "100", "100", "100"),
    "s": ("000", "000", "111", "100", "111", "001", "111"),
    "t": ("010", "010", "111", "010", "010", "010", "011"),
    "u": ("000", "000", "101", "101", "101", "101", "111"),
    "v": ("000", "000", "101", "101", "101", "101", "010"),
    "x": ("000", "000", "101", "101", "010", "101", "101"),
    "y": ("000", "000", "101", "101", "111", "001", "110"),
}


def _draw_rect(img: np.ndarray, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
    img[y0:y1, x0:x1] = color


def _draw_line(img: np.ndarray, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    height, width = img.shape[:2]
    while True:
        if 0 <= x < width and 0 <= y < height:
            img[y, x] = color
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def _draw_text(
    img: np.ndarray,
    x: int,
    y: int,
    text: str,
    color: tuple[int, int, int] = (0, 0, 0),
    scale: int = 2,
) -> None:
    cursor = x
    for ch in text:
        glyph = _FONT.get(ch)
        if glyph is None:
            cursor += 4 * scale
            continue
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "1":
                    _draw_rect(
                        img,
                        cursor + col * scale,
                        y + row * scale,
                        cursor + (col + 1) * scale,
                        y + (row + 1) * scale,
                        color,
                    )
        cursor += 4 * scale


def _nice(value: float) -> str:
    if not math.isfinite(value):
        return "nan"
    if abs(value) >= 1000.0 or (0.0 < abs(value) < 0.01):
        return f"{value:.1e}"
    return f"{value:.3g}"


def plot_line_panels(
    path: str | pathlib.Path,
    x: np.ndarray,
    panels: Iterable[tuple[str, np.ndarray]],
    *,
    width: int = 1600,
    height: int = 1100,
) -> pathlib.Path:
    """Render a 2x2 black-line profile figure to PNG."""
    panel_list = [(title, np.asarray(values, dtype=float)) for title, values in panels]
    if len(panel_list) != 4:
        raise ValueError(f"expected exactly four panels, got {len(panel_list)}")
    x = np.asarray(x, dtype=float)
    if x.ndim != 1 or x.size < 2:
        raise ValueError("x must be a one-dimensional array with at least two samples")
    if any(values.shape != x.shape for _, values in panel_list):
        raise ValueError("all panel arrays must have the same shape as x")

    img = np.full((height, width, 3), 255, dtype=np.uint8)
    black = (0, 0, 0)
    gray = (180, 180, 180)
    margins = (90, 55, 50, 45)  # left, top, right, bottom
    gap_x, gap_y = 70, 75
    plot_w = (width - margins[0] - margins[2] - gap_x) // 2
    plot_h = (height - margins[1] - margins[3] - gap_y) // 2
    xmin, xmax = float(x.min()), float(x.max())
    if xmax == xmin:
        raise ValueError("x range is zero")

    for idx, (title, values) in enumerate(panel_list):
        row, col = divmod(idx, 2)
        x0 = margins[0] + col * (plot_w + gap_x)
        y0 = margins[1] + row * (plot_h + gap_y)
        x1 = x0 + plot_w
        y1 = y0 + plot_h
        _draw_line(img, x0, y0, x1, y0, black)
        _draw_line(img, x0, y1, x1, y1, black)
        _draw_line(img, x0, y0, x0, y1, black)
        _draw_line(img, x1, y0, x1, y1, black)
        _draw_text(img, x0 + 6, y0 + 7, title, black, scale=3)

        ymin, ymax = float(np.nanmin(values)), float(np.nanmax(values))
        pad = 0.06 * (ymax - ymin) if ymax > ymin else 1.0
        ymin -= pad
        ymax += pad
        for frac in (0.25, 0.5, 0.75):
            yy = int(round(y0 + frac * plot_h))
            _draw_line(img, x0, yy, x1, yy, gray)
        for frac in (0.0, 0.5, 1.0):
            xx = int(round(x0 + frac * plot_w))
            _draw_line(img, xx, y1, xx, y1 + 9, black)
        for val, yy in ((ymax, y0 + 31), (ymin, y1 - 18)):
            _draw_text(img, x0 + 8, yy, _nice(val), black, scale=2)

        xs = np.rint(x0 + (x - xmin) / (xmax - xmin) * (plot_w - 1)).astype(int)
        ys = np.rint(y1 - (values - ymin) / (ymax - ymin) * (plot_h - 1)).astype(int)
        for xa, ya, xb, yb in zip(xs[:-1], ys[:-1], xs[1:], ys[1:]):
            _draw_line(img, int(xa), int(ya), int(xb), int(yb), black)

    return save_png_rgb(path, img)


_HEATMAP_STOPS = np.array(
    [
        (31, 38, 86),
        (43, 108, 151),
        (40, 164, 142),
        (235, 221, 83),
        (252, 250, 236),
    ],
    dtype=float,
)


def _normalise_field(values: np.ndarray, vmin: float | None, vmax: float | None) -> tuple[np.ndarray, float, float]:
    arr = np.asarray(values, dtype=float)
    finite = np.isfinite(arr)
    if not finite.any():
        raise ValueError("heatmap field has no finite values")
    lo = float(np.nanmin(arr[finite])) if vmin is None else float(vmin)
    hi = float(np.nanmax(arr[finite])) if vmax is None else float(vmax)
    if not math.isfinite(lo) or not math.isfinite(hi):
        raise ValueError(f"non-finite heatmap limits: {lo}, {hi}")
    if hi <= lo:
        hi = lo + 1.0
    norm = np.clip((arr - lo) / (hi - lo), 0.0, 1.0)
    norm = np.where(finite, norm, 0.0)
    return norm, lo, hi


def _colourise(norm: np.ndarray) -> np.ndarray:
    scaled = np.asarray(norm, dtype=float) * (_HEATMAP_STOPS.shape[0] - 1)
    idx = np.floor(scaled).astype(int)
    idx = np.clip(idx, 0, _HEATMAP_STOPS.shape[0] - 2)
    frac = (scaled - idx)[..., None]
    rgb = _HEATMAP_STOPS[idx] * (1.0 - frac) + _HEATMAP_STOPS[idx + 1] * frac
    return np.clip(np.rint(rgb), 0, 255).astype(np.uint8)


def _resize_nearest(rgb: np.ndarray, height: int, width: int) -> np.ndarray:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError(f"expected RGB image, got {rgb.shape}")
    src_h, src_w = rgb.shape[:2]
    yi = np.linspace(0, src_h - 1, height).round().astype(int)
    xi = np.linspace(0, src_w - 1, width).round().astype(int)
    return rgb[yi][:, xi]


def _draw_heatmap_panel(
    img: np.ndarray,
    field: np.ndarray,
    *,
    x0: int,
    y0: int,
    panel_w: int,
    panel_h: int,
    title: str,
    vmin: float | None,
    vmax: float | None,
    log10: bool,
) -> None:
    arr = np.asarray(field, dtype=float)
    if arr.ndim != 2:
        raise ValueError(f"heatmap fields must be 2D, got {arr.shape}")
    plot = np.log10(np.maximum(np.abs(arr), 1.0e-300)) if log10 else arr
    norm, lo, hi = _normalise_field(plot, vmin, vmax)
    heat = _resize_nearest(_colourise(norm), panel_h, panel_w)
    img[y0:y0 + panel_h, x0:x0 + panel_w] = heat

    black = (0, 0, 0)
    gray = (85, 85, 85)
    _draw_line(img, x0, y0, x0 + panel_w, y0, black)
    _draw_line(img, x0, y0 + panel_h, x0 + panel_w, y0 + panel_h, black)
    _draw_line(img, x0, y0, x0, y0 + panel_h, black)
    _draw_line(img, x0 + panel_w, y0, x0 + panel_w, y0 + panel_h, black)
    _draw_text(img, x0, max(8, y0 - 31), title, black, scale=3)
    _draw_text(img, x0, y0 + panel_h + 12, "x", gray, scale=2)
    _draw_text(img, max(6, x0 - 24), y0 + panel_h // 2, "y", gray, scale=2)

    bar_x = x0 + panel_w + 14
    bar_w = 22
    bar = _colourise(np.linspace(1.0, 0.0, panel_h)[:, None])
    bar = np.repeat(bar, bar_w, axis=1)
    img[y0:y0 + panel_h, bar_x:bar_x + bar_w] = bar
    _draw_line(img, bar_x, y0, bar_x + bar_w, y0, black)
    _draw_line(img, bar_x, y0 + panel_h, bar_x + bar_w, y0 + panel_h, black)
    _draw_line(img, bar_x, y0, bar_x, y0 + panel_h, black)
    _draw_line(img, bar_x + bar_w, y0, bar_x + bar_w, y0 + panel_h, black)
    _draw_text(img, bar_x + bar_w + 8, y0, _nice(hi), black, scale=2)
    _draw_text(img, bar_x + bar_w + 8, y0 + panel_h - 14, _nice(lo), black, scale=2)


def plot_heatmap_panels(
    path: str | pathlib.Path,
    panels: Sequence[dict[str, object] | tuple[str, np.ndarray]],
    *,
    columns: int | None = None,
    panel_size: int = 520,
    margin: int = 64,
    gap: int = 94,
    title_gap: int = 42,
) -> pathlib.Path:
    """Render one or more 2D scalar fields as titled RGB heatmap panels.

    Each panel may be either ``(title, field)`` or a dict with ``title``,
    ``field``, and optional ``vmin``, ``vmax``, ``log10`` keys.  The writer is
    intentionally small and stdlib-only so validation figures work in minimal
    Python environments without matplotlib/PIL/imageio/cv2.
    """
    if not panels:
        raise ValueError("at least one heatmap panel is required")
    parsed: list[dict[str, object]] = []
    for panel in panels:
        if isinstance(panel, tuple):
            title, field = panel
            parsed.append({"title": title, "field": field})
        else:
            parsed.append(dict(panel))
    cols = columns or min(2, len(parsed))
    if cols <= 0:
        raise ValueError(f"columns must be positive, got {cols}")
    rows = int(math.ceil(len(parsed) / cols))
    colorbar_w = 86
    width = 2 * margin + cols * panel_size + (cols - 1) * gap + cols * colorbar_w
    height = 2 * margin + rows * (panel_size + title_gap) + (rows - 1) * gap + 36
    img = np.full((height, width, 3), 255, dtype=np.uint8)

    for idx, panel in enumerate(parsed):
        row, col = divmod(idx, cols)
        x0 = margin + col * (panel_size + colorbar_w + gap)
        y0 = margin + title_gap + row * (panel_size + title_gap + gap)
        _draw_heatmap_panel(
            img,
            np.asarray(panel["field"], dtype=float),
            x0=x0,
            y0=y0,
            panel_w=panel_size,
            panel_h=panel_size,
            title=str(panel.get("title", "")),
            vmin=panel.get("vmin"),  # type: ignore[arg-type]
            vmax=panel.get("vmax"),  # type: ignore[arg-type]
            log10=bool(panel.get("log10", False)),
        )

    return save_png_rgb(path, img)
