---
name: readability-review
description: "Use when the user invokes $readability-review to grade how well code reads as a story, with letter grades and concrete refactoring suggestions. SKIP if the user wants a bug-focused review \u2014 that's $quick-review or $codereview."
---

# Readability Review Skill

Grade code on how well it "reads like a story" using 8 weighted dimensions. Produces a numeric score (0-100) mapped to a letter grade, with thematic findings and file-by-file breakdown including concrete refactoring suggestions.

## Out of Scope

This skill MUST NOT:
- Modify source code without explicit user approval after the report. Fixing happens only via the Fix Offer phase, only after the user picks "yes" or names specific findings/files/dimensions.
- Expand fixes beyond what was flagged. When the user approves fixes, fix exactly the reported findings - do not bundle "while I'm in this file" cleanup, renames, or unrelated improvements.
- Report on code outside the resolved scope. If the diff/file/PR doesn't include a file, do not flag findings in it.
- Use the P0-P4 severity scale. This skill uses per-dimension scores (1-10) and a weighted total (0-100) mapped to letter grades (A-F). P0-P4 belongs to `$codereview` and `$quick-review` - do not mix the two scales.
- Downgrade severe readability findings to "polish." A function that actively misleads (named `validate` but mutates state), a god-function with 12 abstraction levels, or a name that lies about behavior - these ARE critical findings within the readability domain, even though they don't crash anything. Score them honestly: a 3/10 on a high-weight dimension is a real problem, not a P3 nit.
- Grade outside the 8 fixed dimensions. The skill scores Narrative Flow, Naming as Intent, Cognitive Chunking, SLAP, Function Focus, Structural Clarity, Documentation Quality, No Clever Tricks - and only those.
- Suggest extracting duplicate patterns until 3+ occurrences exist (Rule of Three).
- Apply universal standards to test code. Tests follow DAMP, not DRY - repeated setup for clarity is acceptable and not a finding.

## Invocation

Parse the user's `$readability-review` arguments to determine mode and scope:

| Invocation | Mode | Scope |
|---|---|---|
| `$readability-review` | Branch diff (default) | Current branch vs. fork point |
| `$readability-review src/utils/` | Directory scan | All files recursively |
| `$readability-review --file src/main.cpp` | Single file | One specific file |
| `$readability-review --pr 123` | PR review | Files changed in a GitHub PR |
| `$readability-review --commit abc123` | Commit review | Files changed in a specific commit |
| `$readability-review --min-score 70` | Score filter | Combinable - only show files below threshold |

Arguments are combinable. Examples:
- `$readability-review --pr 42 --min-score 60` - review PR #42, only show files scoring below 60
- `$readability-review src/api/ --min-score 80` - scan directory, only show files below 80
- `$readability-review --file src/main.cpp --min-score 50` - single file, report only if below 50

If the invocation is ambiguous or unrecognizable, ask the user to clarify before proceeding.

---

## Phase 0: Scope Resolution

### 0.1 Load User Preferences

Read `../shared/skill-context.md` for the full protocol (resolve `../shared/...` against the collection root (one level above this SKILL.md) - never the project's working directory). In brief:

1. Read `.codex/skill-context/preferences.md` - if missing, proceed with defaults (do not interrupt the workflow with an interview).
2. Read `.codex/skill-context/readability-review.md` (if it exists) for readability-specific preferences.

**How preferences shape this skill:**

| Preference | Effect on Readability Review |
|---|---|
| Detail level: concise | Shorter findings, focus on highest-impact improvements |
| Detail level: detailed | Include full context on why each dimension scored as it did |
| Assumed knowledge: beginner | Explain what each dimension means, not just the score |
| Assumed knowledge: expert | Skip dimension definitions, focus on non-obvious observations |
| Custom weights | Override default dimension weights from `../shared/story-readability.md` |
| Min-score default | Override the `--min-score` threshold when flag is not explicitly provided |

`$readability-review` is a **silent defaults** skill. **MUST NOT invoke** `$preferences` on first contact - readability reviews should not be interrupted by interviews.

Pass relevant preferences to the analysis subagent in Phase 1.

### 0.2 Base Branch Detection

Read `../shared/review-common.md` Section Base Branch Detection.

### 0.3 File Gathering

Read `../shared/review-common.md` Section File Gathering.

### 0.4 Content Loading

Load the **full content** of every file in scope - not just diff hunks. Story readability requires function-level context to judge narrative flow, abstraction consistency, and cognitive chunking.

Also capture the **diff itself** (`git diff <base>...HEAD` or equivalent) if in branch-diff or PR mode, so the analysis can highlight what changed.

### 0.5 Target Language Detection

Read `../shared/review-common.md` Section Target Language Detection.

---

## Phase 1: Analysis

Dispatch a **single subagent** via the Codex agent workflow. Readability grading is a unified, qualitative judgment - it is not split across multiple domain subagents. No cross-model dispatch (the scoring is calibrated to the principle file and must be internally consistent). No static analysis tooling (this is a qualitative, judgment-based review).

**MUST spawn the subagent** with `model: "fable"`.

### Subagent Prompt

Before dispatch, substitute **every** `<ANGLE_BRACKET>` placeholder in the template below. In particular, replace `<PRINCIPLE_PATH>` with the **absolute path** to `../shared/story-readability.md`, resolved against the collection root (one level above this SKILL.md) - never against the project's working directory; subagents start in the project cwd and cannot find plugin files by relative path. The remaining placeholders (`<TARGET_LANGUAGE>`, `<CUSTOM_WEIGHTS_OR_...>`, `<USER_PREFERENCES_OR_"None">`, `<FILES_CONTENT>`, `<DIFF_CONTENT_OR_...>`) take their resolved values or the quoted fallback.

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
<CUSTOM_WEIGHTS_OR_"Use defaults from the principle file above">

## User Preferences
<USER_PREFERENCES_OR_"None">

## Files Under Review
<FILES_CONTENT>

## Diff Context (if applicable)
<DIFF_CONTENT_OR_"N/A - directory/file scan mode">

## Output Format
For each file, output a table with one row per dimension (all 8, in the
principle file's order). Fill the Weight column with the weights you used -
the principle file's defaults, or the custom weights above if provided:

### <filename>
| # | Dimension | Score | Weight | Weighted |
|---|-----------|-------|--------|----------|
| 1 | <dimension> | X/10 | XX% | X.X |
| ... | | | | |
| | **Weighted Total** | | | **X.X/100** |

#### Findings
For each dimension scoring 7 or below:

**[Dimension Name]** - `file:line_or_function`
**Before**:
```<target_language>
// the current code
```
**After**:
```<target_language>
// the improved code
```
**Why this improves the story**: Explanation.

If all dimensions score 8+, output: "No findings - this file reads like a well-told story."
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

Present a summary scorecard as a markdown header followed by a markdown table. The markdown table renders as a styled HTML table in the companion report and is more readable in raw markdown than ASCII box-drawing.

```markdown
**READABILITY REVIEW - {scope}**
{Language} * {N} files * {Date}

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

Dimension scores are averaged across files, weighted by lines of code when files vary significantly in size. The Weight column above shows the **default** weights - if custom dimension weights are configured (`.codex/skill-context/readability-review.md`), fill it with the weights actually applied. Apply the grade mapping from `../shared/story-readability.md` Section Grade Mapping to both the overall score and per-dimension scores; that mapping is defined over 0-100, so multiply a per-dimension 1-10 score by 10 before looking it up, and round the weighted total to the nearest integer first.

If `--min-score` was specified and some files were filtered out, note: "Showing {M} of {N} files (filtered by --min-score {threshold})."

### Layer 2: Findings Summary

Write 2-4 paragraphs describing:
- **Thematic patterns** - what recurring readability issues appear across files
- **What's working well** - which dimensions are consistently strong
- **Recurring issues** - specific anti-patterns seen multiple times
- **Highest-impact improvements** - the 1-3 changes that would most improve the overall score

### Layer 3: File-by-File Breakdown

Present each file ordered by score **ascending** (worst first). For each file:

1. **Per-dimension scores table** - same format as the subagent output
2. **Findings** - each finding includes:
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

- **Independent files:** dispatch parallel fix agents (one per file)
- **Same-file fixes:** apply sequentially to avoid conflicts
- Each fix agent **MUST be spawned** with `model: "fable"` via the Codex agent workflow
- Each fix agent receives:
  - The finding details (dimension, location, before/after, explanation)
  - The full file content
  - Instruction to apply the fix using the Edit tool
  - Instruction to verify the before-code still matches before editing
- Fix agents **MUST NOT expand scope** - apply exactly what was flagged, nothing more

### Post-Fix Summary

After fixes are applied, present:
- List of files modified with a brief description of each change
- Number of findings addressed vs. total findings
- Estimated score improvement (based on dimension weight of fixed findings)
- Any findings intentionally skipped (with reason)
- Suggest re-running `$readability-review` to verify the new scores

---

## First Run Behavior

If no `.codex/skill-context/readability-review.md` exists:

1. Use default weights and settings from `../shared/story-readability.md`
2. After presenting the report, ask:
   > "Would you like to customize the dimension weights or set a default min-score threshold? I can save your preferences for future reviews."
3. If the user says yes, collect their preferences and write `.codex/skill-context/readability-review.md`
4. If the user says no, continue using defaults - no file is created

---

## Guardrails

Read `../shared/review-common.md` Section Cross-Skill Discipline for the base constraints (evidence, language-adaptive, specificity, no over-engineering, test-code DAMP, profile-first).

Additional readability-review-specific guardrails:

1. **Calibration-anchored scoring.** Always reference the calibration examples in `../shared/story-readability.md` when assigning scores. **MUST NOT score** based on vibes or general impressions - anchor every score to the concrete examples.

2. **Language-aware judgment.** Consult the Language-Aware Notes section in `../shared/story-readability.md` before scoring. An idiomatic Go short variable name is not a naming violation; a Python list comprehension is not a clever trick (unless nested).

3. **Before/after required for every finding.** Never report a finding without showing both the current code and the improved version. Abstract advice ("consider renaming") is not acceptable.

---

## Error Handling

Read `../shared/review-common.md` Section Shared Error Handling for common errors (no changed files, base branch detection, PR/commit not found, file not found). The "no violations" and "too many files" rows there are written for codereview/quick-review - this skill instead emits its scorecard (high grades) for a findings-free scope, and handles large scopes via its own Section Large Scope Handling (>30-file batching), not the >100-file warning.

Additional readability-review-specific errors:

| Error | Action |
|---|---|
| Analysis subagent fails | "Analysis failed - could not complete readability review. Please try again." |
| No files in scope | "No files found in the specified scope. Check the path and try again." |
| All files above `--min-score` | "All {N} files score above {threshold}. No findings to report." |
| Fix agent fails | Report which fixes failed and which files were affected. Suggest manual application of the before/after examples from the report. |
