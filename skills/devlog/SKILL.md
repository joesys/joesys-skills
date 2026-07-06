---
name: devlog
description: "Use when the user invokes /devlog to capture development insights as devlog posts or content scraps aimed at budding programmers."
---

# Devlog Skill

Capture development insights and turn them into devlog posts aimed at budding programmers. The skill operates as an interviewer and collaborator — it mines conversation history, git activity, and existing content scraps to reconstruct the developer's thinking, then brainstorms with the human operator to surface the real insight before drafting. The primary deliverable is **insight** — the thinking behind decisions, not the technical how-to (the Writing Principles below define what that means in detail).

**Target audience:** Budding programmers learning how experienced developers think through problems, especially when developing with AI.

## Out of Scope

This skill MUST NOT:
- Draft a full post in scrap mode. Scrap is silent auto-capture; full posts are collaborative (Write mode).
- Generate an empty or hollow scrap. If gathering finds no decision points, no surprises, no clear insights — report that, do not create a placeholder file.
- Skip the one-sentence insight test. If you can't complete *"The interesting thing about this commit is ___"* with something specific and non-trivial, do not capture a scrap.
- Ask multiple questions in a single brainstorming message. One question at a time, each grounded in a specific moment from the content brief.
- Project a narrative onto the developer's experience. Inferences MUST be grounded in conversation, git history, or scraps — and MUST be validated with the developer before being baked into a draft.
- Leave stale scraps in `.scraps/` after publishing a post that incorporated them. Cleanup is mandatory.
- Duplicate an existing published post. Check `docs/devlog/` before drafting; if a similar post exists, ask the developer whether to write a different angle or skip.

## Reference Files

| File | Contents | When to read |
|---|---|---|
| `references/agent-prompts.md` | Guiding principles and full prompt templates for all 3 gathering agents | Before dispatching agents in Phase 2 |

## Invocation

Parse the user's `/devlog` arguments to determine mode and options:

| Invocation | Mode | Description |
|---|---|---|
| `/devlog [topic]` | Write | Full brainstorming + devlog post |
| `/devlog scrap [hint]` | Scrap | Rich auto-captured scrap, no questions asked |
| `/devlog scrap --from-context [hint]` | Scrap (lightweight) | Scrap from current conversation context only — no subagent dispatch |
| `/devlog list` | List | Show scrap backlog with age, published posts |
| `/devlog --since <range>` | Write | Full post, mining sessions from a time range |
| `/devlog --from-scrap <name>` | Write | Full post, starting from a specific scrap |
| `/devlog --since beginning` | Write | Full post, scanning all sessions for the project |

Arguments are combinable. Examples:
- `/devlog the clone bug --since yesterday` — write about the clone bug, mining recent sessions
- `/devlog --from-scrap recursive-fix` — write a post starting from an existing scrap
- `/devlog scrap signing workaround` — quickly capture a scrap about signing
- `/devlog scrap --from-context auth refactor` — capture a scrap using only what's already in the conversation (used by auto-invoke from commit skill)

The `--since` parameter accepts natural language time expressions (`yesterday`, `last week`, `3 days ago`) and absolute dates (`2026-03-20`). The special value `beginning` scans all available history.

If the invocation is ambiguous or unrecognizable, ask the user to clarify before proceeding.

### Mode Detection Logic

1. If the first argument is `list` — **List** mode
2. If the first argument is `scrap` — **Scrap** mode (remaining text is the hint)
3. Otherwise — **Write** mode (remaining text after flags is the topic)

---

## Phase 0: Load User Preferences

Read `shared/skill-context.md` for the full protocol (resolve `shared/...` against the plugin root — two levels above this SKILL.md — never the project's working directory). In brief:

1. Read `.claude/skill-context/preferences.md` — if missing, invoke `/preferences` (streamlined).
2. Read `.claude/skill-context/devlog.md` (if it exists) for devlog-specific preferences.

**How preferences shape this skill:**

| Preference | Effect on Devlog |
|---|---|
| Tone: casual | Conversational voice, contractions, first-person narrative |
| Tone: professional | Clean prose, structured sections, polished for publication |
| Assumed knowledge: beginner | More context on technical concepts, define jargon |
| Devlog-specific: target audience | Shapes the drafting voice and assumed reader background |
| Devlog-specific: writing tone | Override the shared tone preference for devlog specifically |

Pass the audience and tone preferences to all gathering agents and the drafting phase.

**For `--from-context` scraps:** Still load preferences (they affect the scrap's tone and framing) but skip the interview if no preferences exist — scraps are quick captures, not the moment to start a preferences interview.

---

## Phase 1: Session & Timeframe Resolution

**If `--from-context` is set, skip this entire phase** — there are no gathering agents to configure. Proceed directly to Phase 2's fast path.

Before dispatching gathering agents, resolve the timeframe for content mining.

### 1.1 Current Session Detection

Determine the active session by reading the session pointer file:

1. Find the current shell's PID
2. Read `~/.claude/sessions/<PID>.json` to get the `sessionId`
3. The session JSONL file is at `~/.claude/projects/<project-dir>/<sessionId>.jsonl`

The `<project-dir>` is derived from the current working directory with path separators replaced by `--` (e.g., `D:\joesys\Projects\joesys-skills` becomes `D--joesys-Projects-joesys-skills`).

### 1.2 Timeframe Computation

| Invocation | Git Miner Timeframe | Conversation Miner Scope |
|---|---|---|
| `/devlog` (no `--since`) | Commits since current session start | Current session JSONL only |
| `/devlog --since yesterday` | `git log --since="yesterday"` | Sessions with timestamps from yesterday onward |
| `/devlog --since "3 days ago"` | `git log --since="3 days ago"` | Sessions with timestamps from 3 days ago onward |
| `/devlog --since 2026-03-20` | `git log --since="2026-03-20"` | Sessions with timestamps from that date onward |
| `/devlog --since beginning` | Full `git log` | All session JSONL files for this project |
| `/devlog scrap --from-context` | N/A (no subagents) | N/A (uses current conversation context directly) |

For the Conversation Miner, filter session files by checking the first entry's `timestamp` field in each JSONL file. Only pass matching session file paths to the agent.

### 1.3 Progress Indication

Before dispatching agents, print a brief status message:

> Gathering content from [scope description]...

Examples:
- "Gathering content from current session..."
- "Gathering content from the last 3 days..."
- "Gathering content from all project history..."

---

## Phase 2: Parallel Gathering

### `--from-context` fast path

If `--from-context` is set (scrap mode only), **MUST skip all subagent dispatch**. Instead:

1. **Use current conversation context directly.** The invoking session already contains the diff, commit message, conversation history, and any analysis performed. Do not re-mine this information.
2. **Scan for existing scraps** (dedup only). Read `docs/devlog/.scraps/` to check if a scrap with overlapping topic/date already exists. If the directory doesn't exist or is empty, note "no existing scraps" and proceed.
3. **Proceed directly to Phase 3a** with the content brief assembled from conversation context — the commit message (intent, changes, AI review), the diff, and any notable exchanges from the current session.

This path exists because auto-invocations (e.g., from the commit skill) already have rich context in the conversation — dispatching subagents to re-discover it is redundant and slow.

### Full gathering (default)

When `--from-context` is **not** set, dispatch **3 subagents simultaneously** via the Agent tool — all 3 in a single response (3 parallel Agent tool calls).

**MUST use** `model: "opus"` for every Agent tool call.

Read `references/agent-prompts.md` for the full prompt template for each agent. Each subagent receives the guiding principles, resolved timeframe, scope, relevant file paths, and the topic hint (if provided).

### Agent Roster

| # | Agent | Data Source | Key Focus |
|---|---|---|---|
| 1 | Git Miner | git log, git diff | Pivots, surprises, churn, commit narrative |
| 2 | Conversation Miner | Session JSONL files | Corrections, overrides, "aha" moments |
| 3 | Scrap Scanner | docs/devlog/.scraps/ | Existing content, relevance ranking, gaps |

### Gathering Synthesis

After all 3 agents return, synthesize their results into a **content brief**:

1. **Merge timelines** — combine the git narrative and conversation narrative into a single chronological story
2. **Cross-reference** — match git commits to conversation exchanges (by timestamp proximity) to connect code changes with the thinking behind them
3. **Identify candidate insights** — list the moments that look most promising for a devlog post — surprises, pivots, judgment calls
4. **Incorporate scraps** — weave in any relevant scrap content, noting what's already been captured vs. what's new

The content brief is internal — not shown to the user directly. It feeds into either Scrap Mode or Write Mode.

---

## Phase 3a: Scrap Mode

Triggered when the first argument is `scrap`. After the gathering phase, scrap mode proceeds **without any user interaction**.

### Workflow

1. Synthesize the content brief from the 3 agents' results
2. Identify the most interesting moments — decision points, surprises, pivots, dead ends
3. **MUST apply the one-sentence test** before generating any output (see "What's Worth Capturing" below). If you can't articulate the insight in one specific, non-trivial sentence, abort and report empty results (see below).
4. Infer the developer's thinking — reconstruct *why* decisions were made based on conversation flow and git history
5. Generate a topic slug from the hint (if provided) or infer from the content (lowercase, hyphenated, 2–5 words)
6. Write the scrap to `docs/devlog/.scraps/YYYYMMDD-<topic>.md`
7. If a scrap with the same date and topic exists, append a numeric suffix: `YYYYMMDD-<topic>-2.md`
8. Create the `.scraps/` directory if it doesn't exist
9. Report the result to the user

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
session: <current session UUID>
status: unwritten
---

## Situation
<2-3 sentences: what was being worked on and why. Grounded in specific files, features, or goals.>

## Key Moments
<Numbered list of decision points, surprises, or pivots detected. Each entry includes:>
1. **<Brief label>** — <What happened>. Alternative was <what could have been done instead>. <Inferred reasoning for the choice made.>

## The Insight (Inferred)
<The skill's best guess at the transferable takeaway — the principle a budding programmer could apply elsewhere. Clearly labeled as inference.>

## Supporting Evidence
- **Commits:** <list of relevant commit hashes with one-line summaries>
- **Conversation exchanges:** <quoted key exchanges, attributed to "Developer" and "AI">
- **Code snippets:** <focused before/after snippets if applicable>

## Open Questions
<Bulleted list of things the skill couldn't infer — gaps to fill when writing the full post. These become conversation starters for Write Mode.>
```

### Empty Results

If the gathering phase finds nothing noteworthy — no pivots, no surprises, no clear decision points — **MUST NOT** generate a hollow scrap. Instead, report:

> I didn't find any clear decision points or surprises in this session. If something specific caught your attention, try `/devlog scrap <hint>` with a description of what was interesting.

### Post-Scrap Output

After writing the scrap, report to the user:

> Scrap saved to `docs/devlog/.scraps/<filename>`. Key insight captured: "<one-sentence summary of inferred insight>". Turn it into a full post later with `/devlog --from-scrap <topic>`.

---

## Phase 3b: Write Mode

Triggered when the invocation is not `scrap` or `list`. This is a **brainstorming conversation** — the skill and the developer collaborate to find and articulate the insight before drafting.

### Phase 3b.1: Present Inferred Narrative

Synthesize the content brief and present your interpretation of what happened. Be specific — reference actual commits, conversation moments, and code changes: the problem, the approaches tried (with commit hashes), the key decision point, and the inferred reasoning behind any change of direction. End by asking whether the interpretation is right (Writing Principle 9).

Wait for the developer to correct, expand, or confirm. This grounds the conversation in specifics.

If the content brief contains material from scraps, mention them — which scrap, its date and topic, and the key insight it noted.

### Phase 3b.2: Find the Insight

Dig deeper through conversation. Ask targeted questions based on the inferred narrative — not generic questions. For example:

- "You overrode the AI's suggestion to [specific thing] — what felt wrong about it?"
- "The git history shows you reverted [commit] almost immediately — what did you see that told you it was wrong?"

**Rules for this phase:**
- **MUST ask one question at a time**
- Each question MUST reference something specific from the content brief — no generic "tell me more" questions
- The goal is to surface the **surprise** and the **judgment** (Writing Principles 2–3)
- Continue until you have a clear insight or the developer indicates they're done
- If the developer's answer reveals a different insight than what you inferred, pivot to explore that instead

### Phase 3b.3: Identify and Propose Posts

After the brainstorming conversation, assess how many strong insights emerged:

**Single insight:** Proceed directly to drafting.

**Multiple insights:** Present them to the developer as a numbered list — a title plus a one-sentence insight summary for each — and ask whether to write all of them, pick some, or save the rest as scraps.

Each approved post gets its own draft-review-publish cycle (phases 3b.4 and 3b.5). Unselected insights can be saved as scraps using the Scrap Mode workflow.

### Phase 3b.4: Draft the Post

Write the devlog post following the Writing Principles (see below) — they define the voice, length, and insight bar. The structure is **freeform** — shaped by the content, not a rigid template. However, every post should:

1. **Open with the situation** — what you were doing and why, in 2–3 casual sentences
2. **Show the journey** — what happened, including wrong turns and dead ends
3. **Land the insight** — the transferable takeaway, grounded in the specific story
4. **Close short** — no summary paragraph, no "in conclusion." The insight is the ending.

Use the developer's actual words from the brainstorming conversation where possible. Include focused before/after code snippets only where they serve the narrative — never full files.

Present the draft to the developer for review before publishing.

### Phase 3b.5: Review and Publish

1. Present the full draft in the conversation
2. Ask: "How does this look? Anything you'd change, add, or cut?"
3. Iterate on feedback until the developer approves
4. Create the post directory: `docs/devlog/YYYYMMDD-<topic>/`
5. Write the post: `docs/devlog/YYYYMMDD-<topic>/YYYYMMDD-<topic>.md`
6. **MUST delete** any scraps that were incorporated into this post (check the content brief for which scraps were used)
7. Git commit using Conventional Commits with the structured body format:
   ```
   docs(devlog): add post on <topic summary>

   Captures development insight from [session context / scrap / brainstorming].

   [--- Changes ---]

   - docs/devlog/YYYYMMDD-<topic>/: new devlog post
   - docs/devlog/.scraps/: deleted incorporated scraps (if any)

   [--- AI Review (<model name>) ---]

   <Brief assessment of the post quality and insight captured.>
   ```
8. Report to the developer:
   > Post published to `docs/devlog/YYYYMMDD-<topic>/YYYYMMDD-<topic>.md` and committed.

If multiple posts were approved in Phase 3b.3, repeat phases 3b.4 and 3b.5 for each post.

---

## Phase 3c: List Mode

Triggered when the first argument is `list`. No subagents needed — this is a direct filesystem read.

### Workflow

1. Scan `docs/devlog/.scraps/` for scrap files. For each, read the YAML frontmatter to extract `date`, `topic`, and `status`.
2. Scan `docs/devlog/` for post directories. For each, extract the date and topic from the directory name.
3. Compute age for scraps (relative to today).
4. Present the results:

```
Scraps (<N> unwritten):

  Date        Topic                    Age
  2026-03-26  recursive-clone-bug      today
  2026-03-24  ssh-signing-recovery     2 days
  2026-03-20  parallel-subagent-perf   6 days

Posts (<N> published):

  Date        Topic                    Path
  2026-03-25  oneflow-branching        docs/devlog/20260325-oneflow-branching/
  2026-03-18  prompt-as-architecture   docs/devlog/20260318-prompt-as-architecture/
```

- Scraps sorted by age (oldest first — nudge to write them before context fades)
- Posts sorted by date (most recent first)
- If no scraps exist, show: "No scraps. Use `/devlog scrap` to capture insights for later."
- If no posts exist, show: "No published posts yet. Use `/devlog` to write your first one."

---

## Writing Principles

These principles are baked into the skill's behavior for both scrap inference and full post drafting. They are not optional — they define what a good devlog looks like.

1. **One insight per post, but multiple posts per invocation.** If the gathering phase surfaces multiple strong insights, present them to the developer and write each approved post as a separate devlog in its own directory.

2. **Find the surprise.** Specifically look for moments where expectation diverged from reality — in conversation pivots, git reverts, approach changes. If there's no surprise, there's no devlog worth writing.

3. **Show the judgment.** Prioritize the *why* over the *how*. "I chose X over Y because..." is the core content. Code is supporting evidence, not the main event.

4. **Don't teach what AI can already teach.** Skip explaining syntax, APIs, or concepts a reader could ask an AI about. Focus on the thinking, the tradeoffs, the messy middle. A reader can ask Claude "what is git rebase" — they can't ask Claude "what was going through your head when you decided to rebase instead of merge."

5. **Concrete before abstract.** Lead with the specific situation, then zoom out to the transferable principle. Never the reverse. "I was debugging a recursive clone loop, and I realized the config was pointing at its own repo" teaches more than "Always check for circular references in configuration."

6. **Show the wrong path.** Dead ends and pivots are more instructive than the final solution. They teach *how to navigate* — which is the actual skill. Include what you tried that didn't work and why.

7. **Short over comprehensive.** A focused 400–800 word post beats a sprawling 2000-word post. Respect the reader's time. If it can't be said concisely, it's probably two insights crammed into one post.

8. **Casual + story-driven voice.** First person, conversational. "So I ran into this thing where..." not "In this post, we'll explore..." The voice should sound like explaining something interesting to a friend.

9. **Infer the thinking, confirm with the human.** The skill's job is to reconstruct the developer's thought process from evidence (git, conversation, scraps), then validate that interpretation. **MUST NOT project** your own narrative onto the developer's experience. Always ask "Is that right?" after presenting an inference.

---

## File Layout

```
docs/devlog/
├── .scraps/
│   ├── 20260326-recursive-clone-bug.md
│   └── 20260324-ssh-signing-recovery.md
├── 20260325-oneflow-branching/
│   └── 20260325-oneflow-branching.md
└── 20260318-prompt-as-architecture/
    ├── 20260318-prompt-as-architecture.md
    └── before-after-diff.png
```

- **Posts** in `docs/devlog/YYYYMMDD-<topic>/YYYYMMDD-<topic>.md` — directory per post for co-located assets (images, videos, supplementary files)
- **Scraps** in `docs/devlog/.scraps/YYYYMMDD-<topic>.md` — dotdir keeps them hidden from casual browsing
- **Topic slugs** are lowercase, hyphenated, auto-generated from content or user hint (2–5 words)
- **Scraps deleted** after being fully incorporated into a published post
- **Git commit** after publishing using conventional commit format

---

## Error Handling

| Phase | Condition | Action |
|---|---|---|
| Invocation | Empty or unintelligible arguments | Ask user to clarify: "What would you like to write about? Usage: `/devlog [topic]`, `/devlog scrap [hint]`, `/devlog list`" |
| Phase 1 | Session pointer file not found | Fall back to most recent session file by modification time. Warn: "Couldn't detect current session — using most recent session file." |
| Phase 1 | No session files exist for project | Skip conversation mining. Proceed with git history and scraps only. Warn: "No conversation history found for this project." |
| Phase 2 | 1–2 gathering agents fail | Synthesize from successful agents. Note which sources are missing in the content brief. |
| Phase 2 | All gathering agents fail | Report failure. Suggest: "I couldn't gather any content. Try providing more context: `/devlog <topic description>`" |
| Phase 2 | Conversation files are too large to read | Agent reads only user/assistant messages, skipping tool results and file-history-snapshots. Uses topic hint to focus on relevant time ranges. |
| Phase 3a | Scrap directory doesn't exist | Create `docs/devlog/.scraps/` automatically |
| Phase 3a | Gathering finds nothing noteworthy | Don't create an empty scrap. Report the empty-results message (see Scrap Mode). |
| Phase 3b | Developer wants to stop mid-brainstorm | Offer to save current state as a scrap: "Want me to save what we have so far as a scrap?" |
| Phase 3c | No scraps or posts directory exists | Show appropriate "none yet" messages |
| Phase 3b.5 | Git commit fails | Report the error. The post file is already written — suggest the developer commit manually. |
