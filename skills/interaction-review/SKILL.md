---
name: interaction-review
description: "Use when the user invokes /interaction-review to grade the human-AI collaboration quality of past Claude Code or Codex sessions and produce a coaching report."
---

# Interaction Review Skill

Grade how well the user collaborates with an AI coding agent, from past session logs (JSONL files from Claude Code or Codex). Five lens agents score one dimension each in parallel. You combine their scores into a weighted report, a coach agent re-reviews it, and you save it as markdown plus an HTML companion with a short, ranked list of next steps.

The report is a self-improvement tool, not an audit. The tone is coaching, not punitive.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md` (resolve against the plugin root — two levels above this SKILL.md — never the project's working directory).

## Out of Scope

This skill does not cover:
- Code quality. That belongs to `/codereview`, `/quick-review`, and `/codebase-audit`.
- Project retrospectives. That belongs to `/retrospective`.
- Grading model quality. The user cannot control which model they get — only how they work with it.
- Applying changes. The report suggests; the user decides.
- Real-time coaching. The review runs after the sessions are finished.

## Reference Files

| File | Contents | When to read |
|---|---|---|
| `references/agent-prompts.md` | Everything the lens agents and the coach receive | Before Phase 2 and Phase 3.5 |
| `references/output-formats.md` | Final report format, rubric version, grade scale | Before Phase 3 and Phase 4 |

## Invocation

| Invocation | Mode | Description |
|---|---|---|
| `/interaction-review` | Default | Sessions since the last report's `generated_at`. If there is no prior report, all sessions. |
| `/interaction-review session <id>` | Single session | Deep-dive on one session. `<id>` is the session ID (see 1.1). |
| `/interaction-review since YYYY-MM-DD` | Date range | Sessions that start on or after this date. |
| `/interaction-review trend` | Trend | All sessions, with score progression across all prior reports. Marks every rubric version change (see 3.3). |

If the invocation is unclear, ask the user before you continue.

---

## Phase 0: Setup

### 0.1 Load Preferences (silent)

Never interview the user. Read these files if they exist, and use defaults for anything missing:

1. `.claude/skill-context/preferences.md` — shared preferences (detail level, assumed knowledge).
2. `.claude/skill-context/interaction-review.md` — lens weights, scoring strictness (lenient / standard / strict), focus areas.

Defaults: balanced detail, intermediate knowledge, weights 30/25/20/15/10, standard strictness. Shape the report to them: a beginner gets example prompts, an expert only non-obvious patterns, and focus areas get more space. Pass each lens agent only the preferences that affect it.

### 0.2 Locate Previous Reports

List `docs/interaction-review/*-interaction-review.md`, newest first. From the newest report, take its rubric version (`rubric_version` in the front-matter; a report without it is v1), per-lens scores, "Your Next Steps" items, and recurring-pattern flags. In trend mode, read the rubric version of every prior report. With no prior report, this report is the baseline.

---

## Phase 1: Session Discovery

### 1.1 Find the Session Files

Read the logs of the host you run in: Claude Code logs in Claude Code, Codex logs in Codex. If the user asks for both, review both and label every session with its host. For each session, record its absolute path, host, session ID, and start time; the agents need all four.

**Claude Code**
1. Project folder name: take the current working directory and replace every non-alphanumeric character (`:`, `\`, `/`) with a single `-`. For example, `C:\Users\joesy\Projects\my-project` becomes `C--Users-joesy-Projects-my-project` (the double dash is `:` and `\` each becoming one `-`).
2. Session files: `~/.claude/projects/<project-folder>/*.jsonl`. The session ID is the filename stem.
3. Session start: the first line that has a top-level `timestamp`. The leading `mode`, `last-prompt`, and `file-history-snapshot` lines have none.

**Codex**
1. Session files: `~/.codex/sessions/YYYY/MM/DD/rollout-<start-time>-<session-id>.jsonl`. The date folders are the session start date. Older sessions may be compressed in `~/.codex/archived_sessions/*.jsonl.zst` (read with `zstd -dc`).
2. The first line of each file has `type: "session_meta"`. Keep the file only if its `payload.cwd` equals the current working directory. Skip files whose `payload.source` is an object with a `subagent` key — those are subagent runs, not the user's sessions.
3. The session ID is `payload.id` (also the UUID at the end of the filename). The session start is `payload.timestamp`.
4. `~/.codex/history.jsonl` lists user prompts across all projects. The review does not need it; use the session files.

### 1.2 Filter and Confirm

Filter by mode: default keeps sessions that start after the newest report's `generated_at`; single session matches the ID; date range keeps sessions that start on or after the date; trend keeps all.

If nothing matches, tell the user, suggest a wider range or checking the host's session folder, and stop. Otherwise show the session count, date range, and mode, and wait for the user to confirm.

---

## Phase 2: Parallel Analysis

Run the five lenses in parallel as subagents. Build each prompt from `references/agent-prompts.md`: the guiding principles, the session-log guide, the lens prompt template filled with that lens's details, the session list from 1.1, the previous report's findings for that lens, and the relevant preferences.

For same-platform subagents, do not pass a model or reasoning-effort override. Let every subagent inherit the parent model and reasoning effort unless the user explicitly asks for an override.

| # | Lens | Principles File | Weight |
|---|---|---|---|
| 1 | Prompt Craft | `principles/prompt-craft.md` | 30% |
| 2 | Workflow Efficiency | `principles/workflow-efficiency.md` | 25% |
| 3 | Agentic Leverage | `principles/agentic-leverage.md` | 20% |
| 4 | Error Recovery & Adaptation | `principles/error-recovery.md` | 15% |
| 5 | Context & Instruction Quality | `principles/context-instruction.md` | 10% |

Each behavior is scored in one lens only. Each principles file names the behaviors other lenses own.

If one or two agents fail, report on the lenses you have, name the missing ones in the report header, and offer a retry. If three or more fail, do not write a report; tell the user and offer a retry.

---

## Phase 3: Synthesis

Work from the agents' outputs. Do not re-read the transcripts.

### 3.1 Scores

Compute the weighted composite with the configured weights. Leave a missing lens out of the average and note the gap. Map every score to a letter grade with the grade scale in `references/output-formats.md`.

### 3.2 Duplicates

When several lenses flag the same session and turn range, keep the richer finding and add "Also flagged by [lens]" to it.

### 3.3 Compare to the Previous Report

- Per-lens deltas. The current rubric is v2 (see `references/output-formats.md` § Rubric Version). If the previous report uses another rubric version, mark the change as a rubric change, not a gain or loss, as that section describes. In trend mode, mark the point where the version changes in the Progress Tracker.
- For each previous "Your Next Steps" item, look for evidence in the new sessions and mark it addressed (with evidence), partially addressed, or not addressed.
- Flag findings that also appeared in the previous report as recurring, with escalated emphasis (for example, "Recurring pattern (2nd consecutive report)").

### 3.4 Your Next Steps

Collect the agents' improvement suggestions. Estimate each one's score impact, how often the pattern occurred, and its effort (quick win / moderate / habit change). Rank by impact over effort and show at most 5. For each item, say what to change, why (cite findings), the expected impact, and the effort.

### 3.5 Draft Report

Assemble the draft in the section order from `references/output-formats.md`, leaving out the Coach's Note for now.

---

## Phase 3.5: Coach Re-Review

Run one coach subagent after the draft is ready, with the prompt in `references/agent-prompts.md` § Coach Re-Reviewer. Give it the draft report, the session list with the session-log guide (so it can spot-check claims), and the previous report if there is one.

Apply the coach's changes. Recompute the composite after score adjustments. Put the Coach's Note in its section, just before the Progress Tracker. Add missed patterns as findings in the matching lens section, tagged `[Added by Coach]`. Drop any change that breaks the limits in the coach prompt: more than ±10 points per lens, no `[Coach: reason]` tag, or a rewrite for wording alone.

If the coach fails, keep the Phase 3 draft, note in the header that the coach re-review was unavailable and why, and offer a retry.

---

## Phase 4: Report

1. Write the report to `docs/interaction-review/YYYYMMDD-interaction-review.md` (today's date), with the front-matter from `references/output-formats.md`. Create the folder if needed.
2. Render the HTML companion. This is best-effort; the markdown is always saved. Resolve `scripts/html_render.py` to its absolute path under the plugin root (two levels above this SKILL.md) first, because the command runs in the user's project directory. Use `python3`, or `python` on Windows. If rendering fails, warn the user and continue.

   ```
   python scripts/html_render.py docs/interaction-review/YYYYMMDD-interaction-review.md --profile analytical
   ```

3. Give the user the absolute paths of the HTML report (if rendered) and the markdown report, the overall score and grade, the biggest improvement, and the Coach's Note.
4. If the devlog skill is available, offer to capture a devlog scrap from the findings. Skip silently if the user declines.
