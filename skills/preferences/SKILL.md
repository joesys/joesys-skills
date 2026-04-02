---
name: preferences
version: "1.0.0"
description: "Use when the user invokes /preferences to set, view, or update their personal skill preferences. Also invoked automatically by other skills on first contact when no preferences file exists. Captures communication style, explanation preferences, experience level, and project context — shared across all skills in the collection."
---

# Preferences Skill

Capture and manage user preferences that shape how every skill in this
collection behaves. Preferences are personal (per-user, per-project) and
stored in `.claude/skill-context/`.

Read `shared/skill-context.md` for the full file format specification and
how other skills consume these preferences.

## Invocation

| Invocation | Mode |
|---|---|
| `/preferences` | Interactive setup — ask questions, save preferences |
| `/preferences show` | Display current preferences without changing them |
| `/preferences reset` | Clear all preferences and start fresh |
| `/preferences <skill-name>` | Set or update preferences for a specific skill |

When invoked **by another skill** (not the user), the calling skill has
detected no preferences file exists. Run the interview, save results, and
return control to the calling skill.

---

## Mode: Interactive Setup (`/preferences`)

### Step 1: Check for Existing Preferences

Read `.claude/skill-context/preferences.md`.

- **If found:** Display current preferences in a clean summary and ask:
  "Want to update anything, or is this still accurate?"
  - If the user confirms → done.
  - If they want changes → ask about the specific areas they want to change.
    Update the file and show the updated version.
- **If not found:** Proceed to Step 2.

### Step 2: The Interview

Ask questions in a conversational flow — not a rigid survey. Present them
as a group so the user can answer in one message if they want.

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
>    You can be specific — e.g., "senior backend, beginner at frontend,
>    intermediate DevOps"
>
> 4. **About this project:**
>    - What phase is it in? (Prototype / MVP / Active growth / Mature / Maintenance)
>    - How big is the team? (Solo / 2-5 / 6-15 / 16+)
>    - What's the top business priority? (Speed to market / Reliability /
>      Compliance / Cost reduction / Feature completeness)

Accept partial answers gracefully. If the user skips a question, use sensible
defaults and note them. If they give a one-word answer, infer what you can.

#### Round 2: Offer to Go Deeper (always ask)

After capturing Round 1:

> Got it! I've saved your preferences. Would you like to also set preferences
> for specific skills? For example:
> - How `/explain` structures its reports
> - What severity levels `/code-review` focuses on
> - How `/commit` formats messages
>
> You can do this now, or anytime later with `/preferences <skill-name>`.

If the user wants to continue, proceed to skill-specific questions for the
skills they mention. Otherwise, wrap up.

### Step 3: Save

Write `.claude/skill-context/preferences.md` using the format from
`shared/skill-context.md`. Ensure `.claude/skill-context/` directory exists
first (create if needed).

Show the user what was saved:

> Here's what I've captured:
>
> [formatted summary of preferences]
>
> These preferences will be used by all skills in this collection. You can
> update them anytime with `/preferences`, or fine-tune a specific skill with
> `/preferences <skill-name>`.

---

## Mode: Show (`/preferences show`)

Read and display all preference files:

1. Read `.claude/skill-context/preferences.md` — show as "Shared Preferences"
2. Glob `.claude/skill-context/*.md` (excluding `preferences.md`) — show each
   as "{Skill Name} Preferences"
3. If no files exist: "No preferences set yet. Run `/preferences` to get
   started."

Format as a clean summary, not a raw file dump.

---

## Mode: Reset (`/preferences reset`)

Confirm before deleting:

> This will clear all your skill preferences (shared and skill-specific).
> You'll be asked again on next skill use. Proceed? (y/n)

If confirmed, delete all files in `.claude/skill-context/`.

---

## Mode: Skill-Specific (`/preferences <skill-name>`)

### Step 1: Validate the Skill Name

Check if `skills/<skill-name>/SKILL.md` exists. If not:

> Skill "{skill-name}" not found. Available skills: {list}.

### Step 2: Check for Shared Preferences

If `.claude/skill-context/preferences.md` doesn't exist, run the full
interview first (Round 1 above), then proceed to skill-specific questions.

### Step 3: Skill-Specific Interview

Ask 1-3 targeted questions based on the skill. These questions should be
things the skill actually uses to shape its behavior — not abstract
preferences that don't affect output.

#### Skill-Specific Question Bank

**explain:**
> How do you prefer explanations structured?
> - Top-down (big picture first, then details)
> - Bottom-up (start with specifics, build to the whole)
> - Workflow-driven (follow the data/request through the system)
>
> Any areas you want the explanation to emphasize or skip?

**code-review:**
> What matters most in code reviews?
> - Rank these by priority: Security, Correctness, Performance,
>   Architecture, Clean Code, Reliability
> - Should I include minor style findings (P3/P4), or focus on real bugs and
>   security issues only?
> - Do you prefer before/after code examples, or just descriptions?

**quick-review:**
> Same as code-review — read and reuse code-review preferences if they exist.
> Only ask if code-review preferences are missing.

**codebase-audit:**
> Any known trade-offs I should be aware of?
> (intentional debt, upcoming migrations, things that look bad but are
> deliberate)
>
> What deployment cadence does this project use?
> (Continuous / Weekly / Monthly / Release-based / Not yet)

**commit:**
> Any commit message preferences beyond Conventional Commits?
> - Max subject line length?
> - Always include scope?
> - Any specific scopes this project uses?
> - Should commits automatically capture devlog scraps for interesting
>   changes? (on by default — turn off if you don't use the devlog skill
>   or prefer manual capture)

**devlog:**
> Who's the target audience for your devlog?
> (Fellow engineers / General tech audience / Personal notes /
> Company-internal / Blog readers)
>
> What tone should devlog entries use?
> (Technical and precise / Conversational / Narrative storytelling)

**retrospective:**
> How formal should retrospectives be?
> (Casual team reflection / Structured process review / Formal with
> action items and owners)

**export:**
> Any default export preferences?
> - Preferred format: PDF / HTML / PNG
> - Theme: light / dark
> - Include table of contents?

**ai-council, claude, codex, gemini:**
> These delegation skills use shared communication preferences.
> No additional questions needed — they read your shared preferences.
> [Skip to save]

### Step 4: Save

Write to `.claude/skill-context/<skill-name>.md`. Show what was saved.

---

## Invocation by Other Skills

When another skill invokes `/preferences` because no preferences file exists,
the flow is streamlined:

1. The calling skill detected no `.claude/skill-context/preferences.md`
2. It invoked `/preferences`
3. Run the Round 1 interview (core preferences)
4. **Skip Round 2** (don't offer skill-specific deep-dives — the user is in
   the middle of another skill's workflow)
5. Save and return control
6. Optionally, after the calling skill completes, mention: "You can fine-tune
   preferences for specific skills anytime with `/preferences <skill-name>`."

This keeps the interruption brief while still capturing the essentials.

---

## Guardrails

1. **Don't over-interview.** 4 questions for shared, 1-3 per skill. If the
   user gives short answers, work with what you get.
2. **Accept partial answers.** Not every field needs to be filled. Defaults
   are fine. Note them in the saved file as "(default)".
3. **Never block a skill workflow.** If preferences capture fails for any
   reason (user cancels, file write error), the calling skill proceeds with
   sensible defaults.
4. **Preferences are suggestions, not laws.** Skills apply them with
   judgment. A "concise" preference doesn't mean stripping critical
   findings from a security review.
5. **Don't re-ask the same questions.** If the user already has shared
   preferences, don't re-interview for shared context when they're setting
   skill-specific preferences.

---

## Error Handling

| Error | Behavior |
|---|---|
| `.claude/` directory doesn't exist | Create `.claude/skill-context/` |
| Write permission denied | Report error, suggest checking permissions |
| User cancels mid-interview | Save whatever was captured so far |
| Invalid skill name | List available skills |
| Corrupt preferences file | Warn, offer to reset and re-interview |

---

## Graceful Degradation

| Situation | Behavior |
|---|---|
| User refuses to answer questions | Proceed with defaults, note in file |
| Calling skill needs preferences NOW | Capture minimum (detail level + experience), skip the rest |
| File system read-only | Hold preferences in memory for the session, warn that they won't persist |
