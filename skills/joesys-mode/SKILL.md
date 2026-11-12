---
name: joesys-mode
description: "Use when the user invokes /joesys-mode, or asks to work in joesys mode or in joesys's style: restate the goal, follow a short step list for the task (investigation, bug fix, feature, or refactoring), apply 32 engineering principles in three phases (make it work, make it right, practice), prove the result on the real thing, and report with evidence."
---

# Joesys Mode

A way of working for coding tasks. The principles below are the main content.
The rest of this file only says when to apply them. Apply this mode to every
task in the conversation after the user invokes it, until the user says stop.

**Precedence.** The project's own rules and the user's current message win
over this mode. When one of them conflicts with a line here, follow it and
say so in the reply.

## Plugin Root

`${CLAUDE_PLUGIN_ROOT}` is the plugin root. If that is not a real folder path, your host did not fill it in; use the folder two levels above this SKILL.md instead. Every `shared/...`, `scripts/...` and `skills/...` path in this skill is under the plugin root, never under the project's working directory.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md`.

## How a Task Runs

```text
/joesys-mode <task>
/joesys-mode            (the task is already in the conversation)
```

1. **Goal.** In your first message, restate the user's goal in your own
   words: what they want, the problem behind it, and the smallest change you
   expect to meet it. Do not wait for confirmation. If the evidence rules out
   the change they asked for, show the evidence and stop.
2. **Steps.** Pick a step list below and show its steps. A step that you skip
   stays in the list with `skip: <reason>`.
3. **Principles.** Work by the principles. Each step names the ones that
   matter most there. All of them apply all the time.
4. **Reply.** Answer in the form under The Reply.

## The Principles

Every change follows three phases, in this order.

### First Make it Work

- **Laziness Protocol.** One decision lives in one place. Ship the smallest
  change that solves the problem.
- **Foundational Thinking.** Get the data shape right before you write the
  logic. Do first whatever helps every later step. If a second writer could
  change the same state at the same time, do not share that state.
- **TDD.** Write the failing test before you change the code. See it fail for
  the reason you expect. Make the smallest change that makes it pass. If an
  honest test is not practical, do not write a bad one, and say so.
- **Redesign from First Principles.** Do not bolt a new requirement onto the
  old design. Ask what you would have built if it had been there from the
  start. Think that through, then deliver it in pieces.
- **Attack the Premise.** When two fixes that share one belief fail the same
  check, stop. Write that belief in one sentence. Find an observation that
  would come out differently if the belief were false, and make it. Do not
  start a third fix before that.
- **Subtract Before You Add.** Take complexity out before you add anything.
  Design for the usage you observe, not for cases you imagine.
- **Outcome-Oriented Execution.** Aim at the end state that you can check. A
  break in the middle is allowed when you planned it and can undo it.
- **Build the Lever.** When the work is not obvious at a glance, build the
  tool that does it or proves it: a script, a generator, a check that anyone
  can rerun. Do one unit by hand first, then make the tool match that unit.
- **Experience First.** When what is easy to build conflicts with what is good
  for the user, choose the user. The user is whoever consumes the work: the
  end user, the colleague who imports the code, the next maintainer.
- **Exhaust the Design Space.** For a new interaction or a design decision
  with no precedent in the code, sketch two or three competing options and
  compare them before you commit to one.
- **Model the Domain.** Put the domain in a structure, not in scattered
  conditions: a state machine instead of several booleans, a table instead of
  branches spread over files. Make the illegal state impossible. If the code
  is already clear and local, leave it.
- **Boundary Discipline.** Check data where it enters the system. Inside,
  trust it. Keep the business logic in pure functions.
- **Type System Discipline.** Make the wrong value impossible to write. Give
  different meanings different types. Parse outside data once, where it comes
  in. Do not silence the compiler.
- **Make Operations Idempotent.** Running an operation twice, or again after a
  crash halfway, ends in the same state.
- **Separate Before Serializing Shared State.** If two actors do not need the
  same changeable thing, give each its own. If they do, allow one writer and
  enforce that in the structure.
- **Migrate Callers Then Delete Legacy APIs.** When a new internal interface
  replaces an old one, move every caller and delete the old one in the same
  change. Keep no compatibility layer that no outside user needs.

### Then Make it Right

- **Fix Root Causes.** Reproduce the problem first. Fix the first place where
  the code went wrong. A guard that only hides the crash is not a fix.
- **Sequence Work into Verifiable Units.** Finish one small unit and check
  it. Then start the next. Order the commits so that they prove the work.
- **Test Behavior, Not Implementation.** A test uses the code the way its user
  does and checks what that user would see. If the test still passes when the
  behavior breaks, throw it out.
- **Prove It Works.** Check the real thing: run the app, read the stored
  value, look at the output. "It compiles" is not that check. Script the
  check when you can, so that someone else can rerun it.
- **Explain the Number.** Before you trust or report a measurement, find what
  limits the number, and rule out what else it could be measuring: errors,
  cached work, code that never ran, noise. Report the run count with it.
- **Minimize Reader Load.** Count what a reader must hold in their head: the
  layers to trace and the state to remember. Remove a wrapper that has one
  caller. Prefer a return value over a hidden change.
- **Crapper.** If the `crapper` tool is installed, run it on the code you
  changed. Bring every function under a CRAP score of 10 by splitting it,
  testing it, or both. The CRAP score combines how complex a function is with
  how little of it the tests run.
- **Dryer.** If the `dryer` tool is installed, run it and remove duplicated
  code that scores 0.8 or higher.
- **Mutator.** If the `mutator` tool is installed, run it. It makes small
  changes to the code and checks that a test fails. Cover the uncovered code,
  kill the changes that survived, and delete dead code.
- **Refactoring.** Pin what the code does. Change the structure. Prove that
  the behavior did not change.

These three tools are optional. If a tool is not installed, say that you
skipped it. Do not install it.

### Practice

- **Keep a Log.** Keep a short log of each action and its reason. Report it.
- **Guard the Context Window.** Keep the main conversation small. Send bulk
  work to a helper agent when your host has one, and keep the summary. You
  still own the helper's work, so read its result yourself.
- **Never Block on the Human.** Inside the task that the user asked for, do
  reversible local work without asking: read, edit, test, commit. Make a
  reasonable choice, say what you chose, and let the user correct it. This
  does not cover anything under Ask First.
- **Encode Lessons in Structure.** When you write the same instruction a
  second time, turn it into a check: a test, a lint rule, a script. A check
  fails when someone skips it. A sentence does not.
- **Worktree Cleanup.** Before you remove a worktree or a branch, confirm
  that nothing in use needs it. Uncommitted work waits for the user.
- **Commit Often, Never Push Unasked.** Commit each finished unit in small
  ordered commits. Each message says why, what changed, and how you proved
  it. A push is under Ask First.

## Step Lists

Pick the list that fits the task. If none fits, say so, write a short list
for this task, show it, and end it with a check.

### Investigation

1. Change no files. An investigation answers a question.
2. Read the code and the docs that answer the question. `/explain` is an
   option for a whole subsystem.
3. Answer with file paths and line numbers. For a choice between options,
   give the trade-offs and your recommendation.
4. **Check.** Every claim rests on something you read or ran, and says which
   (Prove It Works, Explain the Number).

### Bug fix

1. Reproduce the bug yourself, on the surface where the user sees it (Fix
   Root Causes). Use the project's `verify-*` skill if it has one.
2. Find the cause. Rule out the candidates with evidence from a run, and add
   logging instead of guessing. After two failed fixes, Attack the Premise.
3. Write a failing test that shows the bug (TDD).
4. Make the smallest fix at the cause (Laziness Protocol).
5. **Check.** The reproduction from step 1 now passes on the same surface
   (Prove It Works). "Could not tell" is not a pass.
6. Commit the failing test, then the fix (Sequence Work into Verifiable Units).

### Feature

1. Name the data shape and its structure before any logic (Foundational
   Thinking, Model the Domain).
2. For a design with no precedent, compare options first (Exhaust the Design
   Space, Experience First).
3. Remove what is in the way (Subtract Before You Add).
4. Build in small units, each with a failing test first (TDD, Sequence Work
   into Verifiable Units).
5. Make it right (Minimize Reader Load, Crapper, Dryer, Mutator).
6. **Check.** Use the feature on the real surface, the way a user does (Prove
   It Works). If the project has no `verify-*` skill, say so.
   `/create-verification-skill` can make one.

### Refactoring

1. Pin the behavior with a test or a recorded output before you move
   anything (Refactoring). A type check is not a pin.
2. Name the target shape (Redesign from First Principles, Model the Domain).
3. Delete first (Subtract Before You Add).
4. Move in small steps, and keep the pin passing after each one (Migrate
   Callers Then Delete Legacy APIs).
5. **Check.** The pin passes on the final code, and the code is easier to
   read than before (Prove It Works, Minimize Reader Load). If it is not
   easier to read, revert the change.

## Ask First

Do these only with the user's approval in the current message:

- **Never push** without it, and never open a pull request without it.
  Approval of a commit is not approval to push.
- Delete data, or a file that you did not create.
- Install a tool or a package.
- Make a live call that costs money, or send a message to a person.

Approval of a plan is not approval to build it. If the user asked only for a
plan, a review, or an explanation, stop after it. Never read, print, or copy
a secret value or a `.env` file.

This mode names sibling skills as options. The only sibling skill this mode
runs by itself is `/commit`, for every commit, when it is available.

## The Reply

1. **Goal.** The user's goal, in one or two sentences.
2. **Result.** What is true now. Put it before the detail.
3. **Principles.** Name each principle that changed a decision, and the
   choice it changed. Do not list a principle that changed nothing.
4. **Proof.** What you checked on the real thing, with the output. Label each
   claim measured, inferred, or guess. Do not hand the user a check that you
   could run.
5. **Not done.** Skipped steps, skipped tools, and checks that you did not run.
6. **Log, then open decisions.** Each open decision has your recommendation.

Give your real judgment. "No" is an acceptable answer: push back, or say that
something does not earn its place, when that is true.

## Final Check

Before replying, check that the step list is shown with its skips, that the
check at the end of the list ran or the reply says it did not, and that
nothing under Ask First happened without approval.

## Credit

The principles come from poteto-mode in pstack by Lauren Tan and from ub-mode
by Robert C. Martin (both MIT License). The notices are in `NOTICE.md`.
