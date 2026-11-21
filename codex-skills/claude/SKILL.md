---
name: claude
description: "Use when the user invokes $claude to delegate a prompt to Claude Code CLI, or $claude resume to continue a previous Claude session. SKIP if the user wants you to answer directly \u2014 this skill exists to consult a separate Claude instance, not to substitute your own answer."
---

# Claude Skill

Send the user's prompt to a separate Claude Code CLI instance, show its answer, and evaluate it critically.

## Collection Root

The collection root is the folder one level above this SKILL.md. Every path in this skill that starts with `../` is relative to this skill's folder, so it points into the collection root, never into the project's working directory.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `../shared/report-style.md`.

## Shared Flow

Read `../shared/delegation-common.md` first. It holds the flow for every delegation skill: delegate instead of answering, never send an empty prompt, show Claude's full response verbatim, then evaluate it critically and summarize, and report failures plainly. Take the command template from `../shared/model-defaults.md` Section Claude CLI; do not hardcode the model or flags.

## Running a Task

Arguments to `$claude`:
- `--model <MODEL>` - override the default model (for example `opus`, `sonnet`, `haiku`)
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

A resumed session keeps its model, but it does not keep its permission mode. Give `--permission-mode plan` again on every resume, as Section Claude CLI Resume shows. Override `--model`, `--effort`, or `--bare` only when the user asks, and leave plan mode only when the user asks. After a resume, use the same output flow.

## Same-Family Evaluation

This is Claude evaluating Claude, so apply the same-family rule in `../shared/delegation-common.md` Section Critical Evaluation. Agreement between the two instances is not strong evidence on its own.

## Timeout Tip

Lower the effort (`--effort medium`) or switch to `sonnet`.
