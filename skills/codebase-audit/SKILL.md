---
name: codebase-audit
version: "1.0.0"
description: "Use when the user invokes /codebase-audit to run a language-agnostic codebase quality audit measuring up to 11 quality criteria + development velocity with industry benchmarks, grading, and actionable recommendations."
---

# Codebase Audit Skill

Run a comprehensive, language-agnostic codebase quality audit. Measures up to 11 core quality criteria + development velocity across 6 parallel collection agents, displays graded metrics on console, and optionally writes a full analysis report with industry benchmarks and actionable recommendations.

## Reference Files

This skill uses progressive disclosure — read reference files only when needed:

| File | Contents | When to read |
|---|---|---|
| `references/agent-prompts.md` | Full prompt templates for all 6 collection agents + Phase 4 author agent | Before dispatching agents in Phase 1 or Phase 4 |
| `references/output-schemas.md` | metrics.json schema, metrics.md template, codebase-audit.md preferences template, execution flows | Before writing output files in Phase 5 |
| `references/detection-defaults.md` | Language marker files, language defaults, path auto-detection, polyglot rules, config file format | During Phase 0 detection |

## Invocation

Parse the user's `/codebase-audit` arguments:

| Invocation | Mode |
|---|---|
| `/codebase-audit` | Full pipeline (all 11 criteria + velocity) |
| `/codebase-audit metrics` | Collect + display only, write metrics.json + metrics.md |
| `/codebase-audit analysis` | Re-analyze from most recent metrics.json |
| `/codebase-audit delta` | Compare two most recent audits |
| `/codebase-audit maintainability performance` | Only specified criteria |
| `/codebase-audit velocity` | Just development velocity |
| `/codebase-audit --static-only` | No live commands (no test run, no dep audit) |

### Parsing Rules

- **Reserved phase words:** `metrics`, `analysis`, `delta`
- **Everything else:** Treated as criterion names, validated against the 12 valid names
- **Flags:** `--static-only` — skip all live commands
- **Invalid names:** Print error listing valid options, stop

### Valid Criterion Names

| Argument | Criterion | Category |
|---|---|---|
| `maintainability` | 1. Maintainability | Core |
| `evolvability` | 2. Evolvability | Core |
| `correctness` | 3. Correctness | Core |
| `testability` | 4. Testability | Core |
| `reliability` | 5. Reliability | Core |
| `performance` | 6. Performance | Core |
| `readability` | 7. Readability | Core |
| `modularity` | 8. Modularity | Core |
| `consistency` | 9. Consistency | Core |
| `operability` | 10. Operability | Core |
| `security` | 11. Security | Core |
| `velocity` | 12. Development Velocity | Extended |

---

## Phase 0 — Parse, Detect & Route

Read `references/detection-defaults.md` for language marker files, language defaults, path detection rules, and config file format.

### Detection Steps

1. **Parse arguments** — determine invocation mode: `full`, `metrics`, `analysis`, `delta`, or `scoped`
2. **Load user preferences** — read `shared/skill-context.md` for the full protocol. Load `.claude/skill-context/preferences.md` (shared) and `.claude/skill-context/codebase-audit.md` (skill-specific). If no shared preferences exist, invoke `/preferences` (streamlined mode). Shared preferences supply project phase, team size, and business priority — Phase 3 will skip questions already answered here.
3. **Load config** — read `.claude/audit.yaml` if it exists (all fields optional)
4. **Auto-detect language** — check marker files in priority order (see reference)
5. **Apply language defaults** — function patterns, test runner, extension (see reference)
6. **Detect static analysis tooling** — read `shared/tooling-registry.md` and per-language profiles from `shared/tooling/`. Classify tools as `available`, `configured-but-unavailable`, or `absent`. Build gap recommendations for absent tools.
7. **Auto-detect paths** — source, test, and exclude paths (see reference)
8. **Polyglot detection** — secondary language >10% of source files → add to additional
9. **Auto-detect test runner** — check framework configs, package.json scripts, language default
10. **Domain inference** — read README, package manifests, scan key imports, check directory names. Use WebSearch for comparable projects if available.
11. **Prerequisites check** — verify Python 3 is available for helper scripts. If not, warn and offer qualitative-only mode.
12. **Scope size check** — warn if >1000 source files
13. **Merge config** — auto-detected defaults ← config overrides (config always wins)

### Output of Phase 0

A **project context block** passed to all agents:

```
Language: {primary} (+{additional})
Source paths: {paths}
Test paths: {paths}
Exclude: {patterns}
Test runner: {runner}
Domain: {summary}
Engine: {if detected}
```

If `--static-only` was passed, skip tool execution in Phase 1 but still detect and classify tools.

---

## Phase 1 — Parallel Collection

Spawn **6 measurement agents in parallel** via the Agent tool — all 6 in a single response. Each uses `model: "opus"`. Read `references/agent-prompts.md` for the full prompt template for each agent.

### Agent Roster

| # | Agent | Key Metrics | Helper Script |
|---|---|---|---|
| 1 | Structural | LOC, file/function lengths, nesting, comment density | `helpers/compute_structure.py` |
| 2 | Quality | Cyclomatic complexity, naming, magic numbers, duplication, secrets | `helpers/compute_complexity.py` |
| 3 | Architecture | Coupling, circular deps, CI/CD, dependency health, tooling adoption | — (Grep/Read) |
| 4 | Git/Velocity | Churn, commit frequency, bus factor, knowledge concentration | `helpers/compute_churn.py` |
| 5 | Performance | Algorithm issues, N+1, blocking I/O, memory leaks | — (Grep/Read) |
| 6 | Tests | Pass rate, test ratio, assertion density, test quality | Test runner (if approved) |

### Scoped Invocations

For scoped criteria, launch only the required agents:

| Criterion | Required Agents |
|---|---|
| Maintainability | Structural, Quality |
| Evolvability | Structural, Architecture |
| Correctness | Tests, Structural |
| Testability | Tests, Structural, Architecture |
| Reliability | Architecture, Structural |
| Performance | Performance, Architecture |
| Readability | Structural, Quality |
| Modularity | Architecture |
| Consistency | Quality, Architecture |
| Operability | Architecture, Structural |
| Security | Architecture, Quality |
| Velocity | Git/Velocity |

### Live Command Safety Gate

Before dispatching agents, present all live commands for approval:

> **The following live commands will be executed during collection:**
> - `{test_runner}` (Tests agent)
> - `{audit_command}` (Architecture agent)
> - `{tool_command}` (Tooling — {tool_name})
>
> Options: **Run all** | **Static only** | **Select**

Read-only commands (helper scripts, `git log`, Glob/Grep/Read, tool detection) do not need approval.

### Failure Handling

- **Agent timeout:** 60s default. Proceed with available data, note missing agent.
- **Helper script failure:** Agent falls back to qualitative-only. Metrics marked "Not measured."
- **No test runner:** Tests agent does static analysis only.
- **Live commands declined:** Static analysis fallback. Mark as "Skipped (live commands declined)."

---

## Phase 2 — Display & Gate

### Assemble Results & Grade

Collect structured JSON from each agent. For each criterion, compute a grade using the principle file rubric + benchmark data.

**Audit Confidence Model:** Each criterion gets a confidence level (`high`, `medium`, `low`). Append `~` to grades with low confidence (e.g., "B~"). Overall confidence = lowest among all criteria.

**Tooling Impact on Grades:**

| Criterion | Positive Signal | Negative Signal |
|---|---|---|
| Security | Scanner present + clean | No scanner, or vulnerabilities found |
| Consistency | Formatter + linter clean | Violations, or no formatter/linter |
| Operability | Analysis tooling present, CI-integrated | No tooling at all |
| Maintainability | Static analyzer clean | Analyzer found issues |
| Correctness | Type checker clean | Type errors found |

### Risk Heat Map

Cross-reference complexity (Quality agent) with churn (Git/Velocity agent):

```
              High Churn
                  │
   ┌──────────────┼──────────────┐
   │  Refactor    │  Danger Zone │
   │  candidates  │  (act now)   │
───┼──────────────┼──────────────┼─── High Complexity
   │  Stable      │  Monitor     │
   │  (leave it)  │  (watch)     │
   └──────────────┼──────────────┘
              Low Churn
```

"Danger Zone" files (high complexity + high churn) are named explicitly.

### Grading Scale

| Grade | Meaning |
|---|---|
| A+ | Exceeds industry best practice |
| A | Meets best practice |
| B | Acceptable, minor improvements possible |
| C | Below average, attention needed |
| D | Significant issues, action required |
| F | Critical deficiencies |

Grading is relative to resolved benchmarks (language-specific → general fallback).

### Console Display

Print a summary table directly in the conversation:

```
╔══════════════════════════════════════════════════════════════╗
║  CODEBASE AUDIT — {Project Name}                           ║
║  {Domain Summary} · {Language} · {Date}                    ║
╠══════════════════════════════════════════════════════════════╣
║  Overall Grade: {GRADE} (confidence: {CONFIDENCE})         ║
╠══════════════════════════════════════════════════════════════╣
║  #  Criterion        Grade  Key Metric         Benchmark   ║
║  ── ──────────────── ────── ────────────────── ─────────── ║
║   1 Maintainability    B    CC avg: 8.2        ≤ 10        ║
║   2 Evolvability       B+   Fan-out avg: 3.1   ≤ 5         ║
║  ...                                                       ║
║  ── ──────────────── ────── ────────────────── ─────────── ║
║  12 Velocity           —    +2.1k lines/30d    —           ║
╠══════════════════════════════════════════════════════════════╣
║  Top Risk: {criterion} ({grade}) — {reason}                ║
║  Top Strength: {criterion} ({grade}) — {reason}            ║
║  Danger Zone: {file} (CC:{N}, {N} changes)                 ║
╚══════════════════════════════════════════════════════════════╝
```

Dynamically generated — only measured criteria appear. Failed/skipped agents show "—" with a note.

### Gate

After displaying the table:

> **Metrics collected.** What would you like to do?
> 1. **Write both** — metrics.json + metrics.md + full analysis
> 2. **Metrics only** — write metrics.json + metrics.md (numbers, no commentary)
> 3. **Done** — just the console display, no files

**Routing rules:**
- `/codebase-audit metrics` → skip gate, write metrics files directly
- `/codebase-audit analysis` → skip Phase 1, load most recent metrics.json, proceed to Phase 3
- User selects option 1 → proceed to Phase 3
- User selects option 2 → skip to Phase 5 (write metrics only)
- User selects option 3 → stop

---

## Phase 3 — User Context Interview

Gathers context the code alone can't reveal. Uses the shared preferences
system (`shared/skill-context.md`) to avoid re-asking questions.

### Context Sources (checked in order)

1. **Shared preferences** (`.claude/skill-context/preferences.md`) — loaded in Phase 0 step 2. Contains project phase, team size, business priority.
2. **Audit-specific preferences** (`.claude/skill-context/codebase-audit.md`) — deployment cadence, known trade-offs.
3. **Legacy profile** (`docs/reports/codebase-audit/project-context.md`) — if this exists but no shared preferences file does, migrate its contents into the shared system.

### First Audit — Build the Profile

Check what's already known from shared preferences. Only ask questions whose
answers are not already captured:

| Question | Skip if already in... |
|---|---|
| Project phase | shared preferences → "Project phase" |
| Team size | shared preferences → "Team size" |
| Deployment cadence | shared preferences → "Deployment cadence" **or** audit-specific preferences |
| Business priority | shared preferences → "Business priority" |
| Known trade-offs | audit-specific preferences → "Known trade-offs" |

If shared preferences exist and cover project phase, team size, and business
priority, the only new questions are **deployment cadence** (if missing),
**known trade-offs**, and **informed questions** based on Phase 1 findings
(e.g., "I noticed zero tests — intentional for now?").

If no shared preferences exist at all, `/preferences` was already invoked in
Phase 0 step 2 — those answers are now available. Ask only the audit-specific
questions: deployment cadence, known trade-offs, and informed questions.

Save audit-specific answers to `.claude/skill-context/codebase-audit.md`.

### Returning Audits — Confirm the Profile

Check for existing audit-specific preferences at
`.claude/skill-context/codebase-audit.md`. If found, present the combined
profile (shared + audit-specific) and ask if anything has changed. Quick on
repeat audits.

### Legacy Migration

If `docs/reports/codebase-audit/project-context.md` exists but
`.claude/skill-context/preferences.md` does not:

1. Read the legacy file
2. Extract project phase, team size, deployment cadence, business priority
3. Write shared fields to `.claude/skill-context/preferences.md`
4. Write audit-specific fields (known trade-offs, audit history) to `.claude/skill-context/codebase-audit.md`
5. Inform the user: "Migrated your audit profile to the shared preferences system."
6. The legacy file remains in place (existing reports may reference it) but is no longer the source of truth.

### How User Context Shapes the Analysis

| User Context | Analysis Effect |
|---|---|
| Solo + Prototype | Lighter on process, heavier on "what to invest in first" |
| Team of 10 + Mature | Heavier on consistency, modularity, onboarding friction |
| "Speed to market" priority | Recommendations framed as "do this now" vs. "before scaling" |
| "Low test coverage intentional" | Testability acknowledges trade-off rather than flagging as surprise |

---

## Phase 4 — Analysis Writing

A single author agent writes the full analysis in one pass. Uses `model: "opus"`. Read `references/agent-prompts.md` for the full author agent prompt.

The author receives: assembled metrics JSON, project context, user context, risk heat map, and previous audit data (if any).

### Dynamic Criteria Weighting

The author assigns a **priority rank** (1-11) and **weight** (High/Medium/Low) to each criterion based on language + domain expertise. This affects priority order, overall grade, analysis depth, and recommended actions. Users can override via `criteria_priority` in `audit.yaml`.

---

## Phase 5 — Write & Output

Read `references/output-schemas.md` for the full schemas and templates.

### Output Files

| File | Content | When written |
|---|---|---|
| `metrics.json` | Machine-readable metrics with grades, benchmarks, methodology | Always (options 1 & 2) |
| `metrics.md` | Human-readable metrics table | Always (options 1 & 2) |
| `analysis.md` | Full qualitative report per `templates/analysis-template.md` | Option 1 only |
| `.claude/skill-context/codebase-audit.md` | Audit-specific preferences (trade-offs, cadence, history) | Updated each audit |

Output directory: `docs/reports/codebase-audit/YYYYMMDD/`

### Cleanup

Remove temp files. Report output paths:

> Audit complete.
> - Metrics: `docs/reports/codebase-audit/{DATE}/metrics.md`
> - Analysis: `docs/reports/codebase-audit/{DATE}/analysis.md`
> - Overall grade: **{GRADE}**

Notify completion (cross-platform):

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

1. **Never present a benchmark without a source citation.** Unsourced benchmarks look made up.
2. **Never grade a criterion without at least one measured metric.** Grades based on vibes are worthless.
3. **Never claim "no issues found" without having actually measured.** Absence of evidence ≠ evidence of absence.
4. **If a helper script fails, mark affected metrics as "Not measured" — not "Good."**
5. **Always show delta direction (improved/declined/stable) when comparing.**
6. **Domain inference must be stated explicitly** so the user can challenge it.
7. **Criteria priority rationale must be shown in the report.**
8. **Effort estimates must reference codebase size and team context.**
9. **All Danger Zone files must be named explicitly.**
10. **User context trade-offs must be acknowledged** in relevant criterion sections.

---

## Graceful Degradation

| Situation | Behavior |
|---|---|
| 1-2 agents fail or time out | Proceed with available data. Note missing agents. Offer to retry. |
| All agents fail | Report failure. Suggest retrying or narrowing scope. |
| No git history | Git/Velocity agent skips. Churn/bus factor marked "No git history." |
| No test runner detected | Tests agent does static analysis only. |
| Helper script fails | Agent falls back to qualitative-only. Metrics marked "Not measured." |
| No internet (WebSearch unavailable) | Use cached benchmarks. Note "cached benchmarks only" in methodology. |
| Unknown language | Use general benchmarks. Extension-count fallback. |
| Massive repo (1000+ files) | Warn user. Agents focus on most significant files. |
| No `.claude/audit.yaml` | Fully auto-detected. Note in methodology. |
| Python not available | Qualitative-only for helper-dependent metrics. |
| No previous audit for delta | "Need at least 2 audits for delta comparison." |
| Live commands declined | Static analysis fallback. Mark as "Skipped (live commands declined)." |
| No static analysis tools detected | Gap recommendations included. Criteria graded without tool input. |
| Tool configured but not installed | Graded as absent. Config noted in analysis. |
| Tool execution fails | Skip tool, proceed with remaining tools. Note failure. |
| `--static-only` with tools detected | Tools detected and classified but not executed. |

---

## Error Handling

| Error | Behavior |
|---|---|
| Invalid criterion name | Print valid names, stop |
| `.claude/audit.yaml` is malformed | Report parse error, proceed with auto-detection |
| No source files found | "No source files found in detected paths. Check project structure." |
| metrics.json not found for `analysis` mode | "No previous metrics found. Run `/codebase-audit` first." |
| <2 metrics.json for `delta` mode | "Need at least 2 audits for delta comparison. Found {N}." |
| Output directory creation fails | Report error, suggest alternative path |
| Agent returns malformed JSON | Use what's parseable, note the issue |
| Tool binary not found | Classify as `configured-but-unavailable`, skip, continue |
| Tool output unparseable | Report raw summary, skip structured parsing, continue |
| Tool timeout | Kill process, skip tool, continue with remaining tools |
