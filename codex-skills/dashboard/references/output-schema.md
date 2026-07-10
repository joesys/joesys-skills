# `dashboard.json` output schema

The canonical artifact of the `$dashboard` skill. It is produced by
`helpers/collect_git.py` (deterministic local-git metrics) and then
optionally enriched in place by `helpers/collect_host.py` (`host`),
`helpers/collect_audit.py` (`code_quality`), and a narrative step
(`overall.summary`, per-lens `why` text, `narrative`).

This document describes the **actual** keys the code emits. It was verified
against a real sample generated with:

```
python ../dashboard/helpers/collect_git.py --repo . --now 1750000000 --out sample-dash.json
```

Light values are always one of `"green" | "yellow" | "red" | "na"`.
`"na"` means "not applicable / not enough data" (e.g. a solo repo has no
Team light, an untagged repo has no release light).

---

## Top-level keys

| Key | Type | Description |
| --- | --- | --- |
| `schema` | int | Schema version. Currently `1`. Bump on any breaking shape change. |
| `generated_ts` | int | Unix timestamp the snapshot was computed (the `--now` clock, or wall clock). All "days ago" figures are relative to this. |
| `repo` | object | Repo identity. See [repo](#repo). |
| `flags` | object | Run-shape flags that change how lights are read. See [flags](#flags). |
| `kpis` | object | The flat headline numbers shown at the top of the dashboard. See [kpis](#kpis). |
| `lenses` | object | The three analytical lenses, each with its own light and supporting detail. See [lenses](#lenses). |
| `overall` | object | The single roll-up light and its summary sentence. See [overall](#overall). |
| `repo_state` | object | Static repo facts (modules, file/language counts). See [repo_state](#repo_state). |
| `narrative` | object \| null | Optional free-form narrative block filled by the host agent. `null` until written. |
| `host` | object \| null | Optional GitHub/GitLab enrichment. `null` until `collect_host.py` runs. See [host](#host-enrichment). |
| `code_quality` | object \| null | Optional `$codebase-audit` grade. `null` until `collect_audit.py` runs. See [code_quality](#code_quality-enrichment). |

---

## `repo`

| Field | Type | Description |
| --- | --- | --- |
| `name` | str | Basename of the repo directory. |
| `branch` | str | Current HEAD branch name. |
| `commit` | str | Short HEAD commit SHA. |
| `default_branch` | str | Detected default branch (e.g. `master`/`main`). |

## `flags`

| Field | Type | Description |
| --- | --- | --- |
| `solo` | bool | `true` when the repo has ≤2 distinct authors. When set, the Team light is forced to `"na"` and concentration is expected, not alarming. |
| `shallow` | bool | `true` if the clone is shallow (history truncated, so some metrics are partial). |

## `kpis`

Flat headline numbers. Mirrors values that also live (with more context) inside `lenses`.

| Field | Type | Description |
| --- | --- | --- |
| `pulse` | object | `{count_30d: int, pct_change: float\|null}` — commits in the last 30 days and the fractional change vs. the prior 30 days (`null` if no prior activity). |
| `last_commit_days` | int \| null | Whole days since the most recent commit (`null` if no commits). |
| `bus_factor` | int | Number of authors who together produced >50% of the last 90 days of commits. |
| `active_devs` | int | Distinct authors who committed in the last 30 days. |
| `firefighting_pct` | float | Fraction of last-30-day commits that look like reverts/rollbacks/hotfixes (0.0–1.0). |
| `stale_branches` | int | Count of non-default branches idle longer than the stale-branch threshold. |
| `last_release_days` | int \| null | Whole days since the newest tag (`null` if the repo has no tags). |
| `open_prs` | int \| null | Open pull-request count. Always `null` from local git; populated only if `host` enrichment is merged in. |

---

## `lenses`

Three lenses: `delivery`, `health`, `team`. Each has a `light` plus supporting metrics.

### `lenses.delivery`

| Field | Type | Description |
| --- | --- | --- |
| `light` | str | Delivery traffic light — worst of staleness and release-recency lights. |
| `cadence` | int[] | 26 weekly commit counts, oldest → newest, for the sparkline. |
| `release` | object | `{has_tags: bool, days_since: int\|null, last_tag: str\|null}` — newest tag recency. |
| `throughput` | float | Average merge commits per week over the last 12 weeks. |
| `modules` | object[] | Per-module activity: `[{module: str, commits_30d: int}]`. |
| `heatmap` | int[7][24] | "When we work" grid — commit counts by weekday (0=Mon) × UTC hour, over the last 90 days. |

### `lenses.health`

| Field | Type | Description |
| --- | --- | --- |
| `light` | str | Health traffic light — worst of firefighting-rate and stale-branch-count lights. |
| `firefighting_pct` | float | Same fraction as `kpis.firefighting_pct` (reverts/rollbacks/hotfixes in last 30 days). |
| `hotspots` | object[] | Top 5 churn files over 90 days: `[{file: str, changes: int}]`. |
| `stale_branches` | object[] | Idle non-default branches: `[{name: str, idle_days: int}]`, sorted most-idle first. Empty list when none. |
| `debt` | object | Debt-marker grep counts: `{todo: int, fixme: int, hack: int, total: int}`. |
| `hygiene` | object | Repo-hygiene booleans: `{ci: bool, lockfile: bool, env_gitignored: bool, tests: bool}`. |
| `msg_hygiene` | object | Commit-message quality over last 90 days: `{conventional_pct: float, wip_pct: float}`. |

### `lenses.team`

| Field | Type | Description |
| --- | --- | --- |
| `light` | str | Team traffic light — bus-factor based, or `"na"` when `flags.solo` is set. |
| `bus_factor` | object | `{count: int, top_author: str\|null, top_share: float}` — authors producing >50% of last-90-day commits and the single largest contributor's share. |
| `active_devs` | int | Same as `kpis.active_devs` (distinct authors in last 30 days). |
| `distribution` | object | `{authors: [{author: str, commits: int}], gini: float}` — per-author commit counts (last 90 days) and a Gini concentration index (0=even, →1=concentrated). |
| `dormant` | object | `{gone_quiet: str[], newly_active: str[]}` — authors silent >90 days vs. authors first seen within 30 days. |
| `off_hours_pct` | float \| null | Fraction of last-30-day commits made on weekends or outside 08:00–19:00 UTC. `null` unless `off_hours: on` is configured. |

---

## `overall`

| Field | Type | Description |
| --- | --- | --- |
| `light` | str | The single roll-up light — the worst of the three lens lights (ignoring `"na"`). |
| `summary` | str \| null | One-line plain-English summary. `null` until the narrative step fills it. |

## `repo_state`

| Field | Type | Description |
| --- | --- | --- |
| `modules` | str[] | Top-level source directories used as modules (config override or auto-detected). |
| `size` | object | `{files: int, languages: {<ext>: int}}` — count of tracked files and a per-extension breakdown. |

---

## `narrative`

Optional block filled by the host-agent narrative step (`null` until written).
Explains the already-computed numbers; it never recomputes or overrides a light.

| Field | Type | Description |
| --- | --- | --- |
| `overall_summary` | str | ≤20-word summary; also copied into `overall.summary`. |
| `delivery_why` / `health_why` / `team_why` | str | One-sentence explanation per lens; also copied into each `lenses.*.why`. |
| `callouts` | str[] | 2–4 prioritized "look here" items, each naming a file/branch/person. |
| `analysis` | object | Per-metric tooltip text: `{<metric_id>: <one-sentence per-repo reading>}`. Powers the dashboard's on-hover "In this repo" line. Keys are the canonical metric ids (see `references/narrative-prompt.md`); ids without data are omitted. The static "what / why" half of each tooltip is **not** here — it lives in `helpers/tooltips.py` and is added by the renderer regardless (so tooltips still work on `--no-llm`). |

## `host` enrichment

Produced by `helpers/collect_host.py` (GitHub via `gh`; GitLab is not yet
implemented). Merged into the top-level `host` key. Degrades gracefully —
when unavailable, only `available` and `reason` are present.

**Available:**

| Field | Type | Description |
| --- | --- | --- |
| `available` | bool | `true`. |
| `host` | str | `"github"`. |
| `open_prs` | int | Count of open pull requests. |
| `pr_median_age_days` | float \| null | Median age in days of open PRs (`null` if none). |
| `ci_pass_rate` | float \| null | Success fraction of the last 30 CI runs (`null` if no concluded runs). |
| `open_issues` | int | Count of open issues. |

**Unavailable:**

| Field | Type | Description |
| --- | --- | --- |
| `available` | bool | `false`. |
| `reason` | str | Why enrichment was skipped (no GitHub/GitLab remote, `gh` not installed/authenticated, or GitLab not implemented in v1). |

All `host` figures are **point-in-time**: they reflect the moment the CLI was
queried, not `generated_ts`. The narrative layer must cite them with "as of".

## `code_quality` enrichment

Produced by `helpers/collect_audit.py`, which **reads** (never runs) the newest
`$codebase-audit` `docs/reports/codebase-audit/*/metrics.json`. Merged into the
top-level `code_quality` key.

**Available:**

| Field | Type | Description |
| --- | --- | --- |
| `available` | bool | `true`. |
| `date` | str | Date string from the audit report. |
| `commit` | str | Commit SHA the audit was run against. |
| `overall_grade` | str | The audit's overall letter grade (e.g. `A`, `B`). |
| `criteria` | object | `{<criterion_name>: <grade>}` — per-criterion letter grades. |
| `commits_behind` | int | Commits on HEAD since the audited commit (how stale the grade is). |
| `stale` | bool | `true` when `commits_behind` exceeds the staleness threshold (default 200). |
| `report_path` | str | Repo-relative path to the source `metrics.json`. |
| `trend` | object[] | All parseable audits, oldest → newest: `[{date: str, grade: str}]`. |

**Unavailable:**

| Field | Type | Description |
| --- | --- | --- |
| `available` | bool | `false` (no readable audit report found). |

The audit grade is **point-in-time** — it describes `commit`, which may be
`commits_behind` commits behind HEAD. The narrative layer must say "as of" and
respect the `stale` flag.

---

## Representative sample (trimmed)

Real output from this repo, abbreviated (long arrays elided). Author names come
from git history; that is expected for an internal schema doc.

```json
{
  "schema": 1,
  "generated_ts": 1750000000,
  "repo": { "name": "joesys-skills", "branch": "feat/dashboard-skill",
            "commit": "1e3035e", "default_branch": "master" },
  "flags": { "solo": true, "shallow": false },
  "kpis": {
    "pulse": { "count_30d": 0, "pct_change": null },
    "last_commit_days": 0, "bus_factor": 0, "active_devs": 0,
    "firefighting_pct": 0.0, "stale_branches": 0,
    "last_release_days": null, "open_prs": null
  },
  "lenses": {
    "delivery": {
      "light": "green",
      "cadence": [0, 0, 0, "…26 weeks…", 0],
      "release": { "has_tags": false, "days_since": null, "last_tag": null },
      "throughput": 0.0,
      "modules": [ { "module": "skills", "commits_30d": 38 } ],
      "heatmap": [ ["…24 hours…"], "…7 days…" ]
    },
    "health": {
      "light": "green",
      "firefighting_pct": 0.0,
      "hotspots": [ { "file": ".claude-plugin/plugin.json", "changes": 33 } ],
      "stale_branches": [],
      "debt": { "todo": 13, "fixme": 11, "hack": 10, "total": 34 },
      "hygiene": { "ci": false, "lockfile": false,
                   "env_gitignored": true, "tests": true },
      "msg_hygiene": { "conventional_pct": 0.9951, "wip_pct": 0.0 }
    },
    "team": {
      "light": "na",
      "bus_factor": { "count": 0, "top_author": null, "top_share": 0.0 },
      "active_devs": 0,
      "distribution": { "authors": [], "gini": 0.0 },
      "dormant": { "gone_quiet": [], "newly_active": ["<author>"] },
      "off_hours_pct": null
    }
  },
  "overall": { "light": "green", "summary": null },
  "repo_state": {
    "modules": ["docs", "scripts", "shared", "skills", "tests"],
    "size": { "files": 169, "languages": { "md": 89, "py": 33, "…": 0 } }
  },
  "narrative": null,
  "host": null,
  "code_quality": null
}
```
