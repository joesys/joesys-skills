---
name: huh
description: "Use when the user invokes /huh to re-explain the previous assistant message in plain language an ESL reader can follow — the issue, the options with pros and cons, and a recommendation with its trade-off — closing with where the answer is least confident and what the operator has not asked. SKIP if the user wants a second model's independent opinion — that's /claude, /codex, /antigravity, or /ai-council."
---

# Huh Skill

## Purpose

Re-explain the assistant's most recent substantive message in plain English
that a reader with English as a second language can follow. When that message
involves a problem or a decision, also lay out the issue, the context around
it, the options with their good and bad points, and a recommendation with its
trade-off stated openly. Always close with two disclosures: where this
explanation is least confident, and what the operator has not asked yet.

**Boundary:** This skill explains. It never acts — no edits, no commands, no
re-running or re-doing the earlier work. It writes the explanation and stops.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md` (resolve against the plugin root — two levels above this SKILL.md — never the project's working directory).

## Invocation

```text
/huh
/huh <focus>
```

With no arguments, re-explain the whole previous message. Treat any text after
`/huh` as the focus: center the explanation on that part, and keep enough
surrounding context that the answer stands alone.

The target is the most recent substantive assistant message. Relayed output
from another tool or model (a delegation skill, a subagent report) counts as
that message's content. Skip pure acknowledgments such as "Done." and target
the last message with real content.

## Context Loading

Read `.claude/skill-context/preferences.md` if present, and let the
assumed-knowledge level tune the depth.

## Workflow

1. Find the target: the most recent substantive assistant message, narrowed by
   the focus if one was given.
2. Classify it: purely informational, or does it involve a problem or a
   decision?
3. Write the sections below in order. Omit the sections that do not apply —
   never pad them.
4. Run the Final Check, reply in the conversation, and stop. No files, no
   saved reports.

## Output Format

Sections appear in this order, using these exact headings.

| Section heading | When | Content |
|---|---|---|
| **In plain words** | Always | The previous message re-told in simple English. Short sentences, everyday words, jargon explained on first use. |
| **The issue and how we got here** | Only if a real problem exists | What is wrong, and the context: what led to it and why it matters now. |
| **Your options** | Only if a decision is at hand | Each option with its good points and bad points, in plain terms. |
| **What I suggest** | Only when options exist | The recommended option, the reason, and the trade-off being accepted stated openly ("choosing this means giving up ..."). |
| **Where I am least sure** | Always | The part of this very answer with the lowest confidence, and why. |
| **What you have not asked** | Always | The biggest questions the operator has not asked and might not realize exist. |

Length is proportionate to the source: `/huh` after a simple answer produces a
short reply.

## Rules

1. **Faithful first.** Re-tell what the earlier message said; do not rewrite
   history. Label every addition with the marker "(new — the earlier answer
   did not mention this)". If something in the earlier message looks like an
   actual mistake, say so plainly as a labeled addition — never paper over it
   and never silently correct it.
2. **Plain language, exact facts.** Follow the Write for Humans rules above.
3. **Specific confidence, not hedging.** "Where I am least sure" must name a
   concrete part and the reason: a guessed assumption, an unverified claim, or
   thin evidence. Generic disclaimers such as "I could be wrong about
   anything" are banned.
4. **Curated unasked questions.** "What you have not asked" is a spotlight,
   not a brainstorm dump. One to three items, biggest first.

## Edge Cases

| Situation | Response |
|---|---|
| No previous assistant message (fresh session) | Say there is nothing to explain yet and ask what to explain. |
| Previous message already simple | Keep it short; briefly answer the two closing sections; no padding. |
| Previous message is relayed output from another tool or model | Explain that content; "Where I am least sure" covers both the source and the explanation. |
| `/huh` repeated on the same message | Simplify further with different words or an analogy; never repeat the first explanation verbatim. |
| Previous message was an error or failure report | Treat the error as the issue; the full decision-support structure usually applies. |

## Final Check

Before replying, check that this skill explained without acting. If it did
anything else, revise before replying.
