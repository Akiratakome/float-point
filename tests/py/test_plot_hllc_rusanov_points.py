from pathlib import Path

import numpy as np
from PIL import Image

from scripts.figures.plot_hllc_rusanov_points import plot_point_comparison


def test_plot_point_comparison_writes_png(tmp_path: Path) -> None:
    x = np.linspace(0.0, 1.0, 8)
    exact = np.column_stack(
        [x, np.ones_like(x), np.zeros_like(x), np.zeros_like(x), np.ones_like(x)]
    )
    hllc = exact.copy()
    rusanov = exact.copy()
    rusanov[:, 1] += 0.01
    out = tmp_path / "points.png"

    plot_point_comparison(
        test_title="synthetic",
        exact=exact,
        hllc=hllc,
        rusanov=rusanov,
        out_path=out,
    )

    im = Image.open(out)
    assert im.size[0] > 300
    assert im.size[1] > 200
