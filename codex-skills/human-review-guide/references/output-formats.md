# Human Review Guide — Output Formats

Templates for terminal markdown (small changes) and HTML report (large changes) output.

---

## Output Size Thresholds

| Change size | Measurement | Output |
|-------------|-------------|--------|
| Small | ≤5 files **and** ≤200 lines changed | Terminal markdown inline |
| Large | >5 files **or** >200 lines changed | HTML report file |

For artifact mode (non-code files): terminal markdown unless >200 lines.

---

## Terminal Markdown Format

For inline display in the conversation. Compact, scannable.

~~~markdown
## Review Guide

{Executive summary — 2-3 sentences: what the change does, N decisions need your input, estimated M minutes}

### Decision Map

| # | Decision | Location | Reversibility |
|---|----------|----------|---------------|
| 1 | {description} | `{file:line}` | {easy/moderate/costly} |
| 2 | {description} | `{file:line}` | {easy/moderate/costly} |

### Guided Reading

**[DECIDE]** `{file:line}` — {decision title}

{Deep analysis content for DECIDE chunk}

---

**[DECIDE]** `{file:line}` — {decision title}

{Deep analysis content for DECIDE chunk}

---

**[READ]** `{file:line}` — {summary title}

{Deep analysis content for READ chunk}

---

<details>
<summary>For Context ({count} items)</summary>

- **[SKIM]** `{file:line}` — {triage reason}
- **[SKIM]** `{file:line}` — {triage reason}

</details>

**Skipped ({count} files):** {summary — e.g., "14 files with formatting changes, import reordering, and auto-generated code"}

### Open Questions

- {question 1}
- {question 2}

### Review Checklist

- [ ] {actionable item from DECIDE chunk 1}
- [ ] {actionable item from DECIDE chunk 2}
- [ ] {actionable item from DECIDE chunk 3}
~~~

---

## HTML Report Format

For large changes. Rendered from markdown via `../scripts/html_render.py`.

### Front-matter

~~~yaml
---
title: "Human Review Guide — {branch or PR title}"
generated_by: "$human-review-guide"
generated_at: "{ISO8601 timestamp}"
scope: "{N files, M lines changed}"
profile: "analytical"
---
~~~

### Section Order

1. **Executive Summary** — What changed, decision count, estimated review time
2. **Decision Map** — Clickable table linking to each DECIDE section
3. **Guided Reading** — Full walkthrough:
   - DECIDE entries with full deep analysis (expanded by default)
   - READ entries with full deep analysis (expanded by default)
   - SKIM entries in a collapsible section (collapsed by default)
   - SKIP entries as a single summary line (collapsed by default)
4. **Open Questions** — Unresolved items (omit section if none)
5. **Review Checklist** — Copy-pasteable checkboxes

### HTML-Specific Enhancements

- **Tier badges:** Color-coded inline badges
  - DECIDE: red/orange background — `<span class="tier tier-decide">DECIDE</span>`
  - READ: blue background — `<span class="tier tier-read">READ</span>`
  - SKIM: gray background — `<span class="tier tier-skim">SKIM</span>`
  - SKIP: light gray, muted — `<span class="tier tier-skip">SKIP</span>`
- **Collapsible sections:** SKIM and SKIP groups wrapped in `<details>` tags, collapsed by default
- **Code snippets:** Syntax-highlighted via Prism.js (loaded from `docs/.assets/report-lib/`)
- **Decision map links:** Each row in the decision map table links to the corresponding DECIDE section via anchor

### Markdown Structure for Renderer

The markdown fed to the renderer should use this structure (the renderer handles HTML styling):

~~~markdown
# Human Review Guide

## Executive Summary

{2-3 sentences}

## Decision Map

| # | Decision | Location | Reversibility |
|---|----------|----------|---------------|
| 1 | [{description}](#decide-1) | `{file:line}` | {easy/moderate/costly} |

## Guided Reading

### DECIDE 1: {decision title}

`{file:line}`

**The decision:** {content}

**Alternatives not taken:**
- {content}

**Consequences:** {content}

**Ask yourself:**
1. {question}

**Reversibility:** {rating} — {explanation}

---

### READ 1: {summary title}

`{file:line}`

**What this does:** {content}

**Why we do it this way:** {content}

**Why it matters:** {content}

**Gotchas:** {content}

---

<details>
<summary>For Context ({count} items)</summary>

### SKIM: {file:line}

{triage reason}

</details>

**Skipped ({count} files):** {summary}

## Open Questions

- {items}

## Review Checklist

- [ ] {items}
~~~
