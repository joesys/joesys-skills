---
name: architect
description: "Use when the user invokes $architect to design the shape of new code before anyone writes it: the caller's usage, the types, the function signatures, and the module boundaries. Several candidates design the same task alone, and the skill merges them into one design package and stops. SKIP if the user wants the code written now \u2014 the design comes first, and building is a separate request."
---

# Architect Skill

Design the shape of code before the code exists: how a caller uses it, the
types, the function signatures, and the module boundaries. The first design
that comes to mind is rarely the best one. So this skill gets at least two
candidates that differ in their whole shape, from different models when it
can, and merges them into one design.

**Boundary:** This skill designs and stops. It writes no code file in the
project. It does not implement the design, commit, push, or open a pull
request. Approval of a design is not approval to build it: building is a new
request.

## Collection Root

The collection root is the folder one level above this SKILL.md. Every path in this skill that starts with `../` is relative to this skill's folder, so it points into the collection root, never into the project's working directory.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `../shared/report-style.md`.

## Invocation

| Invocation | What happens |
|---|---|
| `$architect <what to design>` | Design, and show the design package in the conversation |
| `$architect --local <what to design>` | Use candidates from this host only. Call no other model. |
| `$architect --save <what to design>` | Also write the package to `docs/architect/<short-name>.md` |
| `$architect --save --path <folder> <what to design>` | Write the package to that folder instead |

## Rules

1. **Design only.** Change no file in the project, except the one package
   file that `--save` asks for.
2. **Never read secrets.** Do not open, print, or copy a `.env` file, a
   credential file, or a secret value. Never put a secret, or a file that
   holds one, into a prompt for another model.
3. **Other models only think.** Call them in their read-only mode, as
   `../shared/cross-model-dispatch.md` says.
4. **A candidate works alone.** It does not see the other candidates or the
   rubric.

## Workflow

### Step 1: Ground the problem

Read every part of the system that the new code touches: the callers, the
types that exist, the tests, the settings. Naming a file is not grounding.
Skip this step only for new code with nothing around it.

When you do not know a subsystem, `$explain <path>` is an option. When the
design changes who owns what, `$why <target>` is an option, so that the
reasons for the present shape become constraints and not guesses.

Then write two things:

- **The grounding note.** Every candidate gets it. It holds the task in one
  paragraph, who the caller is, the constraints (types to work with, callers
  that must not break, rules that cross the boundary), and the list of files
  that a candidate must read.
- **The rubric.** Three to six criteria that you can grade, for what a good
  design is on this task. The rubric is your tool for Step 3. Candidates do
  not see it.

### Step 2: Get the candidates

Get at least two candidates that differ in their whole shape, not in
details.

| Candidate | When | How |
|---|---|---|
| **Host candidate** | Always | One subagent of this host. |
| **Other models** | Unless `--local` | The models that `../shared/cross-model-dispatch.md` Section Host Detection names for this host, each through its own command-line tool. |
| **Second host candidate** | With `--local`, or when fewer than two candidates came back | One more subagent, with a different constraint. |

Start all candidates in one response, so that they run in parallel. For
same-platform subagents, do not pass a model or reasoning-effort override.
Let every subagent inherit the parent model and reasoning effort unless the
user explicitly asks for an override.

When two host candidates run, give each one a different constraint, so that
they do not design the same thing twice. For example: "make the public
interface as small as you can" and "make the most common call as simple as
you can".

**A host candidate** gets the grounding note and the **absolute path** to
`references/candidate-brief.md` in this skill's own folder, with one line
that tells it to read that file first. It reads the project files itself.

**Another model** may not be able to read the project, so its prompt file
holds everything. Let the shell append the brief and the files. Do not type
them out:

```bash
PROMPT_FILE=$(mktemp /tmp/design-candidate-XXXXXX.txt)
cat > "$PROMPT_FILE" << 'PROMPT_EOF'
<GROUNDING_NOTE>
PROMPT_EOF
cat "<ABSOLUTE_PATH_TO>/references/candidate-brief.md" >> "$PROMPT_FILE"
for f in <FILE_LIST>; do printf '\n## File: %s\n' "$f"; cat "$f"; done >> "$PROMPT_FILE"
```

Keep the prompt file under 150,000 bytes, because one of the tools rejects a
larger prompt. Send it with the commands in `../shared/cross-model-dispatch.md`
and delete the file afterwards. If a call fails, continue with the
candidates that you have.

### Step 3: Screen and compare

1. Read every candidate from start to end.
2. Check each one against `references/design-red-flags.md`. A red flag is a
   reason to change a shape or to reject it.
3. Score each one against the rubric, criterion by criterion, and not by
   overall feeling.
4. Compare how much each design hides. Prefer the one that puts more
   behavior behind a smaller public interface.

Do not favour the candidate from your own model family. If you notice that
you prefer it, check that the rubric says so too.

### Step 4: Pick a base and merge

Pick as the base the design that a later maintainer can extend most easily
without breaking a rule. When two are equal, take the smaller public
interface.

Then go through each other candidate once more for what is worth taking.
That is usually one or two things, not most of it. Work each one into the
base by hand, so that the result still reads as one design.

- When the candidates agree on one shape, that is a strong sign. Say so. No
  merge is needed.
- When they differ wildly, the task was not clear enough. Tighten the
  grounding note and run Step 2 once more. If they still differ, show the
  split to the user and ask.

### Step 5: Write the design package and stop

Write the package with the sections of `references/design-package.md`, in
that order. Show it in the conversation. With `--save`, also write it to the
file, and create the folder if it does not exist.

Then stop. Do not start to build. The last section of the package names the
first step, for the request that follows.

For one more opinion on the merged design, `$codex`, `$antigravity`, or
`$ai-council` is an option.

## Edge Cases

| Situation | Response |
|---|---|
| Every other model failed | Continue with host candidates, and say so in the package. |
| Only one candidate came back | Run a second host candidate with a different constraint. One candidate is not a comparison. |
| The change fits inside one function | Say that it needs no design, and stop. |
| The user asks you to build it right away | Finish the package first. Building is the next request. |
| The prompt for another model is too large | Shorten the file list. Say which files you left out. |

## Final Check

Before replying, check these four things:

- At least two candidates with different shapes were compared, or the
  package says why not.
- The package shows the caller's usage before the types.
- "Alternatives considered" names at least one shape that lost, and why.
- No file in the project changed, apart from a package that `--save` asked
  for.

## Credit

Adapted from the `architect` skill in pstack by Lauren Tan (MIT License).
The license notice is in `NOTICE.md` in this skill's folder.
