---
name: readability-review
version: "1.0.0"
description: "Use when the user invokes /readability-review to grade code on 8 story-readability dimensions with numeric scoring (0-100), letter grades, and concrete before/after refactoring suggestions."
---

# Readability Review Skill

Grade code on how well it "reads like a story" using 8 weighted dimensions. Produces a numeric score (0-100) mapped to a letter grade, with thematic findings and file-by-file breakdown including concrete refactoring suggestions.

## Invocation

Parse the user's `/readability-review` arguments to determine mode and scope:

| Invocation | Mode | Scope |
|---|---|---|
| `/readability-review` | Branch diff (default) | Current branch vs. fork point |
| `/readability-review src/utils/` | Directory scan | All files recursively |
| `/readability-review --file src/main.cpp` | Single file | One specific file |
| `/readability-review --pr 123` | PR review | Files changed in a GitHub PR |
| `/readability-review --commit abc123` | Commit review | Files changed in a specific commit |
| `/readability-review --min-score 70` | Score filter | Combinable -- only show files below threshold |

Arguments are combinable. Examples:
- `/readability-review --pr 42 --min-score 60` -- review PR #42, only show files scoring below 60
- `/readability-review src/api/ --min-score 80` -- scan directory, only show files below 80
- `/readability-review --file src/main.cpp --min-score 50` -- single file, report only if below 50

If the invocation is ambiguous or the argument is unrecognizable, ask the user to clarify before proceeding.

---

## Phase 0: Scope Resolution

### 0.1 Load User Preferences

Read `shared/skill-context.md` for the full protocol. In brief:

1. Read `.claude/skill-context/preferences.md` -- if missing, invoke `/preferences` (streamlined).
2. Read `.claude/skill-context/readability-review.md` (if it exists) for readability-specific preferences.

**How preferences shape this skill:**

| Preference | Effect on Readability Review |
|---|---|
| Detail level: concise | Shorter findings, focus on highest-impact improvements |
| Detail level: detailed | Include full context on why each dimension scored as it did |
| Assumed knowledge: beginner | Explain what each dimension means, not just the score |
| Assumed knowledge: expert | Skip dimension definitions, focus on non-obvious observations |
| Custom weights | Override default dimension weights from shared/story-readability.md |
| Min-score default | Override the `--min-score` threshold when flag is not explicitly provided |

Pass relevant preferences to the analysis subagent in Phase 1.

### 0.2 Base Branch Detection

Read `shared/review-common.md` § Base Branch Detection.

### 0.3 File Gathering

Read `shared/review-common.md` § File Gathering.

### 0.4 Content Loading

Load the **full content** of every file in scope -- not just diff hunks. Story readability requires function-level context to judge narrative flow, abstraction consistency, and cognitive chunking.

Also capture the **diff itself** (`git diff <base>...HEAD` or equivalent) if in branch-diff or PR mode, so the analysis can highlight what changed.

### 0.5 Target Language Detection

Read `shared/review-common.md` § Target Language Detection.

---

## Phase 1: Analysis

Dispatch a **single subagent** via the Agent tool. Readability grading is a unified, qualitative judgment -- it is not split across multiple domain subagents. No cross-model dispatch (the scoring is calibrated to the principle file and must be internally consistent). No static analysis tooling (this is a qualitative, judgment-based review).

Always spawn the subagent with `model: "opus"`.

### Subagent Prompt

```
You are a senior readability reviewer. Your job is to grade code on how well it
"reads like a story" using 8 weighted dimensions.

## Instructions
1. Read the principle file at: shared/story-readability.md
   (This file is relative to the project root -- find and read it first.)
2. For each file under review, score ALL 8 dimensions on a 1-10 scale.
   Use the calibration examples in the principle file as anchors:
   - 9-10 = matches the "excellent" calibration example
   - 5-6  = matches the "mediocre" calibration example
   - 2-3  = matches the "poor" calibration example
   Scores between these bands are for cases that fall between the examples.
3. Compute the weighted score per file using the weights from the principle file
   (or custom weights if provided below).
4. For any dimension scoring 7 or below, provide a concrete finding with:
   - The dimension name
   - The specific location (file:line or file:function)
   - A BEFORE code block showing the current code (in <TARGET_LANGUAGE>)
   - An AFTER code block showing the improved version (in <TARGET_LANGUAGE>)
   - A brief explanation: "Why this improves the story"
5. Consult the Language-Aware Notes section in the principle file for
   language-specific scoring adjustments.
6. If custom weights are provided, use them instead of the defaults.

## Custom Weights (if any)
<CUSTOM_WEIGHTS_OR_"Use defaults from shared/story-readability.md">

## User Preferences
<USER_PREFERENCES_OR_"None">

## Files Under Review
<FILES_CONTENT>

## Diff Context (if applicable)
<DIFF_CONTENT_OR_"N/A -- directory/file scan mode">

## Output Format
For each file, output:

### <filename>
| # | Dimension | Score | Weight | Weighted |
|---|-----------|-------|--------|----------|
| 1 | Narrative Flow | X/10 | 20% | X.X |
| 2 | Naming as Intent | X/10 | 15% | X.X |
| 3 | Cognitive Chunking | X/10 | 15% | X.X |
| 4 | Abstraction Consistency (SLAP) | X/10 | 14% | X.X |
| 5 | Function Focus | X/10 | 10% | X.X |
| 6 | Structural Clarity | X/10 | 10% | X.X |
| 7 | Documentation Quality | X/10 | 10% | X.X |
| 8 | No Clever Tricks | X/10 | 6% | X.X |
| | **Weighted Total** | | | **X.X/100** |

#### Findings
For each dimension scoring 7 or below:

**[Dimension Name]** -- `file:line_or_function`
**Before**:
```<target_language>
// the current code
```
**After**:
```<target_language>
// the improved code
```
**Why this improves the story**: Explanation.

If all dimensions score 8+, output: "No findings -- this file reads like a well-told story."
```

### Large Scope Handling

If the file list exceeds **30 files**, batch them into groups of approximately 15 files. Process batches sequentially:

1. Dispatch subagent for batch 1, collect results
2. Dispatch subagent for batch 2, collect results
3. Continue until all batches are processed
4. Synthesize all batch results together in Phase 2

Keep related files in the same batch when possible (e.g., a module and its tests, a class and its interface).

---

## Phase 2: Report

The report has three layers, presented in order.

### Layer 1: Scorecard

Present a summary scorecard as an ASCII box table:

```
+===================================================+
|  READABILITY REVIEW -- {scope}                     |
|  {Language} . {N} files . {Date}                   |
+===================================================+
|  Story Score: {score}/100 ({grade})                |
+===================================================+
|  #  Dimension              Score  Weight  Grade    |
|  -- ---------------------- ------ ------- -------  |
|  1  Narrative Flow         X/10    20%    {grade}  |
|  2  Naming as Intent       X/10    15%    {grade}  |
|  3  Cognitive Chunking     X/10    15%    {grade}  |
|  4  Abstraction (SLAP)     X/10    14%    {grade}  |
|  5  Function Focus         X/10    10%    {grade}  |
|  6  Structural Clarity     X/10    10%    {grade}  |
|  7  Documentation Quality  X/10    10%    {grade}  |
|  8  No Clever Tricks       X/10     6%    {grade}  |
+===================================================+
|  Top opportunity: {dimension} in {file}            |
|  Strongest: {dimension} across {scope}             |
+===================================================+
```

Dimension scores are averaged across files, weighted by lines of code when files vary significantly in size. Apply the grade mapping from `shared/story-readability.md` § Grade Mapping to both the overall score and per-dimension scores.

If `--min-score` was specified and some files were filtered out, note: "Showing {M} of {N} files (filtered by --min-score {threshold})."

### Layer 2: Findings Summary

Write 2-4 paragraphs describing:
- **Thematic patterns** -- what recurring readability issues appear across files
- **What's working well** -- which dimensions are consistently strong
- **Recurring issues** -- specific anti-patterns seen multiple times
- **Highest-impact improvements** -- the 1-3 changes that would most improve the overall score

### Layer 3: File-by-File Breakdown

Present each file ordered by score **ascending** (worst first). For each file:

1. **Per-dimension scores table** -- same format as the subagent output
2. **Findings** -- each finding includes:
   - Dimension name
   - Location (file:line or file:function)
   - Before/after code blocks in the target language
   - "Why this improves the story" explanation

If `--min-score` was specified, only include files scoring below the threshold.

---

## Phase 3: Fix Offer

After presenting the report, ask:

> "Want me to refactor to improve the story score? I can fix all findings, or you can pick specific files or dimensions."

### Supported Responses

| User Response | Action |
|---|---|
| "all" or "yes" | Fix all findings across all files |
| Specific files (e.g., "src/main.cpp, src/utils.cpp") | Fix findings only in named files |
| Specific dimensions (e.g., "narrative flow, naming") | Fix findings only for named dimensions |
| "no" or "skip" | End the review |

### Fix Dispatch

- **Independent files**: dispatch parallel fix agents (one per file)
- **Same-file fixes**: apply sequentially to avoid conflicts
- Each fix agent is spawned with `model: "opus"` via the Agent tool
- Each fix agent receives:
  - The finding details (dimension, location, before/after, explanation)
  - The full file content
  - Instruction to apply the fix using the Edit tool
  - Instruction to verify the before-code still matches before editing

### Post-Fix Summary

After fixes are applied, present:
- List of files modified with a brief description of each change
- Number of findings addressed vs. total findings
- Estimated score improvement (based on dimension weight of fixed findings)
- Any findings intentionally skipped (with reason)
- Suggest re-running `/readability-review` to verify the new scores

---

## First Run Behavior

If no `.claude/skill-context/readability-review.md` exists:

1. Use default weights and settings from `shared/story-readability.md`
2. After presenting the report, ask:
   > "Would you like to customize the dimension weights or set a default min-score threshold? I can save your preferences for future reviews."
3. If the user says yes, collect their preferences and write `.claude/skill-context/readability-review.md`
4. If the user says no, continue using defaults -- no file is created

---

## Guardrails

Read `shared/review-common.md` § Shared Guardrails for the base constraints (no over-engineering, context matters, be specific, language-adaptive, profile first).

Additional readability-review-specific guardrails:

1. **Calibration-anchored scoring**: Always reference the calibration examples in `shared/story-readability.md` when assigning scores. Do not score based on vibes or general impressions -- anchor every score to the concrete examples.

2. **Language-aware judgment**: Consult the Language-Aware Notes section in `shared/story-readability.md` before scoring. An idiomatic Go short variable name is not a naming violation; a Python list comprehension is not a clever trick (unless nested).

3. **Before/after required for every finding**: Never report a finding without showing both the current code and the improved version. Abstract advice ("consider renaming") is not acceptable.

4. **No severity inflation**: This is a readability and maintainability review, not a bug hunt. Findings are about code clarity, not correctness. Do not frame readability issues as critical defects.

5. **Context matters**: Test code has different readability standards. DAMP (Descriptive And Meaningful Phrases) is preferred over DRY in tests. Configuration files, generated code, and vendored dependencies should be scored leniently or excluded.

---

## Error Handling

Read `shared/review-common.md` § Shared Error Handling for common errors (no changed files, base branch detection, PR/commit not found, file not found, no violations, too many files).

Additional readability-review-specific errors:

| Error | Action |
|---|---|
| Analysis subagent fails | "Analysis failed -- could not complete readability review. Please try again." |
| No files in scope | "No files found in the specified scope. Check the path and try again." |
| All files above `--min-score` | "All {N} files score above {threshold}. No findings to report." |
| Fix agent fails | Report which fixes failed and which files were affected. Suggest manual application of the before/after examples from the report. |
