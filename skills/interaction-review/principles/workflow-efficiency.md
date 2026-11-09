# Workflow Efficiency Principles

Evaluate how efficiently the human-AI collaboration reaches its goal. Measures turn economy, correction overhead, and directness of the path from request to resolution.

How fast the session recovers after a mistake is scored only in the Error Recovery lens. Do not score it again here.

## Quick Diagnostic Guide

| Symptom | Likely Category |
|---|---|
| Session takes many turns for a task the agent could finish in one or two | Turn Bloat |
| Same correction given 3+ times in one session | Correction Loops |
| Agent builds something, user rejects it entirely, agent starts over | Wasted Cycles |
| User and agent circle around the requirement without converging | Goal Drift |
| Successful outcome but took 3x the necessary turns | Inefficient Path |
| User manually performs steps the agent could have batched | Missed Batching |

## Evaluation Criteria

### 1. Turn Economy
How many turns does it take relative to the task difficulty?

A turn is one user message plus the agent's full response, including all of its tool calls and edits. Current agents do a lot in one turn. One well-specified turn can finish a whole bug fix, a small feature, or a multi-file change, including running the tests. So do not use fixed turn counts. Instead, ask: how many turns did this task need, compared with what it should have needed, given its difficulty and the information the user had?

**How to judge:**
- A clear, well-scoped task should usually finish in one or two turns. Extra turns need a reason.
- Good reasons for extra turns: real ambiguity that only the user can resolve, a deliberate review checkpoint, new information found during the work, or a task too large to do safely at once.
- Weak reasons: the agent asking for facts the user could have given at the start, or the user releasing requirements one at a time.
- Long sessions are fine when they cover several separate tasks. Judge each task, not the session length.

**What to count as a "wasted" turn:**
- Clarification that could have been avoided with a better initial prompt
- Agent producing output the user immediately rejects
- Repeating information already stated earlier in the session
- Agent exploring wrong paths before being redirected

### 2. Correction Loop Depth
When the agent gets something wrong, how many turns does it take to converge?

**Healthy:** 1 correction -> agent adjusts -> user accepts (2-turn loop)
**Problematic:** 3+ rounds of correction on the same issue

**Look for:**
- User says "no" or "not that" followed by the same mistake repeated
- Progressive narrowing (each correction gets closer) vs. lateral drift (each correction introduces new problems)
- Whether the correction was avoidable (user could have been clearer) vs. genuine complexity

### 3. Goal Directness
Does the conversation move in a straight line toward the goal, or meander?

**Signs of directness:**
- Each turn makes visible progress toward the stated goal
- Tangents are brief and intentional (gathering necessary context)
- User and agent stay aligned on what "done" means

**Signs of meandering:**
- Mid-session goal changes without explicit acknowledgment
- Agent asks questions already answered earlier
- Multiple false starts before the actual work begins
- Long discussions about approach before any code is written (when the approach is straightforward)

### 4. Batching Efficiency
Does the user group related tasks effectively, or issue them one at a time when batching would be more efficient?

**Signs of good batching:**
- Multi-part requests that are logically related
- "While you're at it" additions that are genuinely in scope
- Using skills/tools that handle orchestration

**Signs of poor batching:**
- Sequential individual requests that could have been one prompt
- Re-explaining the same context for each sub-task

## Scoring Rubric

| Score Range | Description |
|---|---|
| 90-100 | Consistently tight sessions. Turn counts match task complexity. Corrections resolved in 1-2 turns. |
| 80-89 | Most sessions efficient. Occasional unnecessary turns but overall good economy. |
| 70-79 | Sessions tend to run 30-50% longer than necessary. Moderate correction loops. |
| 60-69 | Regular turn bloat. Multiple correction loops per session. Frequent rework. |
| 50-59 | Sessions are consistently 2x+ what they should be. Significant wasted effort. |
| Below 50 | Most sessions are dominated by corrections, restarts, and circular discussion. |
