---
name: devlog
description: "Use when the user invokes $devlog to capture development insights as devlog posts or content scraps aimed at budding programmers."
---

# Devlog Skill

Capture development insights for budding programmers. A **scrap** is a short, silent note about one insight, saved for later. A **post** is a full devlog article, written together with the developer. The primary deliverable is **insight** - the thinking behind decisions, not the technical how-to.

**Target audience:** Budding programmers learning how experienced developers think through problems, especially when developing with AI.

This file holds the scrap path in full, because scraps run often and automatically (for example, `$commit` runs `$devlog scrap --from-context` after significant commits). Write mode and List mode live in reference files and are read only when needed.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `../shared/report-style.md` (resolve against the collection root (one level above this SKILL.md) - never the project's working directory).

## Out of Scope

Do not draft a full post in scrap mode. A scrap is a silent capture; a full post is written together with the developer (Write mode).

## Reference Files

| File | Contents | When to read |
|---|---|---|
| `references/write-mode.md` | Session and timeframe resolution, full gathering, Write mode, Writing Principles, file layout, error handling | Write mode, and scrap mode without `--from-context` |
| `references/list-mode.md` | List mode, including the cross-repo scrap backlog | List mode only |
| `references/agent-prompts.md` | Guiding principles and prompt templates for the 3 gathering agents | Before dispatching gathering agents |

## Invocation

| Invocation | Mode | Description |
|---|---|---|
| `$devlog [topic]` | Write | Full brainstorming + devlog post |
| `$devlog scrap [hint]` | Scrap | Rich auto-captured scrap, no questions asked |
| `$devlog scrap --from-context [hint]` | Scrap (lightweight) | Scrap from current conversation context only - no subagent dispatch |
| `$devlog list` | List | Show scrap backlog with age, published posts (across repos if configured) |
| `$devlog --since <range>` | Write | Full post, mining sessions from a time range |
| `$devlog --from-scrap <name or path>` | Write | Full post, starting from a specific scrap |

Arguments can be combined. `--since` accepts natural-language times (`yesterday`, `3 days ago`) and dates (`2026-03-20`); `beginning` means all history.

If the invocation is unclear, ask what the user wants to write about and show the main usage forms.

### Mode Routing

1. First argument is `list` - load preferences (below), then read `references/list-mode.md` and follow it.
2. First argument is `scrap` and `--from-context` is set - load preferences, then follow **Scrap Mode** below. Do not read any reference file.
3. First argument is `scrap` without `--from-context` - load preferences, run Phases 1-2 (resolution and full gathering) from `references/write-mode.md`, then follow **Scrap Mode** below with the gathered content brief.
4. Otherwise - **Write** mode: load preferences, then read `references/write-mode.md` and follow it. The remaining text after flags is the topic.

When a mode dispatches same-platform subagents, do not pass a model or reasoning-effort override. Let every subagent inherit the parent model and reasoning effort unless the user explicitly asks for an override.

---

## Phase 0: Load Preferences (silent)

Read these files if they exist; use defaults for anything missing:

1. `.codex/skill-context/preferences.md` - shared preferences (tone, assumed knowledge).
2. `.codex/skill-context/devlog.md` - devlog preferences (target audience, writing tone). Its writing tone overrides the shared tone.

Defaults: casual, story-driven voice; the reader is a budding programmer. Pass the audience and tone to any gathering agents and to drafting.

---

## Scrap Mode

Scrap mode runs **without any user interaction**.

### `--from-context` fast path

If `--from-context` is set, do not dispatch subagents and do not mine session logs or git history again. The invoking session (for example, `$commit`) already holds the diff, the commit message, and the discussion; finding them again is slow and adds nothing.

1. Build the content brief from the current conversation: the commit message (intent, changes, AI review), the diff, and notable exchanges.
2. List `docs/devlog/.scraps/` to check for a scrap with an overlapping topic and date (to avoid duplicates). If the folder is missing or empty, continue with the workflow below.

### Workflow

1. Take the content brief (from the fast path, or from full gathering).
2. Identify the most interesting moments - decision points, surprises, pivots, dead ends.
3. Apply the capture bar in "What's Worth Capturing" before writing anything. If it fails, stop and follow "Empty Results".
4. Infer the developer's thinking - reconstruct *why* decisions were made from the conversation and git history. Label inferences as inferences.
5. Generate a topic slug from the hint (if provided) or infer it from the content (lowercase, hyphenated, 2-5 words).
6. Create `docs/devlog/.scraps/` if it doesn't exist.
7. Write the scrap to `docs/devlog/.scraps/YYYYMMDD-<topic>.md`. If that file exists, append a numeric suffix: `YYYYMMDD-<topic>-2.md`.
8. Report the scrap path, the one-sentence insight, and the `$devlog --from-scrap <topic>` command to turn it into a post.

### What's Worth Capturing

The capture bar for scraps - applied here and by the commit skill's auto-capture:

**Worth capturing:**
- A non-obvious design decision or tradeoff was made
- A surprising root cause was discovered during debugging
- A novel pattern, technique, or approach emerged from the work
- A pivot or change of direction with a clear "why"
- An insight about the codebase, language, framework, or domain that wasn't obvious going in

**NOT worth capturing:**
- Routine implementation following an established pattern in the codebase
- A straightforward feature with no design decisions or tradeoffs
- A bug fix that was a typo, off-by-one, or other mechanical correction
- A mechanical refactor (rename, extract, reformat) with no judgment calls

**The one-sentence test:** complete *"The interesting thing about this work is ___"* with something specific and non-trivial. If you can't, or the answer is generic ("we added a feature"), do not capture a scrap.

### Scrap Structure

Write the scrap file with this structure:

```markdown
---
date: <YYYY-MM-DD>
topic: <topic slug>
project: <working directory basename>
session: <current session ID, or `unknown` in --from-context mode where session detection is skipped>
status: unwritten
---

## Situation
<2-3 sentences: what was being worked on and why. Grounded in specific files, features, or goals.>

## Key Moments
<Numbered list of decision points, surprises, or pivots detected. Each entry includes:>
1. **<Brief label>** - <What happened>. Alternative was <what could have been done instead>. <Inferred reasoning for the choice made.>

## The Insight (Inferred)
<The skill's best guess at the transferable takeaway - the principle a budding programmer could apply elsewhere. Clearly labeled as inference. Make the first sentence a short, specific summary: List mode shows it as the scrap's title.>

## Supporting Evidence
- **Commits:** <list of relevant commit hashes with one-line summaries>
- **Conversation exchanges:** <quoted key exchanges, attributed to "Developer" and "AI">
- **Code snippets:** <focused before/after snippets if applicable>

## Open Questions
<Bulleted list of things the skill couldn't infer - gaps to fill when writing the full post. These become conversation starters for Write Mode.>
```

### Empty Results

If nothing passes the capture bar, do not write a placeholder scrap. Say that no clear decision point or surprise was found, and suggest `$devlog scrap <hint>` if the user saw something interesting.
