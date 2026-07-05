---
name: codex
version: "1.1.0"
description: "Use when the user invokes /codex to delegate a prompt to OpenAI Codex CLI, or /codex resume to continue a previous Codex session. SKIP if the user wants you to answer directly — this skill exists to consult GPT, not to substitute your own answer."
---

# Codex Skill

Delegate prompts to OpenAI's Codex CLI and critically evaluate the output.

## Out of Scope

This skill MUST NOT:
- Answer the question itself instead of delegating. The user invoked this skill to get GPT's take — substituting your own answer defeats the purpose.
- Skip the critical-evaluation step. Always surface your honest assessment after the delegated model responds.
- Modify the user's project (files, git state, settings) as part of the dispatch. The CLI runs read-only by default per `shared/model-defaults.md`; the skill itself never writes either.
- Save the delegated response to a file. If the user wants it saved, they'll ask in a follow-up turn.
- Combine outputs across multiple invocations into a synthesis. That's `/ai-council`'s job.

## Preflight

Before dispatching, **MUST**:
1. Read `shared/model-defaults.md` § Codex for the current model identifier, reasoning effort, sandbox, and required flags. Never hardcode values.
2. Confirm the user's prompt is non-empty. For `/codex resume` with no prompt, use `AskUserQuestion` to ask what they want to follow up on.

## User Preferences

Read `shared/skill-context.md` for the full protocol. Load `.claude/skill-context/preferences.md` if it exists. **MUST NOT invoke** `/preferences` on first contact — delegation is a pass-through and should not be interrupted by interviews. Shared communication-style preferences shape the critical-evaluation phase only.

## Running a Task

1. Parse `/codex` arguments for overrides:
   - `--model <MODEL>` — override default model
   - `--sandbox <MODE>` — override default sandbox (`read-only`, `workspace-write`, `danger-full-access`)
   - Any remaining text is the prompt
2. Assemble and dispatch the command (use 600000ms timeout on the Bash tool).

   Use the temp-file-and-pipe pattern from `shared/delegation-common.md` § Prompt Delivery. For short, simple prompts with no special characters, passing directly as a positional argument is acceptable.

   Substitute `<CODEX_CMD>` with the current invocation from `shared/model-defaults.md` § Codex, layering any user `--model` or `--sandbox` overrides on top — but replace the template's trailing `2>/dev/null` with `2>"$CODEX_LOG"`: Codex prints its `session id:` banner on stderr, and capturing it is what makes resume reliable.

   ```bash
   PROMPT_FILE=$(mktemp /tmp/codex-prompt-XXXXXX.txt)
   CODEX_LOG=$(mktemp /tmp/codex-log-XXXXXX.txt)
   cat > "$PROMPT_FILE" << 'PROMPT_EOF'
   <USER_PROMPT>
   PROMPT_EOF
   cat "$PROMPT_FILE" | <CODEX_CMD>
   grep -m1 "session id:" "$CODEX_LOG"   # keep this ID for /codex resume
   rm -f "$PROMPT_FILE" "$CODEX_LOG"
   ```
3. **MUST present Codex's full response verbatim** — clearly labeled as **Codex's response** — *before* any assessment. No truncation, no summarization, no interleaving your own commentary.
4. Critically evaluate the output (see Critical Evaluation below).
5. Provide a brief summary: "Here's what Codex said, here's what I think."
6. Inform the user: "You can resume this session with `/codex resume`." Include the captured session ID so resume still works even if other Codex sessions run in between.

## Session Resume

When the user invokes `/codex resume`:

1. If no prompt is provided, use `AskUserQuestion` to ask what they want to follow up on.
2. Run the resume command (use 600000ms timeout). Prefer resuming by the session ID captured at dispatch; fall back to `--last` only when no ID is known:
   ```bash
   codex exec resume <SESSION_ID> --skip-git-repo-check "<FOLLOW_UP_PROMPT>" 2>/dev/null
   ```
   ```bash
   codex exec resume --last --skip-git-repo-check "<FOLLOW_UP_PROMPT>" 2>/dev/null
   ```
3. **Resume rules:**
   - `<SESSION_ID>` is the UUID from the dispatch banner (`session id:` line).
   - Resumed sessions inherit model, reasoning effort, and sandbox from the original run.
   - `--skip-git-repo-check` goes after `resume`, not between `exec` and `resume`.
   - `--sandbox` and `--full-auto` are NOT accepted on `codex exec resume`.
   - `--model` MAY be passed on resume only when the user explicitly requests it.
   - If workspace-write is needed on resume, use the config override:
     ```bash
     codex exec resume <SESSION_ID> --skip-git-repo-check -c sandbox_mode="workspace-write" "<FOLLOW_UP_PROMPT>" 2>/dev/null
     ```
   - **MUST NOT use** `--ephemeral` on the initial run, or resume will have no session to continue.
4. After resume, follow the same output flow: present full response → evaluate → summarize → offer resume.

## Known Limitations

- **Session ID lives on stderr:** `codex exec` prints its `session id:` banner on stderr only — a `2>/dev/null` dispatch discards it. If the ID was not captured, only `--last` resume is possible, and `--last` resumes the *newest* session: **MUST warn** the user if they attempt a `--last` resume after other Codex commands have run.

## Critical Evaluation & Error Handling

Read `shared/delegation-common.md` and apply to Codex.
**Timeout suggestion:** lower reasoning effort (`-c model_reasoning_effort="high"`).
