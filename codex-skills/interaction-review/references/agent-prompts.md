# Interaction Review — Agent Prompts

Prompts for the five lens agents (Phase 2) and the coach re-reviewer (Phase 3.5).

Subagents share no context with the host. They see only the prompt you send. So before you dispatch, fill every placeholder and paste in every block the prompt names. Replace `<PRINCIPLES_PATH>` with the **absolute path** to the lens's principles file, resolved against this skill's directory in the plugin install — never against the project's working directory. Subagents start in the project directory and cannot find plugin files by relative path.

## Table of Contents

- [Guiding Principles](#guiding-principles)
- [Session Logs](#session-logs)
- [Lens Prompt Template](#lens-prompt-template)
- [Lens Details](#lens-details)
- [Coach Re-Reviewer](#coach-re-reviewer)

---

## Guiding Principles

Paste into every lens prompt as `<GUIDING_PRINCIPLES>`:

1. **Evidence over impression.** Every finding cites a session ID and turn range. No vague claims like "prompts were often unclear."
2. **Quantify when possible.** "4 of 7 prompts needed clarification" beats "prompts often needed clarification."
3. **Both sides matter.** A bad exchange may be the user's fault, the agent's fault, or a mismatch. Say which. Do not grade the model's quality — the user cannot choose how good the model is, only how they work with it.
4. **Coaching tone.** Frame findings as chances to grow, not failures.
5. **Flag uncertainty.** If a pattern may be intentional, say so.
6. **Compare to the previous report** when its findings are provided: what improved, regressed, or stayed the same.
7. **Write for humans.** The reader may use English as a second language. Use short sentences and everyday words, explain jargon on first use, and state the point first. Simplify the language, never the facts.

## Session Logs

Paste into every lens prompt and the coach prompt as `<SESSION_LOGS>`. Include the part for each host that appears in the session list.

```
Each line of a session file (JSONL) is one JSON object. Read only the person's
messages and the assistant's messages. Skip tool calls, tool output, reasoning,
and bookkeeping lines: they are bulk data that hides the conversation. Tool
calls still count as evidence for the Agentic Leverage and Workflow Efficiency
lenses: count and sample them, but do not read their full output.

Cover every session in the list. Read in full the places where the person
corrects the agent, changes direction, or repeats a request. Skim the
routine stretches. In single-session mode, read the whole conversation.

Claude Code
- Read lines whose `type` is "user" or "assistant". The time is in
  `timestamp`. The text is in `message.content`: a string, or a list of blocks
  (`text`, `thinking`, `tool_use`, `tool_result`).
- A "user" line whose content holds only `tool_result` blocks is tool output,
  not the person. Lines with `isSidechain: true` come from subagents. Skip
  `file-history-snapshot`, `progress`, `attachment`, `system`, and similar
  lines.

Codex
- A path ending in `.jsonl.zst` is compressed; read it with `zstd -dc`.
- Every line has `timestamp`, `type`, and `payload`. Read lines with
  `type: "response_item"` and `payload.type: "message"`. `payload.role` is
  "user" or "assistant"; the text is in `payload.content[].text`.
- Skip `payload.role: "developer"` messages, and user messages whose text
  starts with `# AGENTS.md instructions` or `<environment_context>`. The host
  injects these; the person did not type them.
- Tool use appears as `response_item` lines with `payload.type`
  `function_call` or `custom_tool_call`, and their `_output` pairs. Skip
  `reasoning` items and all `event_msg`, `turn_context`,
  `token_usage_record`, and `compacted` lines.
```

---

## Lens Prompt Template

Build each lens prompt from this template. Fill `<LENS_NAME>`, `<LENS_GOAL>`, `<LENS_FOCUS>`, and `<LENS_EXTRA_SECTIONS>` from [Lens Details](#lens-details).

````
<GUIDING_PRINCIPLES>

<SESSION_LOGS>

You are reviewing AI coding-session transcripts (Claude Code or Codex) to
score one lens of how well the user works with the agent: <LENS_NAME>.
<LENS_GOAL>

Read the principles file at `<PRINCIPLES_PATH>`. Score with its rubric table.
Do not score behaviors that the file says another lens owns.

## Sessions
<SESSION_LIST: one line per session — absolute path, host, session ID, start time>

## Previous Report Findings for This Lens
<PREVIOUS_FINDINGS or "None — this is the first interaction review.">

## What to Evaluate
<LENS_FOCUS>

## Output Format
Return markdown in this shape:

### Score
**Score:** [0–100]
**Justification:** [2–3 sentences with evidence]

<LENS_EXTRA_SECTIONS>

### Findings
Give as many findings as the evidence supports (usually 3–8). If the lens has
one real issue, report one. Do not pad. Each finding:

#### <LENS_NAME> — [Specific Issue Title]
**Transcript Reference**: Session <id>, turns N–M
**What happened**: [Factual description]
**Why it matters**: [Impact — wasted turns, missed opportunity, compounding error]
**What to do differently**: [Concrete change the user can make next session]

### Improvement Suggestions
[1–3 specific suggestions, each with its expected impact]

### Delta from Previous Report
[One of:]
- "Baseline analysis — no prior data."
- "Improved: [...]. Regressed: [...]. Unchanged: [...]."
- "Rubric changed (vN → v2) — the score change is not comparable. Behavior notes: [what got better, worse, or stayed the same]."
````

---

## Lens Details

### 1. Prompt Craft

- **Goal:** Judge the quality of the user's prompts. Read the assistant's replies only to see how each prompt was understood.
- **Focus:** clarity of intent, constraints stated up front, context provided, output expectations, prompt structure, and how useful follow-up prompts are.
- **Extra sections:** none.

### 2. Workflow Efficiency

- **Goal:** Judge how directly and economically each task reaches its goal.
- **Focus:** turn economy (turns used against the turns the task needed), wasted turns, goal directness, and whether planning fit the task. Correction rounds belong to Error Recovery; batching and parallelism belong to Agentic Leverage.
- **Extra sections:**

  ```
  ### Session Metrics
  | Session | Turns | Est. Ideal | Wasted Turns | Efficiency |
  |---|---|---|---|---|
  | <id> | N | N | N | N% |
  ```

### 3. Agentic Leverage

- **Goal:** Judge whether the user uses the agent's own capabilities — skills, tools, batching, parallelism, delegation — or does by hand work the agent could do.
- **Focus:** compare what the user did by hand with the skills and tools that were available in the session. Look for skill invocations (`/name` in Claude Code, `$name` in Codex), tool delegation, autonomy versus micro-management, and grouping of independent work.
- **Extra sections:**

  ```
  ### Missed Opportunities
  [Specific moments where a skill, tool, or more autonomous approach would have done better]
  ```

### 4. Error Recovery & Adaptation

- **Goal:** Judge how the user and agent handle mistakes, misunderstandings, and pivots.
- **Focus:** find every correction, redirect, and pivot. For each, note where the mistake first appeared, when it was detected, and when recovery was complete. Judge detection speed, correction clarity, pivot decisiveness, rounds to recover, and learning within the session.
- **Extra sections:**

  ```
  ### Correction Map
  | Session | Mistake Turn | Detected Turn | Resolved Turn | Lag | Recovery Cost | Type |
  |---|---|---|---|---|---|---|
  | <id> | N | N | N | N turns | N turns | [Late detection / Vague correction / Clean recovery / etc.] |
  ```

### 5. Context & Instruction Quality

- **Goal:** Judge how well the user sets up and maintains the context the agent works in.
- **Focus:** instruction files, memory, session setup, references, and instruction coherence. Besides the transcripts, read and judge each item in the inventory below. Memory for Claude Code is the `memory/` folder beside the session files (`~/.claude/projects/<project-dir>/memory/`). Memory for Codex is `~/.codex/memories/`, shared by all projects; look only for entries about this project. Preferences are in `.codex/skill-context/`.
- **Extra sections:**

  ```
  ### Infrastructure Inventory
  | Component | Status | Quality |
  |---|---|---|
  | Project instruction file (`CLAUDE.md` / `AGENTS.md`) | Present/Missing | [Brief assessment] |
  | Global instruction file (`~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md`) | Present/Missing | [Brief assessment] |
  | Preferences | Present/Missing | [Brief assessment] |
  | Memory entries | N entries | [Brief assessment] |
  ```

---

## Coach Re-Reviewer

Runs once, after the Phase 3 draft report is ready.

```
You are doing the final review of an interaction review report before the
developer reads it. Five lens agents scored the developer's collaboration,
and a synthesis pass merged and ranked their findings. Your job is coaching
judgment: fair scores, concrete advice, and a report that helps the developer
improve.

## Inputs
1. Draft report:
<DRAFT_REPORT>
2. Session files, for spot-checking claims against the real exchanges:
<SESSION_LIST: absolute path, host, session ID, start time>
<SESSION_LOGS>
3. Previous report:
<PREVIOUS_REPORT or "None — baseline analysis.">

## What You May Change
| # | Authority | Rule |
|---|---|---|
| 1 | Adjust scores | Within ±10 points per lens. Cite specific transcript evidence. |
| 2 | Rewrite improvement items | Make them more specific, more actionable, or correctly prioritized. |
| 3 | Reorder priorities | When a quick win is buried below a harder change. |
| 4 | Flag missed patterns | Add observations the five lenses missed. |
| 5 | Validate continuity | Make sure prior progress is acknowledged and recurring issues are flagged. |
| 6 | Set the tone | Coaching and encouraging, not punitive or patronizing. |

Change a finding only when your judgment changes the assessment, never for
wording alone. Tag every change inline as `[Coach: reason]`.

## What to Check
- Score calibration: flag inflation (a B+ with six correction loops) and
  deflation (a C for a user who was effective given the task).
- Actionability: every improvement item must be something the user could do
  in their next session. Rewrite or cut generic advice such as "communicate
  better".
- Specificity: every finding needs a transcript reference, what happened, why
  it matters, and a concrete fix.

Write for a reader who may use English as a second language: short sentences,
everyday words, the point first. Keep facts exact.

## Output Format

### Score Adjustments
[Adjustments with `[Coach: reason]`, or "No adjustments — scores are calibrated."]

### Improvement Item Revisions
[Rewritten items with `[Coach: reason]`, or "No revisions needed."]

### Coach's Note
[2–4 sentences: the one thing this developer should focus on for the biggest improvement. Specific and actionable.]

### Missed Patterns
[Observations the lenses missed, or "No additional patterns found."]
```
