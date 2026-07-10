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
import thresholds
import tooltips

TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "templates", "dashboard.html")
_DOT = {"green": "green", "yellow": "yellow", "red": "red", "na": "na"}
_CFG = thresholds.DEFAULTS
_STATUS_WORD = {"green": "Healthy", "yellow": "Needs attention",
                "red": "At risk", "na": "Insufficient data"}


def _pct(v):
    return "—" if v is None else f"{v * 100:+.0f}%"


def _analysis(d: dict) -> dict:
    return (d.get("narrative") or {}).get("analysis") or {}


def _tip(metric_id: str, analysis: dict) -> str:
    """Styled info popover for a metric: static what/why + optional per-repo line."""
    t = tooltips.get(metric_id)
    a = (analysis or {}).get(metric_id)
    extra = f'<span class="tip-s">In this repo</span>{escape(str(a))}' if a else ""
    return (
        f'<span class="tip" tabindex="0" role="button" '
        f'aria-label="Explain {escape(t["title"])}">'
        f'<svg class="tip-i" width="13" height="13" viewBox="0 0 16 16" aria-hidden="true">'
        f'<circle cx="8" cy="8" r="7.1" fill="none" stroke="currentColor" stroke-width="1.3"/>'
        f'<text x="8" y="11.6" text-anchor="middle" font-size="10" '
        f'font-style="italic" fill="currentColor" stroke="none">i</text></svg>'
        f'<span class="tip-pop" role="tooltip">'
        f'<b class="tip-h">{escape(t["title"])}</b>'
        f'<span class="tip-s">What this measures</span>{escape(t["what"])}'
        f'<span class="tip-s">Why it matters</span>{escape(t["why"])}'
        f'{extra}</span></span>'
    )


def _kpi_accent(metric_id: str, d: dict) -> str:
    """Reuse the engine's own light functions (defaults) for a KPI tile accent.

    Returns "green" | "yellow" | "red", or "" when no threshold applies or the
    light is "na". No new thresholds are invented here.
    """
    k = d["kpis"]
    rel = d["lenses"]["delivery"]["release"]
    light = ""
    if metric_id == "kpi.last_commit":
        light = thresholds.light_staleness(k["last_commit_days"], _CFG)
    elif metric_id == "kpi.bus_factor":
        light = thresholds.light_bus_factor(k["bus_factor"], _CFG)
    elif metric_id == "kpi.firefighting":
        light = thresholds.light_firefighting(k["firefighting_pct"], _CFG)
    elif metric_id == "kpi.stale_branches":
        light = thresholds.light_stale_branches(k["stale_branches"], _CFG)
    elif metric_id == "kpi.last_release":
        light = thresholds.light_release(k["last_release_days"], rel["has_tags"], _CFG)
    return light if light in ("green", "yellow", "red") else ""


def _tile(label: str, value: str, metric_id: str | None = None,
          accent: str = "", analysis: dict | None = None) -> str:
    cls = "tile" + (f" {accent}" if accent else "")
    tip = _tip(metric_id, analysis or {}) if metric_id else ""
    return (f'<div class="{cls}"><div class="label">{escape(label)}{tip}</div>'
            f'<div class="num">{value}</div></div>')


def _pulse_value(p: dict) -> str:
    n = p["count_30d"]
    pc = p["pct_change"]
    if pc is None:
        return str(n)
    arrow = "▲" if pc > 0 else ("▼" if pc < 0 else "→")
    cls = "up" if pc > 0 else ("down" if pc < 0 else "flat")
    return f'{n} <span class="trend {cls}">{arrow} {_pct(pc)}</span>'


def _kpi_strip(d: dict) -> str:
    k = d["kpis"]
    a = _analysis(d)
    host = d.get("host") or {}
    if host.get("available"):
        tile8 = _tile("Open PRs", escape(str(host["open_prs"])), "kpi.open_prs", "", a)
    else:
        tile8 = _tile("WIP branches", str(k["stale_branches"]), "kpi.wip_branches",
                      _kpi_accent("kpi.stale_branches", d), a)
    tiles = [
        _tile("Pulse 30d", _pulse_value(k["pulse"]), "kpi.pulse", "", a),
        _tile("Last commit", "—" if k["last_commit_days"] is None else f'{k["last_commit_days"]}d',
              "kpi.last_commit", _kpi_accent("kpi.last_commit", d), a),
        _tile("Bus factor", str(k["bus_factor"]), "kpi.bus_factor",
              _kpi_accent("kpi.bus_factor", d), a),
        _tile("Active devs", str(k["active_devs"]), "kpi.active_devs", "", a),
        _tile("Firefighting", f'{k["firefighting_pct"] * 100:.0f}%', "kpi.firefighting",
              _kpi_accent("kpi.firefighting", d), a),
        _tile("Stale branches", str(k["stale_branches"]), "kpi.stale_branches",
              _kpi_accent("kpi.stale_branches", d), a),
        _tile("Last release", "—" if k["last_release_days"] is None else f'{k["last_release_days"]}d',
              "kpi.last_release", _kpi_accent("kpi.last_release", d), a),
        tile8,
    ]
    return "".join(tiles)


def _verdict(d: dict) -> str:
    o = d["overall"]
    a = _analysis(d)
    light = o["light"]
    summary = escape(o["summary"] or _fallback_summary(d))
    return (f'<span class="dot {_DOT[light]}"></span>'
            f'<div class="verdict-body">'
            f'<div class="verdict-head"><h1>{escape(d["repo"]["name"])} — project health</h1>'
            f'{_tip("overall", a)}'
            f'<span class="status-word {_DOT[light]}">{_STATUS_WORD[light]}</span></div>'
            f'<div class="thresh">{summary}</div></div>')


def _fallback_summary(d: dict) -> str:
    label = {"green": "Healthy", "yellow": "Needs attention", "red": "At risk",
             "na": "Insufficient data"}[d["overall"]["light"]]
    return f"{label}. (Run via Claude for a written summary.)"


def _col_label(text: str, metric_id: str, analysis: dict) -> str:
    return f'<div class="label">{escape(text)}{_tip(metric_id, analysis)}</div>'


def _delivery(d: dict) -> str:
    L = d["lenses"]["delivery"]
    a = _analysis(d)
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
        host_col = (f'<div class="col">{_col_label("from " + str(host["host"]), "delivery.host", a)}'
                    f'<div class="named">{escape(str(host["open_prs"]))} open PRs'
                    + (f' · median age {cyc}d' if cyc is not None else '') + '</div>'
                    + (f'<div class="named">CI pass {host["ci_pass_rate"]*100:.0f}%</div>'
                       if host.get("ci_pass_rate") is not None else '')
                    + f'<div class="named">{escape(str(host["open_issues"]))} open issues</div></div>')
    body = (
        f'<div class="col">{_col_label("commit cadence", "delivery.cadence", a)}'
        f'<div class="chartwrap">{spark}<span class="axis">26 wks</span></div>'
        f'<div class="named">throughput {L["throughput"]}/wk{_tip("delivery.throughput", a)}</div>'
        f'<div class="named">{rel_txt}{_tip("delivery.release", a)}</div></div>'
        f'<div class="col">{_col_label("module activity", "delivery.modules", a)}{mods}</div>'
        f'<div class="col">{_col_label("when we work", "delivery.heatmap", a)}'
        f'<div class="chartwrap">{heat}<span class="axis">Mon–Sun · 0–23h UTC</span></div></div>'
        + host_col
    )
    return _lens("Delivery & Momentum", L["light"], "lens.delivery", a,
                 f'Commit cadence (26 wks) · throughput {L["throughput"]}/wk · {rel_txt}', body)


def _health(d: dict) -> str:
    L = d["lenses"]["health"]
    a = _analysis(d)
    hot = "".join(f'<div class="named">{escape(h["file"])} ×{h["changes"]}</div>'
                  for h in L["hotspots"])
    sb = "".join(f'<div class="named">{escape(b["name"])} — {b["idle_days"]}d idle</div>'
                 for b in L["stale_branches"][:8])
    hy = L["hygiene"]
    checks = " · ".join(f'{name} {"✓" if ok else "✗"}'
                        for name, ok in [("CI", hy["ci"]), ("lockfile", hy["lockfile"]),
                                         (".env ignored", hy["env_gitignored"]), ("tests", hy["tests"])])
    debt = L["debt"]
    body = (
        f'<div class="col">{_col_label("churn hotspots", "health.hotspots", a)}'
        f'{hot or "<div class=named>none</div>"}</div>'
        f'<div class="col">{_col_label("stale branches", "health.stale_branches", a)}'
        f'{sb or "<div class=named>none</div>"}</div>'
        f'<div class="col">{_col_label("hygiene", "health.hygiene", a)}'
        f'<div class="named">{checks}</div>'
        f'<div class="named">TODO {debt["todo"]} · FIXME {debt["fixme"]} · HACK {debt["hack"]}'
        f'{_tip("health.debt", a)}</div></div>'
        f'{_code_quality_block(d, a)}'
    )
    return _lens("Health & Risk", L["light"], "lens.health", a,
                 f'Firefighting {L["firefighting_pct"]*100:.0f}% · '
                 f'{debt["total"]} debt markers · {len(L["stale_branches"])} stale branches', body)


def _team(d: dict) -> str:
    L = d["lenses"]["team"]
    a = _analysis(d)
    bf = L["bus_factor"]
    bars = charts.hbar(L["distribution"]["authors"][:8], "author", "commits")
    gone = ", ".join(escape(x) for x in L["dormant"]["gone_quiet"][:6]) or "none"
    bf_txt = f'{bf["top_author"]} owns {bf["top_share"]*100:.0f}% of recent commits' \
        if bf.get("top_author") else "—"
    off = "" if L["off_hours_pct"] is None else \
        f'<div class="named" style="opacity:.7">off-hours commits {L["off_hours_pct"]*100:.0f}% (proxy)' \
        f'{_tip("team.off_hours", a)}</div>'
    body = (
        f'<div class="col">{_col_label("contribution", "team.distribution", a)}{bars}</div>'
        f'<div class="col">'
        f'<div class="named">{escape(bf_txt)}{_tip("team.bus_factor", a)}</div>'
        f'<div class="named">gone quiet (90d+): {gone}{_tip("team.dormant", a)}</div>{off}</div>'
    )
    return _lens("Team & Contribution", L["light"], "lens.team", a,
                 f'Bus factor {bf["count"]} · {L["active_devs"]} active devs · '
                 f'gini {L["distribution"]["gini"]}', body)


def _code_quality_block(d: dict, analysis: dict) -> str:
    cq = d.get("code_quality")
    label = _col_label("code quality", "health.code_quality", analysis)
    if not cq or not cq.get("available"):
        return (f'<div class="col">{label}'
                '<div class="named" style="opacity:.6">not measured — run /codebase-audit</div></div>')
    warn = "⚠ " if cq.get("stale") else ""
    crit = " · ".join(f'{escape(k)} {escape(v)}' for k, v in list(cq["criteria"].items())[:6])
    trend = ""
    if len(cq.get("trend", [])) >= 2:
        trend = charts.grade_trend(cq["trend"])
    prov = (f'from /codebase-audit · {escape(cq["date"])} · commit {escape(cq["commit"])} · '
            f'{cq["commits_behind"]} commits behind HEAD')
    return (f'<div class="col">{label}'
            f'<div class="num">{warn}{escape(cq["overall_grade"])}</div>'
            f'<div class="named">{crit}</div>{trend}'
            f'<div class="thresh">{prov}</div></div>')


def _lens(title: str, light: str, metric_id: str, analysis: dict, why: str, body: str) -> str:
    badge = light.upper() if light != "na" else "N/A"
    return (f'<details class="lens" open><summary>'
            f'<span class="dot {_DOT[light]}"></span>'
            f'<span class="lens-title">{escape(title)}{_tip(metric_id, analysis)}</span>'
            f'<span class="badge {_DOT[light]}">{badge}</span></summary>'
            f'<div class="why">{escape(why)}</div>'
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
           .replace("{{VERDICT_LIGHT}}", _DOT[data["overall"]["light"]])
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
