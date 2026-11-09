# Correctness Principles

Correctness asks one question: does the code do what its author meant, for every input and event it can receive? Use this file as a lens, not a checklist. Report a problem when you can name the input or event that breaks the code and say what goes wrong.

## Bug Detection Heuristics

Scan the changed code for these smells. A smell is a place to check, not a finding on its own. The patterns apply in every language; the examples only show the shape.

| Heuristic | What to Look For |
|---|---|
| **Boundary smell** | `+1`, `-1`, lengths, ranges, slices, and pagination math. Check the first and last valid values by hand: inclusive or exclusive end, 0-based or 1-based, N items or N-1 separators. |
| **Null path** | Every field access, index, and map lookup. Can the value be null, None, or undefined? Can the key be missing? Does the caller ignore a "not found" result? |
| **Negation smell** | `not`, `!=`, and `and`/`or` chains. Negate the condition in your head and check the result. Watch De Morgan mistakes and precedence (`a or b and c` means `a or (b and c)`). A filter that keeps what it should drop is a common form. |
| **Empty collection smell** | First element, min or max, average, split-then-index. What happens with zero elements, an empty string, zero, a negative number, or multi-byte text? |
| **Shared reference smell** | A mutable default argument (one list or map shared by every call), mutation of the caller's data, global or static state, two names for one object. Who else holds a reference? |
| **Missing return** | A branch with no return, a function that returns its input instead of its result, or a shadowed variable. Some languages return null or None silently. |
| **Broad catch smell** | A catch-all handler (`except:`, `catch (Exception e)`, an empty `catch {}`, a bare `recover()`). Does it hide the failure? Does it return a value that looks like success, such as `true`, an empty list, or a default object? |
| **Ignored error** | An error result that is dropped: `_ = err`, an unchecked return code, a promise with no rejection handling, an error unwrapped to a default value. |
| **Missing await** | An async call whose result is not awaited. The work may never finish, may run out of order, or may lose its error. |
| **Check-then-act smell** | A check followed by an action that depends on it (file exists then open, read then write back, "not taken" then insert). Can the state change in between? |
| **Unsynchronized sharing** | Mutable state (maps, counters, caches, lazy singletons) used by more than one thread, goroutine, or task without a lock, atomic, or channel. Many standard maps are unsafe under concurrent writes. A read-modify-write like `count += 1` is not atomic. |
| **Resource not released** | Files, sockets, locks, transactions, database rows, and HTTP response bodies. Is each one closed or released on every path, including errors and early returns? |

## Categories

Use these names as the `[Principle Name]` in findings.

| # | Category | Key Question |
|---|---|---|
| 1 | Off-by-One Errors | Are loop bounds and slice indices right at both ends? |
| 2 | Null/Undefined Handling | Can any value be null at the point of use? |
| 3 | Boolean Logic Errors | Does the condition say what the author meant? (Test by negation.) |
| 4 | Edge Cases | What happens with zero, empty, negative, very large, or Unicode input? |
| 5 | Race Conditions & Concurrency | Can timing change the result? (Check-then-act, shared state, missing await.) |
| 6 | Incorrect Return Values | Does every path return the right value of the right type? |
| 7 | State Management | Is mutable state shared by accident, or used before it is set? Is a cache stale after an update? |
| 8 | Error Handling Gaps | Does every failure surface with its cause? Is a partial operation rolled back? |
| 9 | Resource Cleanup | Is every acquired resource released on every path? |

## Severity Guidance

- **P0:** wrong results, data loss or corruption, a crash on a normal path, or lost money. Examples: a catch-all that reports success after a failed write; a race that loses updates; an off-by-one that drops or duplicates records.
- **P1:** a real bug on a reachable but less common path: edge input, error path, retry, or load. A resource leak in a long-running process is usually P1.
- **P2 or lower** is rare in this domain. Use it for a latent bug that current callers cannot trigger, and say why they cannot.

## When Not to Flag

- Inputs that the types or every visible caller rule out. If you cannot see the callers, report the finding and name the input that triggers it.
- A correct style choice, such as "ask permission" versus "try and handle the error".
- Missing defensive checks inside trusted internal code. That is a reliability question, not a bug.
- Code outside the change, unless the change makes it wrong.
