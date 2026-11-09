# Prompt Craft Principles

Evaluate how well the user communicates intent, constraints, and context to the agent. This is the highest-leverage lens: better prompts improve every other lens.

## Quick Diagnostic Guide

| Symptom | Likely Category |
|---|---|
| Agent asks "what do you mean?" or offers multiple interpretations | Ambiguous Intent |
| User corrects agent direction 2+ turns after initial request | Missing Constraints |
| Agent produces output in wrong format, language, or scope | Unspecified Output Expectations |
| Agent explores irrelevant files or builds unnecessary features | Scope Underspecification |
| Multi-turn back-and-forth to converge on simple requirements | Incremental Drip-Feeding |

## Evaluation Criteria

### 1. Clarity of Intent
Does the user state what they want so the agent cannot guess wrong?
- Strong: the goal comes first and uses precise words ("add a retry with exponential backoff", not "make it more robust").
- Weak: vague directives ("fix this", "clean this up") or ambiguous references ("that file", "the thing we discussed").

### 2. Constraint Specification
Does the user state boundaries, requirements, and non-goals up front?
- Strong: says what not to do and where the scope ends ("only files in `src/auth/`", "don't add a dependency").
- Weak: the first attempt is rejected for breaking a rule the user never stated, or requirements arrive one at a time over many turns.

### 3. Context Provision
Does the user give enough background for the agent to reason well?
- Strong: points to the relevant files, prior work, or an example to follow, and explains why.
- Weak: expects the agent to know conventions that were never stated or pointed to in the prompt. (Persistent instruction files and memory are scored in the Context & Instruction lens.)

### 4. Output Expectations
Does the user say what the deliverable should look like?
- Strong: names the format, completeness, and quality bar ("a test file", "full implementation", "quick prototype").
- Weak: the agent produces a different kind of artifact than the user wanted, and the user rejects its format or length.

### 5. Prompt Structure
Is the prompt organized so the agent can use it?
- Strong: separates goal, context, and constraints, and puts the most important point first.
- Weak: a wall of text where key requirements are buried mid-paragraph or in asides.

### 6. Iterative Refinement
When the first attempt is not right, is the follow-up prompt useful?
- Strong: says what was wrong and what "right" looks like, and narrows the scope instead of restating everything.
- Weak: repeats the same prompt with small changes, or expresses frustration without new information ("no, that's still wrong").

## Scoring Rubric

| Score Range | Description |
|---|---|
| 90-100 | Prompts are consistently clear, well-constrained, and contextually rich. Agent rarely needs clarification. |
| 80-89 | Most prompts are good. Occasional missing constraints but user self-corrects quickly. |
| 70-79 | Prompts are understandable but frequently lack constraints or context. Several clarification loops per session. |
| 60-69 | Prompts often vague or ambiguous. Agent frequently guesses wrong. Significant turn waste. |
| 50-59 | Prompts regularly require 3+ correction cycles. User relies on agent to interpret intent. |
| Below 50 | Prompts are consistently underspecified. Most sessions dominated by clarification and correction. |
