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
