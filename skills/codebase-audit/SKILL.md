---
name: codebase-audit
description: "Use when the user invokes /codebase-audit to run a language-agnostic codebase quality audit measuring up to 11 quality criteria + development velocity with industry benchmarks, grading, and actionable recommendations."
---

# Codebase Audit Skill

Run a comprehensive, language-agnostic codebase quality audit. Measures up to 11 core quality criteria + development velocity across 6 parallel collection agents, displays graded metrics on console, and optionally writes a full analysis report with industry benchmarks and actionable recommendations.

## Reference Files

This skill uses progressive disclosure — read reference files only when needed:

| File | Contents | When to read |
|---|---|---|
| `references/agent-prompts.md` | Full prompt templates for all 6 collection agents + Phase 4 author agent | Before dispatching agents in Phase 1 or Phase 4 |
| `references/output-schemas.md` | metrics.json schema, metrics.md template, project-context.md template, execution flows | Before writing output files in Phase 5 |
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
2. **Load config** — read `.claude/audit.yaml` if it exists (all fields optional)
3. **Auto-detect language** — check marker files in priority order (see reference)
4. **Apply language defaults** — function patterns, test runner, extension (see reference)
5. **Detect static analysis tooling** — read `shared/tooling-registry.md` and per-language profiles from `shared/tooling/`. Classify tools as `available`, `configured-but-unavailable`, or `absent`. Build gap recommendations for absent tools.
6. **Auto-detect paths** — source, test, and exclude paths (see reference)
7. **Polyglot detection** — secondary language >10% of source files → add to additional
8. **Auto-detect test runner** — check framework configs, package.json scripts, language default
9. **Domain inference** — read README, package manifests, scan key imports, check directory names. Use WebSearch for comparable projects if available.
10. **Prerequisites check** — verify Python 3 is available for helper scripts. If not, warn and offer qualitative-only mode.
11. **Scope size check** — warn if >1000 source files
12. **Merge config** — auto-detected defaults ← config overrides (config always wins)

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

Gathers context the code alone can't reveal.

### First Audit — Build the Profile

Ask 3-5 questions maximum:

1. **Project phase:** Prototype / MVP / Active growth / Mature / Maintenance
2. **Team size:** Solo / 2-5 / 6-15 / 16+
3. **Deployment cadence:** Continuous / Weekly / Monthly / Release-based / Not yet
4. **Business priority:** Speed to market / Reliability / Compliance / Cost reduction / Feature completeness
5. **Known trade-offs:** Free text — intentional debt, upcoming migrations, constraints

Also ask **informed questions** based on Phase 1 findings (e.g., "I noticed zero tests — intentional for now?").

### Returning Audits — Confirm the Profile

Check for existing profile at `docs/reports/codebase-audit/project-context.md`. If found, present it and ask if anything has changed. Quick on repeat audits.

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
| `project-context.md` | Persistent project profile | Updated each audit |

Output directory: `docs/reports/codebase-audit/YYYYMMDD/`

### Cleanup

Remove temp files. Report output paths:

> Audit complete.
> - Metrics: `docs/reports/codebase-audit/{DATE}/metrics.md`
> - Analysis: `docs/reports/codebase-audit/{DATE}/analysis.md`
> - Overall grade: **{GRADE}**

Notify completion:

```bash
powershell.exe -c "[Console]::Beep(800, 300)"
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
