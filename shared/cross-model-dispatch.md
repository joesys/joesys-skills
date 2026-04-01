# Cross-Model Dispatch Protocol

Shared infrastructure for dispatching review prompts to a different AI model via CLI. Used by `/code-review` and `/quick-review` to get an independent second opinion from a model outside the host.

Read `shared/model-defaults.md` for current model identifiers and CLI flag details.

---

## Host Detection

Determine which cross-model CLI to dispatch based on who you are:

| You Are | Dispatch To | Command |
|---|---|---|
| Claude | Codex | `codex exec` |
| Codex | Claude | `claude -p` |
| Gemini | Claude | `claude -p` |
| Unknown | Both Codex + Claude | Two parallel dispatches |

---

## Prompt Delivery

**Always** write prompts to a temporary file and pipe via stdin. This avoids shell quoting issues regardless of prompt content (quotes, backticks, dollar signs, newlines).

### Platform-Adaptive Temp Files

Use `mktemp` to create temp files portably (works on Linux, macOS, and Windows Git Bash):

```bash
PROMPT_FILE=$(mktemp /tmp/review-XXXXXX.txt)
cat > "$PROMPT_FILE" << 'PROMPT_EOF'
<prompt content here>
PROMPT_EOF
```

After dispatch completes, clean up:

```bash
rm -f "$PROMPT_FILE"
```

If `mktemp` is unavailable, fall back to a deterministic path: `/tmp/<skill-name>-cross-prompt.txt`.

---

## Dispatch Commands

Substitute `$PROMPT_FILE` with the actual temp file path created above.

### To Codex

```bash
cat "$PROMPT_FILE" | codex exec --model gpt-5.4 \
  -c model_reasoning_effort="xhigh" --sandbox read-only \
  --skip-git-repo-check 2>/dev/null
```

### To Claude CLI

```bash
cat "$PROMPT_FILE" | claude --model opus --effort high \
  --permission-mode plan --name "<review-name>" -p "" 2>/dev/null
```

### To Gemini (via `--include-gemini`)

```bash
cat "$PROMPT_FILE" | gemini -m gemini-3.1-pro-preview \
  --approval-mode plan -p "" 2>/dev/null
```

Use **600000ms** timeout on the Bash tool for all dispatches.

---

## `--include-gemini` Flag

When `--include-gemini` is specified, launch an **additional** parallel dispatch to Gemini alongside the primary cross-model dispatch. The Gemini prompt is identical to the cross-model prompt but written to a separate temp file. Both dispatches run in parallel in the same response.

---

## Failure Handling

If a cross-model dispatch fails or times out, the review continues with host-only findings. Append a note to the report:

- **Single cross-model failure:** "Cross-model review unavailable ([model] [reason]); results are from [host model] only."
- **`--include-gemini` with only Gemini failing:** Primary cross-model results are still included. Note Gemini unavailability separately.
- **All cross-model dispatches fail:** Proceed with host AI subagents only. Note in report header.

---

## Permissions

All cross-model dispatches use **read-only / plan mode**. They only need to read the code/diff and think. Never dispatch with write permissions.
