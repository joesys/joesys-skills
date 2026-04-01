---
name: codex
description: "Use when the user invokes /codex to delegate a prompt to OpenAI Codex CLI, or /codex resume to continue a previous Codex session"
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

## Critical Evaluation & Error Handling

Read `shared/delegation-common.md` and apply to Codex.
Timeout suggestion: lower reasoning effort (`-c model_reasoning_effort="high"`).
