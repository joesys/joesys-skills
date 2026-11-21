# Review by the other frontier model, and the joint consensus

You wrote the report. A second frontier model, from the other provider, now
reviews it against the code. The goal is one list that both models stand
behind, with every open difference printed and not hidden.

## Who reviews

The reviewer and its command are in `shared/model-defaults.md` § Security
Audit Roles. It is always the frontier model of the other provider, so that
the two models do not share the same blind spots. It runs read-only.

## Round 1: the review

Build the reviewer's prompt with the shell, and start it through the same
launcher as a finder:

```bash
REVIEW_PROMPT="$RUN_DIR/reviewer-prompt.txt"
cat > "$REVIEW_PROMPT" << 'PROMPT_EOF'
<REVIEW_NOTE>
PROMPT_EOF
cat "<SKILL_DIR>/references/reviewer-brief.md" "<SKILL_DIR>/references/finding-rules.md" >> "$REVIEW_PROMPT"
python3 "<SKILL_DIR>/helpers/finder_runs.py" start --run-dir "$RUN_DIR" --name reviewer \
  --cwd "<REPO>" --prompt "$REVIEW_PROMPT" <STREAM_FLAG> -- <REVIEWER_CMD>
```

`<STREAM_FLAG>` is `--stream-result` for the Claude command and nothing for
the Codex command, as the registry says.

The review note gives the path of `report.html`, the scope, the commit, and
the paths that must stay closed. The reviewer reads the report and the
code. It does not get the finders' raw answers: it judges the report as its
reader will see it.

Watch the run as in Step 5 of the skill. There is no time limit.

The reviewer answers finding by finding: it agrees, or it disagrees with a
reason and a place in the code. It may also report a flaw that the report
misses, and a sentence that is wrong or unclear.

## What you do with the review

Take each point to the code. The reviewer is a peer. It can be right, and it
can be wrong about the code, as a finder can.

| The reviewer says | You do |
|---|---|
| Agrees | Nothing. You may now write that the reviewer agrees with this finding. |
| A finding is not real | Read the code again with its reason. If it is right, move the finding to the rejected list with that reason. If you still hold the finding, it becomes an open point. |
| A label is too high or too low | Check the four severity answers again. Change the label, or keep it as an open point. |
| A fix is wrong, or breaks something | Check it. Repair the fix, or add what it changes for users. |
| A flaw is missing | Check it like any candidate, by `verify.md`. If it holds, add it as a finding, found by the reviewer. |
| A sentence is wrong or unclear | Repair it. |

Do not give in to end a discussion, and do not hold a point to save face.
The code decides. When the code does not decide, the point stays open.

## Round 2: the open points

If no point is open after round 1, there is no round 2.

Otherwise send the reviewer one message with the open points only. For each
point give your evidence, with file and line, and ask for one answer: accept
or keep, with the reason. Include every correction that you made because of
round 1, and every new finding, so that the reviewer can check them. Ask for
its closing statement.

Resume the reviewer's session, so that it keeps what it has read. The
status line of the launcher shows the session id. Use the resume command of
`shared/model-defaults.md` for that tool, under a new run name such as
`reviewer-2`.

**A resumed session does not stay read-only by itself.** In a live test, a
resumed session of one tool came back with write access and another model,
and a resumed session of the other tool had left its read-only mode. So
give the model, the reasoning effort and the read-only flag again on every
resume, exactly as the registry shows.

If the session cannot be resumed, start a new run. Put the reviewer's own
round 1 answer for the open points into the prompt, so that it can stand by
its words.

## After round 2: what is still open stays open

The models exchange at most two rounds. After the second round, do not try
to win a point. For each point that is still open, print both views in the
finding:

- Add the part `views` to the finding, and the label "Two views" to its
  title line and to the list.
- Give each view in that model's own words, as a short quote with the
  model's name. Do not shorten a view in a way that weakens it.
- When the models differ on the label, show both labels. Sort the finding
  by the higher label, so that nobody overlooks it.
- List every open point under "Where the models still differ", with a link.

A difference between two careful models is useful to the reader. It marks
the place where a person must decide.

## What you may write about the reviewer

- Write that the reviewer agrees only where it said so. "No objection" in
  a review of a long report is not agreement with every sentence.
- Say what the reviewer read and what it did not read: the whole report or
  a part, the code or only the text, the first version or the corrected
  one.
- Print the reviewer's closing statement word for word, in quotation marks,
  in "How this report was made". Then add your own line.
- If the reviewer did not see the last corrections, say so.

## If the reviewer fails

Try once more, as for a finder. If it fails again, deliver the report with
a clear line at the top and in "What was not checked": no second model
reviewed this report. Do not review your own report and call it a
consensus.

## The last check

After the corrections, run the finishing script again until it reports no
problem. Read the assessment, the counts and the repair order once more:
a moved or rejected finding changes them.
