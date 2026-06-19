# test_charts.py
from __future__ import annotations
import charts


def test_sparkline_is_svg_and_handles_flat():
    s = charts.sparkline([1, 2, 3, 2, 5])
    assert s.startswith("<svg") and s.rstrip().endswith("</svg>")
    assert charts.sparkline([0, 0, 0]).startswith("<svg")  # no div-by-zero
    assert charts.sparkline([]).startswith("<svg")          # empty safe


def test_hbar_renders_rows():
    svg = charts.hbar([{"name": "a", "v": 5}, {"name": "b", "v": 2}], "name", "v")
    assert svg.count("<rect") >= 2
    assert "a" in svg and "b" in svg


def test_heatmap_7x24():
    grid = [[0] * 24 for _ in range(7)]
    grid[0][9] = 4
    svg = charts.heatmap(grid)
    assert svg.startswith("<svg")
    assert svg.count("<rect") >= 7 * 24


def test_escapes_html_in_labels():
    svg = charts.hbar([{"name": "<x>&", "v": 1}], "name", "v")
    assert "<x>" not in svg
    assert "&lt;x&gt;&amp;" in svg
