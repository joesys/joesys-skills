---
name: quick-review
description: "Use when the user invokes /quick-review for a fast bug-focused code review using parallel analysis (correctness + security, P0-P1 only). SKIP if the user wants a comprehensive review with style and architecture findings — that's /codereview."
---

# Quick Review Skill

Fast, bug-focused code review. A correctness reviewer and a security reviewer run in parallel, with streamlined static analysis. Only the host model is used, for speed. For a full 7-domain review, use `/codereview`.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md` (resolve against the plugin root — two levels above this SKILL.md — never the project's working directory).

## Out of Scope

This skill MUST NOT:
- Modify source code unless the user explicitly asks for fixes. Quick-review is **report-only** by default. When the user explicitly asks for fixes, fix only the flagged findings they asked for. Follow the fix rules in `skills/codereview/SKILL.md` Phase 4 § Parallel Fix Strategy (resolve against the plugin root, not the project). In short: check that the before-code still matches, and apply exactly what was flagged, nothing more. Then show what changed in each file.
- Report on code outside the resolved scope, even if you notice it while gathering context.
- Report P2 (maintainability), P3 (polish), or P4 (style) findings. This skill reports P0–P1 only, even if subagents or tools return lower-severity findings.

## Invocation

| Invocation | Mode | Scope |
|---|---|---|
| `/quick-review` | Branch diff (default) | Current branch vs. fork point |
| `/quick-review src/utils/` | Directory scan | All files recursively in specified directory |
| `/quick-review --file src/main.py` | Single file | One specific file |
| `/quick-review --pr 123` | PR review | Files changed in a GitHub PR |
| `/quick-review --commit abc123` | Commit review | Files changed in a specific commit |

If the invocation is ambiguous, ask the user to clarify.

---

## Phase 1: Scope Resolution

### 1.0 Load User Preferences

Read `shared/skill-context.md` for the full protocol (resolve `shared/...` against the plugin root — two levels above this SKILL.md — never the project's working directory). Read `.claude/skill-context/preferences.md` and `.claude/skill-context/codereview.md` if present (quick-review shares review preferences with codereview); otherwise use defaults. Pass relevant preferences to the subagents in Phase 2.

### 1.1 Base Branch, Files, and Language

Read `shared/review-common.md` § Base Branch Detection, § File Gathering, and § Target Language Detection.

### 1.2 Context Loading

Diff-based modes start from the diff with 50 lines of context, not full files:

- Branch: `git diff -U50 <base>...HEAD`
- `--commit <hash>`: `git diff -U50 <commit>^..<commit>`
- `--pr <n>`: `gh pr diff` has no context-width flag, so fetch and diff locally: `git fetch origin pull/<n>/head && git diff -U50 $(git merge-base HEAD FETCH_HEAD)...FETCH_HEAD`

Open more of a file only to confirm or reject a specific finding. Do not tell subagents the diff has 50-line context if the command did not provide it. Directory-scan and single-file modes have no diff: read the specified files directly.

### 1.3 Static Analysis (Streamlined)

Read `shared/review-common.md` § Static Analysis Tooling — Detection Protocol (steps 1–3: detect, check availability, classify). Then:

- Run `available` read-only tools (linters, type checkers, SAST) on the changed files only, without a safety gate.
- Skip every tool marked `⚠️ DANGER: auto-modifies`. Quick-review never runs auto-modifying tools.
- Cap each tool at 30 seconds. Kill it after that and continue.
- Build the slim TOOLING_CONTEXT (findings only, same format as codereview's slim version). Include only the tools that succeeded.

---

## Phase 2: Parallel Analysis

Run the two reviews in parallel as subagents, one per domain:

| # | Domain | Principle File |
|---|---|---|
| 1 | Correctness | `skills/codereview/principles/correctness.md` |
| 2 | Security | `skills/codereview/principles/security.md` |

For same-platform subagents, do not pass a model or reasoning-effort override. Let every subagent inherit the parent model and reasoning effort unless the user explicitly asks for an override.

### Subagent Prompt Template

Before dispatch, substitute every `<ANGLE_BRACKET>` placeholder. In particular, replace `<PRINCIPLE_PATH>` with the **absolute path** to the principle file, resolved against the plugin root (two levels above this SKILL.md — the paths point into the sibling `codereview` skill) — never against the project's working directory. Subagents start in the project cwd and cannot find plugin files by relative path.

```
You are a senior <DOMAIN> reviewer performing a quick, bug-focused review.

## Instructions
1. Read the principle file at: <PRINCIPLE_PATH>. Use it as your lens. Report only problems that matter in this change.
2. Report only P0 or P1 findings: real bugs and security holes.
3. Code examples must be in <TARGET_LANGUAGE>.
4. If you find nothing, output: "No <DOMAIN> violations found."
5. Write for humans: the reader may speak English as a second language. Use short sentences, everyday words, and explain jargon on first use. State the point first, then the detail. Simplify the language, never the facts — paths, line numbers, and claims stay exact.

## User Preferences
<USER_PREFERENCES_OR_"None">

## Code Changes (Diff with Context)
<DIFF_U50>

## Static Analysis Results
{TOOLING_CONTEXT}

If a tool flagged the same issue you found, note it in your finding. If a tool
found a P0-P1 issue you missed, include it with a "[{tool_name}]" prefix.

## Output Format
For each violation:

### [Principle Name] — [Specific Issue]
**Severity**: P0 | P1
**Location**: `file.ext:line_number`
**Problem**: What is wrong and why it is a bug or vulnerability.
**Suggested Fix**: Brief description or short code snippet.
**Why**: What could go wrong if this is not addressed.
```

---

## Phase 3: Synthesis

### 3.1 Merge and Attribute

Merge findings only when they describe the same problem at the same place. Do not merge a correctness finding with an unrelated security finding on nearby lines. When merging, keep the most detailed explanation and the highest severity, and credit every source.

| Bucket | Criteria | Display |
|---|---|---|
| **Cross-domain** | Same issue flagged by both subagents | `[Correctness + Security]` |
| **Tool-confirmed** | AI finding confirmed by a static analysis tool | `[Confirmed by: tool_name]` |
| **Single-source** | Found by one source only | `[Correctness]`, `[Security]`, `[eslint]`, etc. |

A tool finding that no subagent flagged becomes its own finding with a `[tool_name]` prefix. Map its severity per `shared/review-common.md` § Tool Severity Mapping, and drop it if it is below P1.

Within each severity level, list correctness findings (wrong logic, off-by-one, null dereference, race conditions) first.

### 3.2 Output Format

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

### P1: High
#### api/handler.go:156
- **[Confirmed by: golangci-lint]** Unchecked error return — `db.Close()` error silently discarded
  > Suggested fix: log or return the error
```

Show only P0 and P1 sections, and omit empty ones. Use no before/after code blocks; `/codereview` gives the detailed treatment. If there are no findings, say no bugs or security issues were found.

---

## Guardrails

Read `shared/review-common.md` § Cross-Skill Discipline and § Severity Discipline.

**Diff-only context has limits.** The `-U50` diff can miss problems that need the whole file, such as unused imports, unreachable code paths, or architectural problems. Say so when it matters, and point to `/codereview` for full-file analysis.

---

## Error Handling

Read `shared/review-common.md` § Shared Error Handling for common errors.

If one subagent fails, continue with the other subagent and the static analysis, and name the domain that was not analyzed. If both fail, report that the review could not run and suggest trying again.
