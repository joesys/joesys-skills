---
date: 2026-11-12
topic: first-runs-found-live-bug
project: joesys-skills
session: unknown
status: unwritten
---

## Situation

Five skills were adapted from pstack, a public skill collection by Lauren
Tan: `/why`, `/blast-radius`, `/benchmark-checklist`,
`/maintain-verification-skill`, and `/architect`. Each skill is a markdown
file of instructions for an AI agent. Each one got contract tests first
(tests that check the words of the skill), and then one real run on work in
this repository.

## Key Moments

1. **Run the new skill on the project itself** — After each skill's tests
   passed, the skill was used once on a real question about this repository,
   and the gaps it showed went into a second commit. Alternative was to stop
   when the tests were green and call the skill done. Inferred reasoning:
   the tests check that a sentence is present. They cannot show whether an
   agent that follows the sentence does the right thing.
2. **A claim written before the measurement turned out false** — For
   `/benchmark-checklist`, the claim was "building the Codex copy with 26
   skills is not measurably slower than with 23". Seven alternating runs on
   each side showed 197 ms against 231 ms, 17% slower. A profile showed why:
   one regular-expression pass for each skill name over every file.
   Alternative was to time it once and trust the feeling that three small
   files cannot matter.
3. **A proof that passed on its first run was not trusted** — For
   `/blast-radius`, a script showed that a new skill name changes nothing
   else in the generated copy. It passed at once. Only a control case showed
   that it could fail: a skill named `health` rewrites the web route
   `/health` in another skill's text. Alternative was to accept the pass.
4. **Two design candidates found the same live bug** — For `/architect`, two
   helper agents designed a repair for that rewrite rule. Both opened with
   the same finding: the committed Codex copy of `/ai-council` already has
   seven broken file paths (`<RUN_DIR>/codex.txt` became
   `<RUN_DIR>$codex.txt`). The bug was older than this work, and 348 passing
   tests had not seen it.
5. **The bug was reported, not fixed** — The repair design exists, but
   building it was left for a separate decision. Inferred reasoning: the
   request was to adapt five skills, and approval of a design is not
   approval to build.

## The Insight (Inferred)

A check that compares two builds of the same code cannot see a bug that
both builds share. This repository had a test that rebuilt the generated
copy and compared it with the committed copy. Both sides came from the same
rewrite rule, so both held the same wrong text, and the test stayed green.
What found the bug was not a better test. It was using the tools on a real
task and reading the real output. This is an inference from one session:
three of the five first runs found something true about the repository that
no test covered.

## Supporting Evidence

- **Commits:**
  - `806588f` merge: adapt five skills from pstack
  - `af3b597` fix: the benchmark run and the 17% result
  - `a0c517e` fix: the proof script and the `health` control case
  - `28bd633` fix: the `/architect` run and the `/ai-council` bug
- **Conversation exchanges:**
  - AI, before measuring: "The claim to test, written before measuring:
    'Building the Codex copy with 26 skills is not measurably slower than
    with 23 skills.'"
  - Design candidate A: "Problem 1 is already live.
    `codex-skills/ai-council/SKILL.md` holds 7 corrupted paths."
- **Code snippets:**
  - Source: `cat > <RUN_DIR>/codex.txt << 'PROMPT_EOF'`
  - Generated copy: `cat > <RUN_DIR>$codex.txt << 'PROMPT_EOF'`

## Open Questions

- Did any Codex user run `/ai-council` with the broken paths, and what
  happened?
- Would the bug have been found sooner by one real run of the Codex copy
  than by more tests?
- The helper agents that found the bug used about 222,000 tokens. Was that
  a fair price, or luck?
- How should a generated copy be checked, when the generator is the only
  source of the expected output?
