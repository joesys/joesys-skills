# Reliability

## Definition

Reliability measures the system's ability to handle failures gracefully, recover from errors without data loss, and continue operating under adverse conditions.

## Signals to Look For

- Swallowed exceptions that hide failures.
- Network and external calls without a timeout; no retry for transient failures.
- No logging at error boundaries.
- Resource cleanup not guaranteed (context managers, `finally`, `defer`).
- Multi-step mutations without a transaction or rollback.

## Measurement Guidance

| Metric | How to Measure | Source |
|---|---|---|
| Error handling coverage | Ratio of functions with explicit error handling | Agent qualitative |
| Retry/fallback patterns | Grep for retry, backoff, circuit_breaker patterns | Architecture agent |
| Logging presence | Grep for logging/logger usage at error boundaries | Architecture agent |
| Health check endpoints | Check for /health, /ready, /alive routes | Architecture agent |
| Resource management | Check for context managers, defer, finally | Structural agent |
| Timeout presence | Grep for timeout parameters on network calls | Architecture agent |

## Grading Rubric

| Grade | Criteria |
|---|---|
| A+ | Comprehensive error handling, retry + fallback patterns, health checks, structured logging, graceful shutdown |
| A | Good error handling, some retry/fallback, logging present at boundaries |
| B | Basic error handling, logging present but inconsistent |
| C | Inconsistent error handling, minimal logging, no retry patterns |
| D | Missing error handling in critical paths, exceptions swallowed |
| F | No error handling strategy, no logging, failures propagate silently |

## Language-Aware Notes

- **Rust:** `Result<T, E>` forces explicit error handling at every call site. Rust codebases inherently score well on error handling coverage. Focus on whether error context is preserved (`?` operator with `.context()`).
- **Go:** Error returns are explicit but can be silently ignored. Check for `_ = ` error discarding. Go's `defer` handles resource cleanup well.
- **Python:** Context managers (`with`) are the idiomatic cleanup pattern. Check for `try/finally` or `with` around resource-sensitive operations.
- **C#:** `using` statements for IDisposable are critical. Check for async disposal patterns in .NET 6+.
- **TypeScript/JavaScript:** Promise rejection handling — check for unhandled promise rejections and missing `.catch()` chains.
