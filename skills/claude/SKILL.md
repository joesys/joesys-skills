---
name: claude
description: "Use when the user invokes /claude to delegate a prompt to Claude Code CLI, or /claude resume to continue a previous Claude session"
---

# Claude Skill

Delegate prompts to Anthropic's Claude Code CLI and critically evaluate the output.

## Defaults

- **Model:** `opus`
- **Effort:** `high`
- **Permission mode:** `plan` (read-only)
- **Always use:** `-p` flag for non-interactive mode, `2>/dev/null`

## Running a Task

1. Parse the user's `/claude` arguments for any overrides:
   - `--model <MODEL>` overrides the default model (e.g., `sonnet`, `haiku`, `opus[1m]`)
   - `--permission-mode <MODE>` overrides the default permission mode (`default`, `acceptEdits`, `dontAsk`)
   - `--effort <LEVEL>` overrides the default effort (`low`, `medium`, `max`)
   - `--bare` enables bare mode (skips hooks, plugins, CLAUDE.md, MCP servers)
   - Any remaining text is the prompt
2. Derive a short session name from the prompt topic (kebab-case, 2-4 words).
3. Assemble and run the command (use 600000ms timeout on the Bash tool).

   **For short, simple prompts** (no quotes, backticks, dollar signs, or other shell metacharacters), pass directly:
   ```bash
   claude --model opus --effort high --permission-mode plan --name "<derived-name>" -p "<USER_PROMPT>" 2>/dev/null
   ```

   **For long or complex prompts** (contains special characters, multi-line, or very long), write to a temp file and pipe via stdin to avoid shell quoting issues:
   ```bash
   cat > /tmp/claude-prompt.txt << 'PROMPT_EOF'
   <USER_PROMPT>
   PROMPT_EOF
   cat /tmp/claude-prompt.txt | claude --model opus --effort high --permission-mode plan \
     --name "<derived-name>" -p "" 2>/dev/null
   rm -f /tmp/claude-prompt.txt
   ```
   The `-p ""` flag triggers non-interactive mode while stdin provides the actual prompt.
4. Present the output clearly labeled as **Claude's response**.
5. Critically evaluate the output (see Critical Evaluation below).
6. Provide a brief summary: "Here's what Claude said, here's what I think."
7. Inform the user: "You can resume this session with `/claude resume` or `/claude resume <name>`."

## Session Resume

When the user invokes `/claude resume`:

1. If no prompt is provided, use `AskUserQuestion` to ask what they want to follow up on.
2. Determine the resume target:
   - `/claude resume <PROMPT>` — continue the most recent session:
     ```bash
     claude -c -p "<FOLLOW_UP_PROMPT>" 2>/dev/null
     ```
   - `/claude resume <NAME> <PROMPT>` — resume a specific named session:
     ```bash
     claude --resume "<NAME>" -p "<FOLLOW_UP_PROMPT>" 2>/dev/null
     ```
3. **Resume rules:**
   - Resumed sessions inherit model, effort, and permission mode from the original run
   - `--model`, `--effort`, `--permission-mode` CAN be overridden on resume if the user explicitly requests it
   - `--bare` CAN be added on resume if the user explicitly requests it
4. After resume, follow the same output flow: present, evaluate, summarize, offer resume.

## Critical Evaluation & Error Handling

Read `shared/delegation-common.md` and apply to Claude.
Timeout suggestion: lower effort (`--effort medium`) or switch to `sonnet`.

### Self-Evaluation Vigilance

Unlike Codex and Gemini, this is Claude evaluating Claude. Be especially vigilant about shared blind spots — if both instances agree, that's not necessarily stronger evidence. Highlight when independent verification (WebSearch, docs) would add value over two instances of the same model reaching the same conclusion.
