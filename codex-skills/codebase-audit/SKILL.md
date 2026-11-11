---
name: codebase-audit
description: "Use when the user invokes $codebase-audit to run a language-agnostic codebase quality audit measuring up to 12 quality criteria + development velocity with industry benchmarks, grading, and actionable recommendations."
---

# Codebase Audit Skill

Measure up to 12 quality criteria and development velocity with 6 collection agents, show graded metrics in the console, and optionally write a full analysis with industry benchmarks and actionable recommendations.

Scores must stay comparable from one audit to the next, so apply the rubrics, benchmarks, adjustments, and labels in the reference files as written.

## Collection Root

The collection root is the folder one level above this SKILL.md. Every path in this skill that starts with `../` is relative to this skill's folder, so it points into the collection root, never into the project's working directory.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `../shared/report-style.md`.

## Out of Scope

This skill MUST NOT:
- Modify the audited code, even to fix an obvious bug. Measurement is read-only: never run write-mode tools (formatter or linter `--fix`, code generators); skip a tool that only runs in fix mode.
- Skip the live-command safety gate, even on `$codebase-audit metrics`. If the user declines live commands, fall back to static-only collection.
- Cite a benchmark number without its source. Copy the source from `benchmarks/*.md`. When that source says "Convention - no single authoritative source", call the number a convention. Never present a convention as an "industry standard" or as the rule of a named authority. Unsourced numbers read as fabrication.
- Grade a criterion without at least one measured metric backing it. If no metric is available, the grade is "Not measured" - never "Good" or "-" by default.
- Inflate grades to be encouraging or deflate them to be alarming. The grade reflects measured evidence, not the reaction it should produce.
- Claim "no issues found" without measuring. Absence of evidence is not evidence of absence.
- Pretend a tool ran when it didn't. If a tool was unavailable, configured-but-unavailable, or timed out, the report says so - it does not fold a missing tool into the "no findings" pile.

## Reference Files

Read each file when its phase needs it:

- `references/detection-defaults.md` - detection rules and the config file format (Phase 0).
- `references/agent-prompts.md` - agent prompts and the path-substitution rule (before any dispatch).
- `references/output-schemas.md` - output schemas and templates, and the `analysis` and `delta` flows (Phase 5 and those modes).

## Invocation

| Invocation | Mode |
|---|---|
| `$codebase-audit` | Full pipeline (all 12 criteria + velocity) |
| `$codebase-audit metrics` | Collect + display only, write metrics.json + metrics.md |
| `$codebase-audit analysis` | Re-analyze from most recent metrics.json |
| `$codebase-audit delta` | Compare two most recent audits |
| `$codebase-audit maintainability performance` | Only specified criteria |
| `$codebase-audit velocity` | Just development velocity |
| `$codebase-audit --static-only` | No live commands (no test run, no dep audit) |

`metrics`, `analysis`, and `delta` are reserved phase words. `--static-only` skips all live commands. Every other word is a criterion name from the table below. If a name is invalid, print the valid names and stop.

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
| `story-readability` | 12. Story Readability | Core |
| `velocity` | 13. Development Velocity | Extended |

---

## Phase 0 - Parse, Detect & Route

Use `references/detection-defaults.md` for detection rules. Use `../shared/tooling-registry.md` and the per-language profiles in `../shared/tooling/` for tools. Use `../shared/skill-context.md` for the preferences protocol.

Phase 0 must produce:

1. **The mode:** `full`, `metrics`, `analysis`, `delta`, or `scoped`.
2. **Loaded context.** Load `.codex/skill-context/preferences.md` (shared) and `.codex/skill-context/codebase-audit.md` (audit-specific). Either may be missing; never run a preferences interview here. Load `.codex/audit.yaml` if it exists. Config always wins: auto-detected defaults <- config overrides.
3. **The project context block**, passed to every agent:

   ```
   Language: {primary} (+{additional})
   Source paths: {paths}
   Test paths: {paths}
   Exclude: {patterns}
   Test runner: {runner}
   Domain: {summary}
   Engine: {if detected}
   ```

   Infer the domain from the README, manifests, key imports, and directory names (web search for comparable projects if available). State the inferred domain so the user can challenge it.
4. **The tool classification.** Classify each static analysis tool as `available`, `configured-but-unavailable`, or `absent`, and build gap recommendations for absent tools. With `--static-only`, still detect and classify tools, but do not run them.
5. **The tier.** Count source files. The repo is `large` tier above **1000 source files**, unless `.codex/skill-context/codebase-audit.md` sets `large_tier_threshold_files`. Large tier turns on Section Large Repo Decomposition and Section Heat-Map-Driven Deep Dive. Below the threshold, analyze the whole repo at once.
6. **Python check.** The helper scripts need Python 3. If it is missing, warn and offer qualitative-only mode.

---

## Phase 1 - Parallel Collection

The collection agents are independent; run them in parallel via the Codex agent workflow. Read `references/agent-prompts.md` for each prompt and apply its path-substitution rule before dispatch.

For same-platform subagents, do not pass a model or reasoning-effort override. Let every subagent inherit the parent model and reasoning effort unless the user explicitly asks for an override.

### Agent Roster

| # | Agent | Key Metrics | Helper Script |
|---|---|---|---|
| 1 | Structural | LOC, file/function lengths, nesting, comment density | `helpers/compute_structure.py` |
| 2 | Quality | Cyclomatic complexity, naming, magic numbers, duplication, secrets | `helpers/compute_complexity.py` |
| 3 | Architecture | Coupling, circular deps, CI/CD, dependency health, tooling adoption | - (search and read the code) |
| 4 | Git/Velocity | Churn, commit frequency, bus factor, knowledge concentration | `helpers/compute_churn.py` |
| 5 | Performance | Algorithm issues, N+1, blocking I/O, memory leaks | - (search and read the code) |
| 6 | Tests | Pass rate, test ratio, assertion density, test quality | Test runner (if approved) |

Security has no agent of its own. The Architecture agent covers it (it reads `principles/security.md` and checks dependency vulnerabilities and security scanners). The Quality agent adds the hardcoded-secrets scan.

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
| Story Readability | Structural, Quality |
| Velocity | Git/Velocity |

### Live Command Safety Gate

**Before dispatching agents, present every live command for approval:**

> **The following live commands will be executed during collection:**
> - `{test_runner}` (Tests agent)
> - `{audit_command}` (Architecture agent)
> - `{tool_command}` (Tooling - {tool_name})
>
> Options: **Run all** | **Static only** | **Select**

Read-only commands (helper scripts, `git log`, searching and reading files, tool detection) do not need approval.

### Large Repo Decomposition (Large Tier Only)

In the large tier, the two **qualitative agents** (Architecture, Performance) review the repo module by module. The four statistical agents still run on the whole repo, because their helpers do not degrade with size.

- **Modules.** Size modules so one reviewer can read each. Default: each top-level directory under the source paths is a module; merge directories with fewer than 20 source files into one `misc` module; split a module that holds more than 50% of source files one level deeper. Record the module list in the methodology.
- **Dispatch.** Cover every module with one Architecture and one Performance agent. Each gets only its module's files plus the project context block. Batch dispatch as the host allows, alongside the four whole-repo agents.
- **Roll-up.** Tag each finding with its `module`. Roll Architecture and Performance results up as the average across modules, weighted by source-file count. Phase 2 grades every criterion that uses these agents (including Security) from the rolled-up results.

### Timeouts

The skill sets no agent timeout. The only configured timeout is `testing.timeout` in `.codex/audit.yaml`, which limits the test run (in milliseconds; the example config uses 60000, which is 60 s).

---

## Phase 2 - Display & Gate

### Assemble Results & Grade

Collect the JSON from each agent. Grade each criterion with its principle file rubric and the benchmark data.

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

Cross-reference complexity (Quality agent) with churn (Git/Velocity agent) into four quadrants: **Danger Zone** (high complexity, high churn - act now), **Refactor candidates** (high churn, low complexity), **Monitor** (high complexity, low churn), and **Stable** (low both - leave it). The layout is in `templates/analysis-template.md` Section Risk Heat Map.

### Heat-Map-Driven Deep Dive (Large Tier Only)

Module decomposition gave breadth; this pass, run after the heat map, gives depth on real risk. The risk clusters are: all Danger Zone files, any module whose Phase 1 qualitative grade was C or below, and cross-module concerns that Phase 1 surfaced (e.g., coupling that spans modules).

For each cluster, dispatch one Architecture and one Performance agent with the cluster's files, their complexity and churn, and the Phase 1 findings for them, so the pass builds on Phase 1 instead of repeating it. Merge the findings into their criteria grades and mark each with `source: heat-map-deep-dive` for the methodology.

Skip this pass when there are no Danger Zone files and every module graded B or above in Phase 1.

### Grading Scale

| Grade | Meaning |
|---|---|
| A+ | Exceeds industry best practice |
| A | Meets best practice |
| B | Acceptable, minor improvements possible |
| C | Below average, attention needed |
| D | Significant issues, action required |
| F | Critical deficiencies |

Grading is relative to resolved benchmarks (language-specific -> general fallback).

The scale has no plus or minus grades. Use only the grades in this table (with `~` for low confidence).

### Console Display

Print a summary table in the conversation:

**CODEBASE AUDIT - {Project Name}**
{Domain Summary} * {Language} * {Date}
**Overall Grade: {GRADE}** (confidence: {CONFIDENCE})

| # | Criterion | Grade | Key Metric | Benchmark |
|---|---|---|---|---|
| 1 | Maintainability | B | CC avg: 8.2 | <= 10 |
| 2 | Evolvability | B | Fan-out avg: 3.1 | <= 5 |
| ... | | | | |
| 12 | Story Readability | B | Narr: 8, Chunk: 6 | >= 7 avg |
| 13 | Velocity | - | +2.1k lines/30d | - |

**Top Risk:** {criterion} ({grade}) - {reason}
**Top Strength:** {criterion} ({grade}) - {reason}
**Danger Zone:** {file} (CC:{N}, {N} changes)

Show only measured criteria. Failed or skipped agents show "-" with a note.

### Gate

After the table, ask what to do next with these three options:

1. **Write both** - metrics.json + metrics.md + full analysis
2. **Metrics only** - write metrics.json + metrics.md (numbers, no commentary)
3. **Done** - just the console display, no files

**Routing rules:**
- `$codebase-audit metrics` -> skip gate, write metrics files directly
- `$codebase-audit analysis` -> skip Phase 1, load most recent metrics.json, proceed to Phase 3
- User selects option 1 -> proceed to Phase 3
- User selects option 2 -> skip to Phase 5 (write metrics only)
- User selects option 3 -> stop

---

## Phase 3 - User Context Interview

Ask only for what neither preference file already holds: project phase, team size, and business priority (shared preferences); deployment cadence (either file); known trade-offs (audit-specific file). Add informed questions from Phase 1 findings (e.g., "I noticed zero tests - intentional for now?"). Ask everything in one short round; these answers change the grading. On a repeat audit, show the combined profile and ask what changed.

Save answers to `.codex/skill-context/codebase-audit.md`. Do not write `.codex/skill-context/preferences.md` - that file belongs to the user.

Weigh findings and recommendations against the stated phase, team size, and known trade-offs.

---

## Phase 4 - Analysis Writing

One author agent writes the full analysis in one pass. Its prompt is in `references/agent-prompts.md`.

Before you start the author, save the assembled metrics as `metrics.json` in this run's output folder (see Phase 5), with `rank` and `weight` still `null`. In `analysis` mode the file is already there. The author's prompt gets the absolute path to that file, never a copy of its contents. It also gets the project context, the user context, the risk heat map, and the absolute path to the previous audit's `metrics.json` if there is one. The previous audit is the newest `metrics.json` outside this run's folder.

**Dynamic criteria weighting:** The author assigns a **priority rank** (1-12) and **weight** (High/Medium/Low) to each criterion for this language and domain. This sets priority order, overall grade, analysis depth, and recommended actions. Users can override it with `criteria_priority` in `audit.yaml`.

---

## Phase 5 - Write & Output

Use `references/output-schemas.md` for the schemas and templates.

| File | Content | When written |
|---|---|---|
| `metrics.json` | Machine-readable metrics with grades, benchmarks, methodology | Always (options 1 & 2) |
| `metrics.md` | Human-readable metrics table | Always (options 1 & 2) |
| `analysis.md` | Full qualitative report per `templates/analysis-template.md` | Option 1 only |
| `.codex/skill-context/codebase-audit.md` | Audit-specific preferences (trade-offs, cadence, history) | Updated each audit |

Output directory: `docs/reports/codebase-audit/YYYYMMDD/`

Choose this folder once, when the run writes its first file, and put every file of the run in it. For option 1 that first file is the `metrics.json` saved before Phase 4; update it here with the final ranks, weights, and overall grade by changing only those fields.

Remove temp files. Report the output paths and the overall grade. Then notify completion:

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

## Degradation and Errors

When something fails, continue with what is left and label the gap with these exact labels:

| Situation | Behavior |
|---|---|
| Some agents fail or time out | Proceed with the rest, name the missing agents, and offer a retry. If all fail, suggest a narrower scope. |
| Helper script fails, or Python is not available | Helper-dependent metrics are "Not measured". The agent falls back to qualitative-only. |
| Large tier - some modules fail | Proceed with successful modules. The roll-up grade notes "N of M modules analyzed." |
| Live commands declined | Static analysis fallback. Mark as "Skipped (live commands declined)." |
| `--static-only` with tools detected | Tools are detected and classified but not run. |
| No git history | Git/Velocity skips. Churn and bus factor say "No git history." |
| No test runner detected | Tests agent does static analysis only. |
| Tool configured but binary not found | Classify as `configured-but-unavailable` and grade as absent. Note the config in the analysis. |
| Tool fails, times out, or gives unparseable output | Skip it, note the failure, and continue with the other tools. |
| No static analysis tools detected | Include gap recommendations. Grade the criteria without tool input. |
| No internet (web search unavailable) | Use cached benchmarks. Note "cached benchmarks only" in the methodology. |
| Unknown language | Use general benchmarks and the extension-count fallback. |
| `.codex/audit.yaml` is malformed | Report the parse error and use auto-detection. |
| No source files found | "No source files found in detected paths. Check project structure." |
| No metrics.json for `analysis` mode | "No previous metrics found. Run `$codebase-audit` first." |
| Fewer than 2 metrics.json for `delta` mode | "Need at least 2 audits for delta comparison. Found {N}." |
