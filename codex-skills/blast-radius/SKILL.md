---
name: blast-radius
description: "Use when the user invokes $blast-radius, or asks what a change could break somewhere else, to find the breakage that the diff does not show and to prove, by running real code, the one fact that makes the change safe. SKIP if the user wants the changed code itself reviewed for bugs \u2014 that's $quick-review or $codereview."
---

# Blast Radius Skill

Find what a change breaks somewhere else, before it ships. A list of callers
is not the answer: a search finds those in a second. The answer is the
breakage that a search does not show.

A written analysis reads as convincing whether or not it is true. So this
skill does not hand back an analysis alone. It finds the one or two facts
that the safety of the change depends on, and it proves them by running
code.

**Boundary:** This skill changes no product code. It writes a proof script,
and it does not commit, push, or open a pull request.

## Collection Root

The collection root is the folder one level above this SKILL.md. Every path in this skill that starts with `../` is relative to this skill's folder, so it points into the collection root, never into the project's working directory.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `../shared/report-style.md`.

## Invocation

| Invocation | The change |
|---|---|
| `$blast-radius` | The current branch against its fork point, plus uncommitted changes |
| `$blast-radius --commit abc123` | One commit |
| `$blast-radius --pr 123` | One pull request |
| `$blast-radius <description>` | A change that is planned and not written yet |

Find the fork point as `../shared/review-common.md` Section Base Branch Detection
says.

## Rules

1. **Leave product code alone.** Put the proof script in a scratch folder
   outside the project when it can run from there. If it must sit inside the
   project to run, leave it uncommitted and name it in the reply.
2. **Never read secrets.** Do not open, print, or copy a `.env` file, a
   credential file, or a secret value.
3. **Ask before a live call that costs money or acts on the outside world.**
   When the project has a fake or a test mode at that boundary, use it, and
   say `fake` in the proof.
4. **Never make up a caller, a path, or an interface.** Cite a real
   `file:line`. A search that finds nothing is an answer too.

## How Sure Are You

For each fact that the safety of the change depends on, go as far down this
list as is cheap, and say where you stopped.

1. **Said.** You stated it. This is worth nothing alone.
2. **Pointed.** You cited the real `file:line`, or the source code of the
   library.
3. **Walked.** You followed the failure step by step and showed that it
   cannot reach the bad state.
4. **Ran.** A script or a test calls the real code and fails loudly if you
   are wrong.
5. **Reproduced.** You saw it in the running app.

Level 4 is usually one small script. It loads the same version of the
library that the app ships, and it calls the exact function that you worry
about. For level 5, use the project's `verify-*` skill if it has one.

## Workflow

### Step 1: Read the change

Read the diff, and the symbols that it adds, changes, and deletes. Say what
the code now does differently, including the part that the diff does not
spell out. Read the commit messages, and the pull request if there is one.
When the reason for the old code matters, `$why` is an option.

### Step 2: Find the one fact

Most changes that look risky are safe because of one fact, such as "this
call only drops cache entries that are already dead, and does nothing else".
Find that fact. If it holds, most of the risky cases are cleared at once.
Spend your time here, not on a long list of maybes.

### Step 3: Look where a search stops

- **The library.** Read the source of what the change calls, at the pinned
  version, with any local patch.
- **Time.** Work out when each piece runs: at startup, at shutdown, in a
  callback, in a retry, in a second process.
- **What a symbol search misses.** The data that a service returns, a
  database column, a file format, another program that reads the same
  bytes, a feature flag, a setting, generated copies of a file, and code
  three steps downstream.

### Step 4: Weigh each risk

Give each risk a real chance of happening and a real cost if it does. Keep
the risks that you confirmed. List the ones that you checked and cleared
separately.

### Step 5: Prove the one fact

Write a script or a test that runs the real code. Run it, and paste the
output. If you cannot run it, write `unproven`, say which level you reached,
and say what would prove it.

### Step 6: Reply

- **What it does.** What changed, including the part that is not obvious.
- **The one fact it is safe because of.** The fact, the level that you
  reached, and the proof.
- **Risks.** For each one: how it breaks, the `file:line`, how likely, how
  bad, and how to check. Paste the proof for the ones that matter.
- **Cleared.** What you checked, and why it is fine.
- **Before you merge.** The cheapest test or reproduction that would catch
  the real bug, with the path of the script that you wrote.

For a big or wide change, a second model's reading is an option: `$codex`,
`$antigravity`, or `$ai-council`. Different models catch different bugs.

## Edge Cases

| Situation | Response |
|---|---|
| There is no change to read | Ask which change the user means. |
| The change is only planned | Prove the fact against the current code. Say that no diff was read. |
| The fact needs production data or a paid service | Stop at the level that you can reach. Write `unproven` and what would prove it. |
| The proof fails | That is the finding. Report it as a confirmed risk, with the output. Do not fix the code unless the user asks. |

## Final Check

Before replying, check these four things:

- The reply states the one fact and the level that you reached.
- A proof is pasted, or the reply says `unproven`.
- Every risk cites a real `file:line`.
- No product code changed, and the reply names every file that you wrote.

## Credit

Adapted from the `blast-radius` skill in pstack by Lauren Tan (MIT License).
The license notice is in `NOTICE.md` in this skill's folder.
