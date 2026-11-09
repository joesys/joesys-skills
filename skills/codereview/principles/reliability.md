# Reliability Principles

Reliability asks: when something goes wrong, does the system notice, report it clearly, and fail in a safe way? Use this file as a lens, not a checklist. Report only problems that would make a real failure worse in this change: hidden, far from its cause, unrecoverable, or impossible to diagnose.

## Quick Diagnostic Guide

| Symptom | Likely Principle |
|---|---|
| Error surfaces far from where it originated | Fail-Fast & Defensive Programming |
| Caller passes garbage and function silently proceeds | Design by Contract |
| API rejects valid input over minor formatting | Postel's Law |
| One failing dependency brings down the entire system | Resilience & Graceful Degradation |
| Service account has write access but only reads data | Principle of Least Privilege |
| "Not my code, not my problem" attitude toward messy code | Boy Scout Rule |
| Production failure with no logs, metrics, or traces | Observability & Transparency |

## Principle Tensions

| Tension | Guidance |
|---|---|
| **Fail-Fast vs. Resilience** | Fail-fast on programming errors (wrong types, broken invariants). Be resilient against operational errors (network timeouts, temporary unavailability). The distinction is: can the caller fix it by retrying? |
| **Defensive Programming vs. Design by Contract** | DbC trusts the caller to meet preconditions and crashes hard if they don't. Defensive programming trusts nobody. Use DbC at internal module boundaries; use defensive programming at system edges (APIs, user input, deserialization). |
| **Postel's Law vs. Fail-Fast** | Being liberal in what you accept can mask bugs upstream. Accept reasonable variations (trailing whitespace, mixed case), but reject structurally invalid data. Do not silently coerce `"yes"` into `True` unless that is an explicit, documented feature. |
| **Least Privilege vs. Developer Velocity** | Strict permissions slow down local development. Use broad permissions in dev/test, strict in staging/production. Never relax production permissions to speed up development. |
| **Boy Scout Rule vs. Scope Creep** | Cleaning up code while working on a feature is good. Refactoring an entire module when you were asked to fix a typo is scope creep. Clean the campground, not the forest. |
| **Observability vs. Security** | Logs and traces are essential but can leak secrets. Never log credentials, tokens, PII, or full request bodies. Structured logging with explicit field selection prevents accidental exposure. |

## Matching the Response to the Error

| Error Type | Example | Strategy |
|---|---|---|
| **Precondition violation** | Null argument, negative age | Raise immediately — caller's bug |
| **Transient failure** | Network timeout, lock contention | Retry with backoff — may self-heal |
| **Deterministic failure** | File not found, invalid SQL | Fail with clear message — retrying won't help |
| **Invariant violation** | Negative account balance after debit | Assert — indicates logic bug |

## Principle Notes

| Principle | Flag When |
|---|---|
| Fail-Fast & Defensive Programming | Invalid input or config is accepted and fails later, far from its cause. Required config is read lazily deep inside a request instead of checked at startup. |
| Design by Contract | A function's preconditions are unclear and callers violate them silently. Check at system edges; trust internal callers that meet a stated contract. |
| Postel's Law | Input handling is so strict it rejects harmless variation (whitespace, case, an extra field), or so loose it guesses at malformed data. Output should always be strict and consistent. |
| Resilience & Graceful Degradation | A call to an external service has no timeout, retries without backoff and jitter, or retries forever. One optional dependency failing takes down the whole response. Useful patterns: backoff with jitter, a circuit breaker after repeated failures, and fallback from cache to stale cache to a default. Tell the caller when a response is partial. |
| Principle of Least Privilege | A process, database user, token, or cloud role has more permission than the change needs, such as write access on a read path or a wildcard resource. |
| Boy Scout Rule | Only as a P4 note for code this change already touches. Never ask for cleanup of untouched code. |
| Observability & Transparency | A failure would leave no trace, or a trace with no context. Anti-patterns: silent failure (an empty catch), opaque errors ("Error" with no cause or IDs), secrets in logs, print-debugging left in, and logging so much that real signals drown. Good logs are structured and carry IDs (request, order, user) and the original cause. |

## When to Relax Rules

| Principle | Relax When | Example |
|---|---|---|
| **Fail-Fast** | Batch processing where partial results are valuable | Log the error, skip the bad record, continue processing |
| **Design by Contract** | Performance-critical inner loops where assertions add overhead | Disable assertions in release builds after thorough testing |
| **Postel's Law** | Security-sensitive input (auth tokens, SQL, HTML) | Reject anything that doesn't match the exact expected format |
| **Resilience** | Data integrity operations where partial results are dangerous | Financial transactions must be all-or-nothing, not degraded |
| **Least Privilege** | Local development and prototyping | Use broader permissions locally, but never deploy them to production |
| **Boy Scout Rule** | Under tight deadline with no test coverage | Don't refactor code you can't verify — note it as tech debt instead |
| **Observability** | Extremely hot paths where logging adds latency | Sample logs (1 in 1000) instead of logging every event |

## Severity Guidance

- **P0:** a failure is hidden while the system reports success, or a partial failure corrupts data (no rollback, money moved once but recorded twice).
- **P1:** an external call with no timeout on a request path; retries that can storm a failing service; a failure that would leave no usable log; excess privilege that widens the damage of a bug.
- **P2:** late validation, unclear errors, or missing context in logs.
- **P3–P4:** polish, and Boy Scout notes.

## When Not to Flag

- Defensive checks inside trusted internal code whose callers already meet the contract.
- Retry or circuit-breaker machinery for a call that is local, cheap, or one-time. Do not add resilience layers the change does not need.
- Code outside the change.
