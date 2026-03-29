---
name: retrospective
description: "Use when the user invokes /retrospective to run a structured retrospective — mines git history, conversations, code quality, plans, and tests, then facilitates topic-by-topic discussion with the human to produce action items, process improvements, and a narrative summary."
---

# Retrospective Skill

Run a structured retrospective facilitated by AI, interleaved with human check-ins at every phase. Dispatch 5 parallel channel agents — each mining a different data source (git history, conversations, code quality, planning docs, tests) — to build a comprehensive digest. Derive discussion topics from the data, walk through them with the human, and produce three output layers: action items, process improvements, and skill improvements. Finish with a readable narrative written by a fresh-context agent.

## Invocation

Parse the user's `/retrospective` arguments to determine mode and time boundary:

| Invocation | Mode | Description |
|---|---|---|
| `/retrospective` | Chain (default) | From last retro to now (or beginning if first) |
| `/retrospective --since 2026-03-15` | Date-based | From a specific date to now |
| `/retrospective --since v1.0` | Tag-based | From a git tag to now |
| `/retrospective --since v1.0..v1.1` | Tag range | Between two tags |
| `/retrospective --output docs/sprints/3/` | Output override | Combinable with any mode |
| `/retrospective continue` | Resume | Resume an interrupted retro |

Arguments are combinable. Examples:
- `/retrospective --since v2.0 --output docs/releases/v2.1/retro/` — retro from tag with custom output
- `/retrospective --since "2 weeks ago"` — natural language date

The `--since` parameter accepts dates (`2026-03-15`), natural language (`yesterday`, `2 weeks ago`), git tags (`v1.0`), tag ranges (`v1.0..v1.1`), and the special value `beginning` (from first commit).

If the invocation is ambiguous or unrecognizable, ask the user to clarify before proceeding.

### Time Boundary Resolution

1. If `--since` is provided, use it directly
2. If no `--since`, scan `docs/retros/` for existing retro directories (sorted by date). If found, chain from the most recent retro's date.
3. If no previous retro exists, ask the human:

   Use `AskUserQuestion`:
   - **From beginning** — "Run from the first commit (`<first commit date>`)"
   - **Specify a start point** — "I'll provide a date, tag, or commit"

4. If a `--since` value is ambiguous (could be a branch name or a date), ask.

The **end boundary** is always HEAD / current date.

### Output Directory

Default: `docs/retros/YYYY-MM-DD/` where the date is the retro execution date.

If `--output` is specified, use that path instead. Create the directory if it doesn't exist.

### Previous Retro Detection

To find the most recent previous retro:

```bash
ls -d docs/retros/*/  # list retro directories, sorted by name (dates sort naturally)
```

Take the last entry. Read its `03-retro-summary.md` to extract the period end date — this becomes the start boundary for the current retro.

---
