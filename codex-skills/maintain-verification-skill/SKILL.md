---
name: maintain-verification-skill
description: "Use when the user invokes $maintain-verification-skill to bring a project's `verify-<app>` skill and its feature map back in line with the app: read the source of every feature, drive every feature once in the real app, and correct only what a run proved. SKIP if the project has no verification skill yet \u2014 that's $create-verification-skill."
---

# Maintain Verification Skill

A feature map goes stale as soon as the app changes. This skill is the
upkeep pass for a skill that `$create-verification-skill` wrote, or for any
project-local skill that has launch and drive sections and a feature map.
The unit of care is the feature, not the sentence: read every feature from
the source, and drive every feature once in the real app.

**Boundary:** This skill edits the verification skill and nothing else. It
does not commit, push, or open a pull request. It leaves its corrections
uncommitted and lists them.

## Collection Root

The collection root is the folder one level above this SKILL.md. Every path in this skill that starts with `../` is relative to this skill's folder, so it points into the collection root, never into the project's working directory.

## Write for Humans

Write the final report in plain English for a reader who uses English as a second language. Follow `../shared/report-style.md`. The verification skill is text for an agent: keep it exact and literal.

## Invocation

```text
$maintain-verification-skill
$maintain-verification-skill <skill name or folder>
```

## Outcomes

Give the pass one outcome, and say which:

- **clean**: every feature was read from the source and driven live, and
  nothing needed a correction.
- **changed**: proven corrections to the map, the skill, or its helper
  scripts are on disk, uncommitted.
- **blocked**: the pass could not finish. Say exactly what stopped it.

Next to the outcome, say how many features were driven out of how many. A
pass that did not drive every feature cannot be `clean`.

## Rules

1. **Edit only the verification skill's own folder:** its `SKILL.md`, its
   `features/`, and the scripts that it owns. Never edit product code. When
   the map describes behavior that the app no longer has, it is either a
   stale map or a broken product. Fix a stale map. Report a broken product,
   and do not hide it in the map.
2. **Correct only what a run proved.** A reading of the source finds
   candidates. Only the live pass confirms them.
3. **Never read secrets.** Do not open, print, or copy a `.env` file, a
   credential file, or a secret value.
4. **Ask before a live call that costs money or acts on the outside world.**
   Each feature file names its outside services in its first precondition.
   Collect them. Ask once, before the live pass, for the calls that need
   approval. Use a fake or a test mode where the project has one. A feature
   without approval is `not run`.
5. **The verification skill's own safety rules hold.** Never drive an
   instance that you did not start. Never stop a process by name.

## Workflow

### Step 1: Find the target

Find the project-local skill whose body has launch and drive sections and a
feature map. It is usually in `.agents/skills/verify-*/` (or
`.agents/skills/verify-*/` in Antigravity). If there are several, ask which one.
If there is none, stop and point to `$create-verification-skill`. Do not invent
a target.

### Step 2: Tidy the index

Read `features/README.md` and list the files next to it. Fix entries that
are missing, extra, doubled, or dead.

### Step 3: Read the source of every feature

Run one read-only subagent for each feature file, all in parallel. For
same-platform subagents, do not pass a model or reasoning-effort override.
Let every subagent inherit the parent model and reasoning effort unless the
user explicitly asks for an override.

Each subagent gets the path of its feature file and returns four things:

1. How the feature works, from the source, with its entry points.
2. Where the feature file likely differs from the source, with a
   `file:line` for each point, or "none".
3. One short recipe to check the feature live.
4. The outside services that the feature calls, and whether a call costs
   money.

The subagents never drive the app and never edit a file. If your host has
no subagents, read each feature yourself, one at a time.

### Step 4: Reconcile

Every feature file now has a summary. Merge recipes that need the same app
state, so that the live pass needs few launches. Open the cited differences
and check them. Do not prove again what came back clean. Then look at the
recent changes for a user-facing feature that the map does not list. Call
one missing only when you can name its source path.

### Step 5: Drive every feature live

Required even when the source looks clean. You do all the driving, and you
follow the Launch section of the verification skill: one long-lived
instance, or a fresh session for each drive. Keep three rules for the whole
pass:

1. **Check health first.** Run Doctor before the first drive, on each fresh
   session, and again after any failed drive. When Doctor cannot see the
   problem, such as a stuck screen on a healthy process, go back to a known
   state or start the app again.
2. **The evidence survives every cleanup.** Check it at the place that the
   skill names. Do not assume it.
3. **Nothing that a drive started outlives the drive.** Clean up after a
   failed attempt too.

When Doctor fails because the verification skill itself is out of date,
that is a stale skill: fix it under rule 1 and try once more before you call
the pass `blocked`.

A feature is `unreachable` only when you can name the concrete thing that
is missing (a sign-in, a paid plan, an operating system, outside state) and
the route that you tried. If the feature file does not list that
precondition, the file is stale.

### Step 6: Sort what you found

| Finding | What it is | What to do |
|---|---|---|
| The file describes the feature wrongly, or leaves a part out | A stale map | Correct the file. |
| A user-facing feature has no file | A stale map | Drive it first. Then write its file in the shape of the others, and add it to the index. |
| The feature works, but the recipe or a helper cannot drive it | A gap in the harness | Fix the recipe or the helper, and drive it again before the fix stays. A helper is executable, and the skill body shows how to call it. |
| The app itself is broken | A product problem | Report it to the user. Keep it out of the corrections. |

### Step 7: Update the marks and report

In the index, mark each feature `run` with today's date, or `not run` with
the reason. When a drive hit a product problem, name the step that fails in
the mark, so that a bare `run` does not read as "works". The recipe itself
stays as it is: it describes what the app should do. Read every file that
you changed once more. Then stop the app,
after the last drive, so that nothing outlives the pass. The evidence
stays.

Reply in the conversation with these parts:

- **Outcome,** and how many features were driven out of how many.
- **What changed.** Every corrected file, with one line on the run that
  proved the correction. All of them are uncommitted.
- **Product problems.** Each one with the command and the output.
- **Not run and unreachable.** Each feature, with the reason.
- **Services.** `live` or `fake` for each outside service that a drive
  touched.

## Final Check

Before replying, check these four things:

- Every feature file has a summary from the source and a live result, or
  the report says why not.
- A run proved every correction.
- No file outside the verification skill's folder changed.
- Nothing that this pass started is still running.

## Credit

Adapted from the `maintain-verification-skill` skill in pstack by Lauren Tan
(MIT License). The license notice is in `NOTICE.md` in this skill's folder.
