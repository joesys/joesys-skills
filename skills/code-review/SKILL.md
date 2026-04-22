---
name: code-review
version: "1.1.0"
description: "Use when the user invokes /code-review to analyze code for correctness, quality, architecture, reliability, security, and performance violations with concrete before/after examples."
---

# Code Review Skill

Dispatch 7 parallel analysis subagents — each a domain expert (correctness, clean code, architecture, reliability, security, performance, story readability) — against the target code. Collect their findings, deduplicate overlapping violations, and synthesize a severity-grouped report with concrete before/after fixes in the target language.

## Invocation

Parse the user's `/code-review` arguments to determine mode and scope:

| Invocation | Mode | Scope |
|---|---|---|
| `/code-review` | Branch diff (default) | Current branch vs. fork point |
| `/code-review src/utils/` | Directory scan | All files recursively in specified directory |
| `/code-review --file src/main.py` | Single file | One specific file |
| `/code-review --pr 123` | PR review | Files changed in a GitHub PR |
| `/code-review --commit abc123` | Commit review | Files changed in a specific commit |
| `/code-review --min-severity P1` | Severity filter | Combinable with any mode |
| `/code-review --include-gemini` | Add Gemini | Adds Gemini as additional cross-model reviewer |

Arguments are combinable. Examples:
- `/code-review --pr 42 --min-severity P1` — review PR #42, only show P1+ findings
- `/code-review src/api/ --min-severity P2` — scan directory, show P2+ findings
- `/code-review --include-gemini` — add Gemini as a third model reviewer

If the invocation is ambiguous or the argument is unrecognizable, ask the user to clarify before proceeding.

---

## Phase 1: Scope Resolution

### 1.0 Load User Preferences

Read `shared/skill-context.md` for the full protocol. In brief:

1. Read `.claude/skill-context/preferences.md` — if missing, invoke `/preferences` (streamlined).
2. Read `.claude/skill-context/code-review.md` (if it exists) for review-specific preferences.

**How preferences shape this skill:**

| Preference | Effect on Code Review |
|---|---|
| Detail level: concise | Shorter findings, omit minor context, focus on top issues |
| Detail level: detailed | Include architectural context, explain why something is a problem |
| Assumed knowledge: beginner | Explain what the violation means, not just what to fix |
| Assumed knowledge: expert | Skip obvious explanations, focus on non-obvious implications |
| Review-specific: severity focus | Override `--min-severity` default (e.g., user always wants P0-P1 only) |
| Review-specific: priority domains | Reorder which domains get emphasis in the synthesis |

Pass relevant preferences to each domain subagent in Phase 2 — append as a `## User Preferences` section after the principle file content.

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
| Small | ≤ 30 files | Single-shot: one dispatch of 7 domain subagents + cross-model over all files (Phase 2 as-is) |
| Medium | 31–100 files | File-batching — see § 1.4a |
| Large | > 100 files **OR** > 5,000 LOC changed | Logical-cluster dispatch — see § 1.4b |

Thresholds are defaults. Users can override in `.claude/skill-context/code-review.md` with any of:
- `medium_tier_threshold_files` (default `30`)
- `large_tier_threshold_files` (default `100`)
- `large_tier_threshold_loc` (default `5000`)

### 1.4a Medium Tier — File Batching

Batch files into groups of roughly equal size (aim for 10-15 per batch). Keep related files in the same batch when possible (e.g., a module and its tests, a component and its styles). Each batch gets its own full dispatch (7 domain subagents + cross-model). Process batches sequentially:

1. Dispatch 7 parallel subagents + cross-model for batch 1, collect results
2. Dispatch for batch 2, collect results
3. Continue until all batches are processed
4. Synthesize all batch results together in Phase 3

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

Every changed file must appear in exactly one cluster. If a file is missing, rerun the scoping pass.

**Step 2 — Cluster dispatch.** For each cluster, dispatch a full review (7 domain subagents + cross-model) in parallel. Every cluster gets all 7 domains regardless of cluster type — the cluster tag is reader context and synthesis priority, not a reviewer filter.

All cluster dispatches fire in a single parallel batch. With N clusters, that's N × 8 tool calls in one response. No user gate between scoping and dispatch — the scoping pass returns, dispatch fires automatically.

Each cluster dispatch receives only its cluster's files (per Phase 1.3 content loading) plus the diff slice for those files.

**Step 3 — Continue to Phase 3.** Cross-cluster synthesis runs there — see § 3.1a.

### 1.5 Target Language Detection

Read `shared/review-common.md` § Target Language Detection.

### 1.6 Static Analysis Tooling

Read `shared/review-common.md` § Static Analysis Tooling — Detection Protocol (steps 1-3: detect, check availability, classify).

Then continue with code-review-specific steps:

4. **Build scoped commands**: For `available` tools, construct report-only commands targeting only the changed files using the tool's scope-to-files flag from the per-language profile.
5. **Safety Gate**: Present scoped tool commands to the user for approval (alongside any other live commands).
6. **Execute approved tools**: Run each tool. Respect timeouts (from `audit.yaml` if present, else adaptive: <10k LOC = 30s, 10-100k = 60s, >100k = 120s per tool).
7. **Build TOOLING_CONTEXT**: Assemble the slim version (findings only — no gap analysis, no build-integrated detection).

---

## Phase 2: Parallel Analysis

Dispatch **7 subagents simultaneously** via the Agent tool — all 7 in a single response (7 parallel Agent tool calls). Each subagent is a domain expert that analyzes the code against one principle set.

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

Each subagent receives a prompt structured as follows. Adjust `<DOMAIN>` and `<PRINCIPLE_FILE>` per agent:

```
You are a senior <DOMAIN> reviewer.

## Instructions
1. Read the principle file at: skills/code-review/<PRINCIPLE_FILE>
   (This file is relative to the project root — find and read it first.)
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
**Before**:
```<target_language>
// the problematic code
```
**After**:
```<target_language>
// the corrected code
```
**Why**: Explanation of why this matters and what could go wrong.
```

Always spawn subagents with `model: "opus"` to ensure high-quality analysis.

#### Story Readability Subagent Adjustments

The Story Readability subagent (domain 7) uses the same prompt template as the other 6, with two adjustments:

1. **Additional output:** In addition to the standard violation format, the Story Readability subagent outputs per-dimension scores (1–10) for each file reviewed. These scores follow the scoring protocol defined in `shared/story-readability.md`.
2. **Severity calibration:** Story readability findings naturally cluster at P2–P4. The subagent does not artificially inflate severity — narrative concerns are maintainability issues, not critical bugs. Typical mapping:
   - P2: Functions that actively mislead (e.g., a function named `validate` that also mutates state)
   - P3: Functions that don't read as stories but aren't misleading (e.g., missing cognitive chunking, mixed abstraction levels)
   - P4: Minor narrative polish (e.g., paragraph spacing, slight naming improvements)

### Subagent Output Format

Each subagent returns zero or more findings in this structure:

```
### [Principle Name] — [Specific Issue]
**Severity**: P0 | P1 | P2 | P3 | P4
**Location**: `file.ext:line_number`
**Problem**: Description
**Before**: (code block in target language)
**After**: (code block in target language)
**Why**: Explanation
```

Severity levels are defined in `shared/review-common.md` § Severity Scale (P0 critical through P4 optional).

### Cross-Model Dispatch

In addition to the 7 domain subagents, dispatch a cross-model review request in the **same parallel batch** — all 8 invocations (7 subagents + 1 cross-model CLI) launch simultaneously in a single response.

#### Dispatch Protocol

Read `shared/cross-model-dispatch.md` for host detection, platform-adaptive temp file creation, CLI command templates, and failure handling. Read `shared/model-defaults.md` for current model identifiers.

#### Cross-Model Prompt

Write the prompt to a temp file (use `mktemp` per `shared/cross-model-dispatch.md`):

```bash
PROMPT_FILE=$(mktemp /tmp/code-review-cross-XXXXXX.txt)
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
### [Category] — [Specific Issue]
**Severity**: P0 | P1 | P2 | P3 | P4
**Location**: `file.ext:line_number`
**Problem**: What is wrong.
**Before**: (code block in target language)
**After**: (code block in target language)
**Why**: What could go wrong.

If you find no issues, output: "No issues found."
PROMPT_EOF
```

Dispatch using the CLI command templates from `shared/cross-model-dispatch.md`, substituting `$PROMPT_FILE` for the temp file path and `"code-review-cross"` for the `--name` flag on Claude CLI. Use 600000ms timeout. Clean up: `rm -f "$PROMPT_FILE"` after completion.

The cross-model reviewer receives the **same full file content and diff** that the 7 domain subagents receive — not the reduced context used in quick-review. When files are batched (Phase 1.4), the cross-model dispatch is included in each batch alongside the 7 subagents.

#### --include-gemini

When `--include-gemini` is specified, launch an additional parallel dispatch to Gemini per `shared/cross-model-dispatch.md` § `--include-gemini` Flag. The Gemini prompt is identical to the cross-model prompt above, written to a separate temp file (use `mktemp`).

#### Failure Handling

If cross-model dispatch fails, the review continues with the 7 domain subagents only. Note in the report header: "Cross-model review unavailable; results are from domain subagents only."

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

Output findings in the same format as domain subagents (§ Subagent Output Format), with one addition — after `**Location**`:

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
- Add `[Corroborated by: {model_name}]` annotation — this boosts confidence (two different models independently identified the same issue)
- Keep the domain subagent's explanation (richer, principle-grounded context)

**Cross-model-only findings** (cross-model found something no domain subagent flagged):
- Include as a new finding in a section: "**Additional findings from {model_name}**"
- Use the cross-model reviewer's severity rating
- These findings get their own subsection at the end of each severity group

**Domain-only findings** (domain subagents found something the cross-model reviewer did not flag):
- No change — present as normal. Domain analysis is the primary reviewer; cross-model is supplementary.

### 3.3 Apply Severity Filter

If `--min-severity` was specified, filter findings **now** (not during analysis — subagents always perform full analysis). Remove any finding below the threshold. Severity order: P0 > P1 > P2 > P3 > P4.

### 3.4 Prioritize Correctness

Correctness findings (actual bugs — wrong logic, off-by-one errors, null dereferences, race conditions) should be surfaced prominently. These are almost always P0 or P1. If a correctness agent returns a finding rated lower, consider bumping it.

### 3.5 Effort Modifiers

Adjust presentation priority (not severity) based on effort:
- **Quick wins** (one-line fixes, simple renames): bump up in the recommendations list
- **Risky changes** (no test coverage, complex refactors): note the risk, bump down in recommendations

### 3.6 Output Format

Present the synthesized report:

```
## Summary
1-3 sentences on overall code health. Mention the number of findings per severity level and any cross-model corroboration. Include a model line:
"Models: [host model] + [cross-model] | Domains: 6 | Static: [tools]"

## Violations Found

### P0: Critical
#### file.py
- [findings with full details: problem, before/after, why]

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
- Fixes in the **same file** must be applied sequentially to avoid conflicts
- Dispatch parallel fix agents for independent groups via the Agent tool
- Each fix agent receives the finding details (problem, before/after, location) and applies the change using the Edit tool
- Fix agents must verify the before-code still matches (code may have shifted since analysis)

### Post-Fix Summary

After fixes are applied, present:
- List of files modified with a brief description of each change
- Number of findings addressed vs. total findings
- Any findings intentionally skipped (with reason — e.g., "requires architectural decision", "needs test coverage first")
- Suggest running the project's test suite or linter if applicable

---

## Priority Matrix

See `shared/review-common.md` § Severity Scale for the full P0-P4 definitions and fix-when guidance.

---

## Guardrails

Read `shared/review-common.md` § Shared Guardrails for the base constraints (no over-engineering, context matters, be specific, language-adaptive, profile first).

Additional code-review-specific guardrails:

1. **Rule of Three**: Do not flag duplication or suggest extraction until the pattern has been proven with **3 or more occurrences**. Two similar blocks are not enough.

2. **Incidental similarity is not duplication**: Two code blocks that look alike but serve different purposes and evolve independently are not DRY violations. They are coincidentally similar.

---

## Error Handling

Read `shared/review-common.md` § Shared Error Handling for common errors (no changed files, base branch detection, PR/commit not found, file not found, no violations, too many files, tool errors).

Additional code-review-specific errors:

| Error | Action |
|---|---|
| One or more subagents fail | Continue with remaining results; note which domain was not analyzed in the report header. |
| All subagents fail | Report the failure: "Analysis failed — could not complete any domain review. Please try again." |
| All tools declined in gate | Review proceeds without tool findings — AI analysis only |
| Cross-model dispatch fails | Continue with 7 domain subagents; note "Cross-model unavailable" in report header. |
| `--include-gemini` but Gemini CLI not found | Warn and continue without Gemini. |
