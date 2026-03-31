---
name: quick-review
description: "Use when the user invokes /quick-review for a fast bug-focused code review using cross-model parallel analysis (correctness + security, P0-P2 only)."
---

# Quick Review Skill

Fast, bug-focused code review. Dispatches correctness and security subagents alongside a cross-model reviewer (Codex↔Claude) in parallel, with streamlined static analysis. Reports only P0-P2 findings — no style nits, no architecture suggestions.

For comprehensive 6-domain reviews, use `/code-review` instead.

## Invocation

Parse the user's `/quick-review` arguments to determine mode and scope:

| Invocation | Mode | Scope |
|---|---|---|
| `/quick-review` | Branch diff (default) | Current branch vs. fork point |
| `/quick-review src/utils/` | Directory scan | All files recursively in specified directory |
| `/quick-review --file src/main.py` | Single file | One specific file |
| `/quick-review --pr 123` | PR review | Files changed in a GitHub PR |
| `/quick-review --commit abc123` | Commit review | Files changed in a specific commit |
| `/quick-review --include-gemini` | Add Gemini | Combinable with any mode |

Arguments are combinable. Examples:
- `/quick-review --pr 42` — review PR #42
- `/quick-review --include-gemini` — add Gemini as a third reviewer
- `/quick-review --file src/main.py --include-gemini` — single file, three models

The `--include-gemini` flag affects Phase 2 dispatch only — Phase 1 scope resolution is identical regardless of this flag.

If the invocation is ambiguous or the argument is unrecognizable, ask the user to clarify before proceeding.

---

## Phase 1: Scope Resolution

### 1.1 Base Branch Detection

Determine where the current branch diverged. Check candidates in order:

1. The upstream tracking branch (e.g., `origin/feature-x` tracks `origin/main`)
2. `main`
3. `master`

If none exist or the result is ambiguous, ask the user: "Which branch should I compare against?"

Compute the fork point:

```bash
git merge-base <base-branch> HEAD
```

### 1.2 File Gathering

Gather the list of files to review based on the resolved mode:

| Mode | Command |
|---|---|
| Branch diff | `git diff --name-only <base>...HEAD` |
| Directory scan | All files recursively in the specified directory, respecting `.gitignore` |
| Single file | The specified file path |
| PR review | `gh pr diff <number> --name-only` |
| Commit review | `git diff --name-only <commit>^..<commit>` |

### 1.3 Context Loading

Unlike the full code-review skill (which loads entire files), quick-review loads only the diff with expanded context:

```bash
git diff -U50 <base>...HEAD
```

The `-U50` flag expands each hunk to include ~50 lines of surrounding context — enough for local scope, function signatures, variable declarations, and control flow, without loading entire files.

This is the primary time savings over the full code-review. Both host AI subagents and the cross-model dispatch receive the same context.

### 1.4 Target Language Detection

Infer the primary language from file extensions:

| Extension | Language |
|---|---|
| `.ts`, `.tsx` | TypeScript |
| `.js`, `.jsx` | JavaScript |
| `.py` | Python |
| `.rs` | Rust |
| `.go` | Go |
| `.java` | Java |
| `.cs` | C# |
| `.rb` | Ruby |
| `.php` | PHP |
| `.swift` | Swift |
| `.kt` | Kotlin |
| `.cpp`, `.cc`, `.h` | C++ |

If the changeset is polyglot, note all languages and instruct subagents to use the correct language per file.

### 1.5 Static Analysis (Streamlined)

Read the shared tooling registry and per-language profiles:
- `shared/tooling-registry.md` — for detection protocol
- `shared/tooling/{language}.md` — for each detected language
- `shared/tooling/general.md` — for cross-language tools

Follow a streamlined detection flow:

1. **Detect config files**: Glob for each tool's detection markers.
2. **Check availability**: Run `which`/`where` for each tool's binary.
3. **Classify**: Mark each tool as `available`, `configured-but-unavailable`, or `absent`.
4. **Build scoped commands**: For `available` tools, construct report-only commands targeting only the changed files.
5. **Auto-run read-only tools**: Linters, type checkers, and SAST tools are read-only — execute them without a safety gate. Tools marked with `⚠️ DANGER: auto-modifies` in per-language profiles are **skipped** (quick-review never runs auto-modifying tools).
6. **30-second timeout per tool**: Hard cap. If a tool exceeds 30 seconds, kill it and continue.
7. **Build TOOLING_CONTEXT**: Assemble the slim version (findings only — no gap analysis, no build-integrated detection). Same format as code-review's slim TOOLING_CONTEXT.

For large output (>50 findings from a single tool): summarize as "{tool} reported N violations: X errors, Y warnings", include top 3 most severe, tell user: "Run `{exact command}` for full results."

If a tool fails: report error, skip tool, continue.

---

## Phase 2: Parallel Analysis

Launch **all three tracks simultaneously** — static analysis execution (from Phase 1.5), host AI subagents, and cross-model dispatch all begin at the same time. Use parallel tool invocations (multiple Agent and Bash calls in a single response).

### Track 1: Static Analysis

Static analysis was executed in Phase 1.5 (sequentially, before Phase 2 begins). Include TOOLING_CONTEXT in both Track 2 subagent prompts and Track 3 cross-model prompts. If any tools failed or were skipped in Phase 1.5, include only the findings that succeeded.

### Track 2: Host AI Subagents

Dispatch **2 subagents simultaneously** via the Agent tool — both in a single response (2 parallel Agent tool calls).

| # | Domain | Principle File |
|---|---|---|
| 1 | Correctness | `skills/code-review/principles/correctness.md` |
| 2 | Security | `skills/code-review/principles/security.md` |

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

Always spawn subagents with `model: "opus"`.

Quick-review uses `Suggested Fix` instead of full before/after code blocks to prioritize speed and brevity. The full `/code-review` skill uses before/after blocks for detailed treatment.

### Track 3: Cross-Model Dispatch

Dispatch a review request to a different AI model via CLI, running in parallel with Track 2.

#### Host Detection

Determine which cross-model CLI to dispatch based on who you are:

| You Are | Dispatch To | Command |
|---|---|---|
| Claude | Codex | `codex exec` |
| Codex | Claude | `claude -p` |
| Gemini | Claude | `claude -p` |
| Unknown | Both Codex + Claude | Two parallel dispatches |

#### Prompt Construction

Write the prompt to a temporary file and pipe via stdin to avoid shell metacharacter issues:

```bash
cat > /tmp/quick-review-cross-prompt.txt << 'PROMPT_EOF'
You are a bug-focused code reviewer. Your task is to find correctness bugs, security vulnerabilities, and reliability issues in the following code changes.

## Rules
- Only report P0 (critical), P1 (high), or P2 (medium) severity issues.
- No style nits. No architecture suggestions. No formatting complaints.
- P0: Security holes, data loss, actual bugs that will cause failures
- P1: Bugs waiting to happen, logic errors, missing error handling
- P2: Maintainability problems that mask bugs, resource leaks, race conditions

## Code Changes (Diff with Context)
<DIFF_U50>

The diff above was produced with `git diff -U50` and already includes ~50 lines of surrounding context per hunk.

## Static Analysis Results
{TOOLING_CONTEXT}

## Output Format
For each finding:
### [Category] — [Specific Issue]
**Severity**: P0 | P1 | P2
**Location**: `file.ext:line_number`
**Problem**: What is wrong.
**Suggested Fix**: How to fix it.
**Why**: What could go wrong.

If you find no issues, output: "No bugs or security issues found."
PROMPT_EOF
```

Then dispatch based on host detection:

**If dispatching to Codex:**
```bash
cat /tmp/quick-review-cross-prompt.txt | codex exec --model gpt-5.4 \
  -c model_reasoning_effort="xhigh" --sandbox read-only \
  --skip-git-repo-check 2>/dev/null
```

**If dispatching to Claude:**
```bash
cat /tmp/quick-review-cross-prompt.txt | claude --model opus --effort high \
  --permission-mode plan --name "quick-review-cross" -p "" 2>/dev/null
```

Use 600000ms timeout on the Bash tool for both.

Clean up: `rm -f /tmp/quick-review-cross-prompt.txt` after the dispatch completes.

#### --include-gemini

When `--include-gemini` is specified, launch an additional parallel dispatch to Gemini alongside Track 3:

```bash
cat /tmp/quick-review-gemini-prompt.txt | gemini -m gemini-3.1-pro-preview \
  --approval-mode plan -p "" 2>/dev/null
```

The Gemini prompt is identical to the cross-model prompt. Write it to a separate temp file (`/tmp/quick-review-gemini-prompt.txt`). Clean up after completion.

#### Permissions

All cross-model dispatches use read-only / plan mode. They only need to read the diff and think.

#### Failure Handling

If a cross-model dispatch fails or times out, the review continues with host-only findings. Append a note to the final report:

> "Cross-model review unavailable ([model] [reason]); results are from [host model] only."

If `--include-gemini` was specified and only Gemini fails, the primary cross-model results are still included.

---

## Phase 3: Synthesis

### 3.1 Collect Results

Gather findings from all tracks:
- Track 1: Static analysis tool output
- Track 2: Host AI subagents (correctness + security)
- Track 3: Cross-model dispatch (and Gemini, if `--include-gemini`)

If any track failed, note which source was unavailable and proceed with remaining results.

### 3.2 Deduplicate and Classify

When multiple sources flag the **same location** (same file, line range within ±5 lines, same category of issue), merge them into a single finding and classify into one of three buckets.

The ±5 line tolerance is wider than code-review's ±3 because cross-model reviewers working from diff-only context may report slightly different line numbers for the same issue. "Same category" means both findings describe the same type of problem (e.g., both are null-safety issues, both are SQL injection, both are unchecked error returns) — do not merge a correctness finding with an unrelated security finding that happens to be on nearby lines.

| Bucket | Criteria | Display |
|---|---|---|
| **Corroborated** | Same issue flagged by 2+ AI sources (host + cross-model, or host + Gemini, etc.) | `[Corroborated: source1 + source2]` |
| **Tool-confirmed** | AI finding validated by a static analysis tool at the same location | `[Confirmed by: tool_name]` |
| **Single-source** | Found by only one source | Source attribution: `[Claude]`, `[Codex]`, `[Gemini]`, `[eslint]`, etc. |

A finding can be both corroborated AND tool-confirmed (e.g., Claude + Codex + mypy all flag the same null dereference). In this case, show both annotations.

Merge rules:
- Keep the **most detailed explanation** across the duplicates (usually the host AI's)
- Keep the **highest severity** if sources disagree
- Credit all sources that identified the issue
- If fixes differ between sources, present both with attribution

### Tool-Only Findings

When a static analysis tool finds something no AI flagged:
- Include as its own finding with `[tool_name]` prefix
- Map tool severity: error → P1 (P0 if security-related), warning → P2
- Discard tool findings below P2 (quick-review skips P3/P4)

### 3.3 Prioritize Correctness

Correctness findings (actual bugs — wrong logic, off-by-one errors, null dereferences, race conditions) are surfaced first within each severity level. If any finding — regardless of source (host AI, cross-model, or tool) — is rated P2 but describes an actual bug or security vulnerability, bump it to P1.

### 3.4 Output Format

Present the synthesized report:

```
## Quick Review Summary
X findings (Y corroborated across models). Reviewed N files, M lines changed.
Models: [host model] + [cross-model] | Static: [tool1, tool2, ...]
```

If `--include-gemini` was used:
```
Models: [host model] + [cross-model] + Gemini | Static: [tool1, tool2, ...]
```

If cross-model was unavailable:
```
Models: [host model] only (cross-model unavailable) | Static: [tool1, tool2, ...]
```

Then findings grouped by severity:

```
### P0: Critical
#### file.py:42
- **[Corroborated: Claude + Codex]** Null dereference — `user.profile` accessed without null check after `find_user()` which returns Optional
  > Suggested fix: add guard clause before access

#### file.py:87
- **[Claude]** SQL injection — user input interpolated directly into query string
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

**No P3/P4 sections.** No before/after code blocks (keeps output scannable — use `/code-review` for detailed treatment). Findings reference `file:line` for quick navigation. No fix dispatch phase — report only.

---

## Guardrails

1. **P0-P2 only**: Never include P3 (polish) or P4 (style) findings in the output. Subagents are instructed to skip them; synthesis discards any that slip through.
2. **No over-engineering suggestions**: Do not suggest abstractions, patterns, or architectural changes. This is a bug finder, not a design reviewer.
3. **Be specific**: Every finding must include exact file path, line number, and a concrete suggested fix. Vague advice like "consider adding validation" is not acceptable.
4. **Language-adaptive**: Code examples in suggested fixes must be in the target language.
5. **Context matters**: Test code follows different standards — don't flag test-specific patterns (e.g., repeated setup, hardcoded values) as bugs.
6. **Corroboration is signal, not proof**: Two models agreeing increases confidence, but don't present corroborated findings as definitively correct. The human reviewer makes the final call.
7. **Diff-only context has limits**: Quick-review uses `-U50` diff context, not full files. Issues requiring broader file analysis (e.g., unused imports, unreachable code paths, architectural problems) may not be detected. Use `/code-review` for full-file analysis.

---

## Error Handling

| Error | Action |
|---|---|
| No changed files found | "No changes detected on this branch vs. `<base>`. Try specifying a file or directory." |
| Base branch detection fails | Ask: "Which branch should I compare against?" |
| PR number not found | "PR #N not found. Check the number and try again." |
| Commit hash not found | "Commit `<hash>` not found. Check the hash and try again." |
| File not found (single file mode) | "File `<path>` not found. Check the path and try again." |
| One or both host subagents fail | Continue with remaining results; note which domain was not analyzed. |
| Both host subagents fail | Fall back to cross-model results only. If cross-model also failed, report: "Analysis failed — could not complete any review. Please try again." |
| Cross-model dispatch fails | Continue with host-only results; note in summary header. |
| All sources fail | Report: "Analysis failed — no reviewers completed successfully. Please try again." |
| No violations found | "No bugs or security issues found. Code looks solid." |
| Too many files (>100) | Warn about scope size, suggest narrowing with `--file` or a subdirectory, proceed if confirmed. |
| Tool binary not found | Skip tool, continue with remaining tools. |
| Tool crashes or times out | Report error, skip tool, continue. |
| `--include-gemini` but Gemini CLI not installed | Warn: "Gemini CLI not found. Proceeding without Gemini." Continue with host + primary cross-model. |
