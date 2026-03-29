---
name: gemini
description: Use when the user invokes /gemini to delegate a prompt to Google Gemini CLI, /gemini resume to continue a previous Gemini session, or /gemini sessions to list available sessions
---

# Gemini Skill

Delegate prompts to Google's Gemini CLI and critically evaluate the output.

## Defaults

- **Model:** `gemini-3.1-pro-preview`
- **Approval mode:** `plan` (read-only)
- **Always use:** `-p` flag for non-interactive mode, `2>/dev/null`

## Running a Task

1. Parse the user's `/gemini` arguments for any overrides:
   - `--model <MODEL>` overrides the default model
   - `--approval-mode <MODE>` overrides the default approval mode (`default`, `auto_edit`, `yolo`)
   - Any remaining text is the prompt
2. Write the prompt to a temporary file and pipe it to Gemini (use 600000ms timeout on the Bash tool):
   ```bash
   cat > /tmp/gemini-prompt.txt << 'PROMPT_EOF'
   <USER_PROMPT>
   PROMPT_EOF
   cat /tmp/gemini-prompt.txt | gemini -m gemini-3.1-pro-preview --approval-mode plan -p "" 2>/dev/null
   rm -f /tmp/gemini-prompt.txt
   ```
   **Why stdin pipe instead of direct `-p` argument?** Shell argument passing breaks when prompts contain quotes, backticks, dollar signs, or other metacharacters. Piping via stdin is reliable regardless of prompt content. The `-p ""` flag triggers non-interactive mode while stdin provides the actual prompt.

   For short, simple follow-up prompts (e.g., session resume) that contain no special characters, direct `-p "<text>"` is acceptable.
3. Present the output clearly labeled as **Gemini's response**.
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
   - Resumed sessions inherit model and approval mode from the original run
   - `--model` CAN be overridden on resume if the user explicitly requests it
   - `--approval-mode` CAN be overridden on resume if the user explicitly requests it
4. After resume, follow the same output flow: present, evaluate, summarize, offer resume.

## Session Listing

When the user invokes `/gemini sessions`:

1. Run the command:
   ```bash
   gemini --list-sessions
   ```
2. Present the session list to the user.
3. Inform them they can resume any session with `/gemini resume <INDEX> <PROMPT>`.

## Error Handling

| Condition | Action |
|---|---|
| Non-zero exit code | Report failure, suggest checking `gemini --version` or auth setup |
| Empty output | Report that Gemini returned nothing, suggest rephrasing the prompt |
| Partial/warning output | Summarize warnings and ask user how to proceed |
| Timeout | Report timeout, suggest a simpler prompt or switching to `gemini-2.5-flash` |

## Critical Evaluation

Gemini is a peer, not an authority. After every Gemini response:

- **Trust your own knowledge** when confident. If Gemini claims something you know is incorrect, push back.
- **Research disagreements** using WebSearch or project documentation before accepting Gemini's claims.
- **Remember knowledge cutoffs** — Gemini may not know about recent releases, APIs, or changes.
- **Don't defer blindly** — evaluate suggestions critically, especially regarding model names, library versions, API changes, and best practices.

### When You Disagree

1. State the disagreement clearly to the user with evidence.
2. Provide supporting evidence (your own knowledge, web search results, docs).
3. Optionally resume the Gemini session to discuss as a peer AI:
   ```bash
   gemini --resume latest -p "This is Claude (<your current model name>) following up. I disagree with [X] because [evidence]. What's your take?" 2>/dev/null
   ```
   **Note:** A debate resume becomes "the last session." Inform the user that `/gemini resume` will now continue the debate thread, not the original prompt.
4. Frame disagreements as discussions — either AI could be wrong.
5. Let the user decide how to proceed if there is genuine ambiguity.
