# render_dashboard.py
"""Render dashboard.json into a self-contained HTML file.

Usage:
    python render_dashboard.py --metrics dashboard.json [--out docs/dashboard/dashboard.html]
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from html import escape

import charts

TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "templates", "dashboard.html")
_DOT = {"green": "green", "yellow": "yellow", "red": "red", "na": "na"}


def _pct(v):
    return "—" if v is None else f"{v * 100:+.0f}%"


def _tile(label: str, value: str) -> str:
    return f'<div class="tile"><div class="label">{escape(label)}</div>' \
           f'<div class="num">{value}</div></div>'


def _kpi_strip(d: dict) -> str:
    k = d["kpis"]
    host = d.get("host") or {}
    if host.get("available"):
        tile8 = _tile("Open PRs", str(host["open_prs"]))
    else:
        tile8 = _tile("WIP branches", str(k["stale_branches"]))
    tiles = [
        _tile("Pulse 30d", f'{k["pulse"]["count_30d"]} <span style="font-size:12px">'
              f'({_pct(k["pulse"]["pct_change"])})</span>'),
        _tile("Last commit", "—" if k["last_commit_days"] is None else f'{k["last_commit_days"]}d'),
        _tile("Bus factor", str(k["bus_factor"])),
        _tile("Active devs", str(k["active_devs"])),
        _tile("Firefighting", f'{k["firefighting_pct"] * 100:.0f}%'),
        _tile("Stale branches", str(k["stale_branches"])),
        _tile("Last release", "—" if k["last_release_days"] is None else f'{k["last_release_days"]}d'),
        tile8,
    ]
    return "".join(tiles)


def _verdict(d: dict) -> str:
    o = d["overall"]
    summary = escape(o["summary"] or _fallback_summary(d))
    return f'<span class="dot {_DOT[o["light"]]}"></span>' \
           f'<div><h1>{escape(d["repo"]["name"])} — project health</h1>' \
           f'<div class="thresh">{summary}</div></div>'


def _fallback_summary(d: dict) -> str:
    label = {"green": "Healthy", "yellow": "Needs attention", "red": "At risk",
             "na": "Insufficient data"}[d["overall"]["light"]]
    return f"{label}. (Run via Claude for a written summary.)"


def _delivery(d: dict) -> str:
    L = d["lenses"]["delivery"]
    spark = charts.sparkline(L["cadence"])
    rel = L["release"]
    rel_txt = f'last release {escape(str(rel["last_tag"]))} ({rel["days_since"]}d ago)' \
        if rel["has_tags"] else "no releases tagged"
    mods = "".join(f'<div class="named">{escape(m["module"])}: {m["commits_30d"]} commits/30d</div>'
                   for m in L["modules"][:8])
    heat = charts.heatmap(L["heatmap"])
    host = d.get("host") or {}
    host_col = ""
    if host.get("available"):
        cyc = host["pr_median_age_days"]
        host_col = (f'<div class="col"><div class="label">from {escape(host["host"])}</div>'
                    f'<div class="named">{host["open_prs"]} open PRs'
                    + (f' · median age {cyc}d' if cyc is not None else '') + '</div>'
                    + (f'<div class="named">CI pass {host["ci_pass_rate"]*100:.0f}%</div>'
                       if host.get("ci_pass_rate") is not None else '')
                    + f'<div class="named">{host["open_issues"]} open issues</div></div>')
    return _lens("Delivery & Momentum", L["light"],
                 f'Commit cadence (26 wks) · throughput {L["throughput"]}/wk · {rel_txt}',
                 f'<div class="col">{spark}<div class="named">{rel_txt}</div></div>'
                 f'<div class="col">{mods}</div>'
                 f'<div class="col">{heat}<div class="named">when we work</div></div>'
                 + host_col)


def _health(d: dict) -> str:
    L = d["lenses"]["health"]
    hot = "".join(f'<div class="named">{escape(h["file"])} ×{h["changes"]}</div>'
                  for h in L["hotspots"])
    sb = "".join(f'<div class="named">{escape(b["name"])} — {b["idle_days"]}d idle</div>'
                 for b in L["stale_branches"][:8])
    hy = L["hygiene"]
    checks = " · ".join(f'{name} {"✓" if ok else "✗"}'
                        for name, ok in [("CI", hy["ci"]), ("lockfile", hy["lockfile"]),
                                         (".env ignored", hy["env_gitignored"]), ("tests", hy["tests"])])
    debt = L["debt"]
    return _lens("Health & Risk", L["light"],
                 f'Firefighting {L["firefighting_pct"]*100:.0f}% · '
                 f'{debt["total"]} debt markers · {len(L["stale_branches"])} stale branches',
                 f'<div class="col"><div class="label">churn hotspots</div>{hot or "<div class=named>none</div>"}</div>'
                 f'<div class="col"><div class="label">stale branches</div>{sb or "<div class=named>none</div>"}</div>'
                 f'<div class="col"><div class="label">hygiene</div><div class="named">{checks}</div>'
                 f'<div class="named">TODO {debt["todo"]} · FIXME {debt["fixme"]} · HACK {debt["hack"]}</div></div>'
                 f'{_code_quality_block(d)}')


def _team(d: dict) -> str:
    L = d["lenses"]["team"]
    bf = L["bus_factor"]
    bars = charts.hbar(L["distribution"]["authors"][:8], "author", "commits")
    gone = ", ".join(escape(a) for a in L["dormant"]["gone_quiet"][:6]) or "none"
    bf_txt = f'{bf["top_author"]} owns {bf["top_share"]*100:.0f}% of recent commits' \
        if bf.get("top_author") else "—"
    off = "" if L["off_hours_pct"] is None else \
        f'<div class="named" style="opacity:.6">off-hours commits {L["off_hours_pct"]*100:.0f}% (proxy)</div>'
    return _lens("Team & Contribution", L["light"],
                 f'Bus factor {bf["count"]} · {L["active_devs"]} active devs · gini {L["distribution"]["gini"]}',
                 f'<div class="col">{bars}</div>'
                 f'<div class="col"><div class="named">{escape(bf_txt)}</div>'
                 f'<div class="named">gone quiet (90d+): {gone}</div>{off}</div>')


def _code_quality_block(d: dict) -> str:
    cq = d.get("code_quality")
    if not cq or not cq.get("available"):
        return ('<div class="col"><div class="label">code quality</div>'
                '<div class="named" style="opacity:.6">not measured — run /codebase-audit</div></div>')
    warn = "⚠ " if cq.get("stale") else ""
    crit = " · ".join(f'{escape(k)} {escape(v)}' for k, v in list(cq["criteria"].items())[:6])
    trend = ""
    if len(cq.get("trend", [])) >= 2:
        trend = charts.grade_trend(cq["trend"])
    prov = (f'from /codebase-audit · {escape(cq["date"])} · commit {escape(cq["commit"])} · '
            f'{cq["commits_behind"]} commits behind HEAD')
    return (f'<div class="col"><div class="label">code quality (borrowed)</div>'
            f'<div class="num">{warn}{escape(cq["overall_grade"])}</div>'
            f'<div class="named">{crit}</div>{trend}'
            f'<div class="thresh">{prov}</div></div>')


def _lens(title: str, light: str, why: str, body: str) -> str:
    return (f'<details class="lens" open><summary><span class="dot {_DOT[light]}"></span>'
            f'{escape(title)}</summary><div class="why">{escape(why)}</div>'
            f'<div class="body">{body}</div></details>')


def render(data: dict) -> str:
    with open(TEMPLATE, "r", encoding="utf-8") as fh:
        tpl = fh.read()
    footer = f'Generated at commit {escape(data["repo"]["commit"])} · ' \
             f'schema v{data["schema"]} · /dashboard'
    gen = time.strftime("Generated %Y-%m-%d %H:%M UTC", time.gmtime(data["generated_ts"]))
    out = (tpl
           .replace("{{TITLE}}", escape(data["repo"]["name"]) + " — dashboard")
           .replace("{{GENERATED}}", escape(gen))
           .replace("{{VERDICT}}", _verdict(data))
           .replace("{{KPI_STRIP}}", _kpi_strip(data))
           .replace("{{DELIVERY}}", _delivery(data))
           .replace("{{HEALTH}}", _health(data))
           .replace("{{TEAM}}", _team(data))
           .replace("{{FOOTER}}", footer))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Render dashboard.json to self-contained HTML")
    ap.add_argument("--metrics", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    with open(args.metrics, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    html = render(data)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(html)
    else:
        print(html)
    return 0


if __name__ == "__main__":
    sys.exit(main())
