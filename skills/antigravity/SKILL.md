---
name: antigravity
description: "Use when the user invokes /antigravity to delegate a prompt to Google Antigravity CLI (agy), or /antigravity resume to continue a previous Antigravity session. SKIP if the user wants you to answer directly — this skill exists to consult Antigravity, not to substitute your own answer."
---

# Antigravity Skill

Send the user's prompt to Google's Antigravity CLI (`agy`), show its answer, and evaluate it critically.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md` (resolve against the plugin root — two levels above this SKILL.md — never the project's working directory).

## Shared Flow

Read `shared/delegation-common.md` first, and resolve every `shared/...` path against the same plugin root. It holds the flow for every delegation skill: delegate instead of answering, never send an empty prompt, show Antigravity's full response verbatim, then evaluate it critically and summarize, and report failures plainly. Take the command template from `shared/model-defaults.md` § Antigravity; do not hardcode flags.

## Running a Task

The whole `/antigravity` argument is the prompt.

Dispatch through the adapter, not `agy` directly. `<ADAPTER>` is the absolute path to `scripts/agy_adapter.py` under the plugin root; the project's working directory does not contain it. Run it with `python3`, or `python` on Windows. Replace `<AGY_CMD>` with the template from § Antigravity (`python <ADAPTER> --mode plan --sandbox`). Use a 600000 ms timeout.

```bash
PROMPT_FILE=$(mktemp /tmp/antigravity-prompt-XXXXXX.txt)
cat > "$PROMPT_FILE" << 'PROMPT_EOF'
<USER_PROMPT>
PROMPT_EOF
cat "$PROMPT_FILE" | <AGY_CMD>
rm -f "$PROMPT_FILE"
```

CLI quirks:
- The adapter always reads the prompt from stdin. Do not pass `-p`, `--print`, `--input-format`, or `--output-format`; the adapter adds the format flags itself.
- The adapter rejects prompts over 150,000 bytes, because `agy` silently drops the end of very large prompts. Shorten or split such a prompt.

Label the output as **Antigravity's response**. After your evaluation, tell the user they can continue with `/antigravity resume`.

## Session Resume

Deliver the follow-up prompt through the same temp file and stdin pipe.

- `/antigravity resume <PROMPT>` - resume the latest session:
  ```bash
  cat "$PROMPT_FILE" | python <ADAPTER> --mode plan --sandbox -c
  ```
- `/antigravity resume <ID> <PROMPT>` - resume a specific session by conversation ID:
  ```bash
  cat "$PROMPT_FILE" | python <ADAPTER> --mode plan --sandbox --conversation <ID>
  ```

Always pass `--mode plan --sandbox` on resume. Do not rely on the resumed session to stay read-only. After a resume, use the same output flow.

## Timeout Tip

Raise `AGY_ADAPTER_TIMEOUT` (see `shared/model-defaults.md` § Antigravity) or simplify the prompt.
