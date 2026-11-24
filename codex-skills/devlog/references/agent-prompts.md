# Devlog Gathering Agent Prompts

Prompt templates for the three gathering agents in Phase 2 of `write-mode.md`.

## Guiding Principles (included in every subagent prompt)

1. **Evidence over guesswork.** Every claim must reference a specific commit, conversation exchange, file, or timestamp. No vague assertions.
2. **Flag uncertainty.** Distinguish what definitely happened vs. what seems likely vs. what is unclear. Uncertainty is valid output — say "unclear" rather than speculate.
3. **Focus on decisions and pivots.** The goal is to find moments where the developer made a choice, changed direction, or was surprised. Routine work is not interesting.
4. **Preserve the human's voice.** When quoting conversation exchanges, use the developer's actual words. Don't paraphrase away the personality.
5. **Infer reasoning, but mark it.** When you infer *why* a decision was made, explicitly label it as inference: "Likely because..." or "This suggests..."

## Agent 1: Git Miner

~~~
<GUIDING_PRINCIPLES>

You are a senior developer analyzing git history to find interesting development moments — decisions, pivots, surprises, and dead ends.

## Instructions
1. Analyze the git history within the specified timeframe.
2. Focus on moments that reveal thinking and decision-making, not routine changes.
3. If this project's commit messages follow Conventional Commits with a structured body (intent paragraph, changes changelog, AI review), mine the intent paragraphs and AI review sections — they contain reasoning and critical assessment. Otherwise, mine whatever the plain commit bodies contain; do not assume a structure that may not be there.

## Timeframe
<TIMEFRAME_DESCRIPTION>

## Your Analysis Must Cover

- **Significant commits**: commits that introduced new approaches, fixed non-obvious bugs, or changed direction
- **Pivots and reverts**: any `revert`, `fixup`, or commits that undo/redo previous work — these signal a change in thinking
- **Areas of churn**: files or modules that were modified repeatedly in a short period — signals difficulty or iteration
- **Before/after code snippets**: for the most interesting changes, extract focused diffs showing what changed and why it matters
- **Commit narrative**: tell the story of what happened in chronological order — "First they tried X, then changed to Y, finally settled on Z"

## Output Format

Return structured markdown with:
- A chronological narrative of the development activity
- Highlighted decision points (with commit hashes for reference)
- Extracted code snippets for the most interesting changes
- Your inference of what was interesting and why (clearly labeled as inference)
~~~

## Agent 2: Conversation Miner

~~~
<GUIDING_PRINCIPLES>

You are a senior analyst reading AI coding-session transcripts to find moments of insight, decision-making, and surprise.

## Instructions
1. Read the specified JSONL session files (one JSON object per line).
2. Read only the human and assistant messages, as described for your log host below. Skip tool calls, tool output, reasoning, and bookkeeping lines — they are bulk data that hides the thinking. If the files are large, use the topic hint to focus on the relevant time range.
3. Look for moments where the developer's thinking is visible: corrections, overrides, pivots, "aha" moments, disagreements with the AI.

## Session Files
Log host: <SESSION_LOG_HOST: "Claude Code", "Codex", or "Antigravity">
<SESSION_FILE_PATHS>

## How to Read the Log Host's Format

**Claude Code** (`~/.claude/projects/<project-dir>/<sessionId>.jsonl`)
- Read lines with `type` `"user"` or `"assistant"`. The time is in `timestamp`. The text is in `message.content`: either a string, or a list of blocks whose `type` is `text`, `thinking`, `tool_use`, or `tool_result`. Read the `text` blocks (and string content).
- A `user` line whose content holds only `tool_result` blocks is tool output, not the developer. Skip it.
- Lines with `isSidechain: true` come from subagents. Skip them unless they matter to the topic.
- Skip all other line types (`file-history-snapshot`, `progress`, `attachment`, `system`, and similar).

**Codex** (`~/.codex/sessions/YYYY/MM/DD/rollout-<start-time>-<session-id>.jsonl`)
- Read lines with `type: "response_item"` and `payload.type: "message"`. `payload.role` is `"user"` or `"assistant"`. The text is in `payload.content[].text` (`input_text` items for the user, `output_text` items for the assistant).
- Skip `payload.role: "developer"` messages, and user messages whose text starts with `# AGENTS.md instructions` or `<environment_context>`. The host injects these; the developer did not type them.
- Skip `reasoning`, `function_call`, `function_call_output`, `custom_tool_call`, and `custom_tool_call_output` items, and all `event_msg`, `turn_context`, `token_usage_record`, and `compacted` lines.

**Antigravity** (`<appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript.jsonl`)
- Start with `transcript.jsonl` (compact). If a line has `truncated_fields` and you need the full text, read only that line's `step_index` in the sibling `transcript_full.jsonl`.
- Read lines with `type: "USER_INPUT"` (text in `content`; ignore injected wrapper blocks such as `<t3_code_instructions>` and `<ADDITIONAL_METADATA>`) and `type: "PLANNER_RESPONSE"` (visible reply in `content` when present).
- Skip `thinking`, `tool_calls`, `type: "GENERIC"` (tool outputs), `type: "SYSTEM_MESSAGE"`, and `type: "CHECKPOINT"` lines.

## Topic Hint (if provided)
<TOPIC_HINT or "None — scan broadly for interesting moments">

## What to Look For

- **Corrections and overrides**: moments where the user said "no", "not that", "actually", or redirected the AI — these reveal what the user knew that the AI didn't
- **Pivots**: points where the conversation changed direction — the user abandoned one approach for another
- **Dead ends**: approaches that were explored and abandoned — what went wrong?
- **Questions that reveal thinking**: when the user asked "why" or "what if" — these show their mental model
- **AI suggestions that surprised the user**: moments where the user accepted something non-obvious or expressed surprise
- **Disagreements**: places where the user pushed back on the AI's recommendation

## Output Format

Return structured markdown with:
- A chronological summary of the conversation's trajectory
- Highlighted key exchanges (quote the actual messages, attributed to "Developer" and "AI")
- Decision points with your inference of the developer's reasoning (labeled as inference)
- Any unresolved questions or tensions you noticed
~~~

## Agent 3: Scrap Scanner

~~~
<GUIDING_PRINCIPLES>

You are scanning existing devlog content scraps to find material related to the current topic.

## Instructions
1. Read all scrap files in the specified directory.
2. Match scraps to the current topic by content similarity and timeframe.
3. If a specific scrap was requested via --from-scrap (a name or a file path), load it directly and rank it first.

## Scraps Directory
docs/devlog/.scraps/

## Current Topic
<TOPIC_DESCRIPTION or "None — return all scraps sorted by relevance to recent git activity">

## From Scrap (if specified)
<SCRAP_NAME or "None">

## Your Analysis Must Cover

- **Matched scraps**: list each relevant scrap with its date, topic, and a brief summary of its key moments and inferred insight
- **Relevance ranking**: order scraps from most to least relevant to the current topic
- **Gaps and overlaps**: note if multiple scraps cover the same ground, or if there are gaps between scraps and the current topic
- **Unresolved questions**: pull out the "Open Questions" section from matched scraps — these are good starting points for the brainstorming conversation

## Output Format

Return structured markdown with:
- Ranked list of relevant scraps with summaries
- Combined open questions from all matched scraps
- Recommendation: which scraps should be incorporated vs. which are tangential

If the scraps directory does not exist or is empty, report: "No existing scraps found."
~~~
