---
name: interaction-review
description: "Use when the user invokes $interaction-review to grade the human-AI collaboration quality of past Claude Code sessions and produce a coaching report."
---

# Interaction Review Skill

Analyze Claude Code conversation transcripts (JSONL files) to evaluate how effectively the user collaborates with the AI agent. Dispatch 5 parallel analysis subagents - each evaluating a specific dimension of interaction quality (prompt craft, workflow efficiency, agentic leverage, error recovery, context & instruction) - collect their scored findings, synthesize a weighted composite report, run a coach re-review for quality and actionability, and produce dual-format output (HTML + markdown) with a prioritized improvement roadmap.

The report is a self-improvement tool, not an audit. Tone is coaching, not punitive.

## Out of Scope

This skill MUST NOT:
- Analyze code quality. Code correctness, architecture, and style are the domain of `$codereview`, `$quick-review`, and `$codebase-audit`.
- Produce project retrospectives. Process improvement and team reflection are the domain of `$retrospective`.
- Grade model quality. The user cannot control which model they get - only how they interact with it.
- Apply changes automatically. The report contains suggestions; the user decides what to act on.
- Coach in real-time. Analysis is post-hoc, applied to completed session transcripts.
- Rewrite findings during Phase 3.5 for wording alone (see Phase 3.5).
- Silently modify findings in Phase 3.5 (see Phase 3.5).

## Reference Files

| File | Contents | When to read |
|---|---|---|
| `references/agent-prompts.md` | Guiding principles, all 5 lens agent prompts, coach re-reviewer prompt | Before dispatching agents in Phase 2 or Phase 3.5 |
| `references/output-formats.md` | Templates for subagent output and final report | Before writing output in Phase 3 and Phase 4 |

## Invocation

Parse the user's `$interaction-review` arguments:

| Invocation | Mode | Description |
|---|---|---|
| `$interaction-review` | Default | Analyze sessions since the last report. If no prior report, analyze all. |
| `$interaction-review session <id>` | Single session | Deep-dive on one session. `<id>` is the JSONL filename stem (session UUID). |
| `$interaction-review since YYYY-MM-DD` | Date range | Analyze sessions from a specific date forward (ISO8601 date). |
| `$interaction-review trend` | Trend | Multi-session aggregate with score progression across all prior reports. |

If the invocation is ambiguous or unrecognizable, ask the user to clarify before proceeding.

---

## Phase 0: Setup

### 0.1 Load User Preferences

Read `../shared/skill-context.md` for the full protocol (resolve `../shared/...` against the collection root (one level above this SKILL.md) - never the project's working directory). In brief:

1. Read `.codex/skill-context/preferences.md` - if missing, invoke `$preferences` (streamlined).
2. Read `.codex/skill-context/interaction-review.md` (if it exists) for skill-specific preferences.

**How preferences shape this skill:**

| Preference | Effect on Interaction Review |
|---|---|
| Detail level: concise | Shorter findings, focus on top issues, tighter Coach's Note |
| Detail level: detailed | Include more transcript context, richer analysis per finding |
| Assumed knowledge: beginner | Explain why patterns matter, provide examples of better prompts |
| Assumed knowledge: expert | Focus on non-obvious patterns, skip basic prompt advice |
| Skill-specific: lens weights | Override default 30/25/20/15/10 weights |
| Skill-specific: scoring strictness | Lenient / standard / strict calibration |
| Skill-specific: focus areas | Prioritize specific lenses in the report |

### 0.2 Locate Previous Reports

1. Check for `docs/interaction-review/` directory.
2. If it exists, list all `*-interaction-review.md` files, sorted by date (newest first).
3. Read the most recent report for continuity: extract per-lens scores, "Your Next Steps" items, and recurring pattern flags.
4. If no previous reports exist, note this is the baseline report.

---

## Phase 1: Session Discovery & Selection

### 1.1 Resolve Session Directory

1. Determine the project directory slug: take the current working directory path and replace every non-alphanumeric character (`:`, `\`, `/`) with a single `-` (e.g., `C:\Users\joesy\Projects\my-project` becomes `C--Users-joesy-Projects-my-project` - the double dash after the drive letter is `:` and `\` each becoming one `-`).
2. Session files are at: `~/.claude/projects/<project-slug>/*.jsonl`

### 1.2 List and Filter Sessions

1. List all `.jsonl` files in the session directory.
2. For each file, scan entries from the top until the first one containing a `timestamp` field, and use that - the leading entries (`mode`, `last-prompt`, `file-history-snapshot`) carry no top-level `timestamp`.
3. Apply the filter based on invocation mode:
   - **Default:** Sessions with timestamp newer than the most recent report's `generated_at`. If no prior report, include all sessions.
   - **Single session:** Match the session ID (filename stem) against the `<id>` argument.
   - **Date range:** Sessions with first timestamp >= the specified date.
   - **Trend:** All sessions (no filtering - trend mode differs in report generation, not input).

### 1.3 Validate and Confirm

- If no sessions match the filter: report "No sessions found in the specified range. Try a broader date range or check `~/.claude/projects/`." and exit.
- Otherwise, display to the user:
  - Number of sessions found
  - Date range (earliest to latest)
  - Invocation mode being used
- Ask the user to confirm before proceeding to analysis.

---

## Phase 2: Parallel Analysis - 5 Subagents

**MUST dispatch all 5 subagents simultaneously** - all 5 in a single response using the Codex agent workflow. Each uses `model: "opus"`. Read `references/agent-prompts.md` for full prompt templates and guiding principles.

### Agent Roster

| # | Lens | Principles File | Weight |
|---|---|---|---|
| 1 | Prompt Craft | `principles/prompt-craft.md` | 30% |
| 2 | Workflow Efficiency | `principles/workflow-efficiency.md` | 25% |
| 3 | Agentic Leverage | `principles/agentic-leverage.md` | 20% |
| 4 | Error Recovery & Adaptation | `principles/error-recovery.md` | 15% |
| 5 | Context & Instruction Quality | `principles/context-instruction.md` | 10% |

### Agent Dispatch

Each agent receives in its prompt:
1. The guiding principles block from `references/agent-prompts.md`
2. The session file list (paths to the filtered JSONL files from Phase 1)
3. The agent's specific prompt template from `references/agent-prompts.md`
4. Instructions to read its principles file
5. The previous report's findings for its lens (if a prior report exists)
6. User preferences (relevant subset only - detail level, knowledge assumptions)

### Agent Returns

Each agent returns structured markdown per `references/output-formats.md`:
- Numeric score (0-100) with 2-3 sentence justification
- 3-8 findings with transcript references
- 2-3 improvement suggestions
- Delta notes vs. previous report

### Error Handling

- **1-2 agents fail:** Report on available lenses. Note missing ones in the report header: "Error Recovery lens unavailable - agent failed. Other 4 lenses analyzed." Offer retry.
- **3+ agents fail:** "Analysis failed - too many lenses unavailable for a meaningful report. Retry?"

---

## Phase 3: Synthesis

After all agents return (or after handling partial failures):

### 3.1 Compute Scores

1. Collect scores from all successful agents.
2. Compute the weighted composite score using configured weights (default: 30/25/20/15/10).
3. Map all scores (per-lens and composite) to letter grades using the grade scale in `references/output-formats.md`.
4. If a lens is missing (agent failure), exclude it from the weighted average and note the gap.

### 3.2 Deduplicate Findings

Scan all findings across lenses for overlaps:
- Same transcript reference (session + turn range) flagged by multiple lenses
- Keep the richer finding (more specific analysis, better improvement suggestion)
- Cross-reference the other: "Also flagged by [other lens]"

### 3.3 Compare to Previous Report

If a previous report exists:
1. Compute per-lens score deltas (current - previous).
2. Check each previous "Your Next Steps" item:
   - Look for evidence in the new transcripts that the user acted on it
   - Mark as: addressed (with evidence), partially addressed, or not addressed
3. Identify recurring patterns: findings that appeared in the previous report AND reappear now
   - Flag with escalated emphasis: "Recurring pattern (2nd consecutive report)"

### 3.4 Build Improvement Roadmap

1. Collect all improvement suggestions from all 5 agents (10-15 total).
2. For each, estimate: score impact (how many points it could add), frequency (how often the pattern occurred), and effort (quick win / moderate / habit change).
3. Rank by expected impact relative to effort - quick wins (high impact, low effort) first.
4. Select the top 5 as the "Your Next Steps" roadmap.
5. For each selected item, flesh out: what to change, why it matters (cite specific findings), expected impact (estimated score improvement), effort level, and priority rank.

### 3.5 Assemble Draft Report

Build the draft report following the section order in `references/output-formats.md`:
1. Header & Meta
2. Overall Scorecard (with trend deltas if applicable)
3. Session Summary
4. Per-Lens Deep Dive (x5, or fewer if agents failed)
5. Your Next Steps (max 5)
6. Progress Tracker (if prior reports exist)

---

## Phase 3.5: Coach Re-Review

One Agent call, `model: "opus"`. Sequential - runs after Phase 3 produces the draft report. Read `references/agent-prompts.md` Section Phase 3.5 for the full prompt.

### Inputs

1. The draft report from Phase 3 (complete synthesized report)
2. The session file list (so the coach can spot-check claims against actual transcripts)
3. The previous report (if any)

### Coach Authorities

| # | Authority | Effect |
|---|---|---|
| 1 | Adjust scores | Within +/-10 points per lens, with stated reason |
| 2 | Rewrite improvement items | More specific, actionable, or correctly prioritized |
| 3 | Reorder priorities | If a quick win is buried below a harder change |
| 4 | Flag missed patterns | Observations the 5 agents didn't catch |
| 5 | Validate continuity | Prior report progress acknowledged, recurring issues flagged |
| 6 | Set the tone | Coaching-oriented, encouraging, not punitive |

The coach may only modify a finding when judgment changes the assessment - never for wording alone. Every coach change MUST carry a reason citation as `[Coach: reason]`.

### Coach Output

- Score adjustments (if any) with `[Coach: reason]` annotations
- Improvement item revisions (if any)
- Coach's Note (2-4 sentences - the single most important takeaway)
- Missed patterns (if any)

### Applying Coach Feedback

1. Apply any score adjustments to the scorecard (recalculate composite).
2. Replace revised improvement items.
3. Insert Coach's Note as section 6 (Coach's Note), immediately before the Progress Tracker - this shifts the draft's Progress Tracker from #6 to #7, matching the Section Order in `references/output-formats.md`.
4. Add missed patterns as findings in the appropriate lens section, tagged `[Added by Coach]`.

### Error Handling

If the coach re-review fails: fall back to the Phase 3 draft report. Header note: "Coach re-review: unavailable ([reason])". Offer retry.

---

## Phase 4: Report Generation

### 4.1 Write Markdown Report

1. Ensure `docs/interaction-review/` directory exists (create if needed).
2. Write the final report to `docs/interaction-review/YYYYMMDD-interaction-review.md` (using today's date).
3. Include YAML front-matter per `references/output-formats.md`.

### 4.2 Render HTML Companion

Call the HTML renderer (best-effort - markdown is always saved regardless). **Resolve `../scripts/html_render.py` to its absolute path under the collection root (one level above this SKILL.md) before running** - the command executes in the user's project cwd, which does not contain the plugin's `../scripts/` folder (invoke with `python3` where present, falling back to `python` on Windows):

```
python ../scripts/html_render.py docs/interaction-review/YYYYMMDD-interaction-review.md --profile analytical
```

If the renderer fails, warn the user but do not fail the skill.

### 4.3 Surface Report

1. Send the HTML file to the user using `SendUserFile` (if HTML was generated successfully).
2. If HTML failed, send the markdown file instead.
3. If `SendUserFile` is unavailable in this harness, print the absolute report path instead.
4. Display a brief summary: overall score/grade, biggest improvement, and Coach's Note.

### 4.4 Devlog Scrap (Optional)

Offer: "Want me to capture a devlog scrap from this review? (`$devlog scrap --from-context interaction-review findings`)"

Skip silently if the user declines or the devlog skill is unavailable.

---

## Context Management

| Phase | Budget / Strategy |
|---|---|
| Phase 2 agents | ~4,000 lines each. Prioritize breadth across sessions. |
| Phase 3 synthesis | Operates on agent outputs only - no raw transcript re-reading. |
| Phase 3.5 coach | Receives draft report + session list. Spot-checks transcripts selectively. |
| Phase 4 output | Generates from synthesized data. No upstream re-reading. |
