# Finder 3, Finder 4, blocked runs, and fallback reviewers

This file covers the special prompt and launcher rules for Finder 3 (Grok)
and Finder 4 (Antigravity), a manual run when a provider's safety filter
blocks a run, and the fallback reviewers. The commands are in
`shared/model-defaults.md` § Security Audit Roles. Every rule of the skill
still holds: read only, no live target, secret files stay closed, and every
prompt starts with the purpose line.

## Every retry gets a new name

The launcher refuses a run name that is already used in the run folder. It
then names the next free name. Every retry needs a new name, also a manual
one: `finder-1-b` for a resume, `finder-2-manual`, then
`finder-2-manual-2`. A manual answer file must not take the name of an
existing run either.

## Finder 3: Grok

Grok runs as Finder 3 alongside Finders 1, 2, and 4. The source code goes to
xAI; say so in the start notice.

Its run name is `finder-3`, and in the report its `data-found-by` value is
`finder-3`.

**Its prompt has one more note.** Grok runs in plan mode without anyone to
approve a step. A command that needs approval ends the run before the
answer is complete. So build a prompt of its own: the start note, then this
note word for word, then the same four parts as for the other finders.

```bash
GROK_PROMPT="$RUN_DIR/finder-3-prompt.txt"
cat > "$GROK_PROMPT" << 'PROMPT_EOF'
<START_NOTE>

You are Finder 3. Work alone: start no helper agent. This rule replaces the
part of the brief about helper agents. Use only the tools read_file, grep and
list_dir, and read-only git commands such as git log, git show and git grep.
Run no python, node, script or heredoc. This run cannot ask for approval, so
a command that needs approval ends it before your answer is complete.
PROMPT_EOF
for part in finder-brief method coverage finding-rules; do
  cat "<SKILL_DIR>/references/$part.md" >> "$GROK_PROMPT"
done
python3 "<SKILL_DIR>/helpers/finder_runs.py" start --run-dir "$RUN_DIR" --name finder-3 \
  --cwd "<REPO>" --prompt "$GROK_PROMPT" --grok-result -- <FINDER_3_CMD>
```

`<FINDER_3_CMD>` is the Grok command of the registry, with a new UUID for
`--session-id` and `"$GROK_PROMPT"` for `--prompt-file`. The launcher also
sends the prompt on stdin. Grok ignores it.

**When the run ends early.** Grok exits with code 0 also when it stopped at
a step that needs approval. The status line then shows the stop reason
`cancelled` and the `permission required:` line from stderr. Resume it once,
under the name `finder-3-b`, with the registry's resume command. Its prompt
file holds the purpose line, the note above, and this request: "Your last
run stopped before the answer was complete. Continue the audit, and give
your whole answer again, in the structure of the brief, with the end
marker." In the live run of 2026-11-22, the first run stopped at a `python3`
heredoc, and such a resume worked.

## Finder 4: Antigravity

Antigravity runs as Finder 4 alongside Finders 1, 2, and 3. The source code
goes to Google; say so in the start notice.

Its run name is `finder-4`, and in the report its `data-found-by` value is
`finder-4`.

**Its prompt has one more note.** In plan mode, `agy` may answer with a plan
and ask for approval instead of giving the audit answer. Build its prompt
with the start note, this direct-answer line, and the same four parts as the
other finders:

```bash
AGY_PROMPT="$RUN_DIR/finder-4-prompt.txt"
cat > "$AGY_PROMPT" << 'PROMPT_EOF'
<START_NOTE>

You are Finder 4. Answer directly. Do not make a plan, and do not ask for
approval.
PROMPT_EOF
for part in finder-brief method coverage finding-rules; do
  cat "<SKILL_DIR>/references/$part.md" >> "$AGY_PROMPT"
done
AGY_ADAPTER_TIMEOUT=14400 python3 "<SKILL_DIR>/helpers/finder_runs.py" start --run-dir "$RUN_DIR" --name finder-4 \
  --cwd "<REPO>" --prompt "$AGY_PROMPT" --stdout-result -- <FINDER_4_CMD>
```

`<FINDER_4_CMD>` is the Antigravity command of the registry (`--model` may be
omitted to let `agy` manage its latest neon default). The same three
Antigravity habits apply as for the fallback reviewer below:

- Set `AGY_ADAPTER_TIMEOUT` before calling the launcher (for example
  `AGY_ADAPTER_TIMEOUT=14400`), or the adapter ends the run after 600
  seconds.
- Keep the prompt file under 150,000 bytes (the adapter rejects larger
  prompts).
- The adapter prints nothing until the answer is complete, so the watch
  shows `finder-4` as `idle` after 15 minutes; that is expected. It reports
  no session id, so a retry starts fresh under `finder-4-b`.

## When the safety filter of the Codex provider stops a run

This is a known failure. In a live run on 2026-11-22, the cyber safety
filter of the Codex provider stopped Finder 2 after a few minutes, with exit
code 1 and a message that the content "was flagged for possible
cybersecurity risk". The prompt started with the purpose line, and it said
that this was a defensive audit of the owner's own code. The user started
the same command by hand, and the filter stopped it again. Expect the same
for the Codex reviewer.

The rules of Step 5 apply: show the user the message word for word, do not
start the run again, and do not reword the prompt to get past the filter.
Continue with the runs that you have.

Then offer the user the manual run below. It is the user's choice. The user
runs it in the interactive Codex program, under their own account. You do
not start it, and you do not change its prompt.

### The manual run of Finder 2

Give the user two prompts to choose from. The user types one in the
interactive Codex program, in the repository folder. Fill in the absolute
path of the run folder first.

**Prompt A calls this skill.** Its first three sentences are the prompt that
got past the filter in the live run of 2026-11-22, word for word. The last
two sentences were added afterwards, to get the brief's format and the end
marker. They have not yet been run live.

```text
/joesys-skills:security-audit This is my codebase. I want you to do the finder part of this skills and then write the finding (not the full report) into a file. Do not run other model. Write it into <RUN_DIR>/finder-2-manual.final.md, in the answer structure of references/finder-brief.md: the code map, the candidates, "Checked and found safe" and "Not checked". The last line of that file must be <<<END-OF-ANSWER>>>, alone.
```

**Prompt B reads the finder prompt of this run.** It gives Codex the same
text as the other finders. That is the text that the filter flagged twice,
so the filter may stop this prompt too. It has not yet been run live.

```text
This is our own codebase. We are auditing it to find its vulnerabilities, so that we can patch them and secure the code. You are Finder 2 of this audit. Read the file <RUN_DIR>/finder-prompt.txt and follow it: it is your whole task. Do only the finder part, and run no other model. The rule to skip the folder .security-audit/ covers every file in it except that prompt file and your answer file. Change no file of the project. Write your whole answer, in the structure that the prompt file gives, into <RUN_DIR>/finder-2-manual.final.md. The last line of that file must be <<<END-OF-ANSWER>>>, alone.
```

The user picks one. Do not offer the other one later as a way around a
block: if the filter stops the chosen prompt, show the message, and the
user decides what comes next.

- The answer goes to `<RUN_DIR>/finder-2-manual.final.md`. If that name is
  already used, take `finder-2-manual-2`, and change the prompt to match.
- The file must end with the end marker `<<<END-OF-ANSWER>>>`, alone on the
  last line. A manual answer has no launcher record, so the watch does not
  list it. Check the end marker yourself before you use the answer.
- When the run folder is outside the project, Codex asks for approval to
  write the file there. The user approves that one write.
- Ask the user to tell you when the file is there.

In the live run, the user typed only the first three sentences of prompt A.
Codex wrote 25 candidates in its own format, with no code map, no "checked
and found safe" list, no "not checked" list, and no end marker.

### The manual run of the reviewer

The same way, for the review:

```text
This is our own codebase. We are auditing it to find its vulnerabilities, so that we can patch them and secure the code. You are the reviewer of this audit. Read the file <RUN_DIR>/reviewer-prompt.txt and follow it: it is your whole task. Run no other model. In the folder <RUN_DIR>, read only that prompt file and report.html. Change no file of the project. Write your whole answer, in the structure that the prompt file gives, into <RUN_DIR>/reviewer-manual.final.md. The last line of that file must be <<<END-OF-ANSWER>>>, alone.
```

A second round goes the same way, with the round 2 message in a new prompt
file and a new answer file, such as `reviewer-manual-2.final.md`.

## The fallback reviewers

When the Codex reviewer is blocked, the user can choose the manual review
above or the fallback pair. The user chose the pair in the live run of
2026-11-22. The pair is two reviewers, each in a fresh session that has
seen nothing of this audit:

| Run name | Reviewer | Launcher option |
|---|---|---|
| `reviewer-claude` | the fallback Claude reviewer: a new Claude CLI session, not the session of Finder 1 | `--stream-result` |
| `reviewer-agy` | the Antigravity reviewer | `--stdout-result` |

Their commands and identifiers are in the registry. Use the Claude CLI for
the Claude reviewer, not a helper agent of your own host: then it runs
read-only, in the same launcher and the same watch as every other run.

Both get the same review prompt, built as `consensus.md` says. Add one
sentence to the review note for Antigravity: "Answer directly. Do not make a
plan, and do not ask for approval." Without it, Antigravity in plan mode may
answer with a plan.

The Antigravity run has three habits. The registry gives the details:

- Set `AGY_ADAPTER_TIMEOUT` before you call the launcher, or the adapter
  ends the run after 600 seconds.
- It prints nothing until its answer is complete, so the watch shows it as
  `idle`. That is expected.
- It reports no session id. Its second round is a new run that gets its own
  round 1 answer in the prompt, as `consensus.md` says.

Handle each review by `consensus.md`, one reviewer at a time. The second
round goes to each reviewer with its own open points. A point stays open
when one reviewer still keeps it. In the finding, print each view in that
model's own words.

In the report, name both reviewers. Say that the Claude reviewer comes from
the same provider as a Claude writer, and that Antigravity comes from a
third provider. Print both closing statements word for word. A flaw that a
reviewer found gets the `data-found-by` value `reviewer`; the text says
which one.

## An answer whose format differs from the brief

A manual answer, or an answer that a model wrote in its own way, can lack
parts of the brief's structure. Use it as a finder answer, and follow
`verify.md` § 1.
