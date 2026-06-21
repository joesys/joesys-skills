# Narrative prompt (host agent, optional)

This is the prompt the host agent uses to fill `overall.summary` and the
per-lens "why" text in `dashboard.json`. It is an **explanation** layer over
already-computed numbers — it never recomputes or overrides a light.

Input: the full `dashboard.json` (see `references/output-schema.md`).
Output: a single JSON object (shape below) that the skill writes back into the
dashboard.

---

## Prompt

You are writing the plain-English layer for a project-health dashboard. You are
given `dashboard.json` (already-computed numbers and traffic-light states). Do
NOT recompute anything. Do NOT invent numbers absent from the JSON.

Return ONLY this JSON:

```json
{
  "overall_summary": "<=20 words; name the single dominant driver of the overall light",
  "delivery_why": "one sentence explaining the delivery light",
  "health_why": "one sentence explaining the health light",
  "team_why": "one sentence explaining the team light",
  "callouts": ["2-4 prioritized 'look here' items, each naming a specific file/branch/person"],
  "analysis": {
    "<metric_id>": "one sentence: what this metric shows in THIS repo",
    "...": "... one entry per metric id (below) that has data ..."
  }
}
```

Rules:

- One sentence per `*_why`. Name the **dominant driver** of that lens's light —
  the single metric most responsible for it — not a list of everything.
- Never invent numbers that are not in the JSON. Every figure you cite must
  appear verbatim in `dashboard.json`. If a value is `null`, say so or omit it;
  do not guess.
- Never soften a red light or inflate a green one. The light is fixed by the
  engine; your job is to explain it, not to argue with it.
- Borrowed figures — host PR/CI data (`host.*`) and the `/codebase-audit` grade
  (`code_quality.*`) — are **point-in-time**. Say "as of" when you cite them,
  and respect `code_quality.stale` (call out a stale grade rather than treating
  it as current).
- If `flags.solo` is set, frame Team concentration as **expected, not
  alarming** — a single dominant contributor is normal for a solo project, and
  the Team light will be `"na"`.
- `analysis` powers the dashboard's on-hover tooltips (the "In this repo" line).
  For each metric id below that has data, write **one** plain-English sentence on
  what the metric shows *in this repo* — same rules: cite only numbers in the
  JSON, "as of" for borrowed figures, never override a light. Omit ids whose data
  is absent: `delivery.host` when host is unavailable, `team.off_hours` when
  `off_hours_pct` is null, and `kpi.open_prs` vs `kpi.wip_branches` — emit only
  whichever the dashboard shows (open PRs when `host.available`, else WIP).

---

## Field expectations

| Output field | Maps to | Guidance |
| --- | --- | --- |
| `overall_summary` | `overall.summary` | ≤20 words. Lead with the worst lens; name the one driver behind `overall.light`. |
| `delivery_why` | written into the delivery narrative | One sentence. Likely drivers: `lenses.delivery.release`, staleness (`kpis.last_commit_days`), `throughput`, `cadence`. |
| `health_why` | written into the health narrative | One sentence. Likely drivers: `firefighting_pct`, `stale_branches`, `hotspots`, `debt`, `hygiene`. |
| `team_why` | written into the team narrative | One sentence. Likely drivers: `bus_factor`, `distribution.gini`, `dormant`. If `flags.solo`, say concentration is expected. |
| `callouts` | actionable "look here" list | 2–4 items, prioritized worst-first. Each names a concrete file, branch, or person drawn from the JSON (e.g. a `hotspots` file, a `stale_branches` name, a `dormant.gone_quiet` author). |
| `analysis` | per-metric tooltip text | Object keyed by the metric ids below. One sentence each, present-tense, citing only JSON numbers. Omit ids without data. |

---

## Tooltip analysis ids (`analysis` keys)

These are the canonical metric ids the renderer attaches tooltips to (defined in
`helpers/tooltips.py`). Provide an `analysis` entry for each one that has data:

- **Overall:** `overall`
- **KPIs:** `kpi.pulse`, `kpi.last_commit`, `kpi.bus_factor`, `kpi.active_devs`,
  `kpi.firefighting`, `kpi.stale_branches`, `kpi.last_release`, and **one of**
  `kpi.open_prs` (host available) or `kpi.wip_branches` (no host)
- **Delivery:** `lens.delivery`, `delivery.cadence`, `delivery.throughput`,
  `delivery.release`, `delivery.modules`, `delivery.heatmap`,
  `delivery.host` *(only if `host.available`)*
- **Health:** `lens.health`, `health.hotspots`, `health.stale_branches`,
  `health.hygiene`, `health.debt`, `health.code_quality`
- **Team:** `lens.team`, `team.bus_factor`, `team.distribution`, `team.dormant`,
  `team.off_hours` *(only if `off_hours_pct` is not null)*
