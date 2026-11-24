---
date: 2026-11-12
topic: approval-covered-one-service
project: joesys-skills
session: unknown
status: unwritten
---

## Situation

A new skill, `/create-verification-skill`, was written and tested. Its tests only check the words of the skill, so it needed one real run on a real project. The developer offered moirai, a command-line research app, and approved one live call to its paid data provider.

## Key Moments

1. **The question was asked before the app was understood.** The AI asked: "For moirai, please name a ticker that is already cached, or approve one live FMP call." At that point it had read only the first part of the README, which names FMP. The developer answered "I approve a live FMP call". Alternative was to learn the app first and ask afterwards. The question came first because the AI wanted an answer before starting.

2. **The skill's own first step found three more paid services.** Step 1 of the skill is "learn the app from the repository". Reading further showed that `moirai show` also calls the X API (a config comment says about $1.78 for each company in each run), two news search services, and model tools. The approval named FMP only. Alternative was to run `show` anyway, because "the proof was approved". The AI chose `moirai refresh`, which calls FMP only, and read the result back with `moirai history`.

3. **The claim "FMP only" was checked, not assumed.** `refresh` asks model tools for a peer list when none is saved. The AI checked the run history for a saved list before the run. After the run, the history said "Recorded model attempts in this run: 0".

4. **A project rule changed the method.** The plan was to let a fresh agent run the skill, so that someone who did not write the text would read it cold. moirai's `AGENTS.md` says to ask the developer before starting another agent. The AI ran the proof itself and recorded the limit in the commit message.

5. **Each gap became a failing test before it became text.** The run showed four gaps: no question about outside services, no mark for which recipes were really run, no rule for an app that cannot use a separate data folder, and no check for secrets in copied logs.

## The Insight (Inferred)

An approval covers only what the person asking described. If the list of what a command touches is incomplete, the approval is incomplete in the same way. "Ask before a paid call" is not a rule anyone can follow until every call is known. So the inventory comes first, and the question comes second.

## Supporting Evidence

- **Commits:**
  - `4dcf8ce` feat(skills): add /create-verification-skill for proof in the real app
  - `82276fd` fix(skills): close four gaps found by the first live verification run
- **Conversation exchanges:**
  - AI: "`moirai show` can call FMP, your paid data provider. I will not make that call without your approval."
  - Developer: "I approve a live FMP call"
- **Code snippets:** the row added to the skill's first step:

  ```markdown
  | **Services** | Which outside services does each feature call: data providers, model tools, payment, email, messaging? For each service, find out whether a call costs money and whether the project has a fake or a test mode for it. Read past the first service you find, because one command can call several. |
  ```

## Open Questions

- When the developer approved "a live FMP call", did they expect the full `show` workflow to run?
- Would the developer have approved the X API and the news searches too, if the first question had listed them?
- Is a proof that the author ran good enough, or does the cold-reader run still matter?
