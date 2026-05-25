# Context & Instruction Quality Principles

Evaluate how well the user sets up and maintains the environment for effective agent collaboration — CLAUDE.md files, memory utilization, session setup, and reference management. This is the foundational lens: strong context prevents issues flagged by every other lens.

## Quick Diagnostic Guide

| Symptom | Likely Category |
|---|---|
| User re-explains project setup at the start of every session | Missing Persistent Instructions |
| Agent doesn't know the project's conventions, test commands, or build steps | No CLAUDE.md |
| User corrects the same agent behavior across multiple sessions | Missing Memory/Feedback |
| Agent uses wrong language, framework, or pattern for the project | Missing Project Context |
| Session starts with 5+ minutes of "getting the agent up to speed" | Poor Session Setup |
| Agent doesn't remember decisions from a previous session | Memory Underutilization |

## Evaluation Criteria

### 1. CLAUDE.md Utilization
Does the project have a CLAUDE.md (or equivalent) with useful instructions?

**Signs of strong utilization:**
- Project CLAUDE.md exists with project-specific guidance
- Contains build/test commands, coding conventions, architecture notes
- Instructions are current and accurate (not stale)
- User references CLAUDE.md when the agent doesn't follow conventions

**Signs of weak utilization:**
- No project CLAUDE.md at all
- CLAUDE.md exists but is empty, generic, or stale
- User repeatedly tells the agent things that should be in CLAUDE.md
- Global CLAUDE.md only, no project-specific instructions

### 2. Memory System Usage
Does the user leverage the memory system for cross-session continuity?

**Signs of strong usage:**
- Important decisions and preferences are saved to memory
- User asks agent to remember recurring patterns
- Memory entries are specific and actionable (not vague notes)
- Agent references memory to maintain continuity

**Signs of weak usage:**
- No memory entries for the project
- User repeats the same context every session
- Memory exists but is never referenced or updated
- Important corrections are never persisted

### 3. Session Setup Quality
How effectively does the user establish context at the start of a session?

**Signs of strong setup:**
- Clear opening statement of what this session is about
- References to relevant issues, PRs, or prior work
- Provides necessary context that isn't in CLAUDE.md
- Sets expectations for the session's scope

**Signs of weak setup:**
- Jumps into tasks with no context
- Assumes agent knows what happened "last time" without memory
- Doesn't orient the agent to the current state of the work
- Starts with vague "let's continue" without specifying what

### 4. Reference Management
Does the user provide and point to relevant references effectively?

**Signs of strong reference management:**
- Links to relevant documentation, issues, or PRs
- Points agent to example code or patterns to follow
- References specific files or functions as starting points
- Uses git history for context ("check the last 3 commits on this file")

**Signs of weak reference management:**
- Agent operates without any external references
- User describes a pattern from memory instead of pointing to an example
- Relevant documentation exists but is never referenced

### 5. Instruction Coherence
Do the user's instructions remain consistent throughout the session?

**Signs of strong coherence:**
- Requirements don't contradict earlier statements
- Changes in direction are explicitly acknowledged
- Constraints remain stable unless intentionally revised

**Signs of weak coherence:**
- Contradictory requirements within the same session
- Implicit assumption changes without notifying the agent
- "What I actually meant was..." after agent follows stated requirements

## Scoring Rubric

| Score Range | Description |
|---|---|
| 90-100 | Excellent infrastructure. CLAUDE.md, memory, session setup all actively maintained. Agent has rich context from the start. |
| 80-89 | Good infrastructure. Most context is persistent. Occasional manual re-explanation. |
| 70-79 | Partial infrastructure. Some CLAUDE.md or memory usage but gaps cause repeated setup work. |
| 60-69 | Minimal infrastructure. Agent regularly operates without project context. Frequent re-explanation. |
| 50-59 | Almost no persistent context. Every session starts from scratch. |
| Below 50 | No CLAUDE.md, no memory, no session setup. Agent operates blind in every session. |
