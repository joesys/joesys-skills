---
name: ai-council
description: "Use when the user invokes /ai-council to consult three frontier AI models (Claude, GPT, Antigravity) in parallel and synthesize their responses into a consensus analysis"
---

# AI Council Skill

Send the same question to three frontier AI models (Claude, GPT via Codex, Antigravity) in parallel. Then combine their answers into one analysis that shows where they agree and where they differ.

## Write for Humans

Write everything a person reads in plain English for a reader who uses English as a second language. Follow `shared/report-style.md` (resolve against the plugin root — two levels above this SKILL.md — never the project's working directory).

## Ground Rules

- A **leg** is one model's dispatch and response (Claude leg, Codex leg, Antigravity leg). The **council** is all three.
- Dispatch the question to the council. Do not answer it yourself instead.
- Treat the three legs as peers. Do not tilt the synthesis toward the host model; dissent from any leg gets equal weight.
- Never drop a leg silently. If a leg fails, name the missing model in the synthesis and offer a retry.
- Write nothing to the project except the council output folder.
- Read `shared/delegation-common.md` (resolve `shared/...` against the same plugin root) for prompt delivery, critical evaluation, and failure reporting, and `shared/model-defaults.md` for the current CLI command templates.

## Invocation

- `--no-save` - do not write output files (saving is on by default)
- `--path <dir>` - save under this folder instead of `docs/ai-council/`. Relative paths resolve from the current working directory.
- The remaining text is the question.

If the question is empty or unclear, ask the user to clarify.

Read `.claude/skill-context/preferences.md` if present. Apply its communication style (detail level, assumed knowledge, tone) to the synthesis only. The legs get the user's question without preferences, so each model answers in its own way.

## Phase 1: Gather Context

Gather the facts the legs need before you dispatch; this needs no approval. For a project question, read the relevant files and git state. For a general technology question, search the web for recent facts if you can. Give all three legs the same context bundle, and summarize it if it is large. If some context cannot be gathered, continue with what you have.

## Phase 2: Build the Prompts

Each leg gets a four-part prompt:

1. **Role preamble (per leg):** "You are the [Claude/GPT/Antigravity] representative on a multi-model AI council. Give your independent analysis. Be explicit about your confidence level and reasoning. State your position clearly."
2. **Context bundle** (same for all legs).
3. **Refined question** (same for all legs): the user's question restated clearly, with the goals, constraints, and scope that the context implies. Clarify; do not change the user's intent. When in doubt, keep the original wording.
4. **Original question** (same for all legs): "Original question from the user: [verbatim user input]"

Write the prompts to files in a unique folder for this run. The Bash tool starts a new shell on every call, so a shell variable would be gone by the dispatch call. Create the folder in its own call, then copy the printed path literally into every later command (shown below as `<RUN_DIR>`). A unique folder keeps two councils running in parallel from overwriting each other's files.

```bash
mktemp -d "${TMPDIR:-/tmp}/council-XXXXXX"
```

```bash
cat > <RUN_DIR>/codex.txt << 'PROMPT_EOF'
<four-part prompt with the GPT preamble>
PROMPT_EOF
cat > <RUN_DIR>/antigravity.txt << 'PROMPT_EOF'
<four-part prompt with the Antigravity preamble>
PROMPT_EOF
cat > <RUN_DIR>/claude.txt << 'PROMPT_EOF'
<four-part prompt with the Claude preamble>
PROMPT_EOF
```

After all legs finish, delete the folder: `rm -rf <RUN_DIR>`.

## Phase 3: Parallel Dispatch

Launch all three legs in a single response, as three parallel tool calls. Use a 600000 ms timeout on each Bash call.

### Codex Leg

Replace `<CODEX_CMD>` with the template from `shared/model-defaults.md` § Codex, but change its trailing `2>/dev/null` to `2><RUN_DIR>/codex.log`. Codex prints its `session id:` line on stderr. Read that line from the log after the run; the ID makes the later resume offer reliable.

```bash
cat <RUN_DIR>/codex.txt | <CODEX_CMD>
```

### Antigravity Leg

Replace `<AGY_CMD>` with the template from `shared/model-defaults.md` § Antigravity. The adapter reads the prompt from stdin; do not add `-p` or format flags.

```bash
cat <RUN_DIR>/antigravity.txt | <AGY_CMD>
```

### Claude Leg

**Use a Claude Code Fable subagent** only when the parent runs in Claude Code and Phase 1 resolved all the context the question needs. This is an intentional cross-model council leg, so its explicit `model: "fable"` setting is an exception to normal parent-model inheritance. Pass the full four-part prompt. A subagent is faster because there is no CLI startup.

**Use CLI** when the parent is not Claude Code, or when the question points to files or code paths that Phase 1 could not fully resolve and the Claude leg needs tool access to explore. Replace `<CLAUDE_CMD>` with the template from `shared/model-defaults.md` § Claude CLI, change `--model opus` to `--model fable` (the council's Claude leg runs Fable), and append `--name` so it can be resumed:

```bash
cat <RUN_DIR>/claude.txt | <CLAUDE_CMD> --name "council-<topic>"
```

### When Legs Fail

Continue with the legs that answered. Name each missing leg in the synthesis and offer a retry; if two legs failed, warn that the council is degraded. If all three fail, report the failures as `shared/delegation-common.md` § Failures describes. When a retry succeeds, update the synthesis and the saved files.

## Phase 4: Synthesis

1. **Summary** - 2-3 sentences: what the council was asked and the overall direction of the answers.
2. **Confidence Matrix** - include it when the legs covered several dimensions. Rows are the themes the legs addressed; columns are Claude, GPT, and Antigravity. Each cell is **High**, **Medium**, or **Low** (judged from stated certainty and hedging), or **Not addressed**.
3. **Consensus Points** - where all responding legs agree, with the reasoning.
4. **Tensions & Disagreements** - where the legs differ. State each position fairly and explain the nature of the disagreement (for example, "Claude and GPT favor X for reason A, while Antigravity argues Y because of B").
5. **Synthesized Recommendation** - your own recommendation, informed by all legs. Weigh the quality of reasoning, not the vote count.

## Post-Synthesis Options

Offer the next steps and wait for the user's answer:
- Resume commands for the legs that used a CLI: `/codex resume <SESSION_ID>`, `/antigravity resume`, `/claude resume council-<topic>`. A subagent Claude leg cannot be resumed. A resume does not update this synthesis; the user can run `/ai-council` again with a refined question.
- A retry for any failed leg.
- A devlog scrap (`/devlog scrap --from-context`) only when something surprising came up, such as an unexpected disagreement or a recommendation against common practice.

## Phase 5: Save the Output

Save by default unless `--no-save` is set. Write to `docs/ai-council/YYYYMMDD-<topic>/` (or under `--path`):

```
docs/ai-council/20260325-postgresql-vs-mongodb/
├── claude.md
├── codex.md
├── antigravity.md
└── synthesis.md
```

- `<topic>` comes from the question (kebab-case, 3-5 words).
- Each leg file holds that leg's raw response, under a header with the model name, timestamp, and the prompt it received. Skip the file for a leg that failed.
- `synthesis.md` holds the full synthesis as presented.
- If the folder already exists, add a number: `YYYYMMDD-<topic>-2/`, `-3/`, and so on.
- If writing fails, warn the user and show the synthesis in the terminal only.
