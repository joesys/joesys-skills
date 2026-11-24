# Context & Instruction Quality Principles

Evaluate how well the user sets up and maintains the environment the agent works in: project instruction files, memory, session setup, and references. Strong context prevents problems that every other lens would flag.

This lens is the only place that scores persistent context (instruction files, memory, cross-session continuity). Other lenses do not score it again.

**Instruction files.** Claude Code reads `CLAUDE.md`. Codex reads `AGENTS.md`. Antigravity reads `GEMINI.md`, `AGENTS.md`, and `.agents/rules/*.md`. Any of these counts as the project instruction file. Do not mark a project down because it lacks another host's file. The same rule applies to the global file (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, or `~/.gemini/config/`). Claude Code does not load `AGENTS.md` unless `CLAUDE.md` imports it (for example, with `@AGENTS.md`). If the reviewed host cannot see the file, you may report that as a finding.

## Quick Diagnostic Guide

| Symptom | Likely Category |
|---|---|
| User re-explains project setup at the start of every session | Missing Persistent Instructions |
| Agent doesn't know the project's conventions, test commands, or build steps | No Project Instruction File |
| User corrects the same agent behavior across multiple sessions | Missing Memory/Feedback |
| Agent uses wrong language, framework, or pattern for the project | Missing Project Context |
| Session starts with 5+ minutes of "getting the agent up to speed" | Poor Session Setup |
| Agent doesn't remember decisions from a previous session | Memory Underutilization |

## Evaluation Criteria

### 1. Instruction File Utilization
Does the project have an instruction file (`CLAUDE.md` or `AGENTS.md`) with useful, current guidance?
- Strong: it holds build and test commands, conventions, and architecture notes, and they are still accurate.
- Weak: missing, empty, generic, or stale — or the user keeps telling the agent things that belong in it.

### 2. Memory System Usage
Does the user use memory for continuity across sessions?
- Strong: important decisions and corrections are saved as specific entries, and the agent uses them.
- Weak: no entries for the project, or the user repeats the same context and corrections every session.

### 3. Session Setup Quality
Does the user set up context at the start of a session?
- Strong: the opening message says what the session is about and where the work stands.
- Weak: starts with "let's continue" or assumes the agent knows what happened "last time" without memory or a handoff.

### 4. Reference Management
Does the user point the agent to relevant references?
- Strong: points to docs, issues, example code, or git history as starting points.
- Weak: describes a pattern from memory when an example exists, or relevant documentation is never mentioned.

### 5. Instruction Coherence
Do the user's instructions stay consistent through the session?
- Strong: changes in direction are stated openly.
- Weak: requirements contradict earlier ones without notice, or "what I actually meant was…" after the agent followed the stated requirement.

## Scoring Rubric

| Score Range | Description |
|---|---|
| 90-100 | Excellent infrastructure. Instruction file, memory, session setup all actively maintained. Agent has rich context from the start. |
| 80-89 | Good infrastructure. Most context is persistent. Occasional manual re-explanation. |
| 70-79 | Partial infrastructure. Some instruction file or memory usage but gaps cause repeated setup work. |
| 60-69 | Minimal infrastructure. Agent regularly operates without project context. Frequent re-explanation. |
| 50-59 | Almost no persistent context. Every session starts from scratch. |
| Below 50 | No instruction file (`CLAUDE.md` or `AGENTS.md`), no memory, no session setup. Agent operates blind in every session. |
