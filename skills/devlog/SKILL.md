---
name: devlog
description: "Use when the user invokes /devlog to capture development insights as devlog posts or content scraps aimed at budding programmers."
---

# Devlog Skill

Capture development insights for budding programmers. A **scrap** is a short, silent note about one insight, saved for later. A **post** is a full devlog article, written together with the developer. The primary deliverable is **insight** — the thinking behind decisions, not the technical how-to.

**Target audience:** Budding programmers learning how experienced developers think through problems, especially when developing with AI.

This file holds the scrap path in full, because scraps run often and automatically (for example, `/commit` runs `/devlog scrap --from-context` after significant commits). Write mode and List mode live in reference files and are read only when needed.

## Write for Humans

Everything a person reads from this skill — reports, findings, summaries, and conversation replies — MUST use plain language that a non-native English reader can follow. Before writing a report or a long reply, read `shared/report-style.md` (resolve against the plugin root — two levels above this SKILL.md — never the project's working directory) and follow it. In short: short sentences, everyday words, jargon explained on first use, the point stated first. Simplify the language, never the facts — paths, line numbers, and claims stay exact.

## Out of Scope

This skill MUST NOT:
- Draft a full post in scrap mode. Scrap is silent auto-capture; full posts are collaborative (Write mode).
- Generate an empty or hollow scrap. If gathering finds no decision points, no surprises, no clear insights — report that, do not create a placeholder file.
- Skip the one-sentence insight test. If you can't complete *"The interesting thing about this commit is ___"* with something specific and non-trivial, do not capture a scrap.
- Interview the user about preferences. Load preference files if they exist; otherwise use defaults.

## Reference Files

| File | Contents | When to read |
|---|---|---|
| `references/write-mode.md` | Session and timeframe resolution, full gathering, Write mode, Writing Principles, file layout, error handling | Write mode, and scrap mode without `--from-context` |
| `references/list-mode.md` | List mode, including the cross-repo scrap backlog | List mode only |
| `references/agent-prompts.md` | Guiding principles and prompt templates for the 3 gathering agents | Before dispatching gathering agents |

## Invocation

| Invocation | Mode | Description |
|---|---|---|
| `/devlog [topic]` | Write | Full brainstorming + devlog post |
| `/devlog scrap [hint]` | Scrap | Rich auto-captured scrap, no questions asked |
| `/devlog scrap --from-context [hint]` | Scrap (lightweight) | Scrap from current conversation context only — no subagent dispatch |
| `/devlog list` | List | Show scrap backlog with age, published posts (across repos if configured) |
| `/devlog --since <range>` | Write | Full post, mining sessions from a time range |
| `/devlog --from-scrap <name or path>` | Write | Full post, starting from a specific scrap |
| `/devlog --since beginning` | Write | Full post, scanning all sessions for the project |

Arguments are combinable. Examples:
- `/devlog the clone bug --since yesterday` — write about the clone bug, mining recent sessions
- `/devlog --from-scrap recursive-fix` — write a post starting from an existing scrap
- `/devlog scrap signing workaround` — quickly capture a scrap about signing
- `/devlog scrap --from-context auth refactor` — capture a scrap using only what's already in the conversation (used by auto-invoke from the commit skill)

The `--since` parameter accepts natural language time expressions (`yesterday`, `last week`, `3 days ago`) and absolute dates (`2026-03-20`). The special value `beginning` scans all available history.

If the invocation is ambiguous or unrecognizable, ask the user to clarify: "What would you like to write about? Usage: `/devlog [topic]`, `/devlog scrap [hint]`, `/devlog list`"

### Mode Routing

1. First argument is `list` — load preferences (below), then read `references/list-mode.md` and follow it.
2. First argument is `scrap` and `--from-context` is set — load preferences, then follow **Scrap Mode** below. Do not read any reference file.
3. First argument is `scrap` without `--from-context` — load preferences, run Phases 1–2 (resolution and full gathering) from `references/write-mode.md`, then follow **Scrap Mode** below with the gathered content brief.
4. Otherwise — **Write** mode: load preferences, then read `references/write-mode.md` and follow it. The remaining text after flags is the topic.

When a mode dispatches same-platform subagents, do not pass a model or reasoning-effort override. Let every subagent inherit the parent model and reasoning effort unless the user explicitly asks for an override.

---

## Phase 0: Load Preferences (silent)

Never interview the user about preferences. Read these files if they exist; use defaults for anything missing:

1. `.claude/skill-context/preferences.md` — shared preferences (tone, assumed knowledge).
2. `.claude/skill-context/devlog.md` — devlog preferences (target audience, writing tone).

Defaults: casual, story-driven voice; reader is a budding programmer.

| Preference | Effect on Devlog |
|---|---|
| Tone: casual | Conversational voice, contractions, first-person narrative |
| Tone: professional | Clean prose, structured sections, polished for publication |
| Assumed knowledge: beginner | More context on technical concepts, define jargon |
| Devlog-specific: target audience | Shapes the drafting voice and assumed reader background |
| Devlog-specific: writing tone | Overrides the shared tone preference for devlog |

Pass the audience and tone preferences to any gathering agents and to drafting.

---

## Scrap Mode

Scrap mode runs **without any user interaction**.

### `--from-context` fast path

If `--from-context` is set, **MUST NOT dispatch subagents** and MUST NOT mine session logs or git history again. Instead:

1. **Use current conversation context directly.** The invoking session already contains the diff, commit message, conversation history, and any analysis performed.
2. **Scan for existing scraps** (dedup only). List `docs/devlog/.scraps/` and check whether a scrap with an overlapping topic and date already exists. If the directory doesn't exist or is empty, proceed.
3. Build the content brief from that context — the commit message (intent, changes, AI review), the diff, and any notable exchanges from the current session — and continue with the workflow below.

This path exists because auto-invocations (for example, from the commit skill) already have rich context in the conversation. Re-discovering it is redundant and slow.

### Workflow

1. Take the content brief (from the fast path, or from full gathering).
2. Identify the most interesting moments — decision points, surprises, pivots, dead ends.
3. **MUST apply the one-sentence test** before generating any output (see "What's Worth Capturing" below). If you can't state the insight in one specific, non-trivial sentence, stop and report empty results (see below).
4. Infer the developer's thinking — reconstruct *why* decisions were made from the conversation and git history. Mark inferences as inferences.
5. Generate a topic slug from the hint (if provided) or infer it from the content (lowercase, hyphenated, 2–5 words).
6. Create `docs/devlog/.scraps/` if it doesn't exist.
7. Write the scrap to `docs/devlog/.scraps/YYYYMMDD-<topic>.md`. If that file exists, append a numeric suffix: `YYYYMMDD-<topic>-2.md`.
8. Report the result to the user (see "Post-Scrap Output").

### What's Worth Capturing

The capture bar for scraps — applied here and by the commit skill's auto-capture:

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
- Work where you cannot articulate a specific insight in one concrete sentence

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
1. **<Brief label>** — <What happened>. Alternative was <what could have been done instead>. <Inferred reasoning for the choice made.>

## The Insight (Inferred)
<The skill's best guess at the transferable takeaway — the principle a budding programmer could apply elsewhere. Clearly labeled as inference. Make the first sentence a short, specific summary: List mode shows it as the scrap's title.>

## Supporting Evidence
- **Commits:** <list of relevant commit hashes with one-line summaries>
- **Conversation exchanges:** <quoted key exchanges, attributed to "Developer" and "AI">
- **Code snippets:** <focused before/after snippets if applicable>

## Open Questions
<Bulleted list of things the skill couldn't infer — gaps to fill when writing the full post. These become conversation starters for Write Mode.>
```

### Empty Results

If nothing noteworthy was found — no pivots, no surprises, no clear decision points — **MUST NOT** generate a hollow scrap. Instead, report:

> I didn't find any clear decision points or surprises in this session. If something specific caught your attention, try `/devlog scrap <hint>` with a description of what was interesting.

### Post-Scrap Output

After writing the scrap, report to the user:

> Scrap saved to `docs/devlog/.scraps/<filename>`. Key insight captured: "<one-sentence summary of inferred insight>". Turn it into a full post later with `/devlog --from-scrap <topic>`.
