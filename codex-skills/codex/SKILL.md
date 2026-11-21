---
name: codex
description: "Use when the user invokes $codex to delegate a prompt to OpenAI Codex CLI, or $codex resume to continue a previous Codex session. SKIP if the user wants you to answer directly \u2014 this skill exists to consult GPT, not to substitute your own answer."
---

# Codex Skill

Send the user's prompt to OpenAI's Codex CLI, show its answer, and evaluate it critically.

## Collection Root

The collection root is the folder one level above this SKILL.md. Every path in this skill that starts with `../` is relative to this skill's folder, so it points into the collection root, never into the project's working directory.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `../shared/report-style.md`.

## Shared Flow

Read `../shared/delegation-common.md` first. It holds the flow for every delegation skill: delegate instead of answering, never send an empty prompt, show Codex's full response verbatim, then evaluate it critically and summarize, and report failures plainly. Take the command template from `../shared/model-defaults.md` Section Codex; do not hardcode the model or flags.

## Running a Task

Arguments to `$codex`:
- `--model <MODEL>` - override the default model
- `--sandbox <MODE>` - override the default sandbox (`read-only`, `workspace-write`, `danger-full-access`)
- Any remaining text is the prompt

Replace `<CODEX_CMD>` with the template from Section Codex plus any overrides. Replace the template's trailing `2>/dev/null` with `2>"$CODEX_LOG"`. Codex prints its `session id:` line on stderr, and that ID is what makes resume reliable. Use a 600000 ms timeout.

```bash
PROMPT_FILE=$(mktemp /tmp/codex-prompt-XXXXXX.txt)
CODEX_LOG=$(mktemp /tmp/codex-log-XXXXXX.txt)
cat > "$PROMPT_FILE" << 'PROMPT_EOF'
<USER_PROMPT>
PROMPT_EOF
cat "$PROMPT_FILE" | <CODEX_CMD>
grep -m1 "session id:" "$CODEX_LOG"   # keep this ID for $codex resume
rm -f "$PROMPT_FILE" "$CODEX_LOG"
```

Label the output as **Codex's response**. After your evaluation, tell the user they can continue with `$codex resume`, and include the session ID so resume still works if other Codex sessions run in between.

## Session Resume

Commands and flag rules are in `../shared/model-defaults.md` Section Codex Resume. Use a 600000 ms timeout.

- `$codex resume <PROMPT>` - resume this skill's last session by its captured session ID. Use `--last` only when no ID is known.
- `$codex resume <SESSION_ID> <PROMPT>` - resume a specific session by ID.

Rules:
- A resumed session does not keep the model, the reasoning effort, or the sandbox of the first run. It takes them from the user's own Codex settings. Give all three again on every resume, as Section Codex Resume shows. Use the model and the effort of the first run, unless the user asks for others.
- Write access on resume needs the config override listed in Section Codex Resume. Do not guess flags.
- Never use `--ephemeral` on the first run, or there will be no session to resume.
- `--last` resumes the newest Codex session, which may not be this one. If the session ID was not captured and other Codex commands have run since, warn the user before a `--last` resume.

After a resume, use the same output flow.

## Timeout Tip

Lower the reasoning effort (`-c model_reasoning_effort="high"`).
