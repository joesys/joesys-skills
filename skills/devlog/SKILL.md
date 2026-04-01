---
name: devlog
description: "Use when the user invokes /devlog to capture development insights as devlog posts or content scraps. Mines git history, conversation history, and existing scraps to reconstruct the developer's thinking, then brainstorms to surface the real insight before drafting."
---

# Devlog Skill

Capture development insights and turn them into devlog posts aimed at budding programmers. The skill operates as an interviewer and collaborator — it mines conversation history, git activity, and existing content scraps to reconstruct the developer's thinking, then brainstorms with the human operator to surface the real insight before drafting.

The primary deliverable is **insight** — the thinking process behind decisions, not the technical how-to. The content that matters is the surprise (where a mental model broke), the judgment (why one path was chosen over another), and the messy middle (how ambiguity was navigated).

**Target audience:** Budding programmers learning how experienced developers think through problems, especially when developing with AI.

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

If `--from-context` is set (scrap mode only), **skip all subagent dispatch**. Instead:

1. **Use current conversation context directly.** The invoking session already contains the diff, commit message, conversation history, and any analysis performed. Do not re-mine this information.
2. **Scan for existing scraps** (dedup only). Read `docs/devlog/.scraps/` to check if a scrap with overlapping topic/date already exists. If the directory doesn't exist or is empty, note "no existing scraps" and proceed.
3. **Proceed directly to Phase 3a** with the content brief assembled from conversation context — the commit message (intent, changes, AI review), the diff, and any notable exchanges from the current session.

This path exists because auto-invocations (e.g., from the commit skill) already have rich context in the conversation — dispatching subagents to re-discover it is redundant and slow.

### Full gathering (default)

When `--from-context` is **not** set, dispatch **3 subagents simultaneously** via the Agent tool — all 3 in a single response (3 parallel Agent tool calls).

**IMPORTANT:** Every Agent tool call **must** use `model: "opus"` to ensure high-quality analysis.

Each subagent receives a prompt containing:
- The resolved timeframe and scope
- Relevant file paths and session identifiers
- The topic hint (if provided)
- The Guiding Principles block (prepended to every prompt)

### Guiding Principles (included in every subagent prompt)

1. **Evidence over guesswork.** Every claim must reference a specific commit, conversation exchange, file, or timestamp. No vague assertions.
2. **Flag uncertainty.** Distinguish what definitely happened vs. what seems likely vs. what is unclear. Uncertainty is valid output — say "unclear" rather than speculate.
3. **Focus on decisions and pivots.** The goal is to find moments where the developer made a choice, changed direction, or was surprised. Routine work is not interesting.
4. **Preserve the human's voice.** When quoting conversation exchanges, use the developer's actual words. Don't paraphrase away the personality.
5. **Infer reasoning, but mark it.** When you infer *why* a decision was made, explicitly label it as inference: "Likely because..." or "This suggests..."

### Agent 1: Git Miner

~~~
<GUIDING_PRINCIPLES>

You are a senior developer analyzing git history to find interesting development moments — decisions, pivots, surprises, and dead ends.

## Instructions
1. Analyze the git history within the specified timeframe.
2. Focus on moments that reveal thinking and decision-making, not routine changes.
3. The commit messages in this project follow Conventional Commits with a structured body (intent paragraph, changes changelog, AI review). Mine the intent paragraphs and AI review sections — they contain reasoning and critical assessment.

## Timeframe
<TIMEFRAME_DESCRIPTION>

## Your Analysis Must Cover

- **Significant commits**: commits that introduced new approaches, fixed non-obvious bugs, or changed direction
- **Pivots and reverts**: any `revert`, `fixup`, or commits that undo/redo previous work — these signal a change in thinking
- **Areas of churn**: files or modules that were modified repeatedly in a short period — signals difficulty or iteration
- **Before/after code snippets**: for the most interesting changes, extract focused diffs showing what changed and why it matters
- **Commit narrative**: tell the story of what happened in chronological order — "First they tried X, then changed to Y, finally settled on Z"

## Output Format

Return structured markdown with:
- A chronological narrative of the development activity
- Highlighted decision points (with commit hashes for reference)
- Extracted code snippets for the most interesting changes
- Your inference of what was interesting and why (clearly labeled as inference)
~~~

### Agent 2: Conversation Miner

~~~
<GUIDING_PRINCIPLES>

You are a senior analyst reading Claude Code conversation transcripts to find moments of insight, decision-making, and surprise.

## Instructions
1. Read the specified JSONL session files.
2. Focus on user and assistant messages (type: "user" and "assistant"). Skip tool results, file-history-snapshots, and progress messages — they are bulk data that obscures the thinking.
3. Look for moments where the developer's thinking is visible: corrections, overrides, pivots, "aha" moments, disagreements with the AI.

## Session Files
<SESSION_FILE_PATHS>

## Topic Hint (if provided)
<TOPIC_HINT or "None — scan broadly for interesting moments">

## What to Look For

- **Corrections and overrides**: moments where the user said "no", "not that", "actually", or redirected the AI — these reveal what the user knew that the AI didn't
- **Pivots**: points where the conversation changed direction — the user abandoned one approach for another
- **Dead ends**: approaches that were explored and abandoned — what went wrong?
- **Questions that reveal thinking**: when the user asked "why" or "what if" — these show their mental model
- **AI suggestions that surprised the user**: moments where the user accepted something non-obvious or expressed surprise
- **Disagreements**: places where the user pushed back on the AI's recommendation

## Output Format

Return structured markdown with:
- A chronological summary of the conversation's trajectory
- Highlighted key exchanges (quote the actual messages, attributed to "Developer" and "AI")
- Decision points with your inference of the developer's reasoning (labeled as inference)
- Any unresolved questions or tensions you noticed
~~~

### Agent 3: Scrap Scanner

~~~
<GUIDING_PRINCIPLES>

You are scanning existing devlog content scraps to find material related to the current topic.

## Instructions
1. Read all scrap files in the specified directory.
2. Match scraps to the current topic by content similarity and timeframe.
3. If a specific scrap was requested via --from-scrap, load it directly and rank it first.

## Scraps Directory
docs/devlog/.scraps/

## Current Topic
<TOPIC_DESCRIPTION or "None — return all scraps sorted by relevance to recent git activity">

## From Scrap (if specified)
<SCRAP_NAME or "None">

## Your Analysis Must Cover

- **Matched scraps**: list each relevant scrap with its date, topic, and a brief summary of its key moments and inferred insight
- **Relevance ranking**: order scraps from most to least relevant to the current topic
- **Gaps and overlaps**: note if multiple scraps cover the same ground, or if there are gaps between scraps and the current topic
- **Unresolved questions**: pull out the "Open Questions" section from matched scraps — these are good starting points for the brainstorming conversation

## Output Format

Return structured markdown with:
- Ranked list of relevant scraps with summaries
- Combined open questions from all matched scraps
- Recommendation: which scraps should be incorporated vs. which are tangential

If the scraps directory does not exist or is empty, report: "No existing scraps found."
~~~

### Gathering Synthesis

After all 3 agents return, synthesize their results into a **content brief**:

1. **Merge timelines**: combine the git narrative and conversation narrative into a single chronological story
2. **Cross-reference**: match git commits to conversation exchanges (by timestamp proximity) to connect code changes with the thinking behind them
3. **Identify candidate insights**: list the moments that look most promising for a devlog post — surprises, pivots, judgment calls
4. **Incorporate scraps**: weave in any relevant scrap content, noting what's already been captured vs. what's new

The content brief is internal — not shown to the user directly. It feeds into either Scrap Mode or Write Mode.

---

## Phase 3a: Scrap Mode

Triggered when the first argument is `scrap`. After the gathering phase, scrap mode proceeds **without any user interaction**.

### Workflow

1. Synthesize the content brief from the 3 agents' results
2. Identify the most interesting moments — decision points, surprises, pivots, dead ends
3. Infer the developer's thinking — reconstruct *why* decisions were made based on conversation flow and git history
4. Generate a topic slug from the hint (if provided) or infer from the content (lowercase, hyphenated, 2-5 words)
5. Write the scrap to `docs/devlog/.scraps/YYYYMMDD-<topic>.md`
6. If a scrap with the same date and topic exists, append a numeric suffix: `YYYYMMDD-<topic>-2.md`
7. Create the `.scraps/` directory if it doesn't exist
8. Report the result to the user

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

If the gathering phase finds nothing noteworthy — no pivots, no surprises, no clear decision points — do **not** generate a hollow scrap. Instead, report:

> I didn't find any clear decision points or surprises in this session. If something specific caught your attention, try `/devlog scrap <hint>` with a description of what was interesting.

### Post-Scrap Output

After writing the scrap, report to the user:

> Scrap saved to `docs/devlog/.scraps/<filename>`. Key insight captured: "<one-sentence summary of inferred insight>". Turn it into a full post later with `/devlog --from-scrap <topic>`.

---

## Phase 3b: Write Mode

Triggered when the invocation is not `scrap` or `list`. This is a **brainstorming conversation** — the skill and the developer collaborate to find and articulate the insight before drafting.

### Phase 3b.1: Present Inferred Narrative

Synthesize the content brief and present your interpretation of what happened. Be specific — reference actual commits, conversation moments, and code changes:

> "Here's what I think happened: You were working on [specific thing], and hit [specific problem]. I can see from the git history that you first tried [approach A] (commit `abc123`), then pivoted to [approach B]. In the conversation, you [specific exchange]. The key moment seems to be when [specific decision point]. It looks like you changed direction because [inferred reasoning]. Is that right?"

Wait for the developer to correct, expand, or confirm. This grounds the conversation in specifics.

If the content brief contains material from scraps, mention them: "I also found a scrap from [date] about [topic] that seems related — it noted [key insight from scrap]."

### Phase 3b.2: Find the Insight

Dig deeper through conversation. Ask targeted questions based on the inferred narrative — not generic questions. Examples of good questions:

- "You overrode the AI's suggestion to [specific thing] — what felt wrong about it?"
- "You spent a while on [approach A] before switching to [approach B] — was there a specific moment it clicked that A wasn't working?"
- "The git history shows you reverted [commit] almost immediately — what did you see that told you it was wrong?"
- "This pattern — [specific pattern] — shows up in your other work too. Is this a general principle for you, or specific to this situation?"
- "What would you tell a junior developer who's about to make the same mistake you almost made here?"

**Rules for this phase:**
- Ask one question at a time
- Each question must reference something specific from the content brief — no generic "tell me more" questions
- The goal is to surface the **surprise** (where the mental model broke) and the **judgment** (the thinking that isn't obvious from the code)
- Continue until you have a clear insight or the developer indicates they're done
- If the developer's answer reveals a different insight than what you inferred, pivot to explore that instead

### Phase 3b.3: Identify and Propose Posts

After the brainstorming conversation, assess how many strong insights emerged:

**Single insight:** Proceed directly to drafting.

**Multiple insights:** Present them to the developer:

> "I see [N] potential devlogs here:
> 1. **[Title A]** — [one-sentence summary of insight A]
> 2. **[Title B]** — [one-sentence summary of insight B]
> 3. **[Title C]** — [one-sentence summary of insight C]
>
> Want to write all of them, pick some, or save the rest as scraps?"

Each approved post gets its own draft-review-publish cycle (phases 3b.4 and 3b.5). Unselected insights can be saved as scraps using the Scrap Mode workflow.

### Phase 3b.4: Draft the Post

Write the devlog post following the Writing Principles (see below). The structure is **freeform** — shaped by the content, not a rigid template. However, every post should:

1. **Open with the situation** — what you were doing and why, in 2-3 casual sentences
2. **Show the journey** — what happened, including wrong turns and dead ends
3. **Land the insight** — the transferable takeaway, grounded in the specific story
4. **Close short** — no summary paragraph, no "in conclusion." The insight is the ending.

**Voice:** First person from the developer's perspective. Casual and conversational — "So I was trying to..." not "In this post, we'll explore..." Use the developer's actual words from the brainstorming conversation where possible.

**Code snippets:** Include focused before/after snippets only where they serve the narrative. Never include full files. Code should illustrate the insight, not document the implementation.

**Length:** Aim for 400-800 words. A focused post is better than a comprehensive one.

Present the draft to the developer for review before publishing.

### Phase 3b.5: Review and Publish

1. Present the full draft in the conversation
2. Ask: "How does this look? Anything you'd change, add, or cut?"
3. Iterate on feedback until the developer approves
4. Create the post directory: `docs/devlog/YYYYMMDD-<topic>/`
5. Write the post: `docs/devlog/YYYYMMDD-<topic>/YYYYMMDD-<topic>.md`
6. Delete any scraps that were incorporated into this post (check the content brief for which scraps were used)
7. Git commit:
   ```
   docs(devlog): add post on <topic summary>
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

7. **Short over comprehensive.** A focused 400-800 word post beats a sprawling 2000-word post. Respect the reader's time. If it can't be said concisely, it's probably two insights crammed into one post.

8. **Casual + story-driven voice.** First person, conversational. "So I ran into this thing where..." not "In this post, we'll explore..." The voice should sound like explaining something interesting to a friend.

9. **Infer the thinking, confirm with the human.** The skill's job is to reconstruct the developer's thought process from evidence (git, conversation, scraps), then validate that interpretation. Never project your own narrative onto the developer's experience. Always ask "Is that right?" after presenting an inference.

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
- **Topic slugs** are lowercase, hyphenated, auto-generated from content or user hint (2-5 words)
- **Scraps deleted** after being fully incorporated into a published post
- **Git commit** after publishing — using conventional commit format (e.g., `docs(devlog): add post on recursive clone insight`)

---

## Error Handling

| Phase | Condition | Action |
|---|---|---|
| Invocation | Empty or unintelligible arguments | Ask user to clarify: "What would you like to write about? Usage: `/devlog [topic]`, `/devlog scrap [hint]`, `/devlog list`" |
| Phase 1 | Session pointer file not found | Fall back to most recent session file by modification time. Warn: "Couldn't detect current session — using most recent session file." |
| Phase 1 | No session files exist for project | Skip conversation mining. Proceed with git history and scraps only. Warn: "No conversation history found for this project." |
| Phase 2 | 1-2 gathering agents fail | Synthesize from successful agents. Note which sources are missing in the content brief. |
| Phase 2 | All gathering agents fail | Report failure. Suggest: "I couldn't gather any content. Try providing more context: `/devlog <topic description>`" |
| Phase 2 | Conversation files are too large to read | Agent reads only user/assistant messages, skipping tool results and file-history-snapshots. Uses topic hint to focus on relevant time ranges. |
| Phase 3a | Scrap directory doesn't exist | Create `docs/devlog/.scraps/` automatically |
| Phase 3a | Gathering finds nothing noteworthy | Don't create an empty scrap. Report the empty-results message (see Scrap Mode). |
| Phase 3b | Developer wants to stop mid-brainstorm | Offer to save current state as a scrap: "Want me to save what we have so far as a scrap?" |
| Phase 3c | No scraps or posts directory exists | Show appropriate "none yet" messages |
| Phase 3b.5 | Git commit fails | Report the error. The post file is already written — suggest the developer commit manually. |

---

## Guardrails

1. **Scrap mode is silent.** Never ask the developer questions in scrap mode. Make your best inference and write it. The developer invoked scrap mode because they're in the flow and don't want interruption.
2. **Write mode is collaborative.** Always present inferences for validation. Never draft without the developer's input on the insight.
3. **One question at a time.** In write mode brainstorming, never ask multiple questions in a single message.
4. **Evidence over projection.** Every claim about what the developer was thinking must be grounded in conversation exchanges, git history, or scraps. Mark inferences explicitly.
5. **Respect the developer's voice.** The devlog is written from the developer's perspective, using their words where possible. Don't impose a different style or vocabulary.
6. **Clean up after publishing.** Always delete scraps that were incorporated into a published post. Don't leave stale scraps around.
7. **Don't duplicate insights.** Before writing a post, check existing published posts in `docs/devlog/` to avoid covering the same ground. If a similar post exists, mention it and ask if the developer wants to write a different angle or skip.
