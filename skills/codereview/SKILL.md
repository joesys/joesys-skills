---
name: codereview
description: "Use when the user invokes /codereview to analyze code for correctness, quality, architecture, reliability, security, and performance violations with concrete before/after examples."
---

# Code Review Skill

Dispatch 7 parallel analysis subagents — each a domain expert (correctness, clean code, architecture, reliability, security, performance, story readability) — against the target code. Collect their findings, deduplicate overlapping violations, and synthesize a severity-grouped report with concrete before/after fixes in the target language.

## Out of Scope

This skill MUST NOT:
- Modify source code without explicit user approval after the report. The skill produces findings; fixing happens only via the Phase 4 Fix Dispatch, only after the user picks "yes" or names specific findings.
- Expand fixes beyond what was flagged. When the user approves fixes, fix exactly the reported findings — do not bundle "while I'm in this file" cleanup, renames, or unrelated improvements.
- Report on code outside the resolved scope. If the diff/file/PR doesn't include a file, do not flag findings in it — even if you notice them while gathering context.

## Invocation

Parse the user's `/codereview` arguments to determine mode and scope:

| Invocation | Mode | Scope |
|---|---|---|
| `/codereview` | Branch diff (default) | Current branch vs. fork point |
| `/codereview src/utils/` | Directory scan | All files recursively in specified directory |
| `/codereview --file src/main.py` | Single file | One specific file |
| `/codereview --pr 123` | PR review | Files changed in a GitHub PR |
| `/codereview --commit abc123` | Commit review | Files changed in a specific commit |
| `/codereview --min-severity P1` | Severity filter | Combinable with any mode |
| `/codereview --no-re-review` | Suppress re-review | Skip Phase 3.7 — present mechanical synthesis output directly |

Arguments are combinable. Examples:
- `/codereview --pr 42 --min-severity P1` — review PR #42, only show P1+ findings
- `/codereview src/api/ --min-severity P2` — scan directory, show P2+ findings
- `/codereview --no-re-review` — skip the Tech Lead re-review pass (faster, no annotations)

If the invocation is ambiguous or unrecognizable, ask the user to clarify before proceeding.

---

## Phase 1: Scope Resolution

### 1.0 Load User Preferences

Read `shared/skill-context.md` for the full protocol (resolve `shared/...` against the plugin root — two levels above this SKILL.md — never the project's working directory). In brief:

1. Read `.claude/skill-context/preferences.md` — if missing, invoke `/preferences` (streamlined).
2. Read `.claude/skill-context/codereview.md` (if it exists) for review-specific preferences.

**How preferences shape this skill:**

| Preference | Effect on Code Review |
|---|---|
| Detail level: concise | Shorter findings, omit minor context, focus on top issues |
| Detail level: detailed | Include architectural context, explain why something is a problem |
| Assumed knowledge: beginner | Explain what the violation means, not just what to fix |
| Assumed knowledge: expert | Skip obvious explanations, focus on non-obvious implications |
| Review-specific: severity focus | Override `--min-severity` default (e.g., user always wants P0–P1 only) |
| Review-specific: priority domains | Reorder which domains get emphasis in the synthesis |

Pass relevant preferences to each domain subagent in Phase 2 — append a `## User Preferences` section to the subagent prompt (after its `## Instructions` block). The prompt carries the principle file as a `<PRINCIPLE_PATH>` reference, not inlined content, so there is no "principle file content" to append after.

### 1.1 Base Branch Detection

Read `shared/review-common.md` § Base Branch Detection.

### 1.2 File Gathering

Read `shared/review-common.md` § File Gathering.

### 1.3 Content Loading

- Read the **full content** of every changed file — not just the diff hunks. Subagents need surrounding context to judge architecture, naming, and control flow.
- Also capture the **diff itself** (`git diff <base>...HEAD` or equivalent) so subagents can focus on what actually changed while having the full file for context.

### 1.4 Scope-Based Dispatch Strategy

Three tiers based on diff size. Measure LOC from `git diff --shortstat <base>...HEAD` (insertions + deletions).

| Tier | Trigger | Strategy |
|---|---|---|
| Small | ≤ 30 files **and** ≤ 5,000 LOC | Single-shot: one dispatch of 7 domain subagents + cross-model over all files (Phase 2 as-is) |
| Medium | 31–100 files **and** ≤ 5,000 LOC | File-batching — see § 1.4a |
| Large | > 100 files **or** > 5,000 LOC changed | Logical-cluster dispatch — see § 1.4b. The LOC trigger takes precedence: a few files carrying a huge diff (generated code, lockfiles) is Large, not Small. |

Thresholds are defaults. Users can override in `.claude/skill-context/codereview.md` with any of:
- `medium_tier_threshold_files` (default `30`)
- `large_tier_threshold_files` (default `100`)
- `large_tier_threshold_loc` (default `5000`)

### 1.4a Medium Tier — File Batching

Batch files into groups of roughly equal size (aim for 10–15 per batch). Keep related files in the same batch when possible (e.g., a module and its tests, a component and its styles). Each batch gets its own full dispatch (7 domain subagents + cross-model). Process batches sequentially:

1. Dispatch 7 parallel subagents + cross-model for batch 1, collect results
2. Dispatch for batch 2, collect results
3. Continue until all batches are processed
4. Synthesize all batch results together in Phase 3
5. Phase 3.7 (Tech Lead re-review) runs **once** over the fully-merged findings — not per batch

### 1.4b Large Tier — Logical-Cluster Dispatch

When the diff exceeds the large-tier threshold, file-batching stops being enough — related changes span files, and arbitrary slices miss cross-file issues. Instead: scope the diff into logical clusters, dispatch a full review per cluster, then synthesize across clusters.

**Step 1 — Scoping pass (one agent).** Dispatch a single agent with `model: "opus"` that receives only metadata (no full file contents):

- `git diff --stat <base>...HEAD`
- `git log <base>...HEAD --oneline`
- Commit bodies: `git log <base>...HEAD --format='%h %s%n%b'`

The agent partitions changed files into **logical clusters**, each tagged:

| Type | Meaning |
|---|---|
| `feature` | New capability — cohesive set of related changes |
| `bugfix` | Targeted fix to existing behavior |
| `refactor` | Structural change with no behavior change |
| `cross-cutting` | Renames, formatting, mechanical edits spanning many files |
| `test-only` | Changes confined to test files |
| `config/infra` | Build, CI, deployment, dependency files |

Required output format:

```
## Cluster N: <short name>
**Type:** <cluster-type>
**Intent:** <one sentence on what this cluster accomplishes>
**Files:**
- path/to/file1
- path/to/file2
```

Every changed file MUST appear in exactly one cluster. If a file is missing, rerun the scoping pass.

**Step 2 — Cluster dispatch.** For each cluster, dispatch a full review (7 domain subagents + cross-model) in parallel. Every cluster gets all 7 domains regardless of cluster type — the cluster tag is reader context and synthesis priority, not a reviewer filter.

**MUST fire all cluster dispatches in a single parallel batch.** With N clusters, that's N × 9 tool calls in one response. No user gate between scoping and dispatch — the scoping pass returns, dispatch fires automatically.

Each cluster dispatch receives only its cluster's files (per Phase 1.3 content loading) plus the diff slice for those files.

**Step 3 — Continue to Phase 3.** Cross-cluster synthesis runs there — see § 3.1a. Phase 3.7 (Tech Lead re-review) runs **after** the cross-cluster synthesis completes, on the fully-merged findings.

### 1.5 Target Language Detection

Read `shared/review-common.md` § Target Language Detection.

### 1.6 Static Analysis Tooling

Read `shared/review-common.md` § Static Analysis Tooling — Detection Protocol (steps 1–3: detect, check availability, classify).

Then continue with codereview-specific steps:

4. **Build scoped commands** — for `available` tools, construct report-only commands targeting only the changed files using the tool's scope-to-files flag from the per-language profile.
5. **Safety Gate** — present scoped tool commands to the user for approval (alongside any other live commands).
6. **Execute approved tools** — run each tool. Respect timeouts (from `audit.yaml` if present, else adaptive: <10k LOC = 30s, 10–100k = 60s, >100k = 120s per tool).
7. **Build TOOLING_CONTEXT** — assemble the slim version (findings only — no gap analysis, no build-integrated detection).

---

## Phase 2: Parallel Analysis

**MUST dispatch 7 subagents simultaneously** via the Agent tool — all 7 in a single response (7 parallel Agent tool calls). Each subagent is a domain expert that analyzes the code against one principle set. Sequential dispatch is a defect.

### Subagent Roster

| # | Domain | Principle File |
|---|---|---|
| 1 | Clean Code | `principles/clean-code.md` |
| 2 | Architecture | `principles/architecture.md` |
| 3 | Reliability | `principles/reliability.md` |
| 4 | Security | `principles/security.md` |
| 5 | Performance | `principles/performance.md` |
| 6 | Correctness | `principles/correctness.md` |
| 7 | Story Readability | `shared/story-readability.md` |

### Subagent Prompt Template

Each subagent receives a prompt structured as follows. Adjust `<DOMAIN>` and `<PRINCIPLE_PATH>` per agent. Substitute `<PRINCIPLE_PATH>` with the **absolute path** to the roster file: resolve `principles/...` entries against this skill's own directory and `shared/...` entries against the plugin root (two levels above this SKILL.md) — never against the project's working directory. Subagents start in the project cwd and cannot find plugin files by relative path.

```
You are a senior <DOMAIN> reviewer.

## Instructions
1. Read the principle file at: <PRINCIPLE_PATH>
2. Analyze the code below against every principle in that file.
3. For each violation found, output it in the structured format below.
4. All code examples (Before/After) MUST be in <TARGET_LANGUAGE> — do NOT use Python or any other language unless the target code is in that language.
5. If you find no violations in your domain, output: "No <DOMAIN> violations found."

## Code Under Review
<FILES_CONTENT>

## Diff Context
<DIFF_CONTENT>

## Static Analysis Results
{TOOLING_CONTEXT}

Use these tool findings to corroborate or supplement your analysis. If a tool flagged
the same issue you found, note it in your finding. If a tool found something you missed,
include it in your output with "[{tool_name}]" prefix.

## Output Format
For each violation:

### [Principle Name] — [Specific Issue]
**Severity**: P0 | P1 | P2 | P3 | P4
**Location**: `file.ext:line_number`
**Problem**: Description of what is wrong.
**Suggested Fix**: 1–2 sentences stating the fix approach — the strategy that fixes the root cause, not just the diff. Suggested Fix and After MUST agree: the prose states the strategy, the code shows it. If you cannot articulate the strategy in prose, you have not understood the fix — do not emit the finding.
**Before**:
```<target_language>
// the problematic code
```
**After**:
```<target_language>
// the corrected code matching the Suggested Fix
```
**Why**: Explanation of why this matters and what could go wrong.
```

Severity levels are defined in `shared/review-common.md` § Severity Scale (P0 critical through P4 optional).

**MUST spawn subagents** with `model: "opus"` to ensure high-quality analysis.

#### Story Readability Subagent Adjustments

The Story Readability subagent (domain 7) uses the same prompt template as the other 6, with two adjustments:

1. **Additional output:** In addition to the standard violation format, the Story Readability subagent outputs per-dimension scores (1–10) for each file reviewed. These scores follow the scoring protocol defined in `shared/story-readability.md`.
2. **Severity calibration:** Story readability findings naturally cluster at P2–P4. The subagent does not artificially inflate severity — narrative concerns are maintainability issues, not critical bugs. Typical mapping:
   - P2: Functions that actively mislead (e.g., a function named `validate` that also mutates state)
   - P3: Functions that don't read as stories but aren't misleading (e.g., missing cognitive chunking, mixed abstraction levels)
   - P4: Minor narrative polish (e.g., paragraph spacing, slight naming improvements)

### Cross-Model Dispatch

In addition to the 7 domain subagents, dispatch cross-model review requests to **both Codex and Antigravity** in the **same parallel batch** — all 9 invocations (7 subagents + 2 cross-model CLIs) launch simultaneously in a single response.

#### Dispatch Protocol

Read `shared/cross-model-dispatch.md` for host detection, platform-adaptive temp file creation, CLI command templates, and failure handling. Read `shared/model-defaults.md` for current model identifiers.

#### Cross-Model Prompt

Write the prompt to a temp file (use `mktemp` per `shared/cross-model-dispatch.md`):

```bash
PROMPT_FILE=$(mktemp /tmp/codereview-cross-XXXXXX.txt)
cat > "$PROMPT_FILE" << 'PROMPT_EOF'
You are a comprehensive code reviewer. Analyze the following code changes for bugs, security vulnerabilities, performance issues, reliability problems, architectural concerns, and code quality.

## Rules
- Use this severity scale: P0 (critical), P1 (high), P2 (medium), P3 (low), P4 (optional)
- For each finding: file, line, what's wrong, severity, suggested fix, and why it matters
- Be thorough but precise — every finding must reference a specific location
- All code examples (Before/After) MUST be in <TARGET_LANGUAGE>

## Files Under Review
<FILES_CONTENT>

## Diff
<DIFF_CONTENT>

## Static Analysis Results
{TOOLING_CONTEXT}

## Output Format
For each finding:
<FINDING_FORMAT>

If you find no issues, output: "No issues found."
PROMPT_EOF
```

Substitute `<FINDING_FORMAT>` with the finding structure from the § Subagent Prompt Template's Output Format (`### [Principle Name] — [Specific Issue]` through `**Why**`), using `[Category]` in place of `[Principle Name]`.

Write the prompt to **two** separate temp files (one per cross-model CLI) using `mktemp`. Dispatch both in parallel using the CLI command templates from `shared/cross-model-dispatch.md`. Use 600000ms timeout. Clean up both temp files after completion.

Both cross-model reviewers receive the **same full file content and diff** that the 7 domain subagents receive — not the reduced context used in quick-review. When files are batched (Phase 1.4), the cross-model dispatches are included in each batch alongside the 7 subagents.

#### Failure Handling

Cross-model dispatch failures are handled per § Error Handling — continue with whatever sources returned and note unavailable models in the report header.

---

## Phase 3: Synthesis

### 3.1 Collect Results

Gather all findings from the 7 domain subagents and the cross-model dispatch. If any subagent or the cross-model reviewer failed, note which source was unavailable and proceed with the remaining results.

### 3.1a Cross-Cluster Synthesis (Large Tier Only)

**Only runs when large-tier dispatch was used (§ 1.4b).** Skip for small and medium tier.

After all cluster dispatches return, spawn one additional synthesis agent with `model: "opus"`. It receives:

- The cluster manifest from the scoping pass (§ 1.4b Step 1)
- All findings from every cluster's dispatch (pre-dedup)
- The full diff (`git diff <base>...HEAD`)

Its job is to find issues that span two or more clusters — things no single-cluster reviewer could catch:

- Cluster A introduces a field, type, or contract that cluster B consumes incorrectly
- Cluster A deprecates behavior that cluster B still relies on
- Clusters A and B independently mutate overlapping state (race, lost update)
- Security invariants spread across clusters no longer compose (e.g., cluster A adds input, cluster C trusts it)
- Refactor cluster removes a guard that feature cluster's new code needs

Output findings in the same format as domain subagents (the Output Format in § Subagent Prompt Template), with one addition — after `**Location**`:

```
**Spans clusters:** Cluster 2 (auth refactor), Cluster 4 (new login flow)
```

Cross-cluster findings then flow into § 3.2 Deduplicate alongside per-cluster findings.

### 3.2 Deduplicate

When multiple subagents flag the **same location** (same file and line range):
- Merge into a single finding
- Keep the **highest severity** across the duplicates
- Combine the reasoning from all domains that flagged it
- Credit all domains that identified the issue (e.g., "Flagged by: Security, Reliability")

Deduplication heuristics:
- Same file + overlapping line range (within 3 lines) = likely duplicate
- Same file + same code pattern but different principle = merge if the fix is identical, keep separate if fixes differ
- Different files + same pattern = not duplicates (each gets its own finding)

**Clean Code / Story Readability overlap:**
When the Clean Code subagent and Story Readability subagent flag the same location (e.g., both flag a SLAP violation or naming issue), merge them into a single finding. Keep the Story Readability framing (richer narrative context) and credit both domains: "Flagged by: Clean Code, Story Readability."

### Tool-AI Finding Merge

When static analysis tools produced findings (from TOOLING_CONTEXT):

**Overlapping findings** (tool and AI flag same file + overlapping line range within 3 lines):
- Merge into one finding
- Keep the AI finding's explanation (richer context)
- Add "**Confirmed by**: {tool_name} ({rule_id})" annotation
- This boosts confidence — machine and AI agree

**Tool-only findings** (tool found something no AI agent flagged):
- Include as its own finding with "[{tool_name}]" prefix in the principle name
- Map tool severity per `shared/review-common.md` § Tool Severity Mapping
- The `--min-severity` filter applies to tool findings too

**AI-only findings** (AI found something no tool flagged):
- No change — these appear as normal findings

### Cross-Model Finding Merge

When cross-model dispatch produced findings:

**Corroborated findings** (cross-model and one or more domain subagents flag the same file + overlapping line range within 3 lines):
- Merge into the existing domain finding
- **MUST add** `[Corroborated by: {model_name}]` annotation — this boosts confidence (two different models independently identified the same issue)
- Keep the domain subagent's explanation (richer, principle-grounded context)

**Cross-model-only findings** (cross-model found something no domain subagent flagged):
- Include as a new finding in a section: "**Additional findings from {model_name}**"
- Use the cross-model reviewer's severity rating
- These findings get their own subsection at the end of each severity group

**Domain-only findings** (domain subagents found something the cross-model reviewer did not flag):
- No change — present as normal. Domain analysis is the primary reviewer; cross-model is supplementary.

### 3.3 Apply Severity Filter

If `--min-severity` was specified, filter findings (not during analysis — subagents always perform full analysis). Remove any finding below the threshold. Severity order: P0 > P1 > P2 > P3 > P4.

**Timing — this is deferred when re-review runs.** Phase 3.7 (tech-lead re-review) is on by default; it receives ALL findings so it can upgrade a misclassified finding across the threshold, and the filter applies to its verdict afterward (§ 3.7.5). So apply this filter **now only under `--no-re-review`**; otherwise defer it until after Phase 3.7.

### 3.4 Prioritize Correctness

Correctness findings (actual bugs — wrong logic, off-by-one errors, null dereferences, race conditions) MUST be surfaced prominently. These are almost always P0 or P1. If a correctness agent returns a finding rated lower, consider bumping it.

### 3.5 Effort Modifiers

Adjust presentation priority (not severity) based on effort:
- **Quick wins** (one-line fixes, simple renames): bump up in the recommendations list
- **Risky changes** (no test coverage, complex refactors): note the risk, bump down in recommendations

### 3.6 Output Format

Present the synthesized report:

```
## Summary
1-3 sentences on overall code health. Mention the number of findings per severity level and any cross-model corroboration. Include a model line.

When Phase 3.7 ran (default):
"Models: [host model] + Codex + Antigravity + Tech Lead | Domains: 7 | Static: [tools] | Re-review: X rejected, Y severity changes, Z fixes rewritten, A added, B notes"

When Phase 3.7 was skipped (`--no-re-review`):
"Models: [host model] + Codex + Antigravity | Domains: 7 | Static: [tools]"

When Phase 3.7 failed:
"Models: [host model] + Codex + Antigravity | Domains: 7 | Static: [tools] | Tech Lead re-review: unavailable ([reason])"

## Violations Found

### P0: Critical
#### file.py
- [findings in the canonical format from § Subagent Prompt Template]

### P1: High
#### file.py
- [findings...]

### P2: Medium
#### file.py
- [findings...]

### P3: Low
#### file.py
- [findings...]

### P4: Optional
#### file.py
- [findings...]

## Recommendations
Prioritized list, most impactful first. Quick wins highlighted. Risky changes flagged.
```

Omit empty severity sections — if there are no P0 findings, skip the P0 section entirely.

This is the **mechanical** synthesis output. Phase 3.7 below takes it as input and produces the final user-facing report.

---

## Phase 3.7: Senior Tech Lead Re-review

After §3.6 produces the mechanical synthesis, dispatch **one** Agent (model: `"opus"`) acting as a senior tech lead. This is the final judgment pass before the report reaches the user. **Always on by default**; suppressed only with `--no-re-review`.

The tech lead's output **IS** the final report — it replaces §3.6's output. The mechanical synthesis is now the tech lead's input, not the user-facing deliverable.

### 3.7.1 Inputs

The tech lead subagent receives:

- The mechanically-synthesized findings from §3.1–§3.6 (post-dedup, post-severity-filter, post-correctness-prioritization)
- The full diff (`git diff <base>...HEAD` or equivalent for the mode)
- Full file contents (the same context the domain agents received)
- Static analysis findings (TOOLING_CONTEXT)
- Cluster manifest if large-tier (§1.4b)
- Whether `--min-severity` was applied (so the tech lead knows what's been filtered out)

### 3.7.2 Persona Prompt

```
You are a senior tech lead doing a final read of a code review report before it goes to the engineer.

Seven domain agents and a cross-model reviewer produced findings. The mechanical synthesis (deduplication, severity filtering, correctness prioritization) is done. Your job is to apply judgment over their work and produce the FINAL report the engineer will read.

You can:
1. Reject findings as false positives (move to "Rejected by Re-review" with reason)
2. Change severity (up or down) — note inline why
3. Rewrite the **Suggested Fix** and **After** code when a better fix exists
4. Add findings the agents missed (tag inline with [Added by Tech Lead])
5. Merge or split findings when dedup got it wrong
6. Flag analysis gaps and architectural concerns in "Tech Lead Notes"

Guardrails:
- MUST NOT rewrite for style/wording alone — only when judgment changes the verdict (severity, fix, accept/reject)
- MUST cite a reason for every change; no silent edits
- MUST NOT lower severity to manage report volume; same discipline as the domain agents
- MUST NOT add findings outside the resolved review scope
- If you agree with everything as-is, output the mechanical report unchanged with a one-line header note: "Tech Lead: no changes — all findings stand as reported."

## Mechanical Synthesis Output (Your Input)
<MECHANICAL_REPORT>

## Diff Context
<DIFF_CONTENT>

## Full File Contents
<FILES_CONTENT>

## Static Analysis Results
{TOOLING_CONTEXT}

## Cluster Manifest (large tier only)
{CLUSTER_MANIFEST_OR_OMIT}

## --min-severity Active?
{YES_OR_NO}

## Output Format

Produce the final markdown report, structured identically to §3.6 (Summary, severity-grouped findings, Recommendations), with these additions:

1. **Header line** gains a `Tech Lead` segment and a Re-review change-count summary:
   `Models: [host] + Codex + Antigravity + Tech Lead | Domains: 7 | Static: [tools] | Re-review: X rejected, Y severity changes, Z fixes rewritten, A added, B notes`

2. **Inline annotations** appear ONLY on findings you touched. Untouched findings have no annotation. Format:
   - Severity change: `[Tech Lead: P2→P0 — reason]`
   - Fix rewrite: `[Tech Lead: fix rewritten — reason]` (the **Suggested Fix** and **After** code reflect your rewrite)
   - Newly added finding: `[Added by Tech Lead]` (placed in the appropriate severity group)

3. **New section `## Rejected by Re-review`** (only if any rejections) — list each rejected finding with `file:line — [original principle/category] rejected: <reason>`. Place this section AFTER all severity groups and Recommendations, near the bottom.

4. **New section `## Tech Lead Notes`** (only if any) — analysis gaps, architectural concerns spanning findings, test-coverage observations, anything else open-ended. Place after `## Rejected by Re-review`.
```

### 3.7.3 Dispatch Mechanics

| Property | Value |
|---|---|
| Tool | `Agent` |
| Model | `"opus"` |
| Parallelism | Sequential — runs AFTER §3.6 completes; cannot parallelize with the domain agents because it operates on their output |
| Timeout | Standard agent timeout |

The mechanical synthesis output is passed as plain text in the prompt body. The diff, full files, and TOOLING_CONTEXT are passed the same way the domain agents received them.

### 3.7.4 Tier Interactions

| Tier | Re-review timing |
|---|---|
| Small (≤30 files) | Runs once after §3.6, on the full synthesized findings |
| Medium (file batching, 31–100 files) | Runs **once** after all batches are merged and synthesized — not per batch |
| Large (logical-cluster, >100 files or >5,000 LOC) | Runs **after** §3.1a cross-cluster synthesis completes |

The tech lead is always the **last** judgment pass before presentation.

### 3.7.5 Filter and Flag Interactions

- **`--min-severity`** — tech lead receives ALL findings regardless of the filter so it can upgrade a misclassified P3 → P0. The filter is applied **after** the tech lead, so the tech lead's verdict determines what the user actually sees. If the tech lead downgrades something below the threshold, it drops out silently.
- **Dual cross-model (Codex + Antigravity)** — both sets of findings flow through the same dedup → tech lead path.
- **`--no-re-review`** — Phase 3.7 is skipped entirely; the mechanical §3.6 output is presented directly to the user. Header line keeps the pre-enhancement format (no Tech Lead segment).

### 3.7.6 Failure Handling

If the tech lead subagent fails or times out, handle per § Error Handling — fall back to the mechanical §3.6 output unchanged and offer a retry.

### 3.7.7 Phase 4 (Fix Dispatch) Interaction

How tech-lead verdicts govern fixes — rewrites win, added findings are eligible, rejected findings are not — is defined in Phase 4 § Parallel Fix Strategy.

---

## Phase 4: Fix Dispatch

After presenting the report, ask:

> "Want me to fix some or all of these? I can start with the critical/high findings."

### Fix Prioritization

1. **Correctness fixes** (actual bugs) — always first
2. **Security fixes** (P0) — immediate
3. **Remaining P0/P1** — by file, grouped
4. **P2 and below** — only if requested

### Parallel Fix Strategy

- Group fixes by **file independence** — fixes in unrelated files can be dispatched in parallel
- Fixes in the **same file** MUST be applied sequentially to avoid conflicts
- Dispatch parallel fix agents for independent groups via the Agent tool
- Each fix agent receives the finding details (problem, **Suggested Fix**, before/after, location) and applies the change using the Edit tool
- When Phase 3.7 rewrote a fix, the **Suggested Fix and After block reflect the tech lead's rewrite** — apply that, not the original from the domain agent
- Fix agents **MUST verify** the before-code still matches (code may have shifted since analysis)
- Fix agents **MUST NOT expand scope** — apply exactly what was flagged, nothing more
- Rejected findings (those in `## Rejected by Re-review`) are NOT eligible for Fix Dispatch; findings added by the tech lead are eligible like any other

### Post-Fix Summary

After fixes are applied, present:
- List of files modified with a brief description of each change
- Number of findings addressed vs. total findings
- Any findings intentionally skipped (with reason — e.g., "requires architectural decision", "needs test coverage first")
- Suggest running the project's test suite or linter if applicable

---

## Priority Matrix

See `shared/review-common.md` § Severity Scale for the full P0–P4 definitions and fix-when guidance.

---

## Guardrails

Read `shared/review-common.md` § Cross-Skill Discipline for the base constraints (evidence, language-adaptive, specificity, no over-engineering, test-code DAMP, profile-first).

Additional codereview-specific guardrails:

1. **Rule of Three.** **MUST NOT flag** duplication or suggest extraction until the pattern has been proven with **3 or more occurrences**. Two similar blocks are not enough.

2. **Incidental similarity is not duplication.** Two code blocks that look alike but serve different purposes and evolve independently are not DRY violations. They are coincidentally similar.

---

## Error Handling

Read `shared/review-common.md` § Shared Error Handling for common errors (no changed files, base branch detection, PR/commit not found, file not found, no violations, too many files, tool errors).

Additional codereview-specific errors:

| Error | Action |
|---|---|
| One or more subagents fail | Continue with remaining results; note which domain was not analyzed in the report header. |
| All subagents fail | Report the failure: "Analysis failed — could not complete any domain review. Please try again." |
| All tools declined in gate | Review proceeds without tool findings — AI analysis only |
| One cross-model dispatch fails | Continue with remaining cross-model + 7 domain subagents; note unavailable model in report header. |
| Both cross-model dispatches fail | Continue with 7 domain subagents only; note "Cross-model unavailable" in report header. |
| Phase 3.7 tech lead subagent fails or times out | Fall back to the mechanical §3.6 output. Header line shows `Tech Lead re-review: unavailable ([reason])`. Offer retry: "Tech Lead re-review failed. Want to retry it? Or proceed with the synthesized findings as-is?" |
