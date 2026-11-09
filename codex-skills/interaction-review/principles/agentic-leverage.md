# Agentic Leverage Principles

Evaluate whether the user takes full advantage of the agent's autonomous capabilities — skills, tools, parallelism, batching, and delegation — or manually steers work the agent could handle.

This lens applies to Claude Code and Codex. Judge each tool or feature by its purpose, not by its name in one host. Persistent context (instruction files, memory) is scored only in the Context & Instruction lens. Planning before work is scored only in the Workflow Efficiency lens. This lens owns batching and parallelism; Workflow Efficiency does not score them again.

## Quick Diagnostic Guide

| Symptom | Likely Category |
|---|---|
| User manually reads files one by one, asking agent to explain each | Missed Tool Delegation |
| User types out step-by-step instructions for a task a skill handles | Skill Unawareness |
| User sequentially issues 5 independent requests | Missed Parallelism |
| User micro-manages file edits line by line | Over-Steering |
| Agent sits idle while user researches something the agent could search | Underutilized Autonomy |
| User copies output from one tool to manually feed into another | Missed Chaining |

## Evaluation Criteria

Compare what the user did by hand with the skills and tools that were available in the session. A missed opportunity counts only when a real skill or tool would have done the job better.

### 1. Skill Utilization
Does the user invoke an available skill when it would beat manual orchestration? Claude Code invokes a skill as `/name`; Codex invokes it as `$name`.
- Strong: uses a skill for work it is built for (a review, a commit, a codebase explanation) instead of an ad-hoc request.
- Weak: manually rebuilds what a skill does, step by step, or uses a skill with the wrong mode or missing options.

### 2. Tool Awareness
Does the user let the agent use its own tools?
- Strong: asks the agent to search, read, run tests, and handle git, instead of doing these by hand.
- Weak: pastes code or file paths the agent could find itself, or does web searches and test runs by hand and reports the result.

### 3. Autonomy vs. Micro-Management
Does the user give the agent room to work?
- Strong: states the goal, lets the agent choose the approach, and reviews the result.
- Weak: dictates exact names and lines for trivial changes, provides pseudo-code to "just translate", or approves every small step.

### 4. Parallelism and Batching
Does the user group work so it can run together?
- Strong: puts related or independent tasks in one request, and uses multi-agent skills when they fit.
- Weak: sends independent requests one at a time, re-explaining the same context each time, or waits for one task before starting an unrelated one.

## Scoring Rubric

| Score Range | Description |
|---|---|
| 90-100 | Power user. Leverages skills, tools, parallelism, and autonomy effectively. Agent operates near full capability. |
| 80-89 | Good leverage. Uses most features well. Occasional manual work where a tool or skill would be better. |
| 70-79 | Moderate leverage. Knows core features but misses opportunities for skills, parallelism, or delegation. |
| 60-69 | Under-leveraged. Frequently does manually what the agent could handle. Uses few skills or tools. |
| 50-59 | Significant under-use. Treats the agent as a chat assistant rather than an autonomous agent. |
| Below 50 | Barely uses agent capabilities. Manual steering dominates. Agent's tool and skill ecosystem is largely untapped. |
