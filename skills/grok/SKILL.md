---
name: grok
description: "Use when the user invokes /grok to delegate a prompt to xAI's Grok CLI (grok), or /grok resume to continue a previous Grok session. SKIP if the user wants you to answer directly — this skill exists to consult Grok, not to substitute your own answer."
---

# Grok Skill

Send the user's prompt to xAI's Grok CLI (`grok`), show its answer, and evaluate it critically.

## Plugin Root

`${CLAUDE_PLUGIN_ROOT}` is the plugin root. If that is not a real folder path, your host did not fill it in; use the folder two levels above this SKILL.md instead. Every `shared/...`, `scripts/...` and `skills/...` path in this skill is under the plugin root, never under the project's working directory.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md`.

## Shared Flow

Read `shared/delegation-common.md` first. It holds the flow for every delegation skill: delegate instead of answering, never send an empty prompt, show Grok's full response verbatim, then evaluate it critically and summarize, and report failures plainly. Take the command template from `shared/model-defaults.md` § Grok; do not hardcode flags.

## Running a Task

Arguments to `/grok`:
- `--model <MODEL>` - override Grok's default model (`grok models` lists the IDs)
- `--effort <LEVEL>` - override Grok's default reasoning effort (for example `high`)
- Any remaining text is the prompt

Replace `<GROK_CMD>` with the template from § Grok plus any overrides. Grok takes the prompt from the temp file, not from stdin. Choose the session ID before the run, so that resume does not depend on which Grok session is the newest. Run the ID line with `python3`, or `python` on Windows. Use a 600000 ms timeout.

```bash
PROMPT_FILE=$(mktemp /tmp/grok-prompt-XXXXXX.txt)
GROK_LOG=$(mktemp /tmp/grok-log-XXXXXX.txt)
SESSION_ID=$(python3 -c 'import uuid; print(uuid.uuid4())')
cat > "$PROMPT_FILE" << 'PROMPT_EOF'
<USER_PROMPT>
PROMPT_EOF
<GROK_CMD> --session-id "$SESSION_ID" 2>"$GROK_LOG"
echo "session id: $SESSION_ID"   # keep this ID for /grok resume
echo "grok stderr:"
cat "$GROK_LOG"                  # usually empty; see CLI quirks
rm -f "$PROMPT_FILE" "$GROK_LOG"
```

CLI quirks:
- Never discard stderr. When Grok tries something that needs approval, such as a command that changes files, the run stops early. The exit code is still 0 and the answer is cut short. The only sign is a stderr line that starts with `permission required:`. Report such an answer as partial, quote that line, and suggest a prompt that asks Grok to read and explain instead of running commands. Any other stderr line that is not an error message is a note, not a failure.
- For a prompt that asks for changes, Grok answers with a plan and changes nothing. That is the read-only mode working, not a failure.
- Grok reads a prompt that starts with `/` as one of its own commands and does not send it to the model. If the prompt starts with `/`, put the line `Prompt:` above it in the file, and tell the user you did.
- Grok prints its short progress notes directly before the answer, with no line break between them. Show the output as printed.

Label the output as **Grok's response**. After your evaluation, tell the user they can continue with `/grok resume`, and include the session ID so resume still works if other Grok sessions run in between.

## Session Resume

Commands and rules are in `shared/model-defaults.md` § Grok Resume. A resume uses the same block as the first run with one change: it makes no new session ID, and the run line becomes the line below. Use a 600000 ms timeout.

```bash
<GROK_CMD> --resume <SESSION_ID> 2>"$GROK_LOG"
```

- `/grok resume <PROMPT>` - resume this skill's last session by its session ID. Use `-c` in place of `--resume <SESSION_ID>` only when no ID is known.
- `/grok resume <SESSION_ID> <PROMPT>` - resume a specific session by ID.

Rules:
- Keep the whole template on resume. Without `--permission-mode plan`, the resumed session follows the user's own Grok settings and may write files.
- Do not pass `--session-id` on resume. It only names a new session.
- `-c` continues the newest Grok session started in the current folder, which may not be this one. Warn the user before a `-c` resume.

After a resume, use the same output flow.

## Timeout Tip

Pass a lower `--effort`, or simplify the prompt.
