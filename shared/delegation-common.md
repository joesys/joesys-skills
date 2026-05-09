# Shared Delegation Infrastructure

Reference file for `/codex`, `/gemini`, `/claude`, and `/ai-council`. Read this file before dispatching the underlying CLI — it is the canonical source for prompt delivery, sequencing, critical evaluation, and error handling.

---

## Preflight & Sequencing Rules

These rules are absolute. Every delegation skill follows them.

1. **MUST deliver prompts via stdin pipe from a temp file.** Direct `-p "<text>"` is permitted only for short, simple resume prompts with no special characters.
2. **MUST present the delegated CLI's full response verbatim before any assessment.** No truncation, no summarization, no interleaving your own commentary into the model's output. The user's mental model: "this is what the other model said" → "this is what Claude thinks of it."
3. **MUST run the critical-evaluation step after the response is shown.** Skipping the assessment turns delegation into pass-through plagiarism.
4. **MUST NOT answer the question yourself instead of delegating.** The user invoked this skill to get the *other model's* take. Substituting your own answer defeats the invocation.
5. **MUST use 600000ms timeout** on every Bash dispatch. CLI runs are bursty; shorter timeouts produce false failures.

---

## Prompt Delivery

### Platform-Adaptive Temp Files

Use `mktemp` to create temp files portably (Linux, macOS, Windows Git Bash):

```bash
PROMPT_FILE=$(mktemp /tmp/<skill>-prompt-XXXXXX.txt)
cat > "$PROMPT_FILE" << 'PROMPT_EOF'
<USER_PROMPT>
PROMPT_EOF
```

Pipe to the CLI, then clean up:

```bash
cat "$PROMPT_FILE" | <cli-command> 2>/dev/null
rm -f "$PROMPT_FILE"
```

If `mktemp` is unavailable, fall back to a deterministic path: `/tmp/<skill>-prompt.txt`.

The `-p ""` flag (Claude, Gemini) or no `-p` flag (Codex) triggers non-interactive mode while stdin provides the actual prompt.

**Why `2>/dev/null`?** CLI tools emit progress indicators, ANSI escape codes, and status messages on stderr. These pollute captured output when running programmatically.

**Why a temp file?** Single-quoted heredoc delimiters prevent shell expansion of `$`, backticks, and `!`. Long prompts as positional `-p "..."` arguments trip on these characters.

### Direct `-p` exception

For session resume with simple follow-up text (no quotes, no code blocks, no special chars), `-p "<text>"` is acceptable. When in doubt, use a temp file — there is no penalty for the safer path.

---

## Session Resume — Empty Prompt

If the user invokes a resume command with no prompt (e.g., `/codex resume`), use `AskUserQuestion` to ask what they want to follow up on **before** dispatching. Never dispatch an empty prompt.

---

## Critical Evaluation

The delegated model is a peer, not an authority. After every response:

- **Trust your own knowledge** when confident. If the delegated model claims something you know is incorrect, push back.
- **Research disagreements** using WebSearch or project documentation before accepting claims.
- **Remember knowledge cutoffs.** The delegated model may not know about recent releases, APIs, or changes.
- **Do not defer blindly.** Evaluate suggestions critically — model names, library versions, API changes, best practices.

### Self-Evaluation Vigilance

When the host model evaluates output from the same family (Claude evaluating Claude), shared blind spots compound. **MUST flag** when independent verification (WebSearch, docs) would add value over two instances of the same model agreeing.

### When You Disagree

1. State the disagreement clearly with evidence.
2. Cite supporting sources (your own knowledge, web search, docs).
3. Optionally resume the session to discuss as a peer AI:
   > "This is Claude (<your current model name>) following up. I disagree with [X] because [evidence]. What's your take?"

   **Note:** A debate resume becomes "the last session." Inform the user that the resume command will now continue the debate thread, not the original prompt.
4. Frame disagreements as discussions — either AI could be wrong.
5. Let the user decide how to proceed when ambiguity remains.

---

## Error Handling

| Condition | Action |
|---|---|
| CLI not installed / not on PATH | Report: "[tool] CLI not found. Install it or check your PATH." Do not attempt to install it. |
| Authentication failure (API key missing/expired) | Report: "[tool] authentication failed. Check your API key or auth setup." |
| Non-zero exit code | Report failure, show first line of stderr if available, suggest checking CLI version or auth setup. |
| Empty output | Report that the model returned nothing, suggest rephrasing the prompt. |
| Partial/warning output | Summarize warnings and ask the user how to proceed. |
| Timeout | Report timeout, suggest a simpler prompt or lower reasoning/effort (see skill-specific timeout suggestions). |
| Rate limiting / quota exhaustion | Report: "[tool] rate limited or quota exceeded. Wait and retry, or check your plan limits." |
| Malformed output (binary, garbled) | Report: "[tool] returned unparseable output. Try again or rephrase the prompt." |

---

## Interface Contract

These delegation skills expose resume interfaces documented in `shared/skill-interfaces.md`. **Before modifying** the resume syntax or behavior, **MUST update** the interface contract and every caller listed there.
