# Retrospective — Agent Prompts

Prompt templates for the 5 channel agents (Phase 1) and the narrative agent (Phase 4). Give every channel agent the retro time boundary, the Guiding Principles, the carry-forward summary (or "None — this is the first retrospective."), and the project and tone preferences. Fill Agent 2's `<SESSION_LOG_HOST>` (Claude Code or Codex) and Agent 4's `<PLAN_FOLDERS>` (from `.codex/skill-context/retrospective.md`, or "None configured").

## Guiding Principles

Prepend to every channel agent prompt:

1. **Evidence over guesswork.** Every claim must reference a specific commit, conversation exchange, file, or timestamp. No vague assertions.
2. **Flag uncertainty.** Distinguish what definitely happened vs. what seems likely vs. what is unclear. Uncertainty is valid output — say "unclear" rather than speculate.
3. **Focus on friction and surprise.** The goal is to find moments where something didn't go as expected, where the developer changed direction, or where a process broke down. Routine work is not interesting for a retrospective.
4. **Quantify when possible.** Prefer "12 commits touched auth/ in 3 days" over "lots of churn in the auth module."
5. **Infer reasoning, but mark it.** When you infer *why* something happened, explicitly label it: "Likely because..." or "This suggests..."
6. **Write for humans.** The reader may speak English as a second language. Use short sentences and everyday words, and explain jargon on first use. Simplify the language, never the facts.
7. **Scan broadly, read deeply only the signal-rich parts.** Stay within about 4,000 lines of reading.

---

## Agent 1: Git History

```
<GUIDING_PRINCIPLES>

You are analyzing git history for a retrospective. Your job is to extract the timeline, patterns, and notable events from the commit history.

Use git to get the timeline, contributors, change volume, and added and deleted files within the time boundary. If commit messages have structured bodies (intent paragraph, changes list, AI review), mine the intent and AI review sections — they hold the reasoning and critical assessment.

## Time Boundary
<START_REF> to <END_REF>

## Extract and Organize

- **Timeline**: chronological narrative of what happened (first X, then Y, finally Z)
- **Velocity metrics**: total commits, files changed, insertions/deletions, new files created, files deleted
- **Hotspots**: files/directories with the most churn (modified in 3+ commits)
- **Commit patterns**: burst vs. steady work, time-of-day patterns if visible, large commits that may indicate code dumps
- **Notable commits**: commits that introduced new approaches, reverted work, or stand out as pivots
- **Dependency changes**: new dependencies added, removed, or upgraded (look at lockfile/manifest changes)

## Output Format

Return structured markdown with a section per category above. Include commit hashes for notable items.
```

---

## Agent 2: Conversation History

```
<GUIDING_PRINCIPLES>

You are reading AI coding-session transcripts to find moments of human correction, decision-making, and friction for a retrospective.

Find and read the session files for this project, using the section for your log host below. Each line is one JSON object. Read only the human and assistant messages; tool calls, tool output, reasoning, and bookkeeping lines are bulk data that hides the thinking.

## Log Host
<SESSION_LOG_HOST: "Claude Code" or "Codex". Read that host's logs. Read both only if the host says so, and label each finding with its source.>

## Claude Code Session Logs
1. Location: `~/.claude/projects/<project-dir>/<sessionId>.jsonl`. `<project-dir>` is the current working directory with every non-alphanumeric character (the drive `:`, path separators `\` and `/`) replaced by a single `-` (`D:\joesys\Projects\my-project` → `D--joesys-Projects-my-project`; `/home/user/app` → `-home-user-app`). If unsure, list `~/.claude/projects/` and match against the transformed cwd.
2. Session start: the first line that has a top-level `timestamp` (the leading lines often have none). Keep sessions that fall within the retro time boundary.
3. Read lines with `type` `"user"` or `"assistant"`. The text is in `message.content`: a string, or a list of blocks (`text`, `thinking`, `tool_use`, `tool_result`). Read the `text` blocks and string content.
4. A `user` line whose content holds only `tool_result` blocks is tool output, not the developer. Lines with `isSidechain: true` come from subagents. Skip both, and skip all other line types (`file-history-snapshot`, `progress`, `attachment`, `system`, and similar).

## Codex Session Logs
1. Location: `~/.codex/sessions/YYYY/MM/DD/rollout-<start-time>-<session-id>.jsonl`. The date folders are the session start date, so list only the folders inside the retro time boundary. Older sessions may be compressed in `~/.codex/archived_sessions/*.jsonl.zst`; read them with `zstd -dc` only if the boundary needs them.
2. Every line has `timestamp`, `type`, and `payload`. The first line is `type: "session_meta"`: keep the file only if `payload.cwd` equals the project's working directory. Skip files whose `payload.source` is an object with a `subagent` key.
3. Read lines with `type: "response_item"` and `payload.type: "message"`. `payload.role` is `"user"` or `"assistant"`; the text is in `payload.content[].text`.
4. Skip `payload.role: "developer"` messages and user messages whose text starts with `# AGENTS.md instructions` or `<environment_context>` (the host injects these). Skip `reasoning`, `function_call`, `function_call_output`, `custom_tool_call`, and `custom_tool_call_output` items, and all `event_msg`, `turn_context`, `token_usage_record`, and `compacted` lines.
5. `~/.codex/history.jsonl` lists every user prompt across all projects (`session_id`, `ts` in Unix seconds, `text`). It has no folder field. Use it only as a quick prompt index, matched to this project's rollout files by `session_id`.

## Time Boundary
<START_DATE> to <END_DATE>

## What to Look For

- **Human corrections**: moments where the user said "no", "not that", "actually", "stop", or redirected the AI — these reveal what the human knew that the AI didn't
- **Pivots**: points where the conversation changed direction — the user abandoned one approach for another
- **Repeated friction**: the same kind of problem or miscommunication happening across multiple sessions
- **AI failures**: questions the AI couldn't answer, wrong suggestions that had to be corrected, hallucinated solutions
- **Workflow bottlenecks**: long conversations that should have been short, indicating process friction
- **Successful patterns**: approaches that worked well and should be continued

## Output Format

Return structured markdown with:
- Summary statistics: sessions analyzed, total exchanges, correction count
- Highlighted key exchanges (quote the actual messages, attributed to "Developer" and "AI")
- Patterns observed across sessions (not just individual moments)
- Specific friction points with session references
```

---

## Agent 3: Code Quality Delta

```
<GUIDING_PRINCIPLES>

You are analyzing how the codebase's structural quality changed during the retro period.

Compare the codebase structure at the start and end of the retro period. Focus on structural indicators, not code content.

## Time Boundary
<START_REF> to <END_REF>

## Baseline (if available)
<CODEBASE_AUDIT_METRICS_JSON from a `$codebase-audit` run before the retro period, or "None — estimate the delta from git history.">

## Analyze

- **File count delta**: source files, test files, config files — created vs. deleted
- **Test-to-production ratio**: ratio of test code added vs. production code added
- **Complexity indicators**: large files that grew larger, new files that are already large (>300 lines), deeply nested directory structures created
- **Dependency changes**: new dependencies added to manifests/lockfiles, dependencies removed or upgraded
- **Tech debt signals**: TODO/FIXME/HACK comments added vs. removed in the period
- **What got better**: tests added, large files split, dead code removed, types added
- **What got worse**: new dependencies without justification, growing god files, test coverage gaps in high-churn areas

## Output Format

Return structured markdown with quantified deltas where possible. Use "+N" / "-N" notation for changes.
```

---

## Agent 4: Planning vs. Reality

```
<GUIDING_PRINCIPLES>

You are comparing what was planned against what was actually delivered during the retro period.

Read the plan and spec documents from the retro period, and cross-check them against git history to see what was actually built.

## Time Boundary
<START_DATE> to <END_DATE>

## Where to Find Plans
Configured plan folders (from the user's retrospective preferences):
<PLAN_FOLDERS or "None configured">

If folders are configured, search them first. Otherwise, check these common locations, and use the ones that exist:
- `docs/plans/`, `docs/specs/`, `plans/`, `specs/`
- `docs/design/`, `docs/rfcs/`, `docs/adr/`, `docs/decisions/`
- `docs/superpowers/plans/`, `docs/superpowers/specs/` (older projects)
- Any other folder whose name says it holds plans, specs, designs, or roadmaps

If none exist, say so and still list significant unplanned work from the git history.

## Analyze

- **Plans completed**: which plans were fully implemented (all checkboxes checked or equivalent)
- **Plans partially completed**: which plans were started but not finished — what remains
- **Plans abandoned**: which plans were created but never started or explicitly abandoned
- **Unplanned work**: significant commits or features that don't trace to any plan — these represent reactive or emergent work
- **Scope drift**: where implementation diverged from the plan — features added, features cut, approach changed mid-implementation
- **Estimate accuracy**: if plans have time estimates, compare against actual (infer from commit timestamps)

## Output Format

Return structured markdown. For each plan found, state: title, status (complete/partial/abandoned), and notable divergences. End with an "Unplanned Work" section listing significant work that wasn't in any plan.
```

---

## Agent 5: Testing & Reliability

```
<GUIDING_PRINCIPLES>

You are analyzing the health and trajectory of the project's test suite during the retro period.

Analyze test file changes during the retro period, and get the current pass/fail status if you can.

## Time Boundary
<START_REF> to <END_REF>

## Analyze

- **Test suite status**: run the project's documented test command if one exists. If tests cannot run, note why and continue with static analysis.
- **Test file changes**: new test files created, test files modified, test files deleted during the period
- **Test-to-production ratio**: for files changed in the period, how many had corresponding test changes
- **Flaky test indicators**: test files with high churn (modified 3+ times), tests that were added then quickly modified
- **Coverage gaps**: production files with high churn during the period that have no corresponding test file
- **Testing patterns**: what testing conventions emerged or were followed (naming, structure, assertion style)

## Output Format

Return structured markdown with:
- Current test suite status (if runnable): total, passing, failing, skipped
- Test delta during retro period: tests added, modified, deleted
- Coverage gap analysis: high-churn production files without tests
- Notable testing patterns or anti-patterns observed
```

---

## Phase 4: Narrative Agent

Pass this prompt with the writing rules unchanged, plus the paths to `03-retro-summary.md` and `02-topic-discussions.md`.

```
You are writing a retrospective narrative — a readable, engaging account of a development period. You are NOT reformatting a summary into prose. You are telling the story of what happened.

## Source Material
Read the two files provided:
1. The retrospective summary — for the arc, metrics, and takeaways
2. The topic discussions — for the detail, tensions, and human corrections

## Writing Rules

- Write in third person or neutral voice — no fictional characters, no personas
- Short paragraphs, punchy sentences — like a good blog post, not a report
- Ground every point in specifics from the retro — no generic advice or platitudes
- Write for humans: the reader may speak English as a second language. Use short sentences and everyday words, and explain jargon on first use. Simplify the language, never the facts
- Highlight tension and surprise over agreement and success — friction is interesting, smooth sailing is not
- Human corrections and judgment calls get prominent placement — these are the moments where the human's expertise was most visible
- Open with the narrative arc — set the scene for what this period was about
- End with forward tension — what's the challenge going forward? Don't tie a neat bow.
- Target length: 500-1000 words
- Do NOT include headers, bullet points, or structured formatting — this is prose

## Save To
<RETRO_DIR>/04-retro-narrative.md
```
