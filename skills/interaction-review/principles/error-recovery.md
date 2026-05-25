# Error Recovery & Adaptation Principles

Evaluate how both the user and agent handle mistakes, misunderstandings, and pivots. Strong error recovery is about early detection, clear redirection, and avoiding compounding drift.

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
How quickly does the user notice when the agent is going in the wrong direction?

**Signs of early detection:**
- User checks agent's understanding before it starts work ("before you start, confirm: you're going to...")
- Catches misalignment within 1-2 turns of it appearing
- Reads agent's plan/approach before approving execution

**Signs of late detection:**
- Agent produces 20+ lines of code before user realizes it's wrong
- User reviews only the final output, not intermediate steps
- Misunderstanding compounds across multiple turns before being caught

### 2. Correction Clarity
When the user redirects, is the correction clear enough to prevent repetition?

**Signs of clear correction:**
- States what was wrong AND what "right" looks like
- Provides concrete examples or references
- Addresses root cause, not just the symptom

**Signs of vague correction:**
- "No, not that" without specifying what to do instead
- Repeated "try again" without new information
- Correction is ambiguous enough to produce a different but still wrong result

### 3. Pivot Decisiveness
When an approach isn't working, does the user pivot cleanly or drag out a failing strategy?

**Signs of decisive pivoting:**
- Explicit "let's try a different approach" when current one stalls
- Explains why the pivot is happening
- Doesn't revisit abandoned approaches without reason

**Signs of indecisive pivoting:**
- Keeps tweaking a fundamentally wrong approach for 10+ turns
- Oscillates between two approaches without committing
- Partial pivots that leave the session in an inconsistent state

### 4. Recovery Efficiency
After a correction, how quickly does the session get back on track?

**Signs of efficient recovery:**
- Single correction -> agent adjusts -> progress resumes
- User provides enough context in the correction to avoid follow-up questions
- Agent acknowledges the correction and explains its adjusted approach

**Signs of inefficient recovery:**
- Multiple rounds of correction on the same issue
- Recovery itself introduces new problems
- Time spent on the correction exceeds the time the mistake cost

### 5. Learning Within Session
Does the interaction show adaptation — are later mistakes avoided because earlier ones were caught?

**Signs of in-session learning:**
- Similar issues don't recur after being corrected once
- User proactively sets constraints based on earlier corrections
- Agent applies corrections to analogous situations later in the session

**Signs of no learning:**
- Same type of mistake appears 3+ times despite corrections
- User doesn't generalize corrections into broader guidance
- Session-end mistakes are the same class as session-start mistakes

## Scoring Rubric

| Score Range | Description |
|---|---|
| 90-100 | Mistakes caught early, corrections are precise, recovery is fast. Both sides adapt within the session. |
| 80-89 | Good recovery patterns. Most mistakes caught within 2-3 turns. Corrections are mostly clear. |
| 70-79 | Recovery works but is slow. Some late detections, some vague corrections. Moderate turn waste on errors. |
| 60-69 | Regular late detection. Corrections often require 2-3 rounds. Some compounding drift. |
| 50-59 | Frequent compounding errors. Corrections are vague or ineffective. Significant turn waste. |
| Below 50 | Errors dominate the session. Late detection, unclear corrections, repeated mistakes. |
