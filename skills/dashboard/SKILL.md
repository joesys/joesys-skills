---
name: dashboard
description: "Use when the user invokes /dashboard to generate a self-contained HTML project-health dashboard for PMs/EMs from local git + repo state, with optional GitHub/GitLab and /codebase-audit enrichment."
---

# Dashboard Skill

Generate a single self-contained HTML **project-health dashboard** aimed at PMs and EMs. It reads local git history and repo state, computes deterministic traffic-light metrics across three lenses (Delivery, Health, Team), and renders a one-shot HTML "cockpit" — no server, no live refresh. Optional enrichment pulls open PRs / CI from GitHub (via `gh`) and borrows the latest `/codebase-audit` grade. An optional single-pass LLM narrative explains *why* each light is the colour it is, in plain English.

The pipeline is deliberately split: the **numbers and lights are computed by deterministic Python helpers** (so the same repo produces the same dashboard, runnable in CI), and the **prose is a thin explanation layer** on top that never recomputes or overrides a light.

## Out of Scope

This skill MUST NOT:
- Grade code quality itself. Maintainability, complexity, test coverage, and the like are `/codebase-audit`'s job. This skill only *borrows* an existing audit grade (stamped with provenance) and otherwise reports "not measured."
- Modify source code, config, history, or any file outside `docs/dashboard/`. The whole collect step is read-only — no commits, no branch changes, no `gh` writes.
- Be live, auto-refreshing, or interactive. It is a one-shot snapshot at a point in time. To update, run it again.
- Store long-term history or a time-series database. The only persisted history is whatever `/codebase-audit` already wrote (read via `code_quality.trend`) and the tags/commits already in git.
- Emit secrets. No env values, tokens, API keys, connection strings, or PR/issue bodies ever land in the HTML. Only counts, grades, dates, file/branch/author names from git.

## Reference Files

This skill uses progressive disclosure — read reference files only when needed:

| File | Contents | When to read |
|---|---|---|
| `references/output-schema.md` | The full `dashboard.json` schema: every key the helpers emit, the host/audit enrichment shapes, and a representative sample | Before Phase 1 (to know the artifact) and Phase 3 (to know exactly where to merge host/audit/narrative) |
| `references/narrative-prompt.md` | The exact prompt + output JSON shape for the optional narrative step | Before Phase 2, only when the LLM narrative is in play (not on `--no-llm`) |

## Helper Scripts

All under `skills/dashboard/helpers/`. All are read-only with respect to the repo.

**Path resolution (required before every invocation in Phases 1 and 3):** resolve `skills/dashboard/helpers/` to its absolute path under the plugin root (two levels above this SKILL.md) before running any command below. The commands execute in the user's project working directory, which does not contain the plugin's helpers — a bare `skills/dashboard/helpers/...` path fails when the skill is installed. Invoke every helper with `python3` where present, falling back to `python` on Windows (detect once in Phase 0: `command -v python3 || command -v python`).

| Script | Role | Key flags |
|---|---|---|
| `collect_git.py` | Deterministic local-git collector — the source of truth. Builds the entire `dashboard.json` (lights, KPIs, three lenses). | `--repo <path> --out <file> [--now <unix_ts>]` |
| `collect_host.py` | Optional GitHub enrichment (open PRs, PR median age, CI pass rate, open issues) via `gh`. Degrades to `{"available": false, "reason": ...}`. | `--repo <path> [--out <file>]` |
| `collect_audit.py` | Reads (never runs) the newest `/codebase-audit` `metrics.json`, stamping date/commit/staleness. | `--repo <path> [--out <file>]` |
| `render_dashboard.py` | Renders a merged metrics dict into a single self-contained HTML file (inlined template, no external assets). | `--metrics <file> --out <file>` |

## Invocation

Parse the user's `/dashboard` arguments:

| Invocation | Behavior |
|---|---|
| `/dashboard` | Whole-repo health dashboard (default). |
| `/dashboard <path>` | Scope module activity to a subtree — `<path>` becomes the module focus (see Scope below). |
| `/dashboard --no-llm` | Deterministic / CI mode — skip the LLM narrative entirely. Lights, KPIs, and lenses are unchanged; the renderer falls back to its built-in templated summary. |
| `/dashboard --no-host` | Skip host enrichment — do not run `collect_host.py`. The KPI strip shows WIP branches instead of open PRs. |

Flags combine: `/dashboard --no-llm --no-host` is the fully deterministic, fully local mode.

### Scope Detection

- No argument → whole repo. `collect_git.py` auto-detects top-level source directories as modules.
- An argument that matches an existing directory → treat it as a **focus hint for the report layer**, not a collector argument. Still run `collect_git.py --repo <repo>` against the whole repo — there is no per-subtree scope flag, and passing the subtree as `--repo` would mis-scope every metric (wrong repo name, modules, branch stats). The lights and KPIs reflect the whole repo's git history (they are repo-wide signals); in Phase 4, highlight the matching module from `lenses.delivery.modules` in the summary.
- If the argument matches no directory → report: "Path not found: `<path>`. Check the path and try again." and stop.

---

## Phase 0 — Detect

Establish that the skill can run and what enrichment is available. No files are written in this phase.

1. **Verify git repo.** Check with `git -C <repo> rev-parse --is-inside-work-tree` (or simply rely on `collect_git.py`'s own precondition — it exits non-zero with `error: not a git repo: <repo>` when it runs in Phase 1). Do not try to call the `gitlog.is_git_repo` function directly — it is inside a helper module the host cannot import. If it is not a git repo, **stop** and report the error — there is no fallback; every metric derives from git.
2. **Detect host availability.** Note whether a GitHub/GitLab remote exists and whether `gh` is installed + authenticated. `collect_host.py` decides this internally and degrades gracefully; Phase 0 only needs to know so the report can say "host: skipped (reason)". GitLab is not implemented in v1 — it degrades to unavailable.
3. **Detect audit availability.** Note whether any `docs/reports/codebase-audit/*/metrics.json` exists. If none, code quality will read "not measured."
4. **Load config.** `collect_git.py` reads `.claude/dashboard.yaml` (via `thresholds.load_config`) if present and PyYAML is installed; otherwise built-in defaults apply. The config can override thresholds, the module list, `off_hours`, and host mode. You do not load it yourself — the collector does — but note in the report whether a config was found.
5. **Note run shape.** After collection, `dashboard.json` carries `flags.solo` and `flags.shallow`. Solo repos force the Team light to `"na"`; shallow clones mean some history-based metrics are partial. Surface both in the report.

---

## Phase 1 — Collect (deterministic, read-only)

Run the collectors. **These are strictly read-only — they only read git, the filesystem, and (for host) query `gh`. No source file, branch, commit, or remote is mutated. Because nothing is written to the repo and no live build/test is run, there is NO approval gate** — unlike `/codebase-audit`, which must gate its test runner.

1. **Always** run the git collector, writing the canonical artifact:
   ```bash
   python skills/dashboard/helpers/collect_git.py --repo <repo> --out docs/dashboard/dashboard.json
   ```
   This produces the complete deterministic `dashboard.json` (schema, KPIs, three lenses, lights, `overall.light`). `host`, `code_quality`, `narrative`, and `overall.summary` are `null` at this stage.

2. **Unless `--no-host`**, run the host collector to a temp file:
   ```bash
   python skills/dashboard/helpers/collect_host.py --repo <repo> --out /tmp/host.json
   ```
   On any failure (no remote, `gh` missing/unauthenticated, GitLab) it still writes a valid `{"available": false, "reason": ...}` — never an error.

3. **Always** run the audit reader to a temp file (it is cheap and read-only):
   ```bash
   python skills/dashboard/helpers/collect_audit.py --repo <repo> --out /tmp/audit.json
   ```
   When no report exists it writes `{"available": false}`.

> On Windows, substitute a writable temp path for `/tmp/` (in the Bash tool's Git Bash, `$TEMP` or an absolute path like `C:/Users/<you>/AppData/Local/Temp`). The collectors only need a path they can write the small JSON to.

---

## Phase 2 — Narrate (optional; skip on `--no-llm`)

This is the only LLM step, and it is **a single host-agent pass — there is NO subagent fan-out.** This is a deliberate departure from `/handbook`'s multi-agent dispatch: the data is *already computed and small*, so there is nothing to parallelise. The host agent reads one JSON and writes one JSON.

1. Read `docs/dashboard/dashboard.json`.
2. Follow `references/narrative-prompt.md` exactly. Feed it the full `dashboard.json`. It returns a small JSON object — see the reference for the exact shape, including the per-metric `analysis` map and its canonical metric ids. (How the renderer turns `analysis` into tooltips is described in Phase 3.)
3. The narrative **explains, never recomputes.** It must not invent numbers absent from the JSON, must not soften a red or inflate a green (the engine fixed the light), must cite borrowed host/audit figures with "as of," and — when `flags.solo` is set — must frame Team concentration as expected, not alarming.
4. Save the returned object to `/tmp/narrative.json` for the merge.

**On `--no-llm`:** skip this phase entirely. The renderer already produces a templated fallback summary (`_fallback_summary` maps the overall light to "Healthy / Needs attention / At risk / Insufficient data"), and each lens keeps its deterministic `why` line built from its own numbers. No narrative file is written.

---

## Phase 3 — Merge + Render

Merge the enrichment into the metrics dict, then render. The host agent performs the merge directly (it is a handful of key assignments — see `references/output-schema.md` for the exact shapes).

Load `docs/dashboard/dashboard.json` as `data`, then:

| Merge target | Source | Condition |
|---|---|---|
| `data["host"]` | the full object from `/tmp/host.json` | unless `--no-host`; otherwise leave `null` |
| `data["code_quality"]` | the full object from `/tmp/audit.json` | always (it self-reports `available`) |
| `data["overall"]["summary"]` | narrative `overall_summary` | only if a narrative was produced |
| `data["lenses"]["delivery"]["why"]` | narrative `delivery_why` | only if a narrative was produced |
| `data["lenses"]["health"]["why"]` | narrative `health_why` | only if a narrative was produced |
| `data["lenses"]["team"]["why"]` | narrative `team_why` | only if a narrative was produced |
| `data["narrative"]` | the full narrative object (incl. `callouts` and the per-metric `analysis` map) | only if a narrative was produced |

Do **not** touch any `light` value or any computed metric — the merge only adds the optional layers. Write the merged dict back out (e.g. to `docs/dashboard/dashboard.json` or a sibling `merged.json`), then render:

```bash
python skills/dashboard/helpers/render_dashboard.py --metrics docs/dashboard/dashboard.json --out docs/dashboard/dashboard.html
```

The renderer inlines the template (`templates/dashboard.html`) and emits a single self-contained HTML file with zero external dependencies — no CDN, no `http://`/`https://`, sharable by email/Slack. It reads `host` for the KPI strip + Delivery host column, `code_quality` for the Health code-quality block, and `overall.summary` for the verdict line (falling back to the templated summary when `summary` is `null`). It also attaches an explanatory tooltip to every metric and section — static "what this measures / why it matters" copy from `helpers/tooltips.py` plus the optional per-repo `narrative.analysis` line (the "In this repo" block, omitted on `--no-llm`).

---

## Phase 4 — Report

1. Print the output paths:
   - `docs/dashboard/dashboard.json` (the data artifact)
   - `docs/dashboard/dashboard.html` (the dashboard)
2. Print the **overall light** and one-line verdict (the narrative `overall_summary`, or the templated fallback on `--no-llm`).
3. Note any degradation that applied (host skipped, audit not measured, shallow clone, solo reframing).
4. Notify completion (cross-platform):

```bash
if command -v powershell.exe &>/dev/null; then
  powershell.exe -c "[Console]::Beep(800, 300)"
elif command -v afplay &>/dev/null; then
  afplay /System/Library/Sounds/Glass.aiff &
elif command -v paplay &>/dev/null; then
  paplay /usr/share/sounds/freedesktop/stereo/complete.oga &
else
  printf '\a'
fi
```

---

## Guardrails

1. **Every metric is a proxy, not a verdict.** Firefighting rate is a keyword heuristic on commit messages; bus factor is a commit-share heuristic; off-hours is a timestamp heuristic. They point at where to look — they do not prove a problem. Frame them that way.
2. **Thresholds are opinionated and tunable — NOT industry benchmarks.** The green/yellow/red cutoffs in `thresholds.py` are this skill's defaults, overridable via `.claude/dashboard.yaml`. Never present them as established standards (that is `/codebase-audit`'s benchmark territory, and even those are sourced).
3. **Borrowed numbers are stamped with provenance and as-of.** Host PR/CI figures and the `/codebase-audit` grade are point-in-time. The narrative must say "as of," cite the source, and respect `code_quality.stale` rather than treating an old grade as current.
4. **Lights derive only from git signals.** The three lens lights and the overall light come from `collect_git.py` alone. Host and audit data enrich the display but never change a light. The narrative never changes a light either.
5. **Bus factor uses strict majority.** A "bus factor" is the number of authors who together produced **more than 50%** of recent commits. A balanced two-author repo has bus factor 2 (not 1) — both are needed to cross 50%.
6. **No secrets in output.** Only counts, grades, dates, and file/branch/author names appear. PR/issue titles and bodies, env values, and tokens never enter the HTML.

---

## Graceful Degradation

| Situation | Behavior |
|---|---|
| Not a git repo | **Stop.** `collect_git.py` exits with `error: not a git repo: <repo>`. There is no non-git fallback. |
| Shallow clone (`flags.shallow`) | Proceed, but **warn**: history is truncated, so churn/cadence/bus-factor/release figures may be partial. |
| No tags | Release recency light is `"na"`; the Delivery lens reads "no releases tagged." Release does not drag the light red. |
| Solo repo (`flags.solo`, ≤2 authors) | Team light is forced to `"na"` (not red). Concentration is **reframed as expected**, and the narrative says so. |
| `--no-host`, no remote, or `gh` missing/unauthenticated | Host enrichment skipped. KPI strip shows WIP branches instead of open PRs; no Delivery host column. |
| GitLab remote | Not implemented in v1 → host unavailable, reason recorded. |
| No `/codebase-audit` report | Code quality reads **"not measured — run /codebase-audit"** (never a fabricated grade). |
| `/codebase-audit` report is stale (`code_quality.stale`) | Grade still shown, prefixed with a ⚠ and "N commits behind HEAD." The narrative flags it rather than treating it as current. |
| `--no-llm` (or LLM unavailable) | Narrate phase skipped. Renderer uses its templated fallback summary; per-lens `why` lines stay deterministic. Dashboard is fully usable. |
| No `.claude/dashboard.yaml` (or PyYAML absent) | Built-in defaults from `thresholds.py` apply. |

---

## Error Handling

| Condition | Action |
|---|---|
| Not a git repo | Stop. Report `collect_git.py`'s error verbatim. |
| Scoped path does not exist | Report: "Path not found: `<path>`. Check the path and try again." and stop. |
| `collect_host.py` / `collect_audit.py` write `{"available": false}` | Not an error — merge as-is; the renderer shows the degraded state. |
| Corrupt/partial `/codebase-audit` report | `collect_audit.py` skips unreadable reports and never crashes; if all are unreadable, code quality is "not measured." |
| `render_dashboard.py` fails | Report the error and the path to the still-valid `docs/dashboard/dashboard.json` (the data survives even if HTML rendering does not). |
| No Python interpreter | Detect it in Phase 0 (`command -v python3 || command -v python`) and use that for every helper command — `python` alone is absent on stock macOS/Linux even when Python 3 is installed. Only if neither `python3` nor `python` exists: the skill cannot run (the entire pipeline is Python helpers) — report and stop. |
