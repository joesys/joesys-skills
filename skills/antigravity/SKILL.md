---
name: antigravity
description: "Use when the user invokes /antigravity to delegate a prompt to Google Antigravity CLI (agy), or /antigravity resume to continue a previous Antigravity session. SKIP if the user wants you to answer directly — this skill exists to consult Antigravity, not to substitute your own answer."
---

# Antigravity Skill

Delegate prompts to Google's Antigravity CLI (`agy`) and critically evaluate the output.

## Out of Scope

This skill MUST NOT:
- Answer the question itself instead of delegating. The user invoked this skill to get Antigravity's take — substituting your own answer defeats the purpose.
- Skip the critical-evaluation step. Always surface your honest assessment after the delegated model responds.
- Modify the user's project (files, git state, settings) as part of the dispatch. The CLI runs read-only by default per `shared/model-defaults.md`; the skill itself never writes either.
- Save the delegated response to a file. If the user wants it saved, they'll ask in a follow-up turn.
- Combine outputs across multiple invocations into a synthesis. That's `/ai-council`'s job.

## Preflight

Before dispatching, **MUST**:
1. Read `shared/model-defaults.md` § Antigravity for the current required flags — resolve `shared/...` against the plugin root (two levels above this SKILL.md), never the project's working directory. Never hardcode values.
2. Confirm the user's prompt is non-empty. For `/antigravity resume` with no prompt, use `AskUserQuestion` to ask what they want to follow up on.

## User Preferences

Read `shared/skill-context.md` for the full protocol. Load `.claude/skill-context/preferences.md` if it exists. **MUST NOT invoke** `/preferences` on first contact — delegation is a pass-through and should not be interrupted by interviews. Shared communication-style preferences shape the critical-evaluation phase only.

## Running a Task

1. Parse `/antigravity` arguments for overrides:
   - Any remaining text is the prompt
2. Use the temp-file-and-pipe pattern from `shared/delegation-common.md` § Prompt Delivery (use 600000ms timeout on the Bash tool). Substitute `<AGY_CMD>` with the current invocation from `shared/model-defaults.md` § Antigravity.
   ```bash
   PROMPT_FILE=$(mktemp /tmp/antigravity-prompt-XXXXXX.txt)
   cat > "$PROMPT_FILE" << 'PROMPT_EOF'
   <USER_PROMPT>
   PROMPT_EOF
   cat "$PROMPT_FILE" | <AGY_CMD>
   rm -f "$PROMPT_FILE"
   ```

   The adapter always reads the prompt from **stdin** — do **not** pass `-p` (the adapter appends it). The same stdin-pipe pattern is used for session resume.
3. **MUST present Antigravity's full response verbatim** — clearly labeled as **Antigravity's response** — *before* any assessment. No truncation, no summarization, no interleaving your own commentary.
4. Critically evaluate the output (see Critical Evaluation below).
5. Provide a brief summary: "Here's what Antigravity said, here's what I think."
6. Inform the user: "You can resume this session with `/antigravity resume`."

## Session Resume

When the user invokes `/antigravity resume`:

1. If no prompt is provided, use `AskUserQuestion` to ask what they want to follow up on.
2. Determine the resume target. `<ADAPTER>` is the **absolute path** to `scripts/agy_adapter.py` under the plugin root (two levels above this SKILL.md) — the project's working directory does not contain the adapter:
   - `/antigravity resume <PROMPT>` — resume the latest session. Deliver the follow-up
     prompt via the same temp-file-and-stdin pattern as the initial dispatch:
     ```bash
     cat "$PROMPT_FILE" | python <ADAPTER> -c
     ```
   - `/antigravity resume <ID> <PROMPT>` — resume a specific session by conversation ID:
     ```bash
     cat "$PROMPT_FILE" | python <ADAPTER> --conversation <ID>
     ```
3. **Resume rules:**
   - Resumed sessions inherit settings from the original run.
4. After resume, follow the same output flow: present full response → evaluate → summarize → offer resume.

## Critical Evaluation & Error Handling

Read `shared/delegation-common.md` and apply to Antigravity.
**Timeout suggestion:** raise `AGY_ADAPTER_TIMEOUT` (see `shared/model-defaults.md` § Antigravity) or simplify the prompt.
