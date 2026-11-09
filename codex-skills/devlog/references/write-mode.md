# Devlog Write Mode

Reference file for the devlog skill. Read it for Write mode, and for the gathering phases (Phases 1–2) of scrap mode without `--from-context`.

Write mode is a **brainstorming conversation**. The skill acts as interviewer and collaborator: it mines conversation history, git activity, and existing scraps to reconstruct the developer's thinking, then works with the developer to find the real insight before drafting.

Before drafting, check `docs/devlog/` for a similar published post. If one exists, ask the developer whether to take a different angle or skip.

---

## Phase 1: Session & Timeframe Resolution

### 1.0 `--from-scrap` with a path from another repo

`--from-scrap` accepts a scrap name (topic or filename stem in this repo's `docs/devlog/.scraps/`) or a path to a scrap file, as printed by `$devlog list`.

If the path points into a different repo than the current working directory, stop. Tell the user to open a session in that repo and run `$devlog --from-scrap <filename stem>` there, because the post, the scrap cleanup, and the commit all belong in that repo.

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

- No `--since`: commits since the current session started, and the current session file only.
- `--since <range>`: commits in that range, and sessions that started inside it.
- `--since beginning`: full history and every session file for this project.

Filter session files by their start time (see 1.1). Pass only the matching file paths to the Conversation Miner, and tell it which host wrote them (Claude Code or Codex).

---

## Phase 2: Full Gathering

Gather from three sources: git, session logs, and existing scraps. Use parallel subagents when the range is large; for a small range, read the sources directly.

Prompt templates are in `references/agent-prompts.md`. Give each agent the guiding principles, the resolved timeframe and scope, the relevant file paths, the session log host, and the topic hint (if any).

### Agent Roster

| # | Agent | Data Source | Key Focus |
|---|---|---|---|
| 1 | Git Miner | git log, git diff | Pivots, surprises, churn, commit narrative |
| 2 | Conversation Miner | Session JSONL files (Claude Code or Codex) | Corrections, overrides, "aha" moments |
| 3 | Scrap Scanner | docs/devlog/.scraps/ | Existing content, relevance ranking, gaps |

### Gathering Synthesis

Combine the results into an internal **content brief**: one chronological story that links commits to the conversation around them (by time), the most promising moments (surprises, pivots, judgment calls), and relevant scrap content marked as already captured or new. The brief feeds Scrap Mode (SKILL.md) or Write Mode (below). If a source failed, note it in the brief and work from the rest.

---

## Phase 3: Write Mode

### Phase 3.1: Present Inferred Narrative

Present your interpretation of what happened. Be specific: the problem, the approaches tried (with commit hashes), the key decision point, and the inferred reasoning behind any change of direction. Mention any scraps used (date, topic, insight). End by asking whether the interpretation is right (Writing Principle 8), and wait for the developer to correct or confirm it.

### Phase 3.2: Find the Insight

Ask one question at a time. Tie each question to a specific moment in the content brief, never a generic "tell me more". For example: "The git history shows you reverted [commit] almost immediately — what did you see that told you it was wrong?"

The goal is to surface the surprise and the judgment (Writing Principles 1–2). If an answer reveals a different insight than you inferred, follow that one. Continue until the insight is clear or the developer is done. If the developer wants to stop early, offer to save what you have as a scrap.

### Phase 3.3: Identify and Propose Posts

Each post holds one insight. If one strong insight emerged, go straight to drafting. If several emerged, list them (a title and a one-sentence summary each) and ask which to write; offer to save the rest as scraps (Scrap Mode in SKILL.md). Each approved post gets its own draft and publish cycle (Phases 3.4 and 3.5), in its own directory.

### Phase 3.4: Draft the Post

Write the post following the Writing Principles (below). Let the content shape the structure. Do not add a summary paragraph; the insight is the ending.

Use the developer's actual words from the brainstorming where possible. Include focused before/after snippets only where they serve the story — never full files.

### Phase 3.5: Review and Publish

1. Show the full draft and ask for changes. Iterate until the developer approves.
2. Write the post to `docs/devlog/YYYYMMDD-<topic>/YYYYMMDD-<topic>.md`.
3. Delete every scrap that this post incorporated, so no stale scraps stay in `.scraps/`.
4. Commit by invoking the `$commit` skill. Never run a raw `git commit`. Stage only the new post directory and the deleted scraps. Suggest this subject and intent to `$commit`:
   - Subject: `docs(devlog): add post on <topic summary>`
   - Intent: captures a development insight from [session context / scrap / brainstorming]
   - Changes: `docs/devlog/YYYYMMDD-<topic>/` (new devlog post); `docs/devlog/.scraps/` (deleted incorporated scraps, if any)

   If `$commit` is not available or fails, leave the files uncommitted and tell the developer.
5. Report the post path and whether it was committed.

---

## Writing Principles

These principles shape both scrap inference and post drafting. They define what a good devlog looks like.

1. **Find the surprise.** Specifically look for moments where expectation diverged from reality — in conversation pivots, git reverts, approach changes. If there's no surprise, there's no devlog worth writing.

2. **Show the judgment.** Prioritize the *why* over the *how*. "I chose X over Y because..." is the core content. Code is supporting evidence, not the main event.

3. **Don't teach what AI can already teach.** Skip explaining syntax, APIs, or concepts a reader could ask an AI about. Focus on the thinking, the tradeoffs, the messy middle. A reader can ask an AI "what is git rebase" — they can't ask it "what was going through your head when you decided to rebase instead of merge."

4. **Concrete before abstract.** Lead with the specific situation, then zoom out to the transferable principle. Never the reverse. "I was debugging a recursive clone loop, and I realized the config was pointing at its own repo" teaches more than "Always check for circular references in configuration."

5. **Show the wrong path.** Dead ends and pivots are more instructive than the final solution. They teach *how to navigate* — which is the actual skill. Include what you tried that didn't work and why.

6. **Short over comprehensive.** A focused 400–800 word post beats a sprawling 2000-word post. Respect the reader's time. If it can't be said concisely, it's probably two insights crammed into one post.

7. **Casual + story-driven voice.** First person, conversational. "So I ran into this thing where..." not "In this post, we'll explore..." The voice should sound like explaining something interesting to a friend.

8. **Infer the thinking, confirm with the human.** Reconstruct the developer's thought process from evidence (git, conversation, scraps), then check it with them. Do not project your own story onto their experience; ask "Is that right?" after each inference.

---

## File Layout

- **Posts:** `docs/devlog/YYYYMMDD-<topic>/YYYYMMDD-<topic>.md`. Each post has its own directory so images and other assets sit next to it.
- **Scraps:** `docs/devlog/.scraps/YYYYMMDD-<topic>.md`. The dot folder keeps them out of casual browsing.

---

## Error Handling

| Condition | Action |
|---|---|
| Current session not found | Use this project's most recently modified session file, and tell the user. |
| No session files for this project | Skip conversation mining; use git and scraps only, and tell the user. |
| Nothing could be gathered | Report it and ask the user to describe the topic. |
