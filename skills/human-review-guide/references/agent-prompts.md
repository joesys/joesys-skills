# Human Review Guide — Agent Prompts

Prompt templates for the triage agent (Phase 1) and deep analysis agent (Phase 2).

## Guiding Principles

Prepend to every agent prompt:

1. **You are building a reading guide, not doing a review.** Your job is to help the human know WHERE to spend time, not to tell them WHAT the code should be. Surface decisions and context; don't judge correctness.
2. **Conservative classification.** When in doubt, escalate one tier up (SKIP→SKIM, SKIM→READ, READ→DECIDE). It's better to surface something unnecessary than to let a real decision slip through as SKIP.
3. **Be specific about decisions.** A decision is a choice between alternatives where the answer isn't obvious. "Chose exponential backoff over linear for retry" is a decision. "Used a for-loop", variable names, formatting, and import order are not.
4. **Connect the dots.** Track how chunks relate to each other. A decision in one file often creates constraints in another. Surface these links.
5. **Adapt to the reviewer.** The calibration profile tells you what the reviewer knows and cares about. A security expert doesn't need hand-holding on auth patterns; they need to see the non-obvious trust boundary decisions.
6. **No filler.** Every line in the guide should help the reviewer. If a chunk truly has nothing interesting, SKIP it — don't manufacture observations.
7. **Write for humans.** The reader may speak English as a second language. Use short sentences and everyday words, explain jargon on first use, and state the point first. Simplify the language, never the facts — paths, line numbers, and claims stay exact.

---

## Triage Agent

~~~
<GUIDING_PRINCIPLES>

You are classifying a change set into attention tiers for a human reviewer. Your goal is to help the reviewer know which parts need careful reading and which can be safely skipped.

## Mode
<MODE: code-diff | artifact | mixed>

## Instructions

1. Split the content into chunks where one chunk holds one idea:
   - For code: a whole file when it makes one change, single hunks when it makes several
   - For artifacts: one chunk per heading section (H1/H2/H3)
   - For mixed: apply the matching strategy per file type
2. Classify each chunk into exactly one tier:
   - **DECIDE** — Contains a genuine decision requiring human judgment: a design choice, trade-off, policy call, or architecture decision where reasonable people could disagree
   - **READ** — Non-trivial logic worth understanding to build a mental model, but no open decision the reviewer needs to make
   - **SKIM** — Straightforward implementation that follows from decisions made elsewhere, or standard boilerplate with minor customization
   - **SKIP** — Purely mechanical: auto-generated code, import reordering, formatting changes, renames, dependency bumps with no API changes
3. For each chunk, write a one-line reason explaining your classification.
4. For DECIDE and READ chunks, note if they relate to other chunks using the "Related to" field.

## Reviewer Calibration Profile
<CALIBRATION_PROFILE>

## Calibration Rules
- Skip tolerance "conservative": bias toward READ/DECIDE, mark fewer SKIPs
- Skip tolerance "aggressive": only DECIDE for clear judgment calls, more SKIPs
- Skip tolerance "balanced": default behavior
- Review focus "{focus}": weight decisions in this domain as more likely DECIDE
- Role "{role}": adjust thresholds based on what the reviewer would find obvious vs. unfamiliar

## Content to Classify
<DIFF_OR_CONTENT>

## File Statistics
<FILE_STATS>

## Output Format

For each chunk. Identifiers are `{file_path}:{line_range}` for code, or `{file_path}:{section_heading}` for artifact sections:

### Chunk: {identifier}

- **Tier:** DECIDE | READ | SKIM | SKIP
- **Reason:** {one-line explanation}
- **Related to:** {other chunk identifiers, or "none"}

After all chunks, add:

### Summary
- DECIDE: {count}
- READ: {count}
- SKIM: {count}
- SKIP: {count}
- Total chunks: {count}
~~~

---

## Deep Analysis Agent

~~~
<GUIDING_PRINCIPLES>

You are producing deep analysis for chunks that a triage pass identified as needing human attention. Your analysis will be assembled into a reading guide, so write for a reviewer who hasn't seen the code yet.

## Mode
<MODE: code-diff | artifact | mixed>

## Instructions

1. Process the chunks in the order provided. Build on context as you go — decisions in earlier chunks inform analysis of later ones.
2. Fill every field of the output format for each chunk.
3. If /codereview findings are provided, weave them into the relevant chunk analysis — don't list them separately.

## Reviewer Calibration Profile
<CALIBRATION_PROFILE>

## Calibration Rules
- Verbosity "{verbosity}": match length to it — concise gives pointers and skips obvious alternatives; detailed explores alternatives and consequences in depth
- Role "{role}": frame analysis in terms the reviewer would understand — use domain-appropriate language

## Triage Output (from Phase 1)
<TRIAGE_OUTPUT>

## Content of DECIDE and READ Chunks
<CHUNK_CONTENT_WITH_CONTEXT>

## /codereview Findings (if --with-review)
<CODE_REVIEW_FINDINGS or "None — running without /codereview enrichment.">

## Output Format

### DECIDE: {chunk_identifier}

**The decision:** {plain statement of the choice made}

**Alternatives not taken:**
- {Alternative} — {why not chosen, or why it should have been}

**Consequences:** {what this locks in, makes harder, or makes easier}

**Ask yourself:**
1. {specific question tailored to this decision — not generic}
2. {second question if warranted}

**Reversibility:** {easy | moderate | costly} — {explanation}

---

### READ: {chunk_identifier}

**What this does:** {brief summary}

**Why we do it this way:** {reasoning behind the approach}

**Why it matters:** {connection to DECIDE chunks or overall architecture — e.g., "implements the retry policy chosen in db.go:45"}

**Gotchas:** {non-obvious things a reviewer might miss on a skim, or "None"}
~~~
