---
name: claude
version: "1.1.0"
description: "Use when the user invokes /claude to delegate a prompt to Claude Code CLI, or /claude resume to continue a previous Claude session. SKIP if the user wants you to answer directly — this skill exists to consult a separate Claude instance, not to substitute your own answer."
---

# Claude Skill

Delegate prompts to Anthropic's Claude Code CLI and critically evaluate the output.

## Out of Scope

This skill MUST NOT:
- Answer the question itself instead of delegating. The user invoked this skill to get the *other* Claude instance's take — substituting your own answer defeats the purpose.
- Skip the critical-evaluation step. Always surface your honest assessment after the delegated model responds.
- Modify the user's project (files, git state, settings) as part of the dispatch. The CLI runs read-only by default per `shared/model-defaults.md`; the skill itself never writes either.
- Save the delegated response to a file. If the user wants it saved, they'll ask in a follow-up turn.
- Combine outputs across multiple invocations into a synthesis. That's `/ai-council`'s job.

## Preflight

Before dispatching, **MUST**:
1. Read `shared/model-defaults.md` § Claude CLI for the current model identifier, effort level, permission mode, and required flags. Never hardcode values.
2. Confirm the user's prompt is non-empty. For `/claude resume` with no prompt, use `AskUserQuestion` to ask what they want to follow up on.

## User Preferences

Read `shared/skill-context.md` for the full protocol. Load `.claude/skill-context/preferences.md` if it exists. **MUST NOT invoke** `/preferences` on first contact — delegation is a pass-through and should not be interrupted by interviews. Shared communication-style preferences shape the critical-evaluation phase only.

## Running a Task

1. Parse `/claude` arguments for overrides:
   - `--model <MODEL>` — override default model (e.g., `sonnet`, `haiku`, `opus[1m]`)
   - `--permission-mode <MODE>` — override default (`default`, `acceptEdits`, `dontAsk`)
   - `--effort <LEVEL>` — override default (`low`, `medium`, `high`, `max`)
   - `--bare` — bare mode (skips hooks, plugins, CLAUDE.md, MCP servers)
   - Any remaining text is the prompt
2. Derive a short session name from the prompt topic (kebab-case, 2–4 words).
3. Assemble and dispatch the command (use 600000ms timeout on the Bash tool).

   Use the temp-file-and-pipe pattern from `shared/delegation-common.md` § Prompt Delivery. For short, simple prompts with no special characters, direct `-p "<text>"` is acceptable.

   Substitute `<CLAUDE_CMD>` with the current invocation from `shared/model-defaults.md` § Claude CLI, layering any user overrides on top. Append `--name "<derived-name>"` for resumability.

   ```bash
   PROMPT_FILE=$(mktemp /tmp/claude-prompt-XXXXXX.txt)
   cat > "$PROMPT_FILE" << 'PROMPT_EOF'
   <USER_PROMPT>
   PROMPT_EOF
   cat "$PROMPT_FILE" | <CLAUDE_CMD> --name "<derived-name>"
   rm -f "$PROMPT_FILE"
   ```
4. **MUST present Claude's full response verbatim** — clearly labeled as **Claude's response** — *before* any assessment. No truncation, no summarization, no interleaving your own commentary.
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
   - Resumed sessions inherit model, effort, and permission mode from the original run.
   - `--model`, `--effort`, `--permission-mode`, `--bare` MAY be overridden on resume only when the user explicitly requests it.
4. After resume, follow the same output flow: present full response → evaluate → summarize → offer resume.

## Critical Evaluation & Error Handling

Read `shared/delegation-common.md` and apply to Claude.
**Timeout suggestion:** lower effort (`--effort medium`) or switch to `sonnet`.

### Self-Evaluation Vigilance

Unlike `/codex` and `/antigravity`, this is Claude evaluating Claude. **MUST be especially vigilant** about shared blind spots — if both instances agree, that is *not* automatically stronger evidence. **MUST flag** when independent verification (WebSearch, docs) would add value over two instances of the same model reaching the same conclusion.
