# Shared Delegation Infrastructure

Reference file for codex, gemini, and claude skills. Read this file
after presenting the delegated model's response — it contains the
shared logic for critical evaluation and disagreement handling.

## Critical Evaluation

The delegated model is a peer, not an authority. After every response:

- **Trust your own knowledge** when confident. If the delegated model
  claims something you know is incorrect, push back.
- **Research disagreements** using WebSearch or project documentation
  before accepting claims.
- **Remember knowledge cutoffs** — the delegated model may not know
  about recent releases, APIs, or changes.
- **Don't defer blindly** — evaluate suggestions critically, especially
  regarding model names, library versions, API changes, and best practices.

## When You Disagree

1. State the disagreement clearly to the user with evidence.
2. Provide supporting evidence (your own knowledge, web search results, docs).
3. Optionally resume the session to discuss as a peer AI. Use the
   appropriate resume command for the delegated model. Frame as:
   "This is Claude (<your current model name>) following up. I disagree
   with [X] because [evidence]. What's your take?"
   **Note:** A debate resume becomes "the last session." Inform the user
   that the resume command will now continue the debate thread, not the
   original prompt.
4. Frame disagreements as discussions — either AI could be wrong.
5. Let the user decide how to proceed if there is genuine ambiguity.

## Error Handling

| Condition | Action |
|---|---|
| Non-zero exit code | Report failure, suggest checking CLI version or auth setup |
| Empty output | Report that the model returned nothing, suggest rephrasing the prompt |
| Partial/warning output | Summarize warnings and ask user how to proceed |
| Timeout | Report timeout, suggest a simpler prompt or lower reasoning/effort |
