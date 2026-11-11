---
name: claude
description: "Use when the user invokes $claude to delegate a prompt to Claude Code CLI, or $claude resume to continue a previous Claude session. SKIP if the user wants you to answer directly \u2014 this skill exists to consult a separate Claude instance, not to substitute your own answer."
---

# Claude Skill

Send the user's prompt to a separate Claude Code CLI instance, show its answer, and evaluate it critically.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `../shared/report-style.md` (resolve against the collection root (one level above this SKILL.md) - never the project's working directory).

## Shared Flow

Read `../shared/delegation-common.md` first, and resolve every `../shared/...` path against the same plugin root. It holds the flow for every delegation skill: delegate instead of answering, never send an empty prompt, show Claude's full response verbatim, then evaluate it critically and summarize, and report failures plainly. Take the command template from `../shared/model-defaults.md` Section Claude CLI; do not hardcode the model or flags.

## Running a Task

Arguments to `$claude`:
- `--model <MODEL>` - override the default model (for example `sonnet`, `haiku`, `opus[1m]`)
- `--permission-mode <MODE>` - override the default (`manual`, `acceptEdits`, `auto`, `dontAsk`)
- `--effort <LEVEL>` - override the default (`low`, `medium`, `high`, `xhigh`, `max`)
- `--bare` - bare mode (skips hooks, plugins, CLAUDE.md, MCP servers)
- Any remaining text is the prompt

Derive a short session name from the topic (kebab-case, 2-4 words). Replace `<CLAUDE_CMD>` with the template from Section Claude CLI plus any overrides, and append `--name` so the session can be resumed by name. Use a 600000 ms timeout.

```bash
PROMPT_FILE=$(mktemp /tmp/claude-prompt-XXXXXX.txt)
cat > "$PROMPT_FILE" << 'PROMPT_EOF'
<USER_PROMPT>
PROMPT_EOF
cat "$PROMPT_FILE" | <CLAUDE_CMD> --name "<derived-name>"
rm -f "$PROMPT_FILE"
```

Label the output as **Claude's response**. After your evaluation, tell the user they can continue with `$claude resume` or `$claude resume <name>`.

## Session Resume

Commands are in `../shared/model-defaults.md` Section Claude CLI Resume.

- `$claude resume <PROMPT>` - continue the most recent session (`claude -c`).
- `$claude resume <NAME> <PROMPT>` - resume a named session (`claude --resume "<NAME>"`).

Resumed sessions keep the original model, effort, and permission mode. Override `--model`, `--effort`, `--permission-mode`, or `--bare` only when the user asks. After a resume, use the same output flow.

## Same-Family Evaluation

This is Claude evaluating Claude, so apply the same-family rule in `../shared/delegation-common.md` Section Critical Evaluation. Agreement between the two instances is not strong evidence on its own.

## Timeout Tip

Lower the effort (`--effort medium`) or switch to `sonnet`.
