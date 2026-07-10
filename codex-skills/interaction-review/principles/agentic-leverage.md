# Agentic Leverage Principles

Evaluate whether the user is taking full advantage of the agent's autonomous capabilities — skills, tools, parallelism, planning, and delegation — or manually steering work the agent could handle independently.

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

### 1. Skill Utilization
Does the user invoke available skills when they would be more effective than manual orchestration?

**Signs of strong utilization:**
- Uses `$codereview` instead of asking "look at this code for issues"
- Uses `$commit` for structured commits instead of manual `git commit`
- Uses `$explain` for codebase understanding instead of sequential file reads
- Uses `$retrospective` for process reflection instead of ad-hoc discussion

**Signs of weak utilization:**
- Manually replicates what a skill does (e.g., reading files one by one when `$explain` would synthesize)
- Unaware that a skill exists for their current task
- Uses skills but with suboptimal invocations (missing flags, wrong mode)

### 2. Tool Awareness
Does the user leverage the agent's built-in tools effectively?

**Signs of strong awareness:**
- Asks agent to search the codebase instead of specifying exact files
- Lets the agent use Glob/Grep to find relevant code
- Trusts the agent to navigate the filesystem
- Uses agent for git operations, PR creation, etc.

**Signs of weak awareness:**
- Manually provides file paths the agent could discover
- Copies code into the prompt instead of referencing the file
- Performs web searches manually instead of asking the agent
- Doesn't know the agent can read images, run tests, or create branches

### 3. Autonomy vs. Micro-Management
Does the user give the agent room to work, or dictate every step?

**Signs of healthy autonomy:**
- States the goal and lets the agent determine the approach
- Reviews output rather than pre-specifying every detail
- Trusts agent judgment for implementation decisions
- Intervenes only when the agent is clearly going wrong

**Signs of over-steering:**
- Dictates exact file names, function names, and line numbers for trivial changes
- Reviews and approves every intermediate step instead of the final result
- Provides pseudo-code and asks the agent to "just translate this"
- Interrupts agent mid-task to redirect before seeing the result

### 4. Parallelism and Batching
Does the user structure work to take advantage of parallel execution?

**Signs of strong parallelism:**
- Groups independent tasks in a single request
- Uses multi-agent skills when appropriate
- Understands that some tasks can run concurrently

**Signs of missed parallelism:**
- Sequential individual requests for independent tasks
- Waiting for one task to complete before starting an unrelated one
- Not using plan mode or task tracking for complex work

### 5. Context Management
Does the user help the agent maintain effective context?

**Signs of strong management:**
- Uses CLAUDE.md for persistent project context
- References memory for recurring patterns
- Provides links to relevant docs, issues, or PRs
- Uses plan mode for complex multi-step tasks

**Signs of weak management:**
- Re-explains the same project setup every session
- Expects the agent to remember previous sessions without memory
- Provides no CLAUDE.md or project instructions
- Doesn't use worktrees or branches for isolation

## Scoring Rubric

| Score Range | Description |
|---|---|
| 90-100 | Power user. Leverages skills, tools, parallelism, and autonomy effectively. Agent operates near full capability. |
| 80-89 | Good leverage. Uses most features well. Occasional manual work where a tool or skill would be better. |
| 70-79 | Moderate leverage. Knows core features but misses opportunities for skills, parallelism, or delegation. |
| 60-69 | Under-leveraged. Frequently does manually what the agent could handle. Uses few skills or tools. |
| 50-59 | Significant under-use. Treats the agent as a chat assistant rather than an autonomous agent. |
| Below 50 | Barely uses agent capabilities. Manual steering dominates. Agent's tool and skill ecosystem is largely untapped. |
