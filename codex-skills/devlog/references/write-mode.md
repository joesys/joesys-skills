# Devlog Write Mode

Reference file for the devlog skill. Read it for Write mode, and for the gathering phases (Phases 1–2) of scrap mode without `--from-context`.

Write mode is a **brainstorming conversation**. The skill acts as interviewer and collaborator: it mines conversation history, git activity, and existing scraps to reconstruct the developer's thinking, then works with the developer to find the real insight before drafting.

## Write Mode Rules

Write mode MUST NOT:
- Ask multiple questions in a single brainstorming message. One question at a time, each grounded in a specific moment from the content brief.
- Project a narrative onto the developer's experience. Inferences MUST be grounded in conversation, git history, or scraps — and MUST be validated with the developer before being baked into a draft.
- Leave stale scraps in `.scraps/` after publishing a post that incorporated them. Cleanup is mandatory.
- Duplicate an existing published post. Check `docs/devlog/` before drafting; if a similar post exists, ask the developer whether to write a different angle or skip.
- Run a raw `git commit`. Publishing commits go through the `$commit` skill.

---

## Phase 1: Session & Timeframe Resolution

Resolve the timeframe for content mining before dispatching gathering agents.

### 1.0 `--from-scrap` with a path from another repo

`--from-scrap` accepts a scrap name (topic or filename stem in this repo's `docs/devlog/.scraps/`) or a path to a scrap file, as printed by `$devlog list`.

If the path points into a different repo than the current working directory, do not mine or publish from here. Stop and tell the user:

> This scrap lives in `<repo path>`. Open a session in that repo and run `$devlog --from-scrap <filename stem>` there. The post, the scrap cleanup, and the commit all belong in that repo.

### 1.1 Session Log Sources

Read the session logs of the host you are running in: Claude Code logs when you run in Claude Code, Codex logs when you run in Codex. If the user asks for both, read both and label each finding with its source.

**Claude Code**
- Location: `~/.claude/projects/<project-dir>/<sessionId>.jsonl`. `<project-dir>` is the working directory with every non-alphanumeric character (the drive `:`, path separators `\` and `/`) replaced by a single `-` (e.g., `D:\joesys\Projects\joesys-skills` becomes `D--joesys-Projects-joesys-skills`; on POSIX, `/home/user/app` becomes `-home-user-app`). If unsure, list `~/.claude/projects/` and match the entry against the transformed cwd.
- Session start time: the first line that has a top-level `timestamp`. The leading lines (`mode`, `last-prompt`, `file-history-snapshot`, and similar) often have none.
- Current session: list `~/.claude/sessions/*.json`. Each pointer file records the Claude Code process `pid`, its `cwd`, the `sessionId`, and `startedAt`. Pick the file whose `cwd` equals the current working directory; if several match, take the most recently modified. Do NOT use a shell `$$` value — it is a short-lived subprocess PID that never matches these files.

**Codex**
- Location: `~/.codex/sessions/YYYY/MM/DD/rollout-<start-time>-<session-id>.jsonl`. The date folders are the session start date. Older sessions may be moved to `~/.codex/archived_sessions/` as compressed `.jsonl.zst` files; read them with `zstd -dc` only if the time range needs them.
- Every line has `timestamp`, `type`, and `payload`. The first line has `type: "session_meta"`. Its `payload.cwd` is the project folder, `payload.id` is the session ID, and `payload.timestamp` is the start time. Keep only files whose `payload.cwd` equals the current working directory.
- Subagent sessions have `payload.source` set to an object with a `subagent` key. Skip them unless subagent work matters for the topic.
- Current session: the newest rollout file whose `session_meta` `payload.cwd` matches the working directory and that is not a subagent session.
- `~/.codex/history.jsonl` has one line per user prompt across all projects, with `session_id`, `ts` (Unix seconds), and `text`. It has no folder field, so match `session_id` to this project's rollout files. Use it only as a quick prompt index; the rollout files hold the full exchange.

### 1.2 Timeframe Computation

| Invocation | Git Miner Timeframe | Conversation Miner Scope |
|---|---|---|
| `$devlog` (no `--since`) | Commits since current session start | Current session file only |
| `$devlog --since yesterday` | `git log --since="yesterday"` | Sessions that started yesterday or later |
| `$devlog --since "3 days ago"` | `git log --since="3 days ago"` | Sessions that started 3 days ago or later |
| `$devlog --since 2026-03-20` | `git log --since="2026-03-20"` | Sessions that started on that date or later |
| `$devlog --since beginning` | Full `git log` | All session files for this project |

Filter session files by their start time (see 1.1). Pass only the matching file paths to the Conversation Miner, and tell it which host wrote them (Claude Code or Codex).

### 1.3 Progress Indication

Before dispatching agents, print a brief status message:

> Gathering content from [scope description]...

Examples: "Gathering content from current session...", "Gathering content from the last 3 days...", "Gathering content from all project history..."

---

## Phase 2: Full Gathering

Dispatch **3 subagents simultaneously** via the Codex agent workflow — all 3 in a single response (3 parallel Codex agent workflow calls).

For same-platform subagents, do not pass a model or reasoning-effort override. Let every subagent inherit the parent model and reasoning effort unless the user explicitly asks for an override.

Read `references/agent-prompts.md` for the full prompt template for each agent. Each subagent receives the guiding principles, resolved timeframe, scope, relevant file paths, the session log host, and the topic hint (if provided).

### Agent Roster

| # | Agent | Data Source | Key Focus |
|---|---|---|---|
| 1 | Git Miner | git log, git diff | Pivots, surprises, churn, commit narrative |
| 2 | Conversation Miner | Session JSONL files (Claude Code or Codex) | Corrections, overrides, "aha" moments |
| 3 | Scrap Scanner | docs/devlog/.scraps/ | Existing content, relevance ranking, gaps |

### Gathering Synthesis

After all 3 agents return, synthesize their results into a **content brief**:

1. **Merge timelines** — combine the git narrative and conversation narrative into a single chronological story
2. **Cross-reference** — match git commits to conversation exchanges (by timestamp proximity) to connect code changes with the thinking behind them
3. **Identify candidate insights** — list the moments that look most promising for a devlog post — surprises, pivots, judgment calls
4. **Incorporate scraps** — weave in any relevant scrap content, noting what's already been captured vs. what's new

The content brief is internal — not shown to the user directly. It feeds into either Scrap Mode (SKILL.md) or Write Mode (below).

---

## Phase 3: Write Mode

### Phase 3.1: Present Inferred Narrative

Synthesize the content brief and present your interpretation of what happened. Be specific — reference actual commits, conversation moments, and code changes: the problem, the approaches tried (with commit hashes), the key decision point, and the inferred reasoning behind any change of direction. End by asking whether the interpretation is right (Writing Principle 9).

Wait for the developer to correct, expand, or confirm. This grounds the conversation in specifics.

If the content brief contains material from scraps, mention them — which scrap, its date and topic, and the key insight it noted.

### Phase 3.2: Find the Insight

Dig deeper through conversation. Ask targeted questions based on the inferred narrative — not generic questions. For example:

- "You overrode the AI's suggestion to [specific thing] — what felt wrong about it?"
- "The git history shows you reverted [commit] almost immediately — what did you see that told you it was wrong?"

**Rules for this phase:**
- **MUST ask one question at a time**
- Each question MUST reference something specific from the content brief — no generic "tell me more" questions
- The goal is to surface the **surprise** and the **judgment** (Writing Principles 2–3)
- Continue until you have a clear insight or the developer indicates they're done
- If the developer's answer reveals a different insight than what you inferred, pivot to explore that instead

### Phase 3.3: Identify and Propose Posts

After the brainstorming conversation, assess how many strong insights emerged:

**Single insight:** Proceed directly to drafting.

**Multiple insights:** Present them to the developer as a numbered list — a title plus a one-sentence insight summary for each — and ask whether to write all of them, pick some, or save the rest as scraps.

Each approved post gets its own draft-review-publish cycle (Phases 3.4 and 3.5). Unselected insights can be saved as scraps using the Scrap Mode workflow in SKILL.md.

### Phase 3.4: Draft the Post

Write the devlog post following the Writing Principles (below) — they define the voice, length, and insight bar. The structure is **freeform** — shaped by the content, not a rigid template. However, every post should:

1. **Open with the situation** — what you were doing and why, in 2–3 casual sentences
2. **Show the journey** — what happened, including wrong turns and dead ends
3. **Land the insight** — the transferable takeaway, grounded in the specific story
4. **Close short** — no summary paragraph, no "in conclusion." The insight is the ending.

Use the developer's actual words from the brainstorming conversation where possible. Include focused before/after code snippets only where they serve the narrative — never full files.

Present the draft to the developer for review before publishing.

### Phase 3.5: Review and Publish

1. Present the full draft in the conversation
2. Ask: "How does this look? Anything you'd change, add, or cut?"
3. Iterate on feedback until the developer approves
4. Create the post directory: `docs/devlog/YYYYMMDD-<topic>/`
5. Write the post: `docs/devlog/YYYYMMDD-<topic>/YYYYMMDD-<topic>.md`
6. **MUST delete** any scraps that were incorporated into this post (check the content brief for which scraps were used)
7. Commit by invoking the `$commit` skill. Never run a raw `git commit`. Stage only the new post directory and the deleted scraps. Suggest this subject and intent to `$commit`:
   - Subject: `docs(devlog): add post on <topic summary>`
   - Intent: captures a development insight from [session context / scrap / brainstorming]
   - Changes: `docs/devlog/YYYYMMDD-<topic>/` (new devlog post); `docs/devlog/.scraps/` (deleted incorporated scraps, if any)

   If `$commit` is not available, do not commit. Tell the developer the files are written and uncommitted.
8. Report to the developer:
   > Post published to `docs/devlog/YYYYMMDD-<topic>/YYYYMMDD-<topic>.md` and committed.

If multiple posts were approved in Phase 3.3, repeat Phases 3.4 and 3.5 for each post.

---

## Writing Principles

These principles shape both scrap inference and full post drafting. They are not optional — they define what a good devlog looks like.

1. **One insight per post, but multiple posts per invocation.** If the gathering phase surfaces multiple strong insights, present them to the developer and write each approved post as a separate devlog in its own directory.

2. **Find the surprise.** Specifically look for moments where expectation diverged from reality — in conversation pivots, git reverts, approach changes. If there's no surprise, there's no devlog worth writing.

3. **Show the judgment.** Prioritize the *why* over the *how*. "I chose X over Y because..." is the core content. Code is supporting evidence, not the main event.

4. **Don't teach what AI can already teach.** Skip explaining syntax, APIs, or concepts a reader could ask an AI about. Focus on the thinking, the tradeoffs, the messy middle. A reader can ask an AI "what is git rebase" — they can't ask it "what was going through your head when you decided to rebase instead of merge."

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
- **Commit** after publishing through the `$commit` skill

---

## Error Handling

| Phase | Condition | Action |
|---|---|---|
| Phase 1 | `--from-scrap` path is in another repo | Stop and tell the user to run `$devlog --from-scrap <filename stem>` from that repo (see 1.0). |
| Phase 1 | Current session not found | Fall back to the most recent session file for this project by modification time. Warn: "Couldn't detect current session — using most recent session file." |
| Phase 1 | No session files exist for project | Skip conversation mining. Proceed with git history and scraps only. Warn: "No conversation history found for this project." |
| Phase 2 | 1–2 gathering agents fail | Synthesize from successful agents. Note which sources are missing in the content brief. |
| Phase 2 | All gathering agents fail | Report failure. Suggest: "I couldn't gather any content. Try providing more context: `$devlog <topic description>`" |
| Phase 2 | Conversation files are too large to read | Agent reads only human and assistant messages, skipping tool calls, tool output, and bookkeeping lines. Uses the topic hint to focus on relevant time ranges. |
| Scrap | Gathering finds nothing noteworthy | Don't create an empty scrap. Report the empty-results message (see Scrap Mode in SKILL.md). |
| Phase 3 | Developer wants to stop mid-brainstorm | Offer to save current state as a scrap: "Want me to save what we have so far as a scrap?" |
| Phase 3.5 | `$commit` fails | Report the error. The post file is already written — suggest the developer commit it with `$commit` after fixing the problem. |
