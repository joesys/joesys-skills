# Shared Delegation Infrastructure

Reference file for codex, gemini, and claude skills. Read this file
after presenting the delegated model's response — it contains the
shared logic for prompt delivery, critical evaluation, and error handling.

## Prompt Delivery

**Always** write prompts to a temporary file and pipe via stdin to avoid shell quoting issues. This is reliable regardless of prompt content (quotes, backticks, dollar signs, newlines).

### Platform-Adaptive Temp Files

Use `mktemp` to create temp files portably (works on Linux, macOS, and Windows Git Bash):

```bash
PROMPT_FILE=$(mktemp /tmp/<skill>-prompt-XXXXXX.txt)
cat > "$PROMPT_FILE" << 'PROMPT_EOF'
<USER_PROMPT>
PROMPT_EOF
```

Pipe to the CLI tool, then clean up:

```bash
cat "$PROMPT_FILE" | <cli-command> 2>/dev/null
rm -f "$PROMPT_FILE"
```

If `mktemp` is unavailable, fall back to a deterministic path: `/tmp/<skill>-prompt.txt`.

The `-p ""` flag (Claude, Gemini) or no `-p` flag (Codex) triggers non-interactive mode while stdin provides the actual prompt.

**Why `2>/dev/null`?** CLI tools emit progress indicators, ANSI escape codes, and status messages on stderr. These are useful interactively but pollute captured output when running programmatically.

For **short, simple follow-up prompts** (e.g., session resume) that contain no special characters, passing directly via `-p "<text>"` or as a positional argument is acceptable.

## Standard Timeout

All CLI dispatches use **600000ms** (10 minutes) on the Bash tool. This accommodates long-running analysis tasks while preventing indefinite hangs.

## Session Resume — Empty Prompt

If the user invokes a resume command without a prompt (e.g., `/codex resume`, `/gemini resume`, `/claude resume`), use `AskUserQuestion` to ask what they want to follow up on before dispatching.

## Critical Evaluation

The delegated model is a peer, not an authority. After every response:

- **Trust your own knowledge** when confident. If the delegated model
  claims something you know is incorrect, push back.
- **Research disagreements** using WebSearch or project documentation
  before accepting claims.
- **Remember knowledge cutoffs** — the delegated model may not know
  about recent releases, APIs, or changes.
- **Don't defer blindly** — evaluate suggestions critically, especially
  regarding model names, library versions, API changes, and best practices.

### Self-Evaluation Vigilance

When the host model evaluates output from the same model family (e.g., Claude evaluating Claude), be especially vigilant about shared blind spots. If both instances agree, that's not necessarily stronger evidence — they may share the same training biases. Highlight when independent verification (WebSearch, docs) would add value over two instances of the same model reaching the same conclusion.

## When You Disagree

1. State the disagreement clearly to the user with evidence.
2. Provide supporting evidence (your own knowledge, web search results, docs).
3. Optionally resume the session to discuss as a peer AI. Use the
   appropriate resume command for the delegated model. Frame as:
   "This is Claude (<your current model name>) following up. I disagree
   with [X] because [evidence]. What's your take?"
   **Note:** A debate resume becomes "the last session." Inform the user
   that the resume command will now continue the debate thread, not the
   original prompt.
4. Frame disagreements as discussions — either AI could be wrong.
5. Let the user decide how to proceed if there is genuine ambiguity.

## Error Handling

| Condition | Action |
|---|---|
| CLI not installed / not on PATH | Report: "[tool] CLI not found. Install it or check your PATH." Do not attempt to install it. |
| Authentication failure (API key missing/expired) | Report: "[tool] authentication failed. Check your API key or auth setup." |
| Non-zero exit code | Report failure, show first line of stderr if available, suggest checking CLI version or auth setup |
| Empty output | Report that the model returned nothing, suggest rephrasing the prompt |
| Partial/warning output | Summarize warnings and ask user how to proceed |
| Timeout | Report timeout, suggest a simpler prompt or lower reasoning/effort (see skill-specific timeout suggestions) |
| Rate limiting / quota exhaustion | Report: "[tool] rate limited or quota exceeded. Wait and retry, or check your plan limits." |
| Malformed output (binary, garbled) | Report: "[tool] returned unparseable output. Try again or rephrase the prompt." |

## Interface Contract

These delegation skills expose resume interfaces documented in `shared/skill-interfaces.md`. If you modify the resume syntax or behavior, update the interface contract and all callers listed there.
