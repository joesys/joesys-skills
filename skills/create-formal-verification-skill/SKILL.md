---
name: create-formal-verification-skill
description: "Use when the user invokes /create-formal-verification-skill to check one promise of the code for every case in a stated scope, with a model checker, a prover, or another verifier, and to leave a project-local skill that reruns the check when the code changes. Use for concurrency, retries, state machines, parsers, or unsafe code, where a bug costs much and tests rarely reach it. SKIP if the user wants to prove that a feature works in the running app — that's /create-verification-skill."
---

# Create Formal Verification Skill

## Purpose

A test checks the cases that someone thought to write. Formal verification
checks every case inside a stated scope: every order of steps in a model,
every input up to a bound, or every input. This skill finds the place in the
project where that matters most, verifies one promise there, as one or more
properties, and writes a project-local skill, `formal-<area>`. With that
skill, the next agent can check a change against the promise.

Four terms, used the same way everywhere below:

- A **property** is a rule that must always hold.
- A **model checker** is a tool that tries every order of steps in a small
  model of the design.
- A **counterexample** is a sequence of steps that breaks the property.
- A **bound** is the limit of what the tool tried.

The reader of the generated skill is another agent. That agent reads it cold,
in the middle of a change, and has never seen your work. The user must be
able to trust the result and act on it without learning the verification
language.

**Boundary:** This skill writes the verification and the skill that runs it.
It does not commit, push, or open a pull request. It leaves the new files
uncommitted and lists them.

## Plugin Root

`${CLAUDE_PLUGIN_ROOT}` is the plugin root. If that is not a real folder path, your host did not fill it in; use the folder two levels above this SKILL.md instead. Every `shared/...`, `scripts/...` and `skills/...` path in this skill is under the plugin root, never under the project's working directory.

## Write for Humans

Write the final report in plain English for a reader who uses English as a second language. Follow `shared/report-style.md`. The generated skill is text for an agent: keep it exact and literal.

## Invocation

```text
/create-formal-verification-skill
/create-formal-verification-skill <area, file, or bug>
```

With no argument, choose the target yourself (Step 1). Text after the command
names where to start.

## Rules

1. **Findings stay findings.** When the current code breaks the property,
   report it, with the counterexample in the code's own words. Do not weaken
   the property or the model until it passes. Do not change product code
   unless the user asks.
2. **A check that you have never seen fail proves nothing.** Show each
   property failing on a broken variant of the code that it guards, such as a
   removed check or a reordered step.
3. **Say what is covered.** A pass covers the model or the bound, not the
   whole system. State what is verified, under which bounds and assumptions,
   and what is left out.
4. **Ask before you install a tool.** Name the tool, the version, and the
   folder it goes to. Prefer a tool that the project's developers can install
   and run. Record the exact version and a checksum, so that the next run
   uses the same tool. Put a downloaded tool in its own folder that version
   control ignores.
5. **Never read secrets.** Do not open, print, or copy a `.env` file, a
   credential file, or a secret value.

## Workflow

### Step 1: Choose the target from the code

Answer from the code. Ask the user only what you cannot observe. If the user
named an area or a bug, start there.

A good target is a promise that the code makes, where a break harms users and
tests rarely reach the case that breaks it. A doc comment often states the
promise. Look at every candidate before you choose. Choose the strongest
target in the repository, not the one that is easiest to verify. Say why you
chose it, and name the runner-up.

Read the existing tests for the target. They state the promise in the
project's own words, and they show which cases tests already reach.

### Step 2: Let the question choose the tool

Pick the tool that answers the question at the lowest cost.

| The question | The usual tool |
|---|---|
| Can events happen in a bad order? | A model checker over a small model of the design. TLA+ is the default, for code in any language. |
| Does the code itself behave for every input? Examples: memory safety, overflow, a data-structure rule. | A verifier that runs on the code. |
| Must the property hold at every size, where a bound is not enough? | A proof. |

If no verifier runs on this language, say so. Then test the real code with
generated inputs, not a hand model of the function. Tell the user why you
chose the tool.

### Step 3: Write the verification

A good verification has these seven qualities:

- **True to the code.** Every part of the model or proof points to code that
  a reviewer can open: a file and a function. One indivisible step in the
  verification is one indivisible step in the code. The names come from this
  project.
- **Able to fail.** Rule 2 applies. Show that the check reaches the states
  it is about, too. A check that explored nothing passes for the wrong
  reason.
- **Findings stay findings.** Rule 1 applies.
- **Honest about scope.** Rule 3 applies.
- **Readable without the tool.** State the property in one plain sentence and
  the harm in another. Tell a counterexample as a short sequence of steps in
  the code's words.
- **Cheap to rerun.** One command, a pinned tool version, and a run short
  enough that the next agent uses it on every relevant change. The tool's
  own output files go to an ignored folder. After one failing run, look at
  the version-control status to be sure.
- **Kept in step with the code.** Record which files and functions each check
  covers, and the commit at which you last confirmed that the verification
  describes them. That commit is the sync commit. The check command itself
  fails when the covered code differs from the code at the sync commit. A
  tool that reads a model does not read the code, so without this rule a
  changed function still passes. Give the check command a way to run the
  verification alone, without that comparison. Use it only during an
  update.

### Step 4: Write the skill

Write the skill to `.claude/skills/formal-<area>/SKILL.md` in the project (in
Antigravity, write to `.agents/skills/formal-<area>/SKILL.md`). If your host
keeps project skills in a different folder, write it there instead and say which
folder you used. Name the area after the code that the check guards, for example
`formal-payment-retries`. Keep the model and the helper scripts in the same
folder.

Start the file with YAML frontmatter: the `name`, and a `description` that
names the area and says when to use the skill. Without frontmatter, no host
registers the skill.

Then write these sections, with this project's real commands, paths, and
names. Leave no placeholder.

| Section | What it must hold |
|---|---|
| **Property** | The property and the harm, one plain sentence each. |
| **Coverage** | The files and functions that the check covers, the sync commit, the bounds, the assumptions, and what is not covered. |
| **Run** | The one command, the tool and its version, the expected output, and the run time. |
| **Read a failure** | How to tell the two kinds of failure apart. "The covered code changed" means the verification may be stale. A counterexample means the property broke. For a counterexample, replay it against the real code, step by step. If a step cannot happen in the code, the verification is wrong. If every step can happen, it is a bug. |
| **Update** | How to change the verification when a code change is intended. Write the update from the code, not from what makes the check pass. Move the sync commit forward only after you confirm that the verification describes the code at the new commit. |
| **Helpers** | Every script the skill ships. Each one is executable, and the skill body shows how to call it. |

### Step 5: Prove it before you hand off

A verify skill that was never run is a draft. Follow the generated skill
once, as the next agent would, on a scratch change that breaks the property
in the real code. It must catch the break:

1. Confirm that nothing is running the code you are about to change.
2. Make one small scratch change that breaks the property.
3. Run the check. It fails, because the covered code changed.
4. Update the verification to describe the changed code, as the Update
   section says. Run the verification alone. It fails with a
   counterexample.
5. Remove the scratch change with version control, and undo the update. Run
   the check once more. It is back where it started: passing, or failing only
   on the findings that you will report.
6. Then confirm that the working tree is as it was, apart from the new skill.

If the skill misses the break, or a step does not run, fix the skill or the
verification, not the scratch change.

### Step 6: Report

Reply in the conversation with these parts:

- **What is verified.** The property and the harm, the target, and the
  runner-up.
- **The tool.** Its name and version, why you chose it, and what you
  installed and where.
- **The scope.** The bounds, the assumptions, and what is not covered.
- **The result, in plain words.** A finding, or a pass. If the pass follows
  directly from one simple construct, such as one lock around a whole
  function, say so. The check then guards against a later change. It is not a
  discovery.
- **How to run it,** and how long it takes.
- **What you created.** Every new file. All of them are uncommitted.

Suggest a second target only if you found a close one.

## Edge Cases

| Situation | Response |
|---|---|
| No target is worth it | Say so. Do not verify something trivial to have a result. |
| The tool cannot be installed | Stop and report the exact error. |
| The current code breaks the property | Report the finding. Still write the skill. Its check fails on that finding until the code is fixed. |
| `formal-<area>` already exists | Ask whether to update it. |
| The run in Step 5 could not finish | Report the skill as a draft and name the step that failed. |

## Final Check

Before replying, check these four things:

- You saw each property fail on a broken variant.
- The check command fails when the covered code changes.
- The scratch change is gone and the working tree is as it was.
- The report says what the check does not cover.

## Credit

Adapted from the `create-formal-verification-skill` skill in pstack by Lauren
Tan (MIT License). The license notice is in `NOTICE.md` in this skill's
folder.
