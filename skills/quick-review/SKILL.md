---
name: quick-review
version: "1.1.0"
description: "Use when the user invokes /quick-review for a fast bug-focused code review using parallel analysis (correctness + security, P0-P2 only). SKIP if the user wants a comprehensive review with style and architecture findings — that's /codereview."
---

# Quick Review Skill

Fast, bug-focused code review. Dispatches correctness and security subagents in parallel, with streamlined static analysis. Reports only P0–P2 findings — no style nits, no architecture suggestions. No cross-model dispatch — uses only the host model for speed.

For comprehensive 7-domain reviews, use `/codereview`.

## Out of Scope

This skill MUST NOT:
- Modify source code without explicit user approval. Quick-review is **report-only** — there is no fix dispatch phase. If the user wants fixes, they invoke `/codereview`.
- Apply fixes even when the user asks for them inline — hand the findings to `/codereview`, which owns fix dispatch.
- Report on code outside the resolved scope. If the diff/file/PR doesn't include a file, do not flag findings in it — even if you notice them while gathering context.
- Inflate severity to look thorough. P0 means actual bug or security hole. Style polish is P3/P4 (and this skill skips P3/P4 entirely).
- Downgrade real bugs to manage report volume. If correctness or security found something genuine, it stays at its true severity.
- Include P3 (polish) or P4 (style) findings. The skill reports P0–P2 only, even if subagents return lower-severity findings.
- Add a fix-dispatch phase. Quick-review is report-only.
- Load full files. Quick-review uses `git diff -U50` exclusively for context — full-file loading is reserved for `/codereview`.

## Invocation

Parse the user's `/quick-review` arguments to determine mode and scope:

| Invocation | Mode | Scope |
|---|---|---|
| `/quick-review` | Branch diff (default) | Current branch vs. fork point |
| `/quick-review src/utils/` | Directory scan | All files recursively in specified directory |
| `/quick-review --file src/main.py` | Single file | One specific file |
| `/quick-review --pr 123` | PR review | Files changed in a GitHub PR |
| `/quick-review --commit abc123` | Commit review | Files changed in a specific commit |

Arguments are combinable. Examples:
- `/quick-review --pr 42` — review PR #42

If the invocation is ambiguous or unrecognizable, ask the user to clarify before proceeding.

---

## Phase 1: Scope Resolution

### 1.0 Load User Preferences

Read `shared/skill-context.md` for the full protocol. In brief:

1. Read `.claude/skill-context/preferences.md` — if missing, invoke `/preferences` (streamlined).
2. Read `.claude/skill-context/codereview.md` (if it exists) — quick-review shares review preferences with codereview.

**How preferences shape this skill:**

| Preference | Effect on Quick Review |
|---|---|
| Detail level: concise | Even terser findings — just the bug and the fix |
| Assumed knowledge: beginner | Brief explanation of why the bug matters |
| Review-specific: priority domains | Which of correctness/security to emphasize in synthesis |

Pass relevant preferences to subagents in Phase 2.

### 1.1 Base Branch Detection

Read `shared/review-common.md` § Base Branch Detection.

### 1.2 File Gathering

Read `shared/review-common.md` § File Gathering.

### 1.3 Context Loading

Unlike `/codereview` (which loads entire files), quick-review loads only the diff with expanded context:

```bash
git diff -U50 <base>...HEAD
```

The `-U50` flag expands each hunk to include ~50 lines of surrounding context — enough for local scope, function signatures, variable declarations, and control flow, without loading entire files.

This is the primary time savings over the full codereview.

### 1.4 Target Language Detection

Read `shared/review-common.md` § Target Language Detection.

### 1.5 Static Analysis (Streamlined)

Read `shared/review-common.md` § Static Analysis Tooling — Detection Protocol (steps 1–3: detect, check availability, classify).

Then continue with quick-review-specific steps:

4. **Build scoped commands** — for `available` tools, construct report-only commands targeting only the changed files.
5. **Auto-run read-only tools** — linters, type checkers, and SAST tools are read-only — execute them without a safety gate. Tools marked with `⚠️ DANGER: auto-modifies` in per-language profiles are **MUST be skipped** (quick-review never runs auto-modifying tools).
6. **30-second timeout per tool** — hard cap. If a tool exceeds 30 seconds, kill it and continue.
7. **Build TOOLING_CONTEXT** — assemble the slim version (findings only — no gap analysis, no build-integrated detection). Same format as codereview's slim TOOLING_CONTEXT.

---

## Phase 2: Parallel Analysis

**MUST launch both subagents simultaneously in a single response** (2 parallel Agent tool calls). Static analysis (Track 1) already completed in Phase 1.5 — its results feed into the subagent prompts as TOOLING_CONTEXT. Sequential dispatch is a defect.

### Track 1: Static Analysis (already complete)

Static analysis ran in Phase 1.5 before this phase. Include TOOLING_CONTEXT in both subagent prompts. If any tools failed or were skipped, include only the findings that succeeded.

### Track 2: Host AI Subagents

**MUST dispatch 2 subagents simultaneously** via the Agent tool — both in a single response (2 parallel Agent tool calls).

| # | Domain | Principle File |
|---|---|---|
| 1 | Correctness | `skills/codereview/principles/correctness.md` |
| 2 | Security | `skills/codereview/principles/security.md` |

#### Subagent Prompt Template

Each subagent receives a prompt structured as follows. Adjust `<DOMAIN>` and `<PRINCIPLE_FILE>` per agent:

```
You are a senior <DOMAIN> reviewer performing a quick, bug-focused review.

## Instructions
1. Read the principle file at: <PRINCIPLE_FILE>
   (This file is relative to the project root — find and read it first.)
2. Analyze the diff and surrounding context below against every principle in that file.
3. For each violation found, output it in the structured format below.
4. **Only report P0, P1, or P2 severity findings.** Skip P3 (polish) and P4 (style) entirely.
5. All code examples MUST be in <TARGET_LANGUAGE>.
6. If you find no violations in your domain, output: "No <DOMAIN> violations found."

## Code Changes (Diff with Context)
<DIFF_U50>

The diff above was produced with `git diff -U50` and already includes ~50 lines of surrounding context per hunk.

## Static Analysis Results
{TOOLING_CONTEXT}

Use tool findings to corroborate or supplement your analysis. If a tool flagged
the same issue you found, note it in your finding. If a tool found something you missed
at P0-P2 severity, include it with "[{tool_name}]" prefix.

## Output Format
For each violation:

### [Principle Name] — [Specific Issue]
**Severity**: P0 | P1 | P2
**Location**: `file.ext:line_number`
**Problem**: Description of what is wrong and why it is a bug or vulnerability.
**Suggested Fix**: Brief description or short code snippet showing the fix.
**Why**: What could go wrong if this is not addressed.
```

**MUST spawn subagents** with `model: "opus"`.

Quick-review uses `Suggested Fix` instead of full before/after code blocks to prioritize speed and brevity. The full `/codereview` skill uses before/after blocks for detailed treatment.

---

## Phase 3: Synthesis

### 3.1 Collect Results

Gather findings from both tracks:
- Track 1: Static analysis tool output
- Track 2: Host AI subagents (correctness + security)

If any source failed, note which was unavailable and proceed with remaining results.

### 3.2 Deduplicate and Classify

When multiple sources flag the **same location** (same file, line range within ±5 lines, same category of issue), merge them into a single finding.

The ±5 line tolerance applies to all deduplication in quick-review, including tool-AI merges (overriding the ±3 default in `shared/tooling-registry.md`). "Same category" means both findings describe the same type of problem (e.g., both null-safety issues, both SQL injection, both unchecked error returns) — **MUST NOT merge** a correctness finding with an unrelated security finding that happens to be on nearby lines.

| Bucket | Criteria | Display |
|---|---|---|
| **Cross-domain** | Same issue flagged by both correctness and security subagents | `[Correctness + Security]` |
| **Tool-confirmed** | AI finding validated by a static analysis tool at the same location | `[Confirmed by: tool_name]` |
| **Single-source** | Found by only one source | Source attribution: `[Correctness]`, `[Security]`, `[eslint]`, etc. |

Merge rules:
- Keep the **most detailed explanation** across the duplicates
- Keep the **highest severity** if sources disagree
- Credit all sources that identified the issue

### Tool-Only Findings

When a static analysis tool finds something no AI flagged:
- Include as its own finding with `[tool_name]` prefix
- Map tool severity per `shared/review-common.md` § Tool Severity Mapping
- Discard tool findings below P2 (quick-review skips P3/P4)

### 3.3 Prioritize Correctness

Correctness findings (actual bugs — wrong logic, off-by-one errors, null dereferences, race conditions) are surfaced first within each severity level. If any finding — regardless of source (subagent or tool) — is rated P2 but describes an actual bug or security vulnerability, bump it to P1.

### 3.4 Output Format

Present the synthesized report:

```
## Quick Review Summary
X findings. Reviewed N files, M lines changed.
Model: [host model] | Domains: correctness, security | Static: [tool1, tool2, ...]
```

Then findings grouped by severity:

```
### P0: Critical
#### file.py:42
- **[Correctness + Security]** Null dereference — `user.profile` accessed without null check after `find_user()` which returns Optional
  > Suggested fix: add guard clause before access

#### file.py:87
- **[Security]** SQL injection — user input interpolated directly into query string
  > Suggested fix: use parameterized query

### P1: High
#### api/handler.go:156
- **[Confirmed by: golangci-lint]** Unchecked error return — `db.Close()` error silently discarded
  > Suggested fix: log or return the error

### P2: Medium
...
```

Omit empty severity sections. If there are zero findings across all severities, output:

> "No bugs or security issues found. Code looks solid."

**No P3/P4 sections.** No before/after code blocks (keeps output scannable — use `/codereview` for detailed treatment). Findings reference `file:line` for quick navigation. **No fix dispatch phase** — report only.

---

## Guardrails

Read `shared/review-common.md` § Cross-Skill Discipline for the base constraints (evidence, language-adaptive, specificity, no over-engineering, test-code DAMP, profile-first).

Additional quick-review-specific guardrails:

1. **P0–P2 only.** Never include P3 (polish) or P4 (style) findings in the output. Subagents are instructed to skip them; synthesis discards any that slip through.
2. **Diff-only context has limits.** Quick-review uses `-U50` diff context, not full files. Issues requiring broader file analysis (e.g., unused imports, unreachable code paths, architectural problems) may not be detected. Use `/codereview` for full-file analysis.

---

## Error Handling

Read `shared/review-common.md` § Shared Error Handling for common errors (no changed files, base branch detection, PR/commit not found, file not found, no violations, too many files, tool errors).

Additional quick-review-specific errors:

| Error | Action |
|---|---|
| One subagent fails | Continue with remaining subagent + static analysis; note which domain was not analyzed. |
| Both subagents fail | Report: "Analysis failed — could not complete any review. Please try again." |
