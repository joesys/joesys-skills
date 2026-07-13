# Prompt Helper Skill Design

**Date:** 2026-07-13
**Status:** Approved
**Release target:** 18.0.0
**Feature branch:** `feat/prompt-helper-skill`

## Purpose

Add a `/prompt` skill that turns stream-of-consciousness input into a clear,
ready-to-copy prompt. The skill should work for general AI tasks and recognize
when a request needs coding-specific instructions.

The skill is also a teaching tool. After presenting the rewritten prompt, it
will explain the meaningful additions, removals, and structural changes so the
operator can improve their own prompting over time.

## Problem

People often know what they want but describe it in the order ideas occur to
them. Important context may be buried, constraints may be implicit, and the
desired output may be unclear. A capable model can sometimes infer the intent,
but that creates avoidable ambiguity and inconsistent results.

Rigid prompt templates are not a complete solution. They make simple requests
too long and may add irrelevant roles, sections, or constraints. The helper
therefore needs to improve clarity without replacing the operator's intent or
inflating every request into a specification.

## Goals

The implementation will:

1. Accept `/prompt <request>` where the request may be rough,
   conversational, fragmented, or stream-of-consciousness.
2. Produce a portable prompt by default.
3. Recognize coding requests and add relevant engineering instructions.
4. Ask a clarification only when the answer could materially change the
   result.
5. Explain what changed and why after the finished prompt.
6. Teach reusable prompt-writing principles without overwhelming the
   operator.
7. Publish the skill for Claude Code and Codex as release `18.0.0`.

## User Experience

### Invocation

```text
/prompt <something the operator wants>
```

Codex will expose the generated skill as `$prompt` through the existing
adapter.

### Interaction flow

1. Parse the operator's input and identify the intended outcome.
2. Determine whether missing information is material.
3. If it is material, ask one focused clarification at a time and wait for the
   answer.
4. Otherwise, make only conservative assumptions and disclose them.
5. Build the smallest prompt that expresses the request clearly and
   completely.
6. Present the prompt first, followed by a concise teaching explanation.
7. Stop. Do not execute the generated prompt or begin the requested task.

### Clarification policy

A clarification is material when different answers would lead to meaningfully
different work, permissions, scope, deliverables, or success criteria.

The skill will not ask about optional details that can be safely inferred or
omitted. Minor uncertainty should not turn the helper into an interview. When
clarification is required, the skill asks only one question per turn.

### Target policy

Prompts are tool-independent unless the operator names a target AI or the
target materially affects the instructions. When a target is known, the skill
may apply relevant conventions for that model or agent. It must not introduce
provider-specific syntax into an otherwise portable prompt.

## Prompt Construction

### Adaptive structure

The skill will consider these prompt components:

- desired outcome;
- relevant context or source material;
- scope and boundaries;
- important constraints;
- requested deliverable and format;
- audience, tone, or level of detail when relevant;
- success or verification criteria; and
- instructions for handling uncertainty.

Only useful components belong in the result. A simple request may remain a
single paragraph. A complex request may use headings, bullets, delimiters, or
ordered steps.

### Preserve intent

The rewrite must preserve what the operator actually wants. It must not invent
facts, deadlines, technologies, permissions, preferences, or requirements. It
must not silently replace the requested task with a supposedly better task.

If the input contains conflicting requirements, the skill asks the operator to
resolve the conflict rather than choosing one silently.

### Current prompting practices

The skill will apply these cross-provider practices:

- Put the task and desired outcome in clear, direct language.
- Include relevant context and omit unrelated detail.
- Prefer positive instructions that state what to do. Use negative constraints
  when they define a real boundary.
- Define the desired output when format, audience, tone, length, or completeness
  matters.
- Add examples selectively when they communicate the expected format, style,
  or quality more clearly than prose instructions.
- Use a functional role only when it adds relevant expertise, perspective, or
  tone. Do not add decorative claims such as "world-class expert."
- Keep simple tasks simple and structure complex requests consistently.
- Perform a final check for contradictions, missing critical information,
  invented assumptions, and unnecessary detail.

This is an adaptive standard, not a claim that one universal prompt format is
best for every model. Prompt design remains iterative, and target-specific
guidance may override the portable default when a target is explicitly known.

### Coding-aware behavior

For software requests, include engineering details only when relevant, such as:

- whether the operator wants diagnosis, implementation, review, or explanation;
- the repository, files, or feature area in scope;
- constraints on dependencies, interfaces, or existing behavior;
- whether changes are authorized;
- existing work that must be preserved; and
- how the result should be tested or otherwise verified.

The skill must not infer permission for destructive actions, pushes, external
messages, deployments, or other consequential side effects.

## Output Contract

Normal output uses this structure:

````text
## Prompt

```text
<ready-to-copy prompt>
```

## Why this prompt is stronger

- **Added:** <meaningful addition and why it helps>
- **Removed or simplified:** <removed material and why>
- **Reorganized:** <structural change and why>
- **Assumptions:** <conservative assumptions, if any>
````

Only relevant explanation categories are included. The explanation should
teach reusable principles rather than narrate every edit.

The prompt must be copy-friendly. If the generated prompt contains a fenced
code block, use a longer outer fence so its contents remain intact.

## Edge Cases

- **Empty invocation:** Ask what the operator wants turned into a prompt.
- **Material ambiguity:** Ask one focused clarification before generating.
- **Minor uncertainty:** Make a conservative assumption and disclose it.
- **Already-strong prompt:** Preserve it, make only worthwhile changes, and
  identify what was already effective.
- **Contradictory requirements:** Ask the operator to resolve the conflict.
- **Named target AI:** Apply relevant target-specific conventions.
- **Unsafe or disallowed request:** Follow the host's safety rules; do not use
  rewriting to disguise or enable the request.
- **Embedded code fences:** Preserve them with a safe outer delimiter.

## Architecture and Publication

The implementation is a self-contained judgment-based skill:

- `skills/prompt/SKILL.md` is the canonical source.
- No helper script, reference file, template, or shared contract is required.
- `codex-skills/prompt/SKILL.md` is generated by the existing adapter and must
  not be edited by hand.
- README navigation and plugin descriptions will advertise the new helper.
- Published skill inventories will increase from 21 to 22.
- Claude, Codex, marketplace, generated-manifest, and version-contract metadata
  will be synchronized at `18.0.0`.

All design, plan, implementation, and release commits stay on
`feat/prompt-helper-skill` until the user explicitly chooses how to integrate
the branch. Nothing will be pushed without explicit push authorization.

## Testing Strategy

Implementation will follow red-green-refactor. Before writing the skill, add
focused contract tests and confirm they fail because the prompt skill and its
behavioral rules do not yet exist.

Behavioral scenarios will cover:

1. A messy general request becoming a concise prompt.
2. A coding request receiving relevant scope, authorization, and verification
   guidance.
3. Material ambiguity causing exactly one focused clarification.
4. Minor uncertainty producing a disclosed conservative assumption.
5. An already-strong prompt remaining compact.
6. A named target AI receiving appropriate tailoring.
7. A request with embedded code fences remaining copyable.

Repository contracts will verify:

- the canonical and generated skills contain the agreed behavior;
- `/prompt` is adapted to `$prompt` for Codex;
- the published inventory contains 22 skills;
- README documentation covers invocation, output, and teaching behavior;
- all published versions equal `18.0.0`;
- the generated Codex tree matches a fresh adapter build; and
- the full repository test suite passes.

## Expected Files

- `skills/prompt/SKILL.md`
- `tests/test_prompt_skill_contract.py`
- `tests/test_codex_adapter.py`
- `README.md`
- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `.codex-plugin/plugin.json`
- `.agents/plugins/marketplace.json`
- generated files under `codex-skills/`
- `docs/superpowers/specs/2026-07-13-prompt-helper-skill-design.md`
- a later implementation plan under `docs/superpowers/plans/`

## Non-Goals

- Do not execute the generated prompt.
- Do not build a prompt library or save prompt history.
- Do not require a fixed template for every request.
- Do not ask a full questionnaire before producing a prompt.
- Do not optimize exclusively for coding tasks or one AI provider.
- Do not automatically inspect unrelated repository files merely to add more
  context.
- Do not add deterministic helper code for a judgment-based rewrite.
- Do not manually edit generated `codex-skills/` files.

## Acceptance Criteria

- `/prompt <rough request>` produces a clear, ready-to-copy prompt.
- General and coding requests both receive appropriate treatment.
- The default result remains portable across AI systems.
- Clarifications occur only for material ambiguity and are asked one at a time.
- Conservative assumptions are disclosed.
- The rewrite preserves intent and does not invent facts or authority.
- Positive instructions, selective examples, functional roles, and the final
  quality check are applied adaptively.
- The explanation identifies meaningful additions, removals, reorganization,
  assumptions, and already-strong elements when relevant.
- The skill never executes the generated prompt.
- Claude and Codex expose the skill with synchronized release `18.0.0`.
- Focused tests, generated-tree freshness checks, and the complete test suite
  pass.
- Existing unrelated untracked files remain untouched.

## Research Basis

The prompt-building standard was checked on 2026-07-13 against current
first-party guidance:

- [OpenAI Prompting Fundamentals](https://openai.com/academy/prompting/)
- [OpenAI Prompt Engineering Guide](https://developers.openai.com/api/docs/guides/prompt-engineering)
- [Anthropic Prompting Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Google Prompt Design Strategies](https://ai.google.dev/gemini-api/docs/prompting-strategies)

These sources agree on clear instructions, relevant context, explicit output
expectations, and adaptive structure. They differ in model-specific advice,
which supports a portable default with conditional target-specific tailoring.
