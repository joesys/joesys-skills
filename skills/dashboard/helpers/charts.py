# charts.py
"""Pure inline-SVG chart builders. No external libraries, no network."""
from __future__ import annotations
from html import escape


def sparkline(values: list[int], width: int = 220, height: int = 40) -> str:
    if not values:
        return f'<svg class="spark" width="{width}" height="{height}"></svg>'
    n = len(values)
    hi = max(values) or 1
    step = width / max(n - 1, 1)
    pts = " ".join(
        f"{i * step:.1f},{height - (v / hi) * (height - 4) - 2:.1f}"
        for i, v in enumerate(values)
    )
    return (f'<svg class="spark" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">'
            f'<polyline fill="none" stroke="currentColor" stroke-width="1.5" '
            f'points="{pts}"/></svg>')


def hbar(rows: list[dict], label_key: str, value_key: str, width: int = 240) -> str:
    if not rows:
        return f'<svg class="hbar" width="{width}" height="20"></svg>'
    hi = max((r[value_key] for r in rows), default=1) or 1
    bar_h, gap = 16, 6
    height = len(rows) * (bar_h + gap)
    parts = [f'<svg class="hbar" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}">']
    for i, r in enumerate(rows):
        y = i * (bar_h + gap)
        w = (r[value_key] / hi) * (width - 90)
        label = escape(str(r[label_key]))[:24]
        parts.append(f'<rect x="80" y="{y}" width="{w:.1f}" height="{bar_h}" '
                     f'fill="currentColor" opacity="0.45" rx="2"/>')
        parts.append(f'<text x="0" y="{y + 12}" font-size="11">{label}</text>')
        parts.append(f'<text x="{82 + w:.1f}" y="{y + 12}" font-size="10" '
                     f'opacity="0.7">{escape(str(r[value_key]))}</text>')
    parts.append("</svg>")
    return "".join(parts)


def heatmap(grid: list[list[int]], width: int = 240) -> str:
    rows, cols = len(grid), len(grid[0]) if grid else 0
    cell = width / max(cols, 1)
    hi = max((max(r) for r in grid), default=1) or 1
    height = int(rows * cell)
    parts = [f'<svg class="heat" width="{width}" height="{height}" '
             f'viewBox="0 0 {width} {height}">']
    for d in range(rows):
        for h in range(cols):
            v = grid[d][h]
            op = 0.08 + 0.9 * (v / hi) if v else 0.05
            parts.append(f'<rect x="{h * cell:.1f}" y="{d * cell:.1f}" '
                         f'width="{cell:.1f}" height="{cell:.1f}" '
                         f'fill="currentColor" opacity="{op:.2f}"/>')
    parts.append("</svg>")
    return "".join(parts)


def grade_trend(points: list[dict]) -> str:
    if not points:
        return '<svg class="trend" width="200" height="30"></svg>'
    parts = ['<svg class="trend" width="200" height="30" viewBox="0 0 200 30">']
    step = 200 / max(len(points), 1)
    for i, p in enumerate(points):
        parts.append(f'<text x="{i * step:.0f}" y="20" font-size="11">'
                     f'{escape(str(p.get("grade", "")))}</text>')
    parts.append("</svg>")
    return "".join(parts)
