---
name: preferences
description: "Use when the user invokes $preferences to set, view, or update their personal skill preferences. Also invoked automatically by other skills on first contact when no preferences file exists. Captures communication style, explanation preferences, experience level, and project context \u2014 shared across every skill in the collection."
---

# Preferences Skill

Capture and manage user preferences that shape how every skill in this collection behaves. Preferences are personal (per-user, per-project) and stored in `.codex/skill-context/`.

Read `../shared/skill-context.md` for the full file format specification and how other skills consume these preferences (resolve `../shared/...` against the plugin root - two levels above this SKILL.md - never the project's working directory).

## Out of Scope

This skill MUST NOT:
- Re-ask questions the user has already answered. Read existing preferences first; only ask about gaps.
- Block a calling skill's workflow on preference-capture failure. If the user cancels mid-interview or write fails, return control to the caller with sensible defaults.
- Treat preferences as rigid laws. Skills apply them with judgment - "concise" doesn't mean dropping critical security findings.
- Over-interview. 4 questions for shared, 1-3 per skill. Short answers are fine; gaps get sensible defaults.
- Modify `.gitignore` automatically to add `.codex/skill-context/`. Suggest it; do not silently add.

## Invocation

| Invocation | Mode |
|---|---|
| `$preferences` | Interactive setup - ask questions, save preferences |
| `$preferences show` | Display current preferences without changing them |
| `$preferences reset` | Clear all preferences and start fresh |
| `$preferences <skill-name>` | Set or update preferences for a specific skill |

When invoked **by another skill** (not the user), the calling skill has detected no preferences file exists. Run the streamlined Round 1 interview, save results, and return control.

---

## Mode: Interactive Setup (`$preferences`)

### Step 1: Check for Existing Preferences

Read `.codex/skill-context/preferences.md`.

- **Found:** Display current preferences in a clean summary and ask:
  > "Want to update anything, or is this still accurate?"
  - User confirms -> done.
  - User wants changes -> ask about specific areas. Update the file and show the result.
- **Not found:** Proceed to Step 2.

### Step 2: The Interview

Ask questions in a conversational flow - not a rigid survey. Present them as a group so the user can answer in one message if they want.

#### Round 1: Core Preferences (always ask)

> I'd like to learn how you prefer to work so every skill in this collection
> can tailor its output to you. A few quick questions:
>
> 1. **How detailed should skill output be?**
>    Concise (just the essentials) / Balanced / Detailed (full context and reasoning)
>
> 2. **How do you like things explained?**
>    Analogies and real-world parallels / Precise technical language /
>    Visual (lots of diagrams) / Example-driven (show me, don't tell me)
>
> 3. **What's your experience level?**
>    You can be specific - e.g., "senior backend, beginner at frontend,
>    intermediate DevOps"
>
> 4. **About this project:**
>    - What phase is it in? (Prototype / MVP / Active growth / Mature / Maintenance)
>    - How big is the team? (Solo / 2-5 / 6-15 / 16+)
>    - What's the top business priority? (Speed to market / Reliability /
>      Compliance / Cost reduction / Feature completeness)

Accept partial answers gracefully. If the user skips a question, use sensible defaults and note them. If they give a one-word answer, infer what you can.

#### Round 2: Offer to Go Deeper (always ask)

After capturing Round 1:

> Got it! I've saved your preferences. Would you like to also set preferences
> for specific skills? For example:
> - How `$explain` structures its reports
> - What severity levels `$codereview` focuses on
> - How `$commit` formats messages
>
> You can do this now, or anytime later with `$preferences <skill-name>`.

If the user wants to continue, proceed to skill-specific questions for the skills they mention. Otherwise, wrap up.

### Step 3: Save

Write `.codex/skill-context/preferences.md` using the format from `../shared/skill-context.md`. Ensure `.codex/skill-context/` exists first (create if needed).

Show the user what was saved:

> Here's what I've captured:
>
> [formatted summary of preferences]
>
> These preferences will be used by every skill in this collection. You can
> update them anytime with `$preferences`, or fine-tune a specific skill with
> `$preferences <skill-name>`.

---

## Mode: Show (`$preferences show`)

Read and display all preference files:

1. Read `.codex/skill-context/preferences.md` - show as "Shared Preferences"
2. Glob `.codex/skill-context/*.md` (excluding `preferences.md`) - show each as "{Skill Name} Preferences"
3. If no files exist: "No preferences set yet. Run `$preferences` to get started."

Format as a clean summary, not a raw file dump.

---

## Mode: Reset (`$preferences reset`)

**MUST confirm** before deleting:

> This will clear all your skill preferences (shared and skill-specific).
> You'll be asked again on next skill use. Proceed? (y/n)

If confirmed, delete all files in `.codex/skill-context/`.

---

## Mode: Skill-Specific (`$preferences <skill-name>`)

### Step 1: Validate the Skill Name

Check if `skills/<skill-name>/SKILL.md` exists under the plugin root (two levels above this SKILL.md - not the project's working directory). If not:

> Skill "{skill-name}" not found. Available skills: {list}.

### Step 2: Check for Shared Preferences

If `.codex/skill-context/preferences.md` doesn't exist, run the full interview first (Round 1 above), then proceed to skill-specific questions.

### Step 3: Skill-Specific Interview

Ask 1-3 targeted questions based on the skill. Questions MUST be things the skill actually uses - not abstract preferences that don't shape output.

Read `question-bank.md` (in this skill's directory) for the per-skill questions. For any skill without a bank entry, derive 1-3 questions from the target skill's "How preferences shape this skill" table in its SKILL.md.

### Step 4: Save

Write to `.codex/skill-context/<skill-name>.md`. Show what was saved.

---

## Invocation by Other Skills

When another skill invokes `$preferences` because no preferences file exists, the flow is streamlined:

1. The calling skill detected no `.codex/skill-context/preferences.md`
2. It invoked `$preferences`
3. Run the Round 1 interview (core preferences)
4. **MUST skip Round 2** (don't offer skill-specific deep-dives - the user is in the middle of another skill's workflow)
5. Save and return control
6. After the calling skill completes, optionally mention: "You can fine-tune preferences for specific skills anytime with `$preferences <skill-name>`."

This keeps the interruption brief while still capturing the essentials.

---

## Error Handling

| Situation | Behavior |
|---|---|
| `.claude/` directory doesn't exist | Create `.codex/skill-context/` |
| Write permission denied | Report error, suggest checking permissions |
| File system read-only | Hold preferences in memory for the session, warn that they won't persist |
| User cancels mid-interview | Save whatever was captured so far |
| User refuses to answer questions | Proceed with defaults, note in file |
| Invalid skill name | List available skills |
| Corrupt preferences file | Warn, offer to reset and re-interview |
| Calling skill needs preferences NOW | Capture minimum (detail level + experience), skip the rest |
