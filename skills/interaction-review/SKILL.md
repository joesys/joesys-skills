---
name: interaction-review
description: "Use when the user invokes /interaction-review to grade the human-AI collaboration quality of past Claude Code or Codex sessions and produce a coaching report."
---

# Interaction Review Skill

Analyze AI coding-session transcripts (JSONL files from Claude Code or Codex) to evaluate how effectively the user collaborates with the AI agent. Dispatch 5 parallel analysis subagents — each evaluating a specific dimension of interaction quality (prompt craft, workflow efficiency, agentic leverage, error recovery, context & instruction) — collect their scored findings, synthesize a weighted composite report, run a coach re-review for quality and actionability, and produce dual-format output (HTML + markdown) with a prioritized improvement roadmap.

The report is a self-improvement tool, not an audit. Tone is coaching, not punitive.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md` (resolve against the plugin root — two levels above this SKILL.md — never the project's working directory).

## Out of Scope

This skill MUST NOT:
- Analyze code quality. Code correctness, architecture, and style are the domain of `/codereview`, `/quick-review`, and `/codebase-audit`.
- Produce project retrospectives. Process improvement and team reflection are the domain of `/retrospective`.
- Grade model quality. The user cannot control which model they get — only how they interact with it.
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

Parse the user's `/interaction-review` arguments:

| Invocation | Mode | Description |
|---|---|---|
| `/interaction-review` | Default | Analyze sessions since the last report. If no prior report, analyze all. |
| `/interaction-review session <id>` | Single session | Deep-dive on one session. `<id>` is the session ID (see 1.1). |
| `/interaction-review since YYYY-MM-DD` | Date range | Analyze sessions from a specific date forward (ISO8601 date). |
| `/interaction-review trend` | Trend | Multi-session aggregate with score progression across all prior reports. Marks every rubric version change (see 3.3). |

If the invocation is ambiguous or unrecognizable, ask the user to clarify before proceeding.

---

## Phase 0: Setup

### 0.1 Load Preferences (silent)

Never interview the user about preferences. Read these files if they exist; use defaults for anything missing:

1. `.claude/skill-context/preferences.md` — shared preferences (detail level, assumed knowledge).
2. `.claude/skill-context/interaction-review.md` — skill-specific preferences (lens weights, scoring strictness, focus areas).

Defaults: balanced detail, intermediate knowledge, weights 30/25/20/15/10, standard strictness.

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
3. Read the most recent report for continuity: extract the rubric version (`rubric_version` in the front-matter; a report without it is v1), per-lens scores, "Your Next Steps" items, and recurring pattern flags. In trend mode, read the rubric version of every prior report.
4. If no previous reports exist, note this is the baseline report.

---

## Phase 1: Session Discovery & Selection

### 1.1 Resolve Session Files

Read the session logs of the host you are running in: Claude Code logs when you run in Claude Code, Codex logs when you run in Codex. If the user asks for both, review both and label every session with its host.

**Claude Code**
1. Project directory slug: take the current working directory path and replace every non-alphanumeric character (`:`, `\`, `/`) with a single `-` (e.g., `C:\Users\joesy\Projects\my-project` becomes `C--Users-joesy-Projects-my-project` — the double dash after the drive letter is `:` and `\` each becoming one `-`).
2. Session files: `~/.claude/projects/<project-slug>/*.jsonl`. The session ID is the filename stem.
3. Session start: scan lines from the top until the first one with a top-level `timestamp`, and use that. The leading lines (`mode`, `last-prompt`, `file-history-snapshot`) carry no `timestamp`.

**Codex**
1. Session files: `~/.codex/sessions/YYYY/MM/DD/rollout-<start-time>-<session-id>.jsonl`. The date folders are the session start date. Compressed older sessions may be in `~/.codex/archived_sessions/*.jsonl.zst` (read with `zstd -dc`).
2. The first line of each file is `type: "session_meta"`. Keep the file only if its `payload.cwd` equals the current working directory. Skip files whose `payload.source` is an object with a `subagent` key — those are subagent runs, not the user's sessions.
3. The session ID is `payload.id` (also the UUID at the end of the filename). The session start is `payload.timestamp`.
4. `~/.codex/history.jsonl` lists every user prompt across all projects (`session_id`, `ts` in Unix seconds, `text`). It is not needed for the review; use the rollout files.

### 1.2 List and Filter Sessions

1. List this project's session files for the host (see 1.1) and read each session's start time.
2. Apply the filter based on invocation mode:
   - **Default:** Sessions with timestamp newer than the most recent report's `generated_at`. If no prior report, include all sessions.
   - **Single session:** Match the session ID against the `<id>` argument.
   - **Date range:** Sessions with first timestamp >= the specified date.
   - **Trend:** All sessions (no filtering — trend mode differs in report generation, not input).

### 1.3 Validate and Confirm

- If no sessions match the filter: report "No sessions found in the specified range. Try a broader date range or check the session folder (`~/.claude/projects/` for Claude Code, `~/.codex/sessions/` for Codex)." and exit.
- Otherwise, display to the user:
  - Number of sessions found
  - Date range (earliest to latest)
  - Invocation mode being used
- Ask the user to confirm before proceeding to analysis.

---

## Phase 2: Parallel Analysis — 5 Subagents

**MUST dispatch all 5 subagents simultaneously** — all 5 in a single response using the Agent tool. Read `references/agent-prompts.md` for full prompt templates and guiding principles.

For same-platform subagents, do not pass a model or reasoning-effort override. Let every subagent inherit the parent model and reasoning effort unless the user explicitly asks for an override.

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
2. The session file list (paths to the filtered JSONL files from Phase 1), the log host (Claude Code or Codex), and the matching log format from the Session Resolution section of `references/agent-prompts.md`
3. The agent's specific prompt template from `references/agent-prompts.md`
4. Instructions to read its principles file
5. The previous report's findings for its lens (if a prior report exists)
6. User preferences (relevant subset only — detail level, knowledge assumptions)

### Agent Returns

Each agent returns structured markdown per `references/output-formats.md`:
- Numeric score (0–100) with 2–3 sentence justification
- 3–8 findings with transcript references
- 2–3 improvement suggestions
- Delta notes vs. previous report

### Error Handling

- **1–2 agents fail:** Report on available lenses. Note missing ones in the report header: "Error Recovery lens unavailable — agent failed. Other 4 lenses analyzed." Offer retry.
- **3+ agents fail:** "Analysis failed — too many lenses unavailable for a meaningful report. Retry?"

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
1. Compute per-lens score deltas (current - previous). The current rubric is v2 (see `references/output-formats.md` § Rubric Version). If the previous report uses another rubric version, do not show the delta as a gain or loss. Mark it as a rubric change, as that section describes, so a v1→v2 jump is not read as real improvement or decline. In trend mode, mark the point where the version changes in the Progress Tracker.
2. Check each previous "Your Next Steps" item:
   - Look for evidence in the new transcripts that the user acted on it
   - Mark as: addressed (with evidence), partially addressed, or not addressed
3. Identify recurring patterns: findings that appeared in the previous report AND reappear now
   - Flag with escalated emphasis: "Recurring pattern (2nd consecutive report)"

### 3.4 Build Improvement Roadmap

1. Collect all improvement suggestions from all 5 agents (10–15 total).
2. For each, estimate: score impact (how many points it could add), frequency (how often the pattern occurred), and effort (quick win / moderate / habit change).
3. Rank by expected impact relative to effort — quick wins (high impact, low effort) first.
4. Select the top 5 as the "Your Next Steps" roadmap.
5. For each selected item, flesh out: what to change, why it matters (cite specific findings), expected impact (estimated score improvement), effort level, and priority rank.

### 3.5 Assemble Draft Report

Build the draft report following the section order in `references/output-formats.md`:
1. Header & Meta
2. Overall Scorecard (with trend deltas if applicable)
3. Session Summary
4. Per-Lens Deep Dive (×5, or fewer if agents failed)
5. Your Next Steps (max 5)
6. Progress Tracker (if prior reports exist)

---

## Phase 3.5: Coach Re-Review

One Agent call. Sequential — runs after Phase 3 produces the draft report. Read `references/agent-prompts.md` § Phase 3.5 for the full prompt.

### Inputs

1. The draft report from Phase 3 (complete synthesized report)
2. The session file list and the matching log format (so the coach can spot-check claims against actual transcripts)
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

The coach may only modify a finding when judgment changes the assessment — never for wording alone. Every coach change MUST carry a reason citation as `[Coach: reason]`.

### Coach Output

- Score adjustments (if any) with `[Coach: reason]` annotations
- Improvement item revisions (if any)
- Coach's Note (2–4 sentences — the single most important takeaway)
- Missed patterns (if any)

### Applying Coach Feedback

1. Apply any score adjustments to the scorecard (recalculate composite).
2. Replace revised improvement items.
3. Insert Coach's Note as section 6 (Coach's Note), immediately before the Progress Tracker — this shifts the draft's Progress Tracker from #6 to #7, matching the Section Order in `references/output-formats.md`.
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

Call the HTML renderer (best-effort — markdown is always saved regardless). **Resolve `scripts/html_render.py` to its absolute path under the plugin root (two levels above this SKILL.md) before running** — the command executes in the user's project cwd, which does not contain the plugin's `scripts/` folder (invoke with `python3` where present, falling back to `python` on Windows):

```
python scripts/html_render.py docs/interaction-review/YYYYMMDD-interaction-review.md --profile analytical
```

If the renderer fails, warn the user but do not fail the skill.

### 4.3 Surface Report

1. Tell the user the absolute path of the saved HTML report (if HTML was generated successfully) and of the markdown report.
2. Display a brief summary: overall score/grade, biggest improvement, and Coach's Note.

### 4.4 Devlog Scrap (Optional)

Offer: "Want me to capture a devlog scrap from this review? (`/devlog scrap --from-context interaction-review findings`)"

Skip silently if the user declines or the devlog skill is unavailable.

---

## Context Management

| Phase | Budget / Strategy |
|---|---|
| Phase 2 agents | ~4,000 lines each. Prioritize breadth across sessions. |
| Phase 3 synthesis | Operates on agent outputs only — no raw transcript re-reading. |
| Phase 3.5 coach | Receives draft report + session list. Spot-checks transcripts selectively. |
| Phase 4 output | Generates from synthesized data. No upstream re-reading. |
