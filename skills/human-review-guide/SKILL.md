---
name: human-review-guide
description: "Use when the user invokes /human-review-guide to generate a guided reading order that helps a human reviewer focus on the decisions that need their judgment."
---

# Human Review Guide Skill

Generate a personalized reading guide for human review. Analyze a change set or artifact, classify every section by how much human attention it needs, then produce a guided reading order focused on decisions that require human judgment. The guide tells the reviewer what to read carefully, what to skim, and what to skip — saving time by directing attention where it matters.

The existing review skills (`/codereview`, `/quick-review`, `/readability-review`) have the AI do the review. This skill is different — it helps the *human* review more effectively.

## Out of Scope

This skill MUST NOT:
- Perform the review itself. It produces a reading guide, not findings or bug reports. Code quality, correctness, and security analysis are the domain of `/codereview` and `/quick-review`.
- Modify source code. The guide is read-only output — no fixes, no edits.
- Auto-trigger `/codereview`. When `--with-review` is used and no findings exist, prompt the user to run `/codereview` first — never invoke it automatically.
- Make final decisions for the reviewer. `DECIDE` chunks surface the decision and alternatives; the human makes the call.
- Over-classify as SKIP. When in doubt, escalate one tier up (SKIP→SKIM, SKIM→READ, READ→DECIDE). Conservative triage is a feature, not a bug.
- Inflate the decision count. Mechanical choices (variable names, formatting, import order) are not decisions. Reserve `DECIDE` for genuine trade-offs and judgment calls.

## Reference Files

| File | Contents | When to read |
|---|---|---|
| `references/agent-prompts.md` | Triage agent and deep analysis agent prompt templates | Before dispatching agents in Phase 1 and Phase 2 |
| `references/output-formats.md` | Terminal markdown and HTML report format templates | Before writing output in Phase 3 |

## Invocation

Parse the user's `/human-review-guide` arguments:

| Invocation | Mode | Description |
|---|---|---|
| `/human-review-guide` | Branch diff (default) | Guide for current branch diff vs. base |
| `/human-review-guide PR#<number>` | PR review | Guide for a specific GitHub PR |
| `/human-review-guide <path>` | Artifact review | Guide for reviewing a file or directory |
| `/human-review-guide --with-review` | Enriched | Incorporate existing `/codereview` findings from this session |
| `/human-review-guide --calibrate` | Recalibrate | Re-run first-run calibration questions |

Arguments are combinable. Examples:
- `/human-review-guide --with-review` — branch diff guide enriched with `/codereview` findings
- `/human-review-guide PR#42 --with-review` — PR guide with code review findings
- `/human-review-guide docs/spec.md` — guide for reviewing a non-code artifact

If the invocation is ambiguous or unrecognizable, ask the user to clarify before proceeding.

---

## Phase 0: Setup

### 0.1 Load User Preferences

Read `shared/skill-context.md` for the full protocol (resolve `shared/...` against the plugin root — two levels above this SKILL.md — never the project's working directory). In brief:

1. Read `.claude/skill-context/preferences.md` — if missing, invoke `/preferences` (streamlined).
2. Read `.claude/skill-context/human-review-guide.md` (if it exists) for skill-specific preferences.

**How preferences shape this skill:**

| Preference | Effect on Human Review Guide |
|---|---|
| Detail level: concise | Shorter analysis per chunk, tighter executive summary |
| Detail level: detailed | Richer alternative analysis, more consequence detail |
| Assumed knowledge: beginner | Lower SKIP threshold, explain more context in READ chunks |
| Assumed knowledge: expert | Higher SKIP threshold, focus on non-obvious decisions |
| Skill-specific: skip tolerance | Conservative / balanced / aggressive triage thresholds |
| Skill-specific: review focus | Weight triage toward specific concerns (security, architecture, etc.) |
| Skill-specific: verbosity | Concise pointers / moderate explanation / detailed rationale |

### 0.2 First-Run Calibration

If no skill-specific context exists at `.claude/skill-context/human-review-guide.md`, ask calibration questions using `AskUserQuestion`:

1. **Role/expertise** — "What's your background?" with options: Backend developer, Frontend developer, Full-stack developer, DevOps/Infra, PM/Non-technical reviewer, Other
2. **Review focus** — "What do you care most about when reviewing?" with options: Correctness & edge cases, Architecture & design decisions, Security implications, Maintainability & tech debt
3. **Verbosity preference** — "How detailed should the guide be?" with options: Concise (just pointers), Moderate (brief explanations), Detailed (full rationale)
4. **Skip tolerance** — "How aggressively should I mark things as skippable?" with options: Conservative (surface more, miss nothing), Balanced, Aggressive (only flag critical decisions)

Save answers to `.claude/skill-context/human-review-guide.md`:

```markdown
# Human Review Guide Preferences

Last updated: {DATE}

## Calibration
- **Role:** {answer}
- **Review focus:** {answer}
- **Verbosity:** {concise | moderate | detailed}
- **Skip tolerance:** {conservative | balanced | aggressive}
```

If `--calibrate` flag is set, re-run calibration even if the file exists.

### 0.3 Resolve `--with-review`

If `--with-review` is specified:

1. Check the current conversation context for `/codereview` output (look for the structured findings report with severity-grouped findings).
2. **Found:** Extract findings, noting file paths, severities, and descriptions. Hold for Phase 2 enrichment.
3. **Not found:** Display: "No `/codereview` output found in this session. Run `/codereview` first, then re-run `/human-review-guide --with-review`. Or drop `--with-review` to generate the guide without it." Exit.

### 0.4 Determine Mode

Based on the invocation arguments, set the `mode` variable:

| Argument | Mode | Chunking strategy |
|---|---|---|
| *(none)* or branch diff | `code-diff` | Per-file for ≤15 files, per-hunk for >15 files |
| `PR#<number>` | `code-diff` | Same as branch diff, using PR diff |
| `<path>` to a code file | `code-diff` | Per-hunk within the file |
| `<path>` to a non-code file | `artifact` | Per-section/heading |
| `<path>` to a directory | Mixed | Detect per-file: code files → `code-diff`, non-code → `artifact` |

The `mode` variable is passed to the agent prompts to adjust framing.

---

## Phase 1: Input Resolution & Triage

### 1.1 Input Resolution

Gather the content to analyze based on the resolved mode:

**For `code-diff` mode:**

1. Detect base branch — read `shared/review-common.md` § Base Branch Detection.
2. Gather changed files — read `shared/review-common.md` § File Gathering.
3. Capture the diff: `git diff <base>...HEAD` (or `gh pr diff <number>` for PR mode).
4. Capture file list with stats: `git diff --stat <base>...HEAD`.
5. Count files and lines changed for output format decision (Phase 3).

**For `artifact` mode:**

1. Read the target file or directory contents.
2. Split content by heading structure (H1, H2, H3) into logical sections.

**For mixed mode (directory with code and non-code files):**

1. List all files, classify each as code or non-code by extension.
2. For code files: capture `git diff` if they have changes, or read full content.
3. For non-code files: read and split by headings.

### 1.2 Triage — Classification Pass

Dispatch a **single subagent** (`model: "opus"`) to classify every chunk. Read `references/agent-prompts.md` § Triage Agent for the full prompt template.

**Agent receives:**
1. The mode (`code-diff`, `artifact`, or `mixed`)
2. The diff or content chunks
3. The user's calibration profile (role, review focus, skip tolerance)
4. File stats summary (number of files, lines changed)

**Agent returns structured JSON-like markdown for each chunk** (tier, one-line reason, `Related to` links) — output format in `references/agent-prompts.md` § Triage Agent.

**Classification tiers:**

| Tier | Label | Meaning | Reviewer action |
|------|-------|---------|-----------------|
| 1 | `DECIDE` | Contains a decision requiring human judgment | Read carefully, form an opinion |
| 2 | `READ` | Non-trivial logic worth understanding | Read to build mental model |
| 3 | `SKIM` | Straightforward, follows from decisions elsewhere | Glance for context |
| 4 | `SKIP` | Mechanical/boilerplate | Safe to ignore |

**Triage rules:**
- Conservative by default: when in doubt, escalate one tier up
- Calibration adjusts thresholds: `skip_tolerance: aggressive` raises the SKIP bar; `conservative` lowers it
- Role-aware: a backend dev reviewing frontend code → lower SKIP threshold for frontend patterns
- Track `Related to` links between chunks for dependency ordering in Phase 3

### 1.3 Validate Triage Output

- Every chunk must have exactly one tier and a non-empty reason.
- At least one chunk must be classified as DECIDE or READ. If all chunks are SKIM/SKIP, re-prompt the triage agent with: "No decisions or notable logic found — are you sure? Look for any design choices, trade-offs, or non-obvious implementation decisions."
- Count DECIDE chunks for the executive summary.

---

## Phase 2: Deep Analysis

Fires only on chunks classified as `DECIDE` or `READ`. All other chunks pass through to Phase 3 with just their triage label.

Dispatch a **single subagent** (`model: "opus"`) that processes all DECIDE and READ chunks **sequentially** — not parallel, because chunks often relate to each other and the analysis benefits from accumulated context. Read `references/agent-prompts.md` § Deep Analysis Agent for the full prompt template.

### Agent Receives

1. The mode (`code-diff`, `artifact`, or `mixed`)
2. The triage output from Phase 1 (all chunks with tiers and reasons)
3. The full content of DECIDE and READ chunks (diff hunks, file sections, or artifact sections)
4. Surrounding context for each chunk (the file content around the changed hunk, or the parent section for artifacts)
5. The user's calibration profile
6. `/codereview` findings (if `--with-review` and findings were extracted in Phase 0.3)

### DECIDE Chunk Analysis

For each `DECIDE` chunk, the agent produces the decision analysis block (decision, alternatives not taken, consequences, ask-yourself questions, reversibility) — template in `references/agent-prompts.md` § Deep Analysis Agent.

### READ Chunk Analysis

For each `READ` chunk, the agent produces the comprehension block (what this does, why this way, why it matters, gotchas) — template in `references/agent-prompts.md` § Deep Analysis Agent.

### `--with-review` Enrichment

When `/codereview` findings are available, weave them into the relevant chunks:

- Match findings to chunks by file path and line range.
- For DECIDE chunks: note if `/codereview` found issues and whether the fix is mechanical or requires judgment. Example: *"Note: /codereview flagged a P1 race condition here. The fix is mechanical, but the decision to use a mutex vs. channel is yours."*
- For READ chunks: note related findings as gotchas. Example: *"Gotcha: /codereview flagged missing error handling at line 52 (P2). Worth checking if the error case matters for your use case."*
- Do NOT duplicate `/codereview` findings as standalone items — only reference them within the context of the chunk analysis.

### Error Handling

- **Agent fails:** Fall back to a simplified guide using only Phase 1 triage output (tier + reason per chunk, no deep analysis). Header note: "Deep analysis unavailable — showing triage-only guide." Offer retry.
- **Agent returns incomplete analysis (missing chunks):** Note missing chunks in the guide: "Deep analysis skipped for {chunk} — triage classification only."

---

## Phase 3: Guide Synthesis & Output

Assemble the triage classifications + deep analysis into the final reading guide. Read `references/output-formats.md` for the full format templates.

### 3.1 Determine Reading Order

Order entries by **decision dependency**, not file path:

1. Identify dependency links from the `Related to` field in triage output.
2. Topologically sort DECIDE chunks: foundational decisions first, dependent decisions after.
3. Interleave READ chunks after their related DECIDE chunk (so the reader gets context in order).
4. Group SKIM chunks at the end under a "For Context" section.
5. Collapse all SKIP chunks into a single summary line.

If no dependency links exist (all chunks are independent), order DECIDE chunks by estimated impact (larger blast radius first), then READ chunks by file order.

### 3.2 Build Executive Summary

2-3 sentences covering:
- What this change does overall
- Number of decisions needing human input (count of DECIDE chunks)
- Estimated review time: `(DECIDE_count × 3) + (READ_count × 1)` minutes, rounded to nearest 5

### 3.3 Build Decision Map

A table of all DECIDE chunks listed upfront, ordered by reading sequence — table template in `references/output-formats.md`. This is the table of contents for the review — the reviewer can scan this first to know what's coming.

### 3.4 Build Review Checklist

Derive concrete yes/no items from each DECIDE chunk's "Ask yourself" questions — checklist format in `references/output-formats.md`.

### 3.5 Build Open Questions

Collect unresolved items:
- Decisions where the analysis couldn't determine why a choice was made
- Chunks where context was insufficient to assess consequences
- Inconsistencies between chunks (e.g., two files making contradictory assumptions)

If none: omit this section.

### 3.6 Determine Output Format

Choose terminal markdown (small changes) or an HTML report file (large changes) — size thresholds in `references/output-formats.md` § Output Size Thresholds.

### 3.7 Render Output

**Terminal markdown (small):**

Assemble the guide inline using the terminal markdown template from `references/output-formats.md`. Tier badges render as inline markers: `[DECIDE]`, `[READ]`, `[SKIM]`.

**HTML report (large):**

1. Write the guide as markdown to a temporary location following the HTML report template from `references/output-formats.md`.
2. Include YAML front-matter per `shared/html-reports.md`.
3. Call the HTML renderer. **Resolve `scripts/html_render.py` to its absolute path under the plugin root (two levels above this SKILL.md) before running** — the command executes in the user's project cwd, which does not contain the plugin's `scripts/` folder:

````bash
python scripts/html_render.py <report_path> --profile analytical
````

4. If the renderer succeeds: deliver the HTML file via `SendUserFile`.
5. If the renderer fails: deliver the markdown file via `SendUserFile` with a warning.
6. If `SendUserFile` is unavailable in this harness, print the absolute report path instead.

**In both formats:**
- File references use `file:line` format
- `DECIDE` entries are visually prominent (bold headers, tier badge)
- The review checklist is copy-pasteable
- SKIM entries are grouped separately (collapsed in HTML)
- SKIP entries are a single summary line

---

## Context Management

| Phase | Budget / Strategy |
|---|---|
| Phase 1 triage agent | Receives diff/content + calibration. For large diffs (>100 files), send only `git diff --stat` + file list and let the agent request specific file diffs as needed. |
| Phase 2 deep analysis agent | Receives only DECIDE/READ chunk content + surrounding context. SKIM/SKIP chunks are excluded to save context. |
| Phase 3 synthesis | Operates on agent outputs only — no raw content re-reading. |
