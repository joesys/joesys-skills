---
name: claude
description: Use when the user invokes /claude to delegate a prompt to Claude Code CLI, or /claude resume to continue a previous Claude session
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
3. Assemble and run the command (use 600000ms timeout on the Bash tool):
   ```bash
   claude --model opus --effort high --permission-mode plan --name "<derived-name>" -p "<USER_PROMPT>" 2>/dev/null
   ```
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

## Error Handling

| Condition | Action |
|---|---|
| Non-zero exit code | Report failure, suggest checking `claude --version` or auth setup |
| Empty output | Report that Claude returned nothing, suggest rephrasing the prompt |
| Partial/warning output | Summarize warnings and ask user how to proceed |
| Timeout | Report timeout, suggest lowering effort (`--effort medium`) or switching to `sonnet` |

## Critical Evaluation

Claude is a peer, not an authority — even when it is the same model as you. After every Claude response:

- **Trust your own knowledge** when confident. If the spawned Claude claims something you know is incorrect, push back.
- **Research disagreements** using WebSearch or project documentation before accepting claims.
- **Remember context differences** — the spawned Claude lacks your conversation context and may make assumptions.
- **Don't defer blindly** — evaluate suggestions critically, especially regarding model names, library versions, API changes, and best practices.

### Self-Evaluation Vigilance

Unlike Codex and Gemini, this is Claude evaluating Claude. Be especially vigilant about shared blind spots — if both instances agree, that's not necessarily stronger evidence. Highlight when independent verification (WebSearch, docs) would add value over two instances of the same model reaching the same conclusion.

### When You Disagree

1. State the disagreement clearly to the user with evidence.
2. Provide supporting evidence (your own knowledge, web search results, docs).
3. Optionally resume the Claude session to discuss as a peer AI:
   ```bash
   claude -c -p "This is Claude (<your current model name>) from the parent session. I disagree with [X] because [evidence]. What's your take?" 2>/dev/null
   ```
   **Note:** A debate resume becomes the continued session. Inform the user that `/claude resume` will now continue the debate thread, not the original prompt.
4. Frame disagreements as discussions — same model, different context means different conclusions are valid.
5. Let the user decide how to proceed if there is genuine ambiguity.
