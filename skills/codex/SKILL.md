---
name: codex
version: "1.0.0"
description: "Use when the user invokes /codex to delegate a prompt to OpenAI Codex CLI, or /codex resume to continue a previous Codex session"
---

# Codex Skill

Delegate prompts to OpenAI's Codex CLI and critically evaluate the output.

## Defaults

- **Model:** `gpt-5.4`
- **Reasoning effort:** `xhigh`
- **Sandbox:** `read-only`
- **Always use:** `--skip-git-repo-check`, `2>/dev/null`

## User Preferences

Read `shared/skill-context.md` for the full protocol. Load `.claude/skill-context/preferences.md` if it exists. Do not invoke `/preferences` on first contact — delegation is a pass-through operation and should not be interrupted by interviews. Shared communication style preferences shape the critical evaluation phase (how you present your assessment of Codex's output to the user).

## Running a Task

1. Parse the user's `/codex` arguments for any overrides:
   - `--model <MODEL>` overrides the default model
   - `--sandbox <MODE>` overrides the default sandbox (`read-only`, `workspace-write`, `danger-full-access`)
   - Any remaining text is the prompt
2. Assemble and run the command (use 600000ms timeout on the Bash tool).

   Deliver the prompt using the temp-file-and-pipe pattern from `shared/delegation-common.md` § Prompt Delivery. Use `mktemp` for platform-adaptive temp files. For short, simple prompts with no special characters, passing directly as a positional argument is acceptable.

   ```bash
   PROMPT_FILE=$(mktemp /tmp/codex-prompt-XXXXXX.txt)
   cat > "$PROMPT_FILE" << 'PROMPT_EOF'
   <USER_PROMPT>
   PROMPT_EOF
   cat "$PROMPT_FILE" | codex exec --model gpt-5.4 -c model_reasoning_effort="xhigh" \
     --sandbox read-only --skip-git-repo-check 2>/dev/null
   rm -f "$PROMPT_FILE"
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

## Known Limitations

- **Resume fragility:** Codex only supports `--last` for session resume — there is no named-session or index-based resume. If you start another Codex session between the original run and a resume attempt, `--last` will resume the newer session, not the one you intended. This is a CLI limitation, not a skill issue. Warn the user if they attempt `/codex resume` after running other Codex commands.

## Critical Evaluation & Error Handling

Read `shared/delegation-common.md` and apply to Codex.
Timeout suggestion: lower reasoning effort (`-c model_reasoning_effort="high"`).
