# Clean Code Principles

Clean code asks: can the next reader understand and change this code quickly and safely? Use this file as a lens, not a checklist. Report only problems that make this change harder to read, test, or change. A finding must say what the reader loses, not only which principle is broken.

The most common mistake in this domain is noise: renames of taste, trivial wrappers, and extra structure. Prefer the plainer code. Do not suggest abstractions, interfaces, or patterns for code with one use.

## Quick Diagnostic Guide

| Symptom | Likely Principle |
|---|---|
| Function does too many things or has many parameters | Small Functions |
| Deep nesting (3+ levels of indentation) | Guard Clauses |
| Hard to understand what a block of code does at a glance | Cognitive Load |
| Mixing orchestration logic with low-level details | SLAP |
| Cryptic variable/function names or magic numbers | Self-Documenting Code |
| Comments just restate the code | Documentation Discipline |
| Abstractions, interfaces, or features that nothing uses yet | YAGNI |
| Over-engineered solution for a simple problem | KISS |
| Function has surprising side effects or inconsistent returns | Principle of Least Surprise |
| Code works but feels clunky, verbose, or brute-forced | Elegance |

## Principle Tensions

| Tension | Guidance |
|---|---|
| **KISS vs. Small Functions** | Extracting functions adds indirection. Extract a function when either condition holds: it is reused, or it makes the code read better (a clear name that tells the story, for example when the original function mixes abstraction levels). Either one is enough. Do not create trivial one-liner wrappers. |
| **YAGNI vs. Extensibility** | Build only what is needed today. If a second concrete case appears, refactor then. Premature abstraction is more costly than a later refactor. |
| **Self-Documenting Code vs. Documentation Discipline** | Good names reduce the need for comments, but they cannot explain *why* a business rule exists or *why* a non-obvious approach was chosen. Use comments for rationale, not narration. |
| **Small Functions vs. Cognitive Load** | Too many tiny functions force the reader to jump around. If the extraction does not reduce cognitive load, it increases it. Inline trivial helpers. |
| **Guard Clauses vs. SLAP** | Guard clauses are low-level checks. Placing them at the top of a high-level orchestrator can break SLAP. Consider validating in a dedicated validation function. |
| **Elegance vs. KISS** | Elegant code is minimal, but cleverness without clarity is not elegant. If a teammate cannot understand the code in 30 seconds, choose the plainer version. |

## Principle Notes

| Principle | Flag When |
|---|---|
| KISS | A simple job is done with layers, registries, factories, or generic machinery. Suggest the direct version. |
| YAGNI | Code adds options, hooks, interfaces, or extension points that no current caller uses. An interface with one implementation is the usual sign. |
| Small Functions | A function does several jobs, or is too long to hold in your head (roughly 20 lines of logic). Split out a function when either condition holds: it is reused, or it makes the code read better. A wrapper that only renames a built-in adds indirection, not clarity. |
| Guard Clauses | Invalid states are handled inside nested `if` blocks, so the main path is buried (the arrow anti-pattern). Suggest early returns so the happy path sits at the shallowest indentation. |
| Cognitive Load | A compound condition or dense expression forces the reader to simulate it. Suggest named intermediate values, such as named booleans. |
| SLAP | One function mixes high-level steps (`validate`, `save`, `notify`) with low-level details (string splitting, index math). Suggest moving the details into named helpers. |
| Self-Documenting Code | Names like `d`, `tmp`, or `proc` hide intent, or a magic number carries a business meaning. Suggest a name or named constant. |
| Documentation Discipline | Comments restate the code ("get the user"), are stale, or are missing where a business rule or workaround needs a *why*. |
| Elegance | The solution hides the shape of the problem behind manual bookkeeping. Use these questions: **Minimality** (can anything be removed?), **Accomplishment** (does it fully solve the problem?), **Modesty** (would a junior developer follow it?), **Revelation** (does it show the problem's structure?). |
| Principle of Least Surprise | A function does more or less than its name says: a `get_` that writes, a return type that varies by branch, a silent failure. |

## Duplication

Do not flag duplication or suggest extraction *to remove duplication* until the pattern appears three or more times (Rule of Three). Two similar blocks are not enough. Two blocks that look alike but serve different purposes are not duplication at all. This limit does not block extraction for readability: a single block may be split out when a clear name makes the code read better. Two copies of one fact or rule that must stay in sync are an architecture finding (Single Source of Truth).

## Severity Guidance

- **P2:** the code misleads the reader (a name or function that does something other than it says), or structure makes this change hard to modify safely (deep nesting around important logic, a god function).
- **P3:** naming, magic numbers, mixed abstraction levels, and over-built code with a small cost.
- **P4:** comment cleanup and minor polish.
- Clean code findings are not P0 or P1 unless they hide a real bug. Report the bug itself under correctness.

## When Not to Flag

- Test code with repeated setup that keeps each test readable (DAMP over DRY).
- Idioms that are normal in the file's language or the project's style.
- Taste-only renames where the current name is already clear.
- Code outside the change.
