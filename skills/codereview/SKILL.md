---
name: codereview
description: "Use when the user invokes /codereview to analyze code for correctness, quality, architecture, reliability, security, and performance violations with concrete before/after examples."
---

# Code Review Skill

Run seven domain reviewers in parallel — correctness, clean code, architecture, reliability, security, performance, and story readability — plus two cross-model reviewers. Merge their findings, have a senior tech lead check the result, and deliver a severity-grouped report with concrete before/after fixes in the reviewed code's language.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md` (resolve against the plugin root — two levels above this SKILL.md — never the project's working directory).

## Out of Scope

This skill MUST NOT:
- Modify source code without explicit user approval after the report. Fixes happen only in Phase 4, after the user says yes or names specific findings.
- Fix more than was flagged. When the user approves fixes, fix exactly the reported findings. Do not add "while I'm in this file" cleanup, renames, or other improvements.
- Report on code outside the resolved scope, even if you notice problems while gathering context.

## Invocation

| Invocation | Mode | Scope |
|---|---|---|
| `/codereview` | Branch diff (default) | Current branch vs. fork point |
| `/codereview src/utils/` | Directory scan | All files recursively in specified directory |
| `/codereview --file src/main.py` | Single file | One specific file |
| `/codereview --pr 123` | PR review | Files changed in a GitHub PR |
| `/codereview --commit abc123` | Commit review | Files changed in a specific commit |
| `/codereview --min-severity P1` | Severity filter | Combinable with any mode |
| `/codereview --no-re-review` | Suppress re-review | Skip Phase 3.7 — present mechanical synthesis output directly |

Arguments combine, for example `/codereview --pr 42 --min-severity P1`. If the invocation is ambiguous, ask the user to clarify.

---

## Phase 1: Scope Resolution

### 1.0 Load User Preferences

Read `shared/skill-context.md` for the protocol (resolve `shared/...` against the plugin root — two levels above this SKILL.md — never the project's working directory). Read `.claude/skill-context/preferences.md` and `.claude/skill-context/codereview.md` if they exist; otherwise use defaults. Never interview the user about preferences.

Pass the preferences to each subagent as a `## User Preferences` section. Use them to shape detail level and explanation depth in the report. A severity focus in `codereview.md` sets the default `--min-severity`.

### 1.1 Base Branch, Files, and Language

Read `shared/review-common.md` § Base Branch Detection, § File Gathering, and § Target Language Detection.

### 1.2 Content Loading

Load the **full content** of every changed file, not just the diff hunks. Reviewers need the surrounding code to judge structure and control flow. Also capture the **diff** (`git diff <base>...HEAD` or the equivalent for the mode) so reviewers can focus on what changed.

### 1.3 Static Analysis Tooling

Read `shared/review-common.md` § Static Analysis Tooling — Detection Protocol (steps 1–3: detect, check availability, classify). Then:

1. For `available` tools, build report-only commands scoped to the changed files, using each profile's scope-to-files flag.
2. **Safety Gate** — show the commands to the user for approval, with any other live commands. Run nothing the user did not approve.
3. Run the approved tools. Timeouts, large output, and failures follow `shared/tooling-registry.md` § 4.
4. Build the slim TOOLING_CONTEXT (`shared/tooling-registry.md` § 5).

### 1.4 Splitting Large Changes

Every changed file gets all seven domains. If the change is too big for one reviewer to hold, split it into groups of related files and review each group fully.

Count changed lines as insertions plus deletions from `git diff --shortstat <base>...HEAD`.

- At most `medium_tier_threshold_files` files (default `30`) and at most `large_tier_threshold_loc` changed lines (default `5000`): review as one group.
- More files than that, but at most `large_tier_threshold_files` files (default `100`) and still within the line limit: group related files yourself (a module with its tests, a component with its styles).
- More than `large_tier_threshold_files` files, or more than `large_tier_threshold_loc` changed lines: first run one **scoping agent** on metadata only — `git diff --stat`, `git log --oneline`, and commit bodies (`git log --format='%h %s%n%b'`) for `<base>...HEAD`. The line limit wins: a few files with a huge diff (generated code, lockfiles) still need the scoping agent.

Users can override the three keys in `.claude/skill-context/codereview.md`.

When you split, write the groups as a cluster manifest. Every changed file must appear in exactly one cluster; if one is missing, rebuild the manifest. Tag each cluster with one type: `feature`, `bugfix`, `refactor`, `cross-cutting` (renames and mechanical edits), `test-only`, or `config/infra`. The tag is context for the reviewers and the synthesis, not a filter: every cluster still gets all seven domains.

```
## Cluster N: <short name>
**Type:** <cluster-type>
**Intent:** <one sentence on what this cluster accomplishes>
**Files:**
- path/to/file1
- path/to/file2
```

Each cluster's reviewers receive only that cluster's files and its slice of the diff. Run cluster reviews in parallel as far as the host allows. Do not stop for the user between scoping and dispatch.

---

## Phase 2: Parallel Analysis

Run the seven domain reviews in parallel as subagents via the Agent tool, together with the two cross-model reviews below.

For same-platform subagents, do not pass a model or reasoning-effort override. Let every subagent inherit the parent model and reasoning effort unless the user explicitly asks for an override.

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

Substitute every placeholder before dispatch. `<PRINCIPLE_PATH>` must be the **absolute path** to the roster file: resolve `principles/...` against this skill's own directory and `shared/...` against the plugin root (two levels above this SKILL.md). Subagents start in the project directory and cannot find plugin files by relative path.

Replace `<REVIEW_RULES>` with the Review Rules block from `shared/review-common.md` § Cross-Skill Discipline, pasted word for word (the block's contents, without the code fence). Subagents cannot open that file. The same placeholder appears in the cross-model and tech lead prompts below.

```
You are a senior <DOMAIN> reviewer.

## Instructions
1. Read the principle file at: <PRINCIPLE_PATH>. Use it as your lens. Report only problems that matter in this change.
2. Report each finding in the Output Format below.
3. If you find no problems in your domain, output: "No <DOMAIN> violations found."

<REVIEW_RULES>

## User Preferences
<USER_PREFERENCES_OR_"None">

## Code Under Review
<FILES_CONTENT>

## Diff Context
<DIFF_CONTENT>

## Static Analysis Results
{TOOLING_CONTEXT}

If a tool flagged the same issue you found, say so in your finding. If a tool
found something in your domain that you missed and it matters, include it with a
"[{tool_name}]" prefix.

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

#### Story Readability Severity Calibration

Story readability findings usually fall at P2–P4. Narrative problems are maintainability issues, not critical bugs. Add this mapping to the Story Readability subagent's prompt:
- P2: Functions that actively mislead (e.g., a function named `validate` that also mutates state)
- P3: Functions that don't read as stories but aren't misleading (e.g., missing cognitive chunking, mixed abstraction levels)
- P4: Minor narrative polish (e.g., paragraph spacing, slight naming improvements)

### Cross-Model Dispatch

Also send the review to **Codex and Antigravity**, in the same parallel batch as the domain subagents. Read `shared/cross-model-dispatch.md` for host detection, temp files, CLI command templates, and failure handling. Read `shared/model-defaults.md` for model identifiers.

Both cross-model reviewers get the same full file content and diff as the domain subagents. When the change is split into clusters, each cluster gets its own cross-model pair.

Write the prompt to two temp files with `mktemp` (one per CLI), dispatch both in parallel with a 600000 ms timeout, and delete the files afterwards:

```bash
PROMPT_FILE=$(mktemp /tmp/codereview-cross-XXXXXX.txt)
cat > "$PROMPT_FILE" << 'PROMPT_EOF'
You are a comprehensive code reviewer. Analyze the following code changes for bugs, security vulnerabilities, performance issues, reliability problems, architectural concerns, and code quality.

Use this severity scale: P0 (critical), P1 (high), P2 (medium), P3 (low), P4 (optional).
Every finding must reference a specific location.

<REVIEW_RULES>

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

Substitute `<FINDING_FORMAT>` with the Output Format from § Subagent Prompt Template (`### [Principle Name] — [Specific Issue]` through `**Why**`), using `[Category]` in place of `[Principle Name]`.

---

## Phase 3: Synthesis

### 3.1 Collect Results

Gather findings from every domain subagent and cross-model reviewer. If a source failed, continue with the rest and note the missing source in the report header.

### 3.2 Cross-Cluster Synthesis

Run this only when the change was split into more than one cluster. Spawn one synthesis agent with the cluster manifest, all findings from every cluster (before merging), and the full diff (`git diff <base>...HEAD`). Its job is to find issues that span clusters — things no single-cluster reviewer could see:

- Cluster A introduces a field, type, or contract that cluster B uses incorrectly
- Cluster A deprecates behavior that cluster B still relies on
- Clusters A and B change overlapping state (race, lost update)
- Security assumptions no longer compose (cluster A adds input, cluster C trusts it)
- A refactor cluster removes a guard that a feature cluster's new code needs

It reports in the same finding format, with one extra line after `**Location**`:

```
**Spans clusters:** Cluster 2 (auth refactor), Cluster 4 (new login flow)
```

These findings join the merge step below.

### 3.3 Merge Findings

Merge findings that share a root cause and fix. Keep the highest severity, combine the reasoning, and credit every source ("Flagged by: Security, Reliability"). Keep findings separate when their fixes differ. The same pattern in different files gives separate findings.

- **Clean Code and Story Readability** on the same problem: keep the Story Readability framing and credit both. If they disagree on whether to split out a function, either condition is enough: the function is reused, or it makes the code read better.
- **Tool findings:** merge per `shared/tooling-registry.md` § 7. On a merged finding, add `**Confirmed by**: {tool_name} ({rule_id})`. A tool-only finding keeps its `[{tool_name}]` prefix and gets its severity from `shared/review-common.md` § Tool Severity Mapping.
- **Cross-model findings:** when a cross-model reviewer agrees with a domain finding, keep the domain explanation and add `[Corroborated by: {model_name}]`. A cross-model-only finding keeps that reviewer's severity and goes in a "**Additional findings from {model_name}**" subsection at the end of its severity group.

### 3.4 Severity and Order

Severity follows impact, not the reviewer that found it. Real bugs usually have high impact, so they are usually P0 or P1. Do not raise a finding's severity only because the correctness agent reported it. Within each severity group, list correctness bugs first.

In Recommendations, move quick wins (one-line fixes, simple renames) up. Mark risky changes (no test coverage, large refactors) and move them down. This changes order, not severity.

### 3.5 Output Format

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

Omit empty severity sections. Also name any missing source (domain, cross-model reviewer, or tool) in the header. This is the **mechanical** report. Phase 3.7 turns it into the final report.

---

## Phase 3.7: Senior Tech Lead Re-review

Dispatch **one** subagent as a senior tech lead. It is the last judgment pass over all merged findings, including cross-cluster findings. Its output **replaces** the mechanical report. It is on by default; `--no-re-review` skips it and the mechanical report goes to the user directly.

Give the tech lead the mechanical report, the full diff, the full file contents, TOOLING_CONTEXT, the cluster manifest (if any), and whether `--min-severity` is set. Give it **all** findings, even below the threshold, so it can move a misclassified finding across it.

```
You are a senior tech lead doing a final read of a code review report before it goes to the engineer.

Seven domain agents and two cross-model reviewers produced findings. The mechanical synthesis (merging duplicates, ordering) is done. Apply your judgment to their work and produce the FINAL report the engineer will read.

You can:
1. Reject findings as false positives (move to "Rejected by Re-review" with reason)
2. Change severity (up or down) — note inline why
3. Rewrite the **Suggested Fix** and **After** code when a better fix exists
4. Add findings the agents missed (tag inline with [Added by Tech Lead])
5. Merge or split findings when the merge got it wrong
6. Flag analysis gaps and architectural concerns in "Tech Lead Notes"

Guardrails:
- Change something only when your judgment changes the verdict (severity, fix, accept or reject). Do not rewrite for style or wording alone.
- Give a reason for every change. No silent edits.
- Do not lower severity to make the report shorter.
- Stay inside the resolved review scope.
- If you agree with everything, output the mechanical report unchanged with one header note: "Tech Lead: no changes — all findings stand as reported."

<REVIEW_RULES>

## Mechanical Synthesis Output (Your Input)
<MECHANICAL_REPORT>

## Diff Context
<DIFF_CONTENT>

## Full File Contents
<FILES_CONTENT>

## Static Analysis Results
{TOOLING_CONTEXT}

## Cluster Manifest (if the change was split)
{CLUSTER_MANIFEST_OR_OMIT}

## --min-severity Active?
{YES_OR_NO}

## Output Format

Produce the final markdown report with the same structure as the mechanical report (Summary, severity-grouped findings, Recommendations), plus:

1. **Header line** gains a `Tech Lead` segment and a Re-review change count:
   `Models: [host] + Codex + Antigravity + Tech Lead | Domains: 7 | Static: [tools] | Re-review: X rejected, Y severity changes, Z fixes rewritten, A added, B notes`

2. **Inline annotations** appear ONLY on findings you touched:
   - Severity change: `[Tech Lead: P2→P0 — reason]`
   - Fix rewrite: `[Tech Lead: fix rewritten — reason]` (the **Suggested Fix** and **After** code show your rewrite)
   - New finding: `[Added by Tech Lead]` (placed in the right severity group)

3. **`## Rejected by Re-review`** (only if any) — one line per rejected finding: `file:line — [original principle/category] rejected: <reason>`. Place it after the severity groups and Recommendations.

4. **`## Tech Lead Notes`** (only if any) — analysis gaps, concerns that span findings, test-coverage observations. Place it after `## Rejected by Re-review`.
```

If the tech lead fails or times out, use the mechanical report and see § Error Handling.

### Severity Filter

Filter by `--min-severity` after the tech lead: remove every finding below the threshold from the final report (P0 > P1 > P2 > P3 > P4). When the tech lead is skipped or fails, filter the mechanical report instead. Reviewers always analyze at full depth; the filter only changes what the user sees.

---

## Phase 4: Fix Dispatch

After the report, offer to fix findings, starting with the most severe. Wait for the user to say yes or name the findings to fix. Fix in this order: correctness bugs, then security P0s, then other P0/P1 findings grouped by file. Fix P2 and below only when asked.

### Parallel Fix Strategy

- Fixes in unrelated files can run in parallel as separate fix agents via the Agent tool.
- Fixes in the **same file** run one after another, to avoid conflicts.
- Each fix agent receives the finding (location, problem, **Suggested Fix**, Before/After) and applies it with the Edit tool.
- When the tech lead rewrote a fix, apply the rewrite, not the domain agent's original.
- Each fix agent first checks that the Before code still matches the file. The code may have moved since the review. If it no longer matches, report that instead of guessing.
- Apply exactly what was flagged, nothing more.
- Findings in `## Rejected by Re-review` are not eligible. Findings added by the tech lead are eligible like any other.

### Post-Fix Summary

List each modified file with a short description of the change, the number of findings fixed out of the total, and any findings skipped with the reason (for example "needs an architectural decision"). Then run the project's existing tests or linters if that is safe. If it is not safe, or you cannot tell how, say why and give the command for the user to run.

---

## Guardrails

Follow `shared/review-common.md` § Cross-Skill Discipline. Every reviewing prompt carries its Review Rules block, including the Rule of Three for duplication-driven extraction.

**Incidental similarity is not duplication.** Two blocks that look alike but serve different purposes and change for different reasons are not DRY violations.

---

## Error Handling

Read `shared/review-common.md` § Shared Error Handling for common errors.

| Error | Action |
|---|---|
| One or more subagents fail | Continue with remaining results; note which domain was not analyzed in the report header. |
| All subagents fail | Report the failure: "Analysis failed — could not complete any domain review. Please try again." |
| All tools declined in gate | Review proceeds without tool findings — AI analysis only |
| One cross-model dispatch fails | Continue with remaining cross-model + 7 domain subagents; note unavailable model in report header. |
| Both cross-model dispatches fail | Continue with 7 domain subagents only; note "Cross-model unavailable" in report header. |
| Phase 3.7 tech lead subagent fails or times out | Use the mechanical report. The header shows `Tech Lead re-review: unavailable ([reason])`. Offer to retry the re-review or continue with the mechanical findings. |
