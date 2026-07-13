---
name: prompt
description: "Use when the user invokes /prompt or asks to rewrite, improve, or turn rough, fragmented, or stream-of-consciousness thoughts into a prompt for another AI."
---

# Prompt Skill

## Purpose

Turn rough input into a clear, ready-to-copy prompt, then explain the meaningful changes so the operator learns how to write better prompts.

**Boundary:** Do not execute the generated prompt or begin the task it describes. This skill writes the prompt and stops.

## Invocation

```text
/prompt <request>
```

Treat all text after `/prompt` as the operator's source request. For an empty invocation, ask what they want turned into a prompt.

## Workflow

### 1. Recover the intent

Identify what the operator actually wants. Separate the goal from repetition, side comments, uncertainty, and conversational filler. Preserve the operator's intent, priorities, and meaningful voice.

The rewrite must not invent facts, deadlines, technologies, permissions, preferences, or requirements. It must not silently replace the requested task with a supposedly better task.

### 2. Decide whether to clarify

Material ambiguity changes the task, scope, permission, deliverable, or success criteria.

- If information is materially missing, ask one focused clarification at a time and wait for the answer. Do not generate the prompt yet.
- If uncertainty is minor, make a conservative assumption and disclose it in the explanation.
- If requirements conflict, ask the operator to resolve the conflict rather than choosing silently.
- Do not turn optional details into an interview.

### 3. Choose the target

Write a portable prompt by default. Tailor it to a named AI, coding agent, image generator, or other tool only when the operator names that target or the target materially changes the instructions.

Do not add provider-specific syntax to an otherwise portable prompt.

### 4. Build the smallest useful prompt

Create the smallest prompt that expresses the request clearly and completely. Consider:

- desired outcome;
- relevant context or source material;
- scope and boundaries;
- important constraints;
- requested deliverable and format;
- audience, tone, or detail level when relevant;
- success or verification criteria; and
- how the receiving AI should handle uncertainty.

Include only components that improve this request. Keep a simple task as a short paragraph. Use headings, bullets, delimiters, or ordered steps when complexity makes them useful.

### 5. Check and render

Run the Final Check, present the prompt first, explain the meaningful edits, and stop.

## Prompt-Writing Standard

- Put the task and desired outcome in clear, direct language.
- Include relevant context and remove unrelated detail.
- Prefer positive instructions that say what to do. Keep negative constraints when they define a real boundary.
- Define the output when format, audience, tone, length, or completeness matters.
- Add examples only when they communicate the expected format, style, or quality more clearly than prose.
- Use a functional role only when it adds relevant expertise, perspective, or tone. Do not add decorative claims such as "world-class expert."
- Put important instructions where they are easy to find and use consistent structure.
- Avoid repeating a requirement in several forms.

## Coding Requests

For software work, first distinguish diagnosis, implementation, review, or explanation. Add engineering details only when relevant:

- repository, file, feature, or branch scope;
- whether changes are authorized;
- interfaces, dependencies, or existing behavior to preserve;
- the required deliverable;
- how the result should be tested or otherwise verified; and
- how to report missing evidence instead of guessing.

Do not infer permission for destructive actions, pushes, external messages, or deployments. If that authority materially affects the request, clarify it.

## Output Format

Use this normal structure:

````text
## Prompt

```text
<ready-to-copy prompt>
```

## Why this prompt is stronger

- **Added:** <meaningful addition and why it helps>
- **Removed or simplified:** <removed material and why>
- **Reorganized:** <structural change and why>
- **Assumptions:** <conservative assumption and why it was safe>
- **Already strong:** <useful part of the original that was preserved>
````

Include only explanation labels that apply. Do not narrate every edit. Teach a reusable principle behind each meaningful change.

Keep the prompt copy-friendly. If it contains embedded code fences, use a longer outer fence so the entire prompt remains intact.

## Example

Input:

```text
/prompt can you check the auth thing, login sometimes hangs, don't change anything yet just tell me why and maybe what fix should be
```

Output:

````text
## Prompt

```text
Diagnose why login sometimes hangs in the current repository. Inspect the authentication flow and relevant logs or tests, but do not modify files.

Report:
- the most likely root cause with supporting evidence;
- other plausible causes you ruled out;
- the smallest recommended fix; and
- tests that would prove the fix.

If the repository does not contain enough evidence, state what information is missing instead of guessing.
```

## Why this prompt is stronger

- **Added:** A concrete diagnostic deliverable and evidence standard so the response can be checked.
- **Reorganized:** The request now separates the investigation boundary from the requested report.
- **Already strong:** The original "don't change anything yet" instruction was preserved as an explicit read-only boundary.
````

## Edge Cases

| Situation | Response |
|---|---|
| Empty invocation | Ask what the operator wants turned into a prompt. |
| Material ambiguity | Ask one focused question and wait. |
| Minor uncertainty | Use and disclose a conservative assumption. |
| Already-strong prompt | Make only worthwhile edits and explain what was already effective. |
| Contradictory requirements | Ask the operator to resolve the conflict. |
| Named target | Apply relevant target-specific conventions. |
| Embedded code fences | Preserve them with a longer outer fence. |
| Unsafe or disallowed request | Follow the host's safety rules; rewriting is not a bypass. |

## Final Check

Before returning the result, verify:

- Does the prompt preserve the operator's intent?
- Is the outcome clear without unnecessary detail?
- Are material gaps resolved and minor assumptions disclosed?
- Are there contradictory instructions?
- Did the rewrite invent facts, constraints, or authority?
- Is the structure proportionate to the task?
- Is the prompt shown before the teaching explanation?
- Did this skill stop without executing the generated prompt?

If any answer reveals a problem, revise before responding.
