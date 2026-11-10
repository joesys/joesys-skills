# Report Style: Write for Humans

Reference file for every skill in this collection that produces output a person will read — written reports, findings, summaries, HTML report prose, and replies in the conversation. Read this before writing any of those.

---

## Why This Exists

The reader of a skill's output is a human operator, often reading English as a second language. A report only has value if the reader understands it. Readability beats density: a paragraph that is technically complete but hard to parse fails at its only job. Optimize for the operator's understanding, not for sounding precise.

---

## The Rules

1. **Short sentences.** One idea per sentence.
2. **Everyday words.** Prefer the common word over the impressive one: "use" not "utilize", "start" not "initiate". Keep exact technical names when naming real code or tools.
3. **Explain jargon on first use.** Technical terms are fine — follow each one with a short plain explanation the first time it appears. Example: "a race condition (two pieces of code changing the same data at the same time)".
4. **Active voice, named actors.** "The parser drops the last row" — not "the last row is dropped".
5. **Lead with the point.** State the finding or conclusion first, then the supporting detail.
6. **No compressed shorthand.** Avoid arrow chains ("A -> B -> fails"), dense noun stacks, and abbreviations the reader did not introduce. Spell things out.
7. **Concrete over abstract.** Show the actual value, file, or example instead of describing it in general terms.

---

## The Non-Negotiable

Simplify the language, never the facts. File paths, line numbers, symbol names, versions, and the claims themselves stay exact. "This function might have some issues" is plain but useless. "`load_user()` at `auth.py:42` sends the raw form input to the database without escaping it" is plain and exact. Plain language is about the words around the facts, not about softening or blurring the facts.

---

## Before / After

**Before (dense):**

> Mitigation of the N+1 query issue necessitates eager-loading via `selectinload`, obviating per-row DB roundtrips -> latency reduction.

**After (plain):**

> This code runs one database query for every row in the list — 200 rows means 200 queries. Load the related data up front with `selectinload` so it becomes a single query. This is the main cause of the slow response time.

---

## Scope Notes

- This applies to conversation output too: status updates, result summaries, and answers — not only saved report files.
- User preferences (`.codex/skill-context/preferences.md`) still control detail level and explanation style. This file sets the baseline language; preferences tune it on top.
- Out of scope: code blocks, structured fields (JSON, schemas, commit-format headers), and text written for another AI to consume. Those follow their own contracts. But any prose a human reads inside them — a finding description, a commit body explanation — follows these rules.
- When dispatching subagents that write report prose, embed the short style block in their prompt (see below) instead of asking them to read this file — a dispatched agent may not be able to resolve this path.

**Embeddable block for subagent prompts:**

> Write for humans: the reader may speak English as a second language. Use short sentences, everyday words, and explain jargon on first use. State the point first, then the detail. Simplify the language, never the facts — paths, line numbers, and claims stay exact.
