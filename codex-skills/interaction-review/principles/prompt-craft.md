# Prompt Craft Principles

Evaluate how effectively the user communicates intent, constraints, and context to the AI agent. This is the highest-leverage lens — better prompts improve every other dimension.

## Quick Diagnostic Guide

| Symptom | Likely Category |
|---|---|
| Agent asks "what do you mean?" or offers multiple interpretations | Ambiguous Intent |
| User corrects agent direction 2+ turns after initial request | Missing Constraints |
| Agent produces output in wrong format, language, or scope | Unspecified Output Expectations |
| User describes the same project setup across multiple sessions | Missing Persistent Context |
| Agent explores irrelevant files or builds unnecessary features | Scope Underspecification |
| Multi-turn back-and-forth to converge on simple requirements | Incremental Drip-Feeding |

## Evaluation Criteria

### 1. Clarity of Intent
Does the user state what they want unambiguously? A clear prompt leaves no room for the agent to guess wrong.

**Signs of strong clarity:**
- States the goal in the first sentence
- Distinguishes between what to build vs. how to build it
- Uses precise language ("add a retry with exponential backoff" vs. "make it more robust")

**Signs of weak clarity:**
- Vague directives ("fix this", "make it better", "clean this up")
- Ambiguous references ("the thing we discussed", "that file")
- Goal buried mid-paragraph after unrelated context

### 2. Constraint Specification
Does the user communicate boundaries, requirements, and non-goals upfront?

**Signs of strong constraints:**
- States what NOT to do ("don't change the API interface")
- Specifies scope limits ("only files in src/auth/")
- Names technology constraints ("use the existing ORM, don't add a new dependency")

**Signs of weak constraints:**
- Agent's first attempt is rejected for violating unstated constraints
- User says "no, not that way" without having specified the preferred way
- Requirements emerge piecemeal across 5+ turns

### 3. Context Provision
Does the user provide enough background for the agent to reason well?

**Signs of strong context:**
- References relevant files, functions, or prior work
- Explains the "why" behind the request
- Points to examples or patterns to follow

**Signs of weak context:**
- Agent operates with no project-specific knowledge
- User expects agent to "just know" codebase conventions
- No CLAUDE.md or memory utilization for recurring context

### 4. Output Expectations
Does the user specify what the deliverable should look like?

**Signs of strong expectations:**
- Names the desired format ("give me a markdown table", "write a test file")
- Specifies completeness ("full implementation, not pseudocode")
- Sets quality bar ("production-ready" vs. "quick prototype")

**Signs of weak expectations:**
- Agent produces a different artifact type than the user wanted
- User asks for "code" and then rejects the format, length, or style
- No indication of whether this is a draft or final deliverable

### 5. Prompt Structure
Is the prompt well-organized for agent consumption?

**Signs of strong structure:**
- Separates goal, context, and constraints
- Uses formatting (bullets, headers) for multi-part requests
- Puts the most important information first

**Signs of weak structure:**
- Wall-of-text prompts with buried requirements
- Stream-of-consciousness ordering
- Critical details in parenthetical asides

### 6. Iterative Refinement
When the first attempt isn't right, does the user refine effectively?

**Signs of strong refinement:**
- Specifies what was wrong and what "right" looks like
- Narrows scope rather than restating the entire request
- Provides examples of desired output

**Signs of weak refinement:**
- Repeats the same prompt with minor variations
- Expresses frustration without actionable guidance ("no, that's still wrong")
- Abandons and restarts instead of course-correcting

## Scoring Rubric

| Score Range | Description |
|---|---|
| 90-100 | Prompts are consistently clear, well-constrained, and contextually rich. Agent rarely needs clarification. |
| 80-89 | Most prompts are good. Occasional missing constraints but user self-corrects quickly. |
| 70-79 | Prompts are understandable but frequently lack constraints or context. Several clarification loops per session. |
| 60-69 | Prompts often vague or ambiguous. Agent frequently guesses wrong. Significant turn waste. |
| 50-59 | Prompts regularly require 3+ correction cycles. User relies on agent to interpret intent. |
| Below 50 | Prompts are consistently underspecified. Most sessions dominated by clarification and correction. |
