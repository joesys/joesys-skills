---
name: codex
description: Use when the user invokes /codex to delegate a prompt to OpenAI Codex CLI, or /codex resume to continue a previous Codex session
---

# Codex Skill

Delegate prompts to OpenAI's Codex CLI and critically evaluate the output.

## Defaults

- **Model:** `gpt-5.4`
- **Reasoning effort:** `xhigh`
- **Sandbox:** `read-only`
- **Always use:** `--skip-git-repo-check`, `2>/dev/null`

## Running a Task

1. Parse the user's `/codex` arguments for any overrides:
   - `--model <MODEL>` overrides the default model
   - `--sandbox <MODE>` overrides the default sandbox (`read-only`, `workspace-write`, `danger-full-access`)
   - Any remaining text is the prompt
2. Assemble and run the command (use 600000ms timeout on the Bash tool).

   **For short, simple prompts** (no quotes, backticks, dollar signs, or other shell metacharacters), pass directly:
   ```bash
   codex exec --model gpt-5.4 -c model_reasoning_effort="xhigh" \
     --sandbox read-only --skip-git-repo-check "<USER_PROMPT>" 2>/dev/null
   ```

   **For long or complex prompts** (contains special characters, multi-line, or very long), write to a temp file and pipe via stdin to avoid shell quoting issues:
   ```bash
   cat > /tmp/codex-prompt.txt << 'PROMPT_EOF'
   <USER_PROMPT>
   PROMPT_EOF
   cat /tmp/codex-prompt.txt | codex exec --model gpt-5.4 -c model_reasoning_effort="xhigh" \
     --sandbox read-only --skip-git-repo-check 2>/dev/null
   rm -f /tmp/codex-prompt.txt
   ```
3. Present the output clearly labeled as **Codex's response**.
4. Critically evaluate the output (see Critical Evaluation below).
5. Provide a brief summary: "Here's what Codex said, here's what I think."
6. Inform the user: "You can resume this session with `/codex resume`."

## Session Resume

When the user invokes `/codex resume`:

1. If no prompt is provided, use `AskUserQuestion` to ask what they want to follow up on.
2. Run the resume command (use 600000ms timeout):
   ```bash
   codex exec resume --last --skip-git-repo-check "<FOLLOW_UP_PROMPT>" 2>/dev/null
   ```
3. **Resume rules:**
   - Resumed sessions inherit model, reasoning effort, and sandbox from the original run
   - `--skip-git-repo-check` goes after `resume`, not between `exec` and `resume`
   - `--sandbox` is NOT available on `codex exec resume`
   - Exception: `--model` and `--full-auto` CAN be passed on resume if the user explicitly requests them
   - If workspace-write is needed on resume, use `--full-auto`
     ```bash
     codex exec resume --last --skip-git-repo-check --full-auto "<FOLLOW_UP_PROMPT>" 2>/dev/null
     ```
   - Do NOT use `--ephemeral` on the initial run, or resume will have no session to continue
4. After resume, follow the same output flow: present, evaluate, summarize, offer resume.

## Error Handling

| Condition | Action |
|---|---|
| Non-zero exit code | Report failure, suggest checking `codex --version` or auth setup |
| Empty output | Report that Codex returned nothing, suggest rephrasing the prompt |
| Partial/warning output | Summarize warnings and ask user how to proceed |
| Timeout | Report timeout, suggest a simpler prompt or lower reasoning effort (`-c model_reasoning_effort="high"`) |

## Critical Evaluation

Codex is a peer, not an authority. After every Codex response:

- **Trust your own knowledge** when confident. If Codex claims something you know is incorrect, push back.
- **Research disagreements** using WebSearch or project documentation before accepting Codex's claims.
- **Remember knowledge cutoffs** — Codex may not know about recent releases, APIs, or changes.
- **Don't defer blindly** — evaluate suggestions critically, especially regarding model names, library versions, API changes, and best practices.

### When You Disagree

1. State the disagreement clearly to the user with evidence.
2. Provide supporting evidence (your own knowledge, web search results, docs).
3. Optionally resume the Codex session to discuss as a peer AI. For long debate prompts, use the stdin pipe pattern:
   ```bash
   codex exec resume --last --skip-git-repo-check \
     "This is Claude (<your current model name>) following up. I disagree with [X] because [evidence]. What's your take?" 2>/dev/null
   ```
   **Note:** A debate resume becomes "the last session." Inform the user that `/codex resume` will now continue the debate thread, not the original prompt.
4. Frame disagreements as discussions — either AI could be wrong.
5. Let the user decide how to proceed if there is genuine ambiguity.
