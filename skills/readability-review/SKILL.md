---
name: readability-review
description: "Use when the user invokes /readability-review to grade how well code reads as a story, with letter grades and concrete refactoring suggestions. SKIP if the user wants a bug-focused review — that's /quick-review or /codereview."
---

# Readability Review Skill

Grade code on how well it "reads like a story" using 8 weighted dimensions. Produces a numeric score (0–100) mapped to a letter grade, with thematic findings and file-by-file breakdown including concrete refactoring suggestions.

## Plugin Root

`${CLAUDE_PLUGIN_ROOT}` is the plugin root. If that is not a real folder path, your host did not fill it in; use the folder two levels above this SKILL.md instead. Every `shared/...`, `scripts/...` and `skills/...` path in this skill is under the plugin root, never under the project's working directory.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md`.

## Out of Scope

This skill MUST NOT:
- Modify source code without explicit user approval after the report. Fixing happens only via the Fix Offer phase, only after the user picks "yes" or names specific findings/files/dimensions.
- Expand fixes beyond what was flagged. When the user approves fixes, fix exactly the reported findings — do not bundle "while I'm in this file" cleanup, renames, or unrelated improvements.
- Report on code outside the resolved scope. If the diff/file/PR doesn't include a file, do not flag findings in it.
- Use the P0–P4 severity scale. This skill uses per-dimension scores (1–10) and a weighted total (0–100) mapped to letter grades (A–F). P0–P4 belongs to `/codereview` and `/quick-review` — do not mix the two scales.
- Downgrade severe readability findings to "polish." A function that actively misleads (named `validate` but mutates state), a god-function with 12 abstraction levels, or a name that lies about behavior — these ARE critical findings within the readability domain, even though they don't crash anything. Score them honestly: a 3/10 on a high-weight dimension is a real problem, not a P3 nit.
- Grade outside the 8 fixed dimensions. The skill scores Narrative Flow, Naming as Intent, Cognitive Chunking, SLAP, Function Focus, Structural Clarity, Documentation Quality, No Clever Tricks — and only those.
- Suggest extracting code only to remove duplication before 3+ occurrences exist (Rule of Three). Extracting one block so the code reads better is fine at any count.

## Invocation

| Invocation | Mode | Scope |
|---|---|---|
| `/readability-review` | Branch diff (default) | Current branch vs. fork point |
| `/readability-review src/utils/` | Directory scan | All files recursively |
| `/readability-review --file src/main.cpp` | Single file | One specific file |
| `/readability-review --pr 123` | PR review | Files changed in a GitHub PR |
| `/readability-review --commit abc123` | Commit review | Files changed in a specific commit |
| `/readability-review --min-score 70` | Score filter | Combinable — only show files below threshold |

If the invocation is ambiguous, ask the user to clarify.

---

## Phase 0: Scope Resolution

### 0.1 Load User Preferences

Read `shared/skill-context.md` for the full protocol. Read `.claude/skill-context/preferences.md` and `.claude/skill-context/readability-review.md` if present; otherwise use defaults. Two readability settings change the scoring:

| Preference | Effect |
|---|---|
| Custom weights | Override default dimension weights from `shared/story-readability.md` |
| Min-score default | Override the `--min-score` threshold when the flag is not given |

Pass relevant preferences to the analysis subagent in Phase 1.

### 0.2 Base Branch, Files, and Language

Read `shared/review-common.md` § Base Branch Detection, § File Gathering, and § Target Language Detection.

### 0.3 Review Inputs

The subagent reads the code itself. Do not copy file contents or the diff into the prompt: re-typing is slow, costs tokens, and makes the reviewer judge a copy. Prepare two values:

- `<FILE_LIST>`: the path of every file in scope. The subagent reads each file in full, not just the diff hunks. Story readability needs function-level context to judge narrative flow, abstraction consistency, and cognitive chunking.
- `<DIFF_COMMAND>`: in branch-diff or PR mode, the command that prints the change (`git diff <base>...HEAD` or `gh pr diff <number>`), so the analysis can highlight what changed. In directory or file scan mode, use "N/A: directory/file scan mode".

If the working tree does not hold the reviewed version (a pull request that is not checked out), fetch its head commit, name that commit in the prompt, and tell the subagent to read each file with `git show <ref>:<path>`. Use the commit id, not `FETCH_HEAD`, which can change.

---

## Phase 1: Analysis

Dispatch a **single subagent**. Readability grading is one consistent judgment, so it is not split across domain subagents. No cross-model dispatch (the scoring is calibrated to the principle file and must be internally consistent). No static analysis tooling (this is a judgment-based review).

For same-platform subagents, do not pass a model or reasoning-effort override. Let every subagent inherit the parent model and reasoning effort unless the user explicitly asks for an override.

### Subagent Prompt

Before dispatch, substitute **every** `<ANGLE_BRACKET>` placeholder in the template below. In particular, replace `<PRINCIPLE_PATH>` with the **absolute path** to `shared/story-readability.md` under the plugin root; subagents start in the project cwd and cannot find plugin files by relative path. The remaining placeholders take their resolved values or the quoted fallback.

```
You are a senior readability reviewer. Your job is to grade code on how well it
"reads like a story" using 8 weighted dimensions.

## Instructions
1. Read the principle file at: <PRINCIPLE_PATH>
2. For each file under review, score ALL 8 dimensions on a 1-10 scale.
   Use the calibration examples in the principle file as anchors:
   - 9-10 = matches the "excellent" calibration example
   - 5-6  = matches the "mediocre" calibration example where one is given; for
     dimensions 6-8 (only excellent/poor examples given), interpolate
   - 2-3  = matches the "poor" calibration example
   Scores between these bands are for cases that fall between the examples.
3. Compute the weighted score per file using the weights from the principle file,
   or the custom weights below if provided.
4. For any dimension scoring 7 or below, provide a concrete finding with:
   - The dimension name
   - The specific location (file:line or file:function)
   - A BEFORE code block showing the current code (in <TARGET_LANGUAGE>)
   - An AFTER code block showing the improved version (in <TARGET_LANGUAGE>).
     For a large refactor, an AFTER sketch of the new shape is enough.
   - A brief explanation: "Why this improves the story"
5. Consult the Language-Aware Notes section in the principle file for
   language-specific scoring adjustments.
6. Write for humans: the reader may speak English as a second language. Use short sentences, everyday words, and explain jargon on first use. State the point first, then the detail. Simplify the language, never the facts — paths, line numbers, and claims stay exact.

## Custom Weights (if any)
<CUSTOM_WEIGHTS_OR_"Use defaults from the principle file above">

## User Preferences
<USER_PREFERENCES_OR_"None">

## Files Under Review
<FILE_LIST>
Read each file in full yourself before you score it. <READ_FROM_REF_NOTE_OR_OMIT>

## Change Under Review (if applicable)
To see what changed, run: <DIFF_COMMAND>

## Output Format
For each file, output a table with one row per dimension (all 8, in the
principle file's order). Fill the Weight column with the weights you used:

### <filename>
| # | Dimension | Score | Weight | Weighted |
|---|-----------|-------|--------|----------|
| 1 | <dimension> | X/10 | XX% | X.X |
| ... | | | | |
| | **Weighted Total** | | | **X.X/100** |

#### Findings
For each dimension scoring 7 or below:

**[Dimension Name]** — `file:line_or_function`
**Before**:
```<target_language>
// the current code
```
**After**:
```<target_language>
// the improved code
```
**Why this improves the story**: Explanation.

If all dimensions score 8+, output: "No findings — this file reads like a well-told story."
```

### Large Scope Handling

For large scopes (more than about 30 files), split the files into batches of related files, such as a module with its tests or a class with its interface. Give every batch the same principle file and anchors so scores stay comparable. Synthesize all batch results together in Phase 2.

---

## Phase 2: Report

The report has three layers, presented in order.

### Layer 1: Scorecard

```markdown
**READABILITY REVIEW — {scope}**
{Language} · {N} files · {Date}

**Story Score: {score}/100 ({grade})**

| # | Dimension | Score | Weight | Grade |
|---|---|---|---|---|
| 1 | Narrative Flow | X/10 | 20% | {grade} |
| 2 | Naming as Intent | X/10 | 15% | {grade} |
| 3 | Cognitive Chunking | X/10 | 15% | {grade} |
| 4 | Abstraction (SLAP) | X/10 | 14% | {grade} |
| 5 | Function Focus | X/10 | 10% | {grade} |
| 6 | Structural Clarity | X/10 | 10% | {grade} |
| 7 | Documentation Quality | X/10 | 10% | {grade} |
| 8 | No Clever Tricks | X/10 | 6% | {grade} |

**Top opportunity:** {dimension} in {file}
**Strongest:** {dimension} across {scope}
```

Dimension scores are averaged across files, weighted by lines of code when files vary significantly in size. The Weight column above shows the **default** weights — if custom dimension weights are configured (`.claude/skill-context/readability-review.md`), fill it with the weights actually applied. Apply the grade mapping from `shared/story-readability.md` § Grade Mapping to both the overall score and per-dimension scores; that mapping is defined over 0–100, so multiply a per-dimension 1–10 score by 10 before looking it up, and round the weighted total to the nearest integer first.

If `--min-score` filtered out some files, say how many of the total files are shown and the threshold used.

### Layer 2: Findings Summary

Summarize the recurring patterns, what is working well, and the 1–3 changes that would most improve the score.

### Layer 3: File-by-File Breakdown

Present each file ordered by score **ascending** (worst first), with its per-dimension score table and its findings in the subagent's format. If `--min-score` was given, include only files scoring below the threshold.

---

## Phase 3: Fix Offer

After the report, offer to refactor: all findings, or only the files or dimensions the user picks.

### Supported Responses

| User Response | Action |
|---|---|
| "all" or "yes" | Fix all findings across all files |
| Specific files (e.g., "src/main.cpp, src/utils.cpp") | Fix findings only in named files |
| Specific dimensions (e.g., "narrative flow, naming") | Fix findings only for named dimensions |
| "no" or "skip" | End the review |

### Applying Fixes

Apply the approved fixes. Parallelize across independent files when it helps; apply fixes in the same file one after another to avoid conflicts. Before each edit, check that the before-code still matches.

### Post-Fix Summary

After fixes are applied, present:
- Files modified, with a brief description of each change
- Number of findings addressed vs. total findings
- Estimated score improvement (based on dimension weight of fixed findings)
- Any findings intentionally skipped (with reason)
- A suggestion to re-run `/readability-review` to verify the new scores

---

## Guardrails

Read `shared/review-common.md` § Cross-Skill Discipline for the base constraints.

1. **Calibration-anchored scoring.** Anchor every score to the calibration examples in `shared/story-readability.md`.
2. **Language-aware judgment.** An idiomatic Go short variable name is not a naming violation; a Python list comprehension is not a clever trick (unless nested).
3. **Concrete findings.** Every finding shows the current code and the improved version (or an AFTER sketch for a large refactor). Abstract advice ("consider renaming") is not acceptable.

---

## Error Handling

Read `shared/review-common.md` § Shared Error Handling for common errors (no changed files, base branch detection, PR/commit not found, file not found). The "no violations" and "too many files" rows there are written for codereview/quick-review — this skill instead emits its scorecard (high grades) for a findings-free scope, and handles large scopes via its own § Large Scope Handling, not the >100-file warning.

Additional readability-review decisions:

| Error | Action |
|---|---|
| Analysis subagent fails | Report that the review could not complete and suggest trying again. |
| No files in scope | Report it and ask the user to check the path. |
| All files above `--min-score` | Report the file count and threshold; there are no findings to show. |
| Fix fails | Report which fixes failed and which files were affected. Point to the report's before/after examples for manual application. |
