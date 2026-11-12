# Shared Delegation Flow

Read this file before running `/codex`, `/claude`, `/antigravity`, `/grok`, or `/ai-council`. It is the one home for the shared flow: prompt delivery, presenting the answer, critical evaluation, and failures. Each skill file keeps only its own CLI commands and quirks. Current CLI command templates live in `shared/model-defaults.md`.

---

## The Flow

1. **Delegate. Do not answer yourself.** The user wants the other model's view. Your own view comes after it, as an evaluation.
2. **Never send an empty prompt.** If the prompt is empty (for example, a bare `/codex resume`), ask the user what to send.
3. **Stay read-only.** The CLI runs in its read-only mode from `shared/model-defaults.md`. The skill itself does not change the user's project either, unless the user overrides the mode on purpose.
4. **Show the full response first, word for word.** Label it as that model's response. Do not shorten it, summarize it, or mix your comments into it.
5. **Then evaluate it critically** (see Critical Evaluation). Never skip this step.
6. **End with a short summary:** what the model said, and what you think.
7. **Offer the resume command** for the session.

Preferences: read `.claude/skill-context/preferences.md` if present (see `shared/skill-context.md`). Preferences shape only your evaluation and summary. The delegated model gets the user's prompt unchanged.

---

## Prompt Delivery

Write the prompt to a temp file with a single-quoted heredoc, pipe it to the CLI on stdin, then delete the file. Use a 10-minute timeout (600000 ms) on every Bash dispatch; CLI runs are slow and a shorter timeout causes false failures.

```bash
PROMPT_FILE=$(mktemp /tmp/<skill>-prompt-XXXXXX.txt)
cat > "$PROMPT_FILE" << 'PROMPT_EOF'
<USER_PROMPT>
PROMPT_EOF
cat "$PROMPT_FILE" | <cli-command>
rm -f "$PROMPT_FILE"
```

- **Why a temp file:** the quoted heredoc stops the shell from expanding `$`, backticks, and `!`. Long prompts passed as arguments break on these characters.
- **Why `2>/dev/null` in the templates:** CLIs write progress bars and color codes to stderr, which pollute the captured answer. Exceptions: Codex prints its `session id:` line on stderr, so capture stderr to a file when resume matters. Grok reports an answer that was cut short only on stderr, so always capture its stderr to a file and show it.
- **Grok does not read stdin:** pass the same temp file with `--prompt-file "$PROMPT_FILE"` instead of the pipe.
- **Short resume prompts:** a plain follow-up with no quotes, code, or special characters may go inline (`-p "<text>"` for Claude, a positional prompt for Codex). When in doubt, use the temp file. Antigravity always takes the prompt on stdin, and Grok always takes the temp file.

---

## Critical Evaluation

The delegated model is a peer, not an authority.

- **Trust your own knowledge** when you are confident. If the model claims something you know is wrong, say so.
- **Check disagreements** with web search or project docs before you accept or reject a claim.
- **Remember knowledge cutoffs.** The model may not know recent releases, APIs, or changes.
- **Do not defer blindly** on model names, library versions, API changes, or best practices.

**Same-family evaluation:** when Claude evaluates Claude, both share blind spots. Agreement between them is weak evidence. Say when an independent check (web search, docs) would add value.

### When You Disagree

1. State the disagreement clearly, with evidence and sources.
2. Optionally resume the session and discuss it as a peer, for example: "This is Claude (<your model name>) following up. I disagree with [X] because [evidence]. What's your take?" Tell the user that the resume command now continues this debate, not the original prompt.
3. Treat it as a discussion. Either model could be wrong.
4. When doubt remains, let the user decide.

---

## Failures

Report the failure plainly, with the first line of stderr if there is one. Never install or reconfigure the CLI. On a timeout, give the skill's timeout tip (for example, lower the reasoning effort) or suggest a simpler prompt. If the model returns nothing, or the output is garbled or partial, say so and ask how to proceed.

---

## Interface Contract

The resume commands of these skills are a contract in `shared/skill-interfaces.md`. If you change resume syntax or behavior, update that file and every caller it lists.
