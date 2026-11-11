# Skill evals

These evals check that a skill still does its job after its text changes. Each
one runs the committed version ("old") and the working-tree version ("new") of
a skill headless (`claude -p`) on the same fixture, then scores the reports.
They make real model calls and cost money. Results go to `evals/results/`,
which git ignores.

```bash
python3 evals/run_eval.py --skill quick-review --runs 1           # ~$1-2,  ~7 min per run
python3 evals/run_eval.py --skill codereview --runs 2 --budget 20  # ~$6-11, ~15 min per run
python3 evals/run_eval.py --skill codebase-audit --runs 1          # ~$14-16, ~32 min per run
python3 evals/run_eval.py --skill interaction-review --runs 1      # ~$7-9,  ~15 min per run
python3 evals/audit_scoring.py <old summary.json> <new summary.json>  # grade differences
```

Use `--only old|new` to run one side and `--old-ref <commit>` to pick the
baseline. Run each side at least twice before you trust a difference: single
runs vary.

| Skill | Fixture | What is scored |
|---|---|---|
| codereview, quick-review | `fixtures/review-target`: 10 planted bugs, 4 correct look-alikes, 1 readability-only issue | bugs found, false alarms, out-of-scope findings, other citations |
| codebase-audit | `review-target` plus `fixtures/audit-context` (pre-filled preferences) and 5 seeded commits | overall and per-criterion grades; old-vs-new grade moves |
| interaction-review | `fixtures/interaction-session`: synthetic Claude Code session with 7 designed issues | lens scores against wide bands, issues mentioned |

The review fixture is easy: the old versions already find every planted bug.
So these evals catch a skill getting worse, not one getting better.

## Results: step 3 of the November 2026 skill review

Old = `a3d93f9` (release 19.1.0). New = the trimmed codereview, codebase-audit
and interaction-review. Two runs per side except quick-review.

| Skill | Measure | Old | New |
|---|---|---|---|
| codereview | planted bugs found | 10/10, 10/10 | 10/10, 10/10 |
| | false alarms | 0, 0 | 0, 0 |
| | cost / time | $11.09, $8.58 / 17-18 min | $5.66, $7.48 / 13-14 min |
| quick-review | bugs found / false alarms | 9/9 / 0 | 9/9 / 0 |
| | cost | $1.25 | $1.11 |
| codebase-audit | overall grade | D, D | D, D |
| | criteria that moved | — | modularity B→A in both runs; security F/D and evolvability A/B vary between runs on both sides |
| | cost | $13.66, $13.81 | $15.65, $16.26 |
| interaction-review | designed issues found | 7/7, 7/7 | 6/7, 7/7 |
| | overall score (bad session) | 57, 57 | 60, 61 |
| | cost | $7.32, $8.52 | $7.31, $6.71 |

Reading: the trims kept every planted bug and designed issue. codereview got
cheaper and faster. interaction-review scores about 3-4 points more leniently
on the same session (error recovery +5, context +7), and codebase-audit moved
modularity up one step; both are noted here so later trend comparisons are
read with that in mind.

## Results: first runs on Fable 5.2 (2026-11-11)

One run per skill of the working tree after the Fable 5.2 review edits
(`--only new --model claude-fable-5-2`). There is no "old" run on Fable, so
these runs show that the skills work on this model, not that the edits made
them better.

| Skill | Measure | Fable 5.2 (1 run) | Opus 5.5, for scale (step 3 "new") |
|---|---|---|---|
| quick-review | required bugs found / false alarms | 9/9 / 0 | 9/9 / 0 |
| | cost / time | $3.85 / 7 min | $1.11 |
| codereview | planted bugs found / false alarms | 10/10 / 0 | 10/10 / 0 |
| | cost / time | $12.92 / 20 min | $5.66, $7.48 / 13-14 min |
| interaction-review | designed issues found | 6/7 | 6/7, 7/7 |
| | overall score (bad session) | 62 | 60, 61 |
| | cost / time | $10.96 / 18 min | $7.31, $6.71 |

What the transcripts show:

- Reviewer prompts held no pasted code: about 3,400-4,000 characters each, with
  a file list. Each reviewer read the files itself.
- The plugin root variable was filled in: the loaded skill text shows the
  temporary plugin folder as the plugin root. The runs still listed the plugin's
  folders once to find file names.
- quick-review also reported the N+1 query, a performance bug that only
  codereview is required to find.
- codereview made 8 helper-agent calls: seven reviewers and the tech lead.
- interaction-review scored agentic leverage 72, two points above the band
  (10-70), and missed "files read one by one". Opus missed the same issue in one
  of two runs. Watch this lens on the next run.
- codereview on Fable tried to send the review to Codex and Antigravity, which
  the Opus runs never did. The harness denied the command, because
  `ALLOWED_TOOLS` has no rule for it. So the cross-model path is still not
  tested, and a run that should test it needs a wider allow list.
- The fixture reviews a folder, not a diff, so the diff-command wording in the
  review skills was not exercised.
