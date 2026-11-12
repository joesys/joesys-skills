---
name: create-verification-skill
description: "Use when the user invokes $create-verification-skill to generate a project-local skill that starts the real app, uses it the way a user does, and captures proof that a feature works \u2014 for a web page, a command-line tool, a service, a desktop or mobile app, or a library. Also use when the user asks for a scripted way to prove behavior in the running app because the project has none."
---

# Create Verification Skill

## Purpose

Unit tests show that code paths work. They do not show that the real app
works for a user. This skill gives a project a scripted way to show that. It
writes one project-local skill, `verify-<app>`, which tells an agent how to
start the app, use a feature the way a user does, and capture evidence.

The reader of the generated skill is another agent. That agent reads the
skill cold, in the middle of a task, and has never seen the app. Write every
step for that reader: exact commands, real names from this project, and no
placeholders.

**Boundary:** This skill writes the verification skill and its feature map.
It does not change product code, and it does not commit, push, or open a pull
request. It leaves the new files uncommitted and lists them.

## Collection Root

The collection root is the folder one level above this SKILL.md. Every path in this skill that starts with `../` is relative to this skill's folder, so it points into the collection root, never into the project's working directory.

## Write for Humans

Write the final report in plain English for a reader who uses English as a second language. Follow `../shared/report-style.md`. The generated skill is text for an agent: keep it exact and literal.

## Invocation

```text
$create-verification-skill
$create-verification-skill <app or folder>
```

With no argument, use the project in the working directory. Text after the
command names the app or the folder, for a repository that holds several apps.

## Rules

1. **Never read secrets.** Do not open, print, or copy a `.env` file, a
   credential file, or a secret value. When the app needs a secret to start,
   write down the name of the variable or file and how the user provides it,
   never the value. If the app cannot start unless you read a secret, stop
   and ask the user.
2. **Ask before a live call that costs money or acts on the outside world.**
   Examples: a paid API, a real email or message, a payment, a write to
   production data. When the project already has a fake or a test mode at
   that boundary, use it.
3. **Label every proof `live` or `fake`.** For each outside service that a
   proof touched, say which one answered. A proof that used a fake does not
   prove that the live service works.
4. **Leave product code alone.** If the app does not build or start from the
   checkout as it is, report the exact command and the error, and stop. A
   skill written against a broken app teaches wrong steps. One exception: a
   missing file that has nothing to do with the behavior may block startup,
   such as a sample config or an empty static folder. The generated skill may
   create that file, mark it as verification scaffolding, and remove it in
   cleanup.
5. **Use the tools the project already has.** If driving the app needs a tool
   that is not installed, name the tool and ask before you install it.
6. **Never stop a process by name.** Stop only the processes that this run
   started, by their process ID or their session name.
7. **Never drive an instance you did not start.** The user's open session or
   a shared server may hold real work. If only one instance can run at a
   time, say so in the generated skill.
8. **Do not overwrite an existing verification skill.** If `verify-<app>`
   already exists, ask whether to update it.

## Workflow

### Step 1: Learn the app from the repository

Answer these questions from the code and the docs. Ask the user only what
you cannot observe.

| Question | What to find |
|---|---|
| **Surface** | What does a user touch? A web page, a command-line or terminal app, a desktop app, a service, a mobile app, or a library. A repository can have several. Pick the main one and note the rest. |
| **Run** | How does the app start locally? Prefer the project's own documented command: a package script, a Makefile target, the README quick start. Note the ports, the names of the environment variables, the seed data, and the sign-in. |
| **Services** | Which outside services does each feature call: data providers, model tools, payment, email, messaging? For each service, find out whether a call costs money and whether the project has a fake or a test mode for it. Read past the first service you find, because one command can call several. |
| **Drive** | How can an agent use the app from a script? Look for existing harnesses first: browser test specs, terminal scripts, endpoints that accept a plain request, a debug port. Only then choose a general recipe: a browser driver for a web or Electron app, a terminal session for a command-line or terminal app, plain HTTP for a service, a small script on the public interface for a library. |
| **Observe** | What evidence can be captured? Screenshots, terminal transcripts, response bodies, logs, exit codes, stored data. |
| **Isolate** | Can two instances run side by side, with their own ports, data folders, and profiles? |

### Step 2: Write the skill

Write the skill to `.agents/skills/verify-<app>/SKILL.md` in the project. If
your host keeps project skills in a different folder, write it there instead
and say which folder you used.

Start the file with YAML frontmatter: `name: verify-<app>`, and a
`description` that names the app, the surface, and when to use the skill.
Without frontmatter, no host registers the skill.

Then write these sections. Each one uses what Step 1 found.

| Section | What it must hold |
|---|---|
| **Launch** | The exact command that starts the app for verification, and the sign that it is ready, such as a log line or a prompt. Launch must reach a usable state from an empty data folder, including migrations and seed data. Ready means usable, not only that a process answers: a database health check can pass while its setup scripts still run. Say how to stop the app. If the app cannot use a separate data folder, say so, and say what a run changes in the user's data. A short-lived command-line tool has no server to keep alive: build it once, then run each drive in its own isolated terminal session. |
| **Doctor** | One read-only check that answers "is this instance worth driving?": the process is up, the version or build is the right one, this run owns the port, the sign-in is valid. The reader runs it first whenever something looks wrong. |
| **Drive** | The recipe, with real selectors and commands from this project, not examples. Prefer stable handles (accessible labels, data attributes, prompt strings, route paths) over screen coordinates and tab order. |
| **Evidence** | What to capture for a proof, where it goes, and the proof standards below. |
| **Cleanup** | How to stop what the run started and remove its scratch data. Cleanup never removes the evidence. |
| **Helpers** | Every script the skill ships. Each one is executable, and the skill body shows how to call it. A helper that the reader must reverse-engineer is not a helper. |

Write these proof standards into the Evidence section:

- Use the real user path. Do not call internal setters or test-only
  endpoints.
- Capture the action and the state that results, not only the last screen.
- Check side effects (files written, rows stored, messages sent) as well as
  what is visible.
- Say `live` or `fake` for each outside service, as rule 3 requires.
- Check every log and transcript for secret values before you keep or
  quote it. Count the matches. Do not print the matching lines.
- When the safe path is a dry run or a test mode, observe what it really
  skips: files, network calls, version-control refs. Do not trust its name.
  Some dry runs still use the network or open a browser.

### Step 3: Write the feature map

Create `features/README.md` next to the generated `SKILL.md`, plus one file
per user-facing feature. Start with the three to five most important
features. Find them in the routes, commands, menus, or docs.

Each feature file starts with a title and one paragraph about what the user
sees. Then it has exactly these four sections, in this order:

1. `Sub-features`: short IDs, with one line for each behavior.
2. `How to get to it (user POV)`: every way a user reaches the feature.
3. `Driving it with <harness>`: the preconditions, then each user action
   paired with the exact command and the result to observe. The first
   precondition names every outside service that the feature calls, and
   says for each one whether a call costs money.
4. `Gotchas`: traps that waste or spoil a verification run.

In the index, mark each feature `run` with the date, or `not run`. A recipe
that you wrote from the docs and never ran is `not run`.

`references/feature-map-example.md` shows the index file and one feature file.

The map is the project's maintained source for verification. A proof that
drives one easy entry point is incomplete when the map lists others. If the
seed data lacks something that a journey needs, the journey reports a failure
and the reason goes under `Gotchas`. Never weaken a journey to make it pass.

### Step 4: Run the generated skill once

A generated skill that was never run is a draft. Follow its own instructions
from start to end, as the next agent would:

1. Launch.
2. Doctor.
3. Drive one mapped feature. One is enough: the map lets later runs cover
   the rest.
4. Capture the evidence.
5. Clean up. Then confirm that the evidence still exists at the place the
   skill names. A cleanup that deletes the proof fails this step.

Fix what fails in the generated skill, not in the product. Run the generated
cleanup after every failed attempt too, so a broken attempt leaves no process
and no port behind.

You may have run it on a stand-in for the real target: a container in place
of a fresh machine, or a local stack in place of a remote one. Then list
every setup step that the stand-in did and the real target will not. Those
steps stay unproven until a run on the real target covers them.

### Step 5: Report

Reply in the conversation with these parts:

- **Where the skill is.** The folder path. Other agent hosts read project
  skills from other folders, so say which host this folder serves.
- **What is proven.** The feature, the entry point, the evidence path, and
  `live` or `fake` for each outside service.
- **What is not proven.** The other features in the map, and every stand-in
  step.
- **What you created.** Every new file. All of them are uncommitted.
- **What you need from the user.** For example a secret, or approval for a
  live call or an install.

## Edge Cases

| Situation | Response |
|---|---|
| The repository holds several apps | Ask which one, unless the user named it. Write one skill per app. |
| The app does not start as checked out | Report the command and the error, and stop (rule 4). |
| The app is a library with no running surface | Drive it with a small script that calls the public interface the way a caller does. |
| Only one instance can run, and the user's instance is open | Do not drive it. Say so and ask. |
| `verify-<app>` already exists | Ask whether to update it (rule 8). |
| The run in Step 4 could not finish | Report the skill as a draft and name the step that failed. Do not call it proven. |

## Final Check

Before replying, check these four things:

- The generated skill has no placeholder left.
- You ran it once and the evidence still exists, or the report calls it a
  draft.
- No secret value is in any file you wrote.
- Nothing that this run started is still running.

## Credit

Adapted from the `create-verification-skill` skill in pstack by Lauren Tan
(MIT License). The license notice is in `NOTICE.md` in this skill's folder.
