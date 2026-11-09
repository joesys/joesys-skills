# Interaction Review — Output Formats

Format of the final report. The lens agents' output format is in `agent-prompts.md` § Lens Prompt Template, because the agents see only their prompt.

---

## Final Report Format

The HTML companion is generated from the markdown report by `../scripts/html_render.py`.

### Front-matter

```yaml
---
title: "Interaction Review — YYYY-MM-DD"
generated_by: "$interaction-review"
rubric_version: 2
rubric_date: "2026-11-09"
generated_at: "2026-05-25T14:30:00Z"
scope: "5 sessions, 2026-05-10 to 2026-05-25"
profile: "analytical"
sessions_analyzed: 5
previous_report: "docs/interaction-review/20260510-interaction-review.md"
---
```

### Rubric Version

The current rubric is **v2, dated 2026-11-09**. Always write `rubric_version: 2` and `rubric_date: "2026-11-09"`.

- A report without `rubric_version` is a v1 report.
- v2 changed how scores are given: turn-count targets now match current agents, and each behavior is scored in only one lens. So a v1 score and a v2 score are not directly comparable.
- When the previous report has a different rubric version, show the trend as `rubric vN→v2` instead of `+N`/`-N`, and say in the Header & Meta section that the rubric changed. A jump between versions is not real improvement or decline.

### Section Order

1. **Header & Meta** — Report date, rubric version, sessions analyzed, date range, invocation mode, previous report link
2. **Overall Scorecard** — Weighted composite table with trend deltas
3. **Session Summary** — Per-session overview (date, turns, topic, quality signal)
4. **Per-Lens Deep Dive** (×5) — Score, justification, findings, comparison
5. **Your Next Steps** — Max 5 improvement items with full detail
6. **Coach's Note** — 2–4 sentence coaching perspective
7. **Progress Tracker** — Mermaid chart or table of score trends (multi-report only)

### Scorecard Table Format

```markdown
| Lens | Score | Grade | Trend |
|---|---|---|---|
| Prompt Craft | 72 | B- | +8 |
| Workflow Efficiency | 65 | C+ | new |
| Agentic Leverage | 58 | C | -3 |
| Error Recovery | 81 | A- | +12 |
| Context & Instruction | 45 | D+ | -- |
| **Overall** | **66** | **C+** | **+5** |
```

Trend values: `+N` (improvement), `-N` (regression), `new` (first report), `--` (no prior data for this lens), `rubric vN→v2` (previous report used another rubric version; the scores are not comparable).

### Improvement Item Format

```markdown
### Priority N: [What to Change]
**Why it matters:** [Connected to specific findings — cite session/turn references]
**Expected impact:** [What score/grade improvement to expect and why]
**Effort:** Quick win | Moderate | Habit change
```

### Grade Scale

| Grade | Score Range |
|---|---|
| A+ | 97–100 |
| A | 93–96 |
| A- | 90–92 |
| B+ | 87–89 |
| B | 83–86 |
| B- | 80–82 |
| C+ | 77–79 |
| C | 73–76 |
| C- | 70–72 |
| D+ | 67–69 |
| D | 63–66 |
| D- | 60–62 |
| F | Below 60 |

### Progress Tracker Chart (Mermaid)

When 3+ prior reports exist, use an xychart. If the reports use more than one rubric version, label each x-axis point with its version (for example, `"May 25 (v1)"`, `"Nov 9 (v2)"`). Add a note under the chart: "Rubric changed from v1 to v2 on 2026-11-09. Do not read the score change across this point as real improvement or decline."

````markdown
```mermaid
xychart-beta
    title "Score Progression"
    x-axis ["May 1", "May 10", "May 25"]
    y-axis "Score" 0 --> 100
    line "Prompt Craft" [55, 64, 72]
    line "Workflow Efficiency" [58, 60, 65]
    line "Agentic Leverage" [50, 55, 58]
    line "Error Recovery" [69, 75, 81]
    line "Context & Instruction" [40, 42, 45]
```
````

When fewer than 3 data points exist, use a simple comparison table instead:

```markdown
| Lens | Previous | Current | Delta |
|---|---|---|---|
| Prompt Craft | 64 | 72 | +8 |
```

If the previous report used another rubric version, write `rubric vN→v2` in the Delta column instead of a number.
