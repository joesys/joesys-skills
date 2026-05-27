# Cross-Model Dispatch Protocol

Shared infrastructure for dispatching review prompts to a different AI model via CLI. Used by `/codereview` and `/quick-review` to get an independent second opinion from a model outside the host.

Read `shared/model-defaults.md` for current model identifiers and CLI flag details.

---

## Discipline

- **MUST use read-only / plan mode** for every cross-model dispatch. Cross-model reviewers think; they never write.
- **MUST deliver prompts via temp-file-and-stdin-pipe** to avoid shell quoting issues with code blocks, backticks, and special characters.
- **MUST run dispatches in parallel** with the host AI subagents — all in a single response. Sequential dispatch defeats the speedup.
- **MUST clean up temp files** after dispatch completes (`rm -f "$PROMPT_FILE"`).

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

### Platform-Adaptive Temp Files

Use `mktemp` to create temp files portably (Linux, macOS, Windows Git Bash):

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

Substitute `$PROMPT_FILE` with the temp file path. Substitute `<CODEX_CMD>`, `<CLAUDE_CMD>`, `<GEMINI_CMD>` with the current invocations from `shared/model-defaults.md` (§ Codex, § Claude CLI, § Gemini).

### To Codex

```bash
cat "$PROMPT_FILE" | <CODEX_CMD>
```

### To Claude CLI

Append `--name "<review-name>"` for resumability:

```bash
cat "$PROMPT_FILE" | <CLAUDE_CMD> --name "<review-name>"
```

### To Gemini (via `--include-gemini`)

```bash
cat "$PROMPT_FILE" | <GEMINI_CMD>
```

Use **600000ms** timeout on the Bash tool for all dispatches.

---

## `--include-gemini` Flag

When `--include-gemini` is specified, launch an **additional** parallel dispatch to Gemini alongside the primary cross-model dispatch. The Gemini prompt is identical to the cross-model prompt but written to a separate temp file. **Both dispatches MUST run in parallel** in the same response.

---

## Failure Handling

If a cross-model dispatch fails or times out, the review continues with host-only findings. Append a note to the report:

- **Single cross-model failure:** "Cross-model review unavailable ([model] [reason]); results are from [host model] only."
- **`--include-gemini` with only Gemini failing:** Primary cross-model results are still included. Note Gemini unavailability separately.
- **All cross-model dispatches fail:** Proceed with host AI subagents only. Note in the report header.
