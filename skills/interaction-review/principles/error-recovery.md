# Error Recovery & Adaptation Principles

Evaluate how the user and agent handle mistakes, misunderstandings, and pivots. Strong recovery means early detection, clear redirection, and no compounding drift.

This lens owns how fast a wrong turn is caught and corrected, including how many rounds a correction takes. Workflow Efficiency counts correction turns only as part of the turn total.

## Quick Diagnostic Guide

| Symptom | Likely Category |
|---|---|
| User notices wrong direction at turn 6, redirects at turn 14 | Late Course Correction |
| Agent repeats the same mistake after being corrected | Failed Correction Uptake |
| User gives up on approach without explaining why | Silent Abandonment |
| Small misunderstanding escalates into a full restart | Escalation Spiral |
| Agent confidently continues down wrong path unchecked | Unchallenged Drift |
| Error is identified but the redirect is vague | Imprecise Correction |

## Evaluation Criteria

### 1. Early Detection
How quickly does the user notice that the agent is going the wrong way?
- Strong: checks the agent's plan or first result before asking for more work built on it.
- Weak: a wrong assumption is caught only after one or more full turns of work on it. One turn can now produce hundreds of lines, so each missed turn is expensive.

### 2. Correction Clarity
Is the redirect clear enough to stop the mistake from coming back?
- Strong: says what was wrong and what "right" looks like, and addresses the cause, not only the symptom.
- Weak: "no, not that" or "try again" with no new information, which produces a different but still wrong result.

### 3. Pivot Decisiveness
When an approach is failing, does the user pivot cleanly?
- Strong: says "let's try a different approach" when the current one stalls, and explains why.
- Weak: keeps tweaking a clearly failing approach for many turns, or switches back and forth between two approaches.

### 4. Recovery Efficiency
After a correction, how many rounds until the session is back on track?
- Strong: one correction, the agent adjusts, progress resumes (a 2-turn loop).
- Weak: 3+ rounds on the same issue, or the fix itself introduces new problems.

### 5. Learning Within Session
Are later mistakes avoided because earlier ones were caught?
- Strong: a corrected issue does not come back, and the user turns a correction into a general rule for the rest of the session.
- Weak: the same type of mistake appears 3+ times despite corrections.

## Scoring Rubric

| Score Range | Description |
|---|---|
| 90-100 | Mistakes caught early, corrections are precise, recovery is fast. Both sides adapt within the session. |
| 80-89 | Good recovery patterns. Most mistakes caught in the next turn or two. Corrections are mostly clear. |
| 70-79 | Recovery works but is slow. Some late detections, some vague corrections. Moderate turn waste on errors. |
| 60-69 | Regular late detection. Corrections often require 2-3 rounds. Some compounding drift. |
| 50-59 | Frequent compounding errors. Corrections are vague or ineffective. Significant turn waste. |
| Below 50 | Errors dominate the session. Late detection, unclear corrections, repeated mistakes. |
