---
name: gemini
version: "1.1.0"
description: "Use when the user invokes /gemini to delegate a prompt to Google Gemini CLI, /gemini resume to continue a previous Gemini session, or /gemini sessions to list available sessions. SKIP if the user wants you to answer directly — this skill exists to consult Gemini, not to substitute your own answer."
---

# Gemini Skill

Delegate prompts to Google's Gemini CLI and critically evaluate the output.

## Out of Scope

This skill MUST NOT:
- Answer the question itself instead of delegating. The user invoked this skill to get Gemini's take — substituting your own answer defeats the purpose.
- Skip the critical-evaluation step. Always surface your honest assessment after the delegated model responds.
- Modify the user's project (files, git state, settings) as part of the dispatch. The CLI runs read-only by default per `shared/model-defaults.md`; the skill itself never writes either.
- Save the delegated response to a file. If the user wants it saved, they'll ask in a follow-up turn.
- Combine outputs across multiple invocations into a synthesis. That's `/ai-council`'s job.

## Preflight

Before dispatching, **MUST**:
1. Read `shared/model-defaults.md` § Gemini for the current model identifier, approval mode, and required flags. Never hardcode values.
2. Confirm the user's prompt is non-empty. For `/gemini resume` with no prompt, use `AskUserQuestion` to ask what they want to follow up on.

## User Preferences

Read `shared/skill-context.md` for the full protocol. Load `.claude/skill-context/preferences.md` if it exists. **MUST NOT invoke** `/preferences` on first contact — delegation is a pass-through and should not be interrupted by interviews. Shared communication-style preferences shape the critical-evaluation phase only.

## Running a Task

1. Parse `/gemini` arguments for overrides:
   - `--model <MODEL>` — override default model
   - `--approval-mode <MODE>` — override default (`default`, `auto_edit`, `yolo`)
   - Any remaining text is the prompt
2. Use the temp-file-and-pipe pattern from `shared/delegation-common.md` § Prompt Delivery (use 600000ms timeout on the Bash tool). Substitute `<GEMINI_CMD>` with the current invocation from `shared/model-defaults.md` § Gemini, layering any user overrides on top.
   ```bash
   PROMPT_FILE=$(mktemp /tmp/gemini-prompt-XXXXXX.txt)
   cat > "$PROMPT_FILE" << 'PROMPT_EOF'
   <USER_PROMPT>
   PROMPT_EOF
   cat "$PROMPT_FILE" | <GEMINI_CMD>
   rm -f "$PROMPT_FILE"
   ```

   For short, simple follow-up prompts (e.g., session resume) with no special characters, direct `-p "<text>"` is acceptable.
3. **MUST present Gemini's full response verbatim** — clearly labeled as **Gemini's response** — *before* any assessment. No truncation, no summarization, no interleaving your own commentary.
4. Critically evaluate the output (see Critical Evaluation below).
5. Provide a brief summary: "Here's what Gemini said, here's what I think."
6. Inform the user: "You can resume this session with `/gemini resume` or list sessions with `/gemini sessions`."

## Session Resume

When the user invokes `/gemini resume`:

1. If no prompt is provided, use `AskUserQuestion` to ask what they want to follow up on.
2. Determine the resume target:
   - `/gemini resume <PROMPT>` — resume the latest session:
     ```bash
     gemini --resume latest -p "<FOLLOW_UP_PROMPT>" 2>/dev/null
     ```
   - `/gemini resume <INDEX> <PROMPT>` — resume a specific session by index:
     ```bash
     gemini --resume <INDEX> -p "<FOLLOW_UP_PROMPT>" 2>/dev/null
     ```
3. **Resume rules:**
   - Resumed sessions inherit model and approval mode from the original run.
   - `--model` and `--approval-mode` MAY be overridden on resume only when the user explicitly requests it.
4. After resume, follow the same output flow: present full response → evaluate → summarize → offer resume.

## Session Listing

When the user invokes `/gemini sessions`:

1. Run the command:
   ```bash
   gemini --list-sessions
   ```
2. Present the session list to the user.
3. Inform them they can resume any session with `/gemini resume <INDEX> <PROMPT>`.

## Critical Evaluation & Error Handling

Read `shared/delegation-common.md` and apply to Gemini.
**Timeout suggestion:** switch to `gemini-2.5-flash`.
