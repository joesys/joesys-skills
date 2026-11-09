---
name: human-review-guide
description: "Use when the user invokes /human-review-guide to generate a guided reading order that helps a human reviewer focus on the decisions that need their judgment."
---

# Human Review Guide Skill

Generate a personalized reading guide for human review. Analyze a change set or artifact, classify every section by how much human attention it needs, then produce a guided reading order focused on decisions that require human judgment. The guide tells the reviewer what to read carefully, what to skim, and what to skip — saving time by directing attention where it matters.

The existing review skills (`/codereview`, `/quick-review`, `/readability-review`) have the AI do the review. This skill is different — it helps the *human* review more effectively.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md` (resolve against the plugin root — two levels above this SKILL.md — never the project's working directory).

## Out of Scope

This skill does not:
- Perform the review itself. It produces a reading guide, not findings or bug reports. Code quality, correctness, and security analysis belong to `/codereview` and `/quick-review`.
- Modify source code. The guide is read-only output.
- Invoke `/codereview` for the user, even with `--with-review`.
- Make final decisions for the reviewer. `DECIDE` chunks surface the decision and alternatives; the human makes the call.

## Reference Files

| File | Contents | When to read |
|---|---|---|
| `references/agent-prompts.md` | Triage agent and deep analysis agent prompt templates | Before dispatching agents in Phase 1 and Phase 2 |
| `references/output-formats.md` | Terminal markdown and HTML report format templates | Before writing output in Phase 3 |

## Invocation

| Invocation | Mode | Description |
|---|---|---|
| `/human-review-guide` | Branch diff (default) | Guide for current branch diff vs. base |
| `/human-review-guide PR#<number>` | PR review | Guide for a specific GitHub PR |
| `/human-review-guide <path>` | Artifact review | Guide for reviewing a file or directory |
| `/human-review-guide --with-review` | Enriched | Incorporate existing `/codereview` findings from this session |
| `/human-review-guide --calibrate` | Calibrate | Ask the four reviewer-profile questions and save the answers |

Arguments combine. If the invocation is ambiguous or unrecognizable, ask the user to clarify before proceeding.

---

## Phase 0: Setup

### 0.1 Load User Preferences

Read `shared/skill-context.md` for the full protocol (resolve `shared/...` against the plugin root — two levels above this SKILL.md — never the project's working directory). In brief: read `.claude/skill-context/preferences.md` and `.claude/skill-context/human-review-guide.md` if present; otherwise use defaults.

Preferences tune triage and depth. A beginner or a conservative skip tolerance surfaces more chunks; an expert or an aggressive skip tolerance surfaces fewer and focuses on non-obvious decisions. Review focus weights triage toward that concern. Detail level and verbosity set how long each analysis is.

### 0.2 Reviewer Profile

Read the reviewer profile from `.claude/skill-context/human-review-guide.md` if it exists. If it does not, use defaults and do not ask: role inferred from shared preferences (otherwise "developer"), review focus balanced, verbosity moderate, skip tolerance balanced.

Only when the user passes `--calibrate`, ask these four questions (one `AskUserQuestion` call) and save the answers to `.claude/skill-context/human-review-guide.md`:

1. **Role/expertise** — Backend, Frontend, Full-stack, DevOps/Infra, PM/Non-technical reviewer, Other
2. **Review focus** — Correctness & edge cases, Architecture & design decisions, Security implications, Maintainability & tech debt
3. **Verbosity** — Concise (just pointers), Moderate (brief explanations), Detailed (full rationale)
4. **Skip tolerance** — Conservative (surface more), Balanced, Aggressive (only critical decisions)

```markdown
# Human Review Guide Preferences

Last updated: {DATE}

## Calibration
- **Role:** {answer}
- **Review focus:** {answer}
- **Verbosity:** {concise | moderate | detailed}
- **Skip tolerance:** {conservative | balanced | aggressive}
```

### 0.3 Resolve `--with-review`

If `--with-review` is specified, look in the current conversation for `/codereview` output (the severity-grouped findings report). If found, extract file paths, line ranges, severities, and descriptions for Phase 2. If not found, tell the user to run `/codereview` first or drop `--with-review`, then stop.

### 0.4 Determine Mode

| Target | Mode |
|---|---|
| Branch diff (default) or `PR#<number>` | `code-diff` |
| `<path>` to a code file | `code-diff` |
| `<path>` to a non-code file | `artifact` (chunk by heading section) |
| `<path>` to a directory | `mixed` (code files → `code-diff`, non-code → `artifact`) |

Pass the mode to the agent prompts. For code, chunk at the size where one chunk holds one idea: a whole file when the file makes one change, single hunks when it makes several.

---

## Phase 1: Input Resolution & Triage

### 1.1 Input Resolution

- **`code-diff`:** detect the base branch and gather changed files per `shared/review-common.md` § Base Branch Detection and § File Gathering. Capture the diff and per-file stats (`gh pr diff <number>` in PR mode). Count files and lines changed for the output format decision in Phase 3.
- **`artifact`:** read the target and split it by heading structure (H1, H2, H3).
- **`mixed`:** classify each file as code or non-code by extension. For code, use its diff if it has changes, otherwise its full content. For non-code, split by headings.

### 1.2 Triage — Classification Pass

Dispatch a **single subagent** to classify every chunk, using `references/agent-prompts.md` § Triage Agent. Give it the mode, the content, the calibration profile, and file stats.

For same-platform subagents, do not pass a model or reasoning-effort override. Let every subagent inherit the parent model and reasoning effort unless the user explicitly asks for an override.

**Classification tiers:**

| Tier | Label | Meaning | Reviewer action |
|------|-------|---------|-----------------|
| 1 | `DECIDE` | Contains a decision requiring human judgment | Read carefully, form an opinion |
| 2 | `READ` | Non-trivial logic worth understanding | Read to build mental model |
| 3 | `SKIM` | Straightforward, follows from decisions elsewhere | Glance for context |
| 4 | `SKIP` | Mechanical/boilerplate | Safe to ignore |

For large diffs (more than about 100 files), send the file list and stats **plus the resolved base ref** (or the `gh pr diff` command in PR mode), and tell the agent to run `git diff <base>...HEAD -- <file>` itself for any file it needs. A dispatched agent cannot ask the host for more content mid-run.

### 1.3 Validate Triage Output

Every chunk needs exactly one tier and a reason; re-ask the agent for any it missed. If nothing is `DECIDE` or `READ`, say the change is mechanical and show the skip summary — do not invent decisions or run Phase 2.

---

## Phase 2: Deep Analysis

Runs only on `DECIDE` and `READ` chunks. Other chunks pass to Phase 3 with their triage label.

Dispatch a **single subagent** that processes the `DECIDE` and `READ` chunks **in order, one after another** — chunks often relate, and later analysis benefits from earlier context. Use `references/agent-prompts.md` § Deep Analysis Agent. Give it the mode, the triage output, the chunk content with surrounding context (the file around the hunk, or the parent section), the calibration profile, and any `/codereview` findings.

It returns a decision block per `DECIDE` chunk and a comprehension block per `READ` chunk.

**`--with-review` enrichment:** match findings to chunks by file and line range. In a `DECIDE` chunk, note the finding and whether its fix is mechanical or a judgment call. In a `READ` chunk, list it as a gotcha. Never list findings as standalone items.

**If the agent fails,** fall back to a triage-only guide (tier and reason per chunk), say deep analysis was unavailable, and offer a retry. If it skips chunks, mark those chunks as triage-only in the guide.

---

## Phase 3: Guide Synthesis & Output

Assemble the guide from the agent outputs, without re-reading raw content. Follow `references/output-formats.md`.

### 3.1 Determine Reading Order

Order entries by **decision dependency**, not file path:

1. Use the `Related to` links from triage.
2. Topologically sort `DECIDE` chunks: foundational decisions first, dependent decisions after.
3. Place each `READ` chunk after its related `DECIDE` chunk.
4. Group `SKIM` chunks at the end under "For Context".
5. Collapse all `SKIP` chunks into one summary line.

If there are no links, order `DECIDE` chunks by impact (larger blast radius first), then `READ` chunks by file order.

### 3.2 Build the Guide

- **Executive summary:** what the change does, how many decisions need human input, and estimated review time: `(DECIDE_count × 3) + (READ_count × 1)` minutes, rounded to the nearest 5.
- **Decision map:** a table of all `DECIDE` chunks in reading order, so the reviewer sees what is coming.
- **Review checklist:** concrete yes/no items derived from each `DECIDE` chunk's "Ask yourself" questions.
- **Open questions:** decisions whose reason is unclear, chunks with too little context to judge consequences, and contradictions between chunks. Omit the section if there are none.

Use `file:line` references throughout.

### 3.3 Render Output

Choose terminal markdown for small changes and an HTML report for large ones — thresholds in `references/output-formats.md` § Output Size Thresholds.

**HTML report:**

1. Write the guide as markdown to `docs/review-guides/YYYYMMDD-HHMMSS-<slug>.md` (create the folder if needed), with YAML front-matter per `shared/html-reports.md`. The renderer writes the `.html` next to it.
2. Call the HTML renderer. **Resolve `scripts/html_render.py` to its absolute path under the plugin root (two levels above this SKILL.md) before running** — the command runs in the user's project cwd, which does not contain the plugin's `scripts/` folder (use `python3` where present, falling back to `python` on Windows):

````bash
python scripts/html_render.py <report_path> --profile analytical
````

3. On success, give the absolute path of the HTML file. On failure (for example, pandoc is missing), give the absolute path of the markdown file and a one-line warning that HTML was skipped.
