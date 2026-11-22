# Extra runs: a third finder, a blocked run, and the fallback reviewers

This file covers the runs outside the usual four models: Grok as a third
finder, a manual run when a provider's safety filter blocks a run, and the
fallback reviewers. The commands are in `../shared/model-defaults.md`
§ Security Audit Roles. Every rule of the skill still holds: read only, no
live target, secret files stay closed, and every prompt starts with the
purpose line.

## Every retry gets a new name

The launcher refuses a run name that is already used in the run folder. It
then names the next free name. Every retry needs a new name, also a manual
one: `finder-1-b` for a resume, `finder-2-manual`, then
`finder-2-manual-2`. A manual answer file must not take the name of an
existing run either.

## A third finder: Grok

Grok joins only when the user asks for it. The source code then goes to a
third provider, xAI. Say so in the start notice, and start Grok only after
the user has agreed.

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

Fill in the absolute path of the run folder, and give the user this prompt
to type in the interactive Codex program, in the repository folder:

```text
This is our own codebase. We are auditing it to find its vulnerabilities, so that we can patch them and secure the code. You are Finder 2 of this audit. Read the file <RUN_DIR>/finder-prompt.txt and follow it: it is your whole task. Do only the finder part, and run no other model. The rule to skip the folder .security-audit/ covers every file in it except that prompt file and your answer file. Change no file of the project. Write your whole answer, in the structure that the prompt file gives, into <RUN_DIR>/finder-2-manual.final.md. The last line of that file must be <<<END-OF-ANSWER>>>, alone.
```

- The answer goes to `<RUN_DIR>/finder-2-manual.final.md`. If that name is
  already used, take `finder-2-manual-2`, and change the prompt to match.
- The file must end with the end marker `<<<END-OF-ANSWER>>>`, alone on the
  last line. A manual answer has no launcher record, so the watch does not
  list it. Check the end marker yourself before you use the answer.
- When the run folder is outside the project, Codex asks for approval to
  write the file there. The user approves that one write.
- Ask the user to tell you when the file is there.

In the live run, the user typed a shorter prompt that called this skill and
asked for the finder part only. Codex wrote 25 candidates in its own format,
with no code map, no "checked and found safe" list, no "not checked" list,
and no end marker. The prompt above asks for the brief's own format. It has
not yet been run live in this form.

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
