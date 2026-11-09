# Workflow Efficiency Principles

Evaluate how directly the human-AI collaboration reaches its goal: turn economy, goal directness, and planning.

Two behaviors are owned by other lenses. Do not score them again here:
- How fast a wrong turn is caught and corrected, and how many rounds a correction takes, is owned by the Error Recovery lens. Correction turns still count toward the turn total below, as cost only.
- Batching and parallel work (grouping related or independent requests) is owned by the Agentic Leverage lens.

## Quick Diagnostic Guide

| Symptom | Likely Category |
|---|---|
| Session takes many turns for a task the agent could finish in one or two | Turn Bloat |
| Agent builds something, user rejects it entirely, agent starts over | Wasted Cycles |
| User and agent circle around the requirement without converging | Goal Drift |
| Successful outcome but took 3x the necessary turns | Inefficient Path |
| Large change started without a plan, then rebuilt after the approach was rejected | Missing Plan |

## Evaluation Criteria

### 1. Turn Economy
How many turns did the task take, compared with what it should have needed, given its difficulty and the information the user had?

A turn is one user message plus the agent's full response, including all of its tool calls and edits. Current agents do a lot in one turn. One well-specified turn can finish a whole bug fix, a small feature, or a multi-file change, including running the tests. So do not use fixed turn counts.

- A clear, well-scoped task should usually finish in one or two turns. Extra turns need a reason.
- Good reasons: real ambiguity only the user can resolve, a deliberate review checkpoint, new information found during the work, or a task too large to do safely at once.
- Long sessions are fine when they cover several separate tasks. Judge each task, not the session length.

Count a turn as wasted when it did not move the task forward: a question a better first prompt would have answered, output rejected at once, information repeated from earlier, or a wrong path explored before a redirect.

### 2. Goal Directness
Does each turn make visible progress toward a goal both sides agree on?
- Strong: tangents are short and gather needed context; user and agent agree on what "done" means.
- Weak: the goal changes mid-session without anyone saying so, or there are several false starts before the real work begins.

### 3. Planning
Does the amount of planning fit the task?
- Strong: asks for a plan or task list before complex or risky work (for example, a plan mode or task-tracking tool, where the host offers one), and goes straight to the work when the task is simple.
- Weak: a large change starts without a plan and is rebuilt after the approach is rejected, or a simple change gets a long discussion about approach.

## Scoring Rubric

| Score Range | Description |
|---|---|
| 90-100 | Consistently tight sessions. Turn counts match task complexity. Corrections resolved in 1-2 turns. |
| 80-89 | Most sessions efficient. Occasional unnecessary turns but overall good economy. |
| 70-79 | Sessions tend to run 30-50% longer than necessary. Moderate correction loops. |
| 60-69 | Regular turn bloat. Multiple correction loops per session. Frequent rework. |
| 50-59 | Sessions are consistently 2x+ what they should be. Significant wasted effort. |
| Below 50 | Most sessions are dominated by corrections, restarts, and circular discussion. |

The rubric mentions correction loops because they add turns. Read those words as turn cost here. The quality of each correction is scored in Error Recovery.
