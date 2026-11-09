# Performance Principles

Performance asks: will this code be too slow or use too much memory for the data it will really see? Use this file as a lens, not a checklist. Report only problems on paths whose input can grow or that run often. Each finding should say why the path is hot or the data is large. Without that evidence, skip micro-optimizations.

Choosing the right algorithm, avoiding N+1 queries, and not blocking an event loop are not premature optimization. They are basic design. Shaving small constant costs without a measurement is.

## Quick Diagnostic Guide

| Symptom | Likely Principle |
|---|---|
| Nested loops searching or matching across two collections | Algorithm Complexity |
| One database query per item in a loop | N+1 Queries |
| Repeated string concatenation or copying inside a loop | Unnecessary Allocations/Copies |
| A blocking call (sync HTTP, sleep, file or CPU-heavy work) inside an async function | Blocking I/O in Async Contexts |
| Same expensive computation repeated on every request | Missing Caching |
| File handles opened but never closed, unbounded list growth | Memory Leaks / Resource Management |
| Loading an entire table when only 10 rows are displayed | Lazy vs. Eager Loading |
| Optimizing code that runs once at startup | Premature vs. Legitimate Optimization |

## Principle Tensions

| Tension | Guidance |
|---|---|
| **Caching vs. Correctness** | Caching stale data is worse than recomputing. Always define an invalidation strategy before adding a cache. If you cannot articulate when the cache becomes stale, do not cache. |
| **Lazy Loading vs. N+1 Queries** | Lazy loading avoids fetching unused data but can trigger N+1 queries when you iterate. Use eager loading when you know you will access all related objects; use lazy loading when most calls never touch the relation. |
| **Readability vs. Performance** | A readable O(n^2) solution is fine for small n. Only replace it with a harder-to-read O(n) solution when profiling shows the readable version is a bottleneck. Comment the optimization so future readers know why. |
| **Pre-allocation vs. YAGNI** | Pre-allocating buffers or pools adds complexity. Do it only when allocation cost is measured and significant — not because it "might be faster." |
| **Async vs. Simplicity** | Async code is harder to read, debug, and test. Use it when I/O concurrency is a proven requirement, not as a default architectural choice. |
| **Eager Optimization vs. Profiling First** | Never optimize without evidence. A profiler tells you where time is actually spent. Intuition about bottlenecks is wrong more often than right. |

## Principles and When to Care

| Principle | What Goes Wrong | When to Care |
|---|---|---|
| Algorithm Complexity | Nested search over two collections, or membership tests on a list, turn O(n) work into O(n^2). A set or map lookup usually removes the inner loop. | Collections of thousands of items, per-request paths, or code inside a loop that runs many times. For 10 items, the nested loop is fine. |
| N+1 Queries | One query for a list, then one more query per item. Round-trip latency grows with the data. Pagination only caps N; it does not fix the pattern. Fix with a join, an `IN (...)` batch, or the ORM's eager-loading option. | Any real data path (request handler, job, loop over data that can grow). This is usually P1. A one-time script over a small fixed list is not a finding. |
| Unnecessary Allocations/Copies | Building a string by repeated concatenation copies everything each time (O(n^2)). Copying large collections or creating temporary objects in a tight loop. | Loops with hundreds or more iterations, large files, or allocation that shows up in a profile. Concatenating 5 strings is fine. |
| Blocking I/O in Async Contexts | A blocking call inside async code freezes the event loop and stalls every other task. Use the async version of the call, or move the work to a thread or process pool. | Any async code (asyncio, Node.js, async Rust, async C#). Synchronous frameworks expect blocking I/O; this does not apply there. |
| Missing Caching | The same expensive, deterministic result is computed again and again. Do not cache data that changes often, auth or permission data that must respect revocation, very large results, or non-deterministic values such as the current time. | Repeated calls with the same arguments within a request or process, for work that costs more than a few milliseconds. Always name the invalidation rule. |
| Memory Leaks / Resource Management | Collections that grow without a bound, listeners never removed, closures that keep large objects alive, handles never closed. | Long-running processes (servers, workers, daemons), large batch jobs, and any state that grows over time. |
| Lazy vs. Eager Loading | Loading a whole table or file when only a page or a count is needed. Computing aggregates in application code instead of the database. | Any query that can return an unbounded number of rows, paginated endpoints, reports over large data. |
| Premature vs. Legitimate Optimization | Readable code replaced by clever code for a gain nobody measured. | Use the decision table below. |

## Should This Be Optimized?

| Question | If Yes | If No |
|---|---|---|
| Is it on a hot path (called per-request, per-event, per-item)? | Consider optimizing | Leave it alone |
| Does it operate on large data (1000+ items)? | Consider optimizing | Leave it alone |
| Has profiling confirmed it is a bottleneck? | Optimize now | Profile first |
| Will the optimization hurt readability? | Document why + add benchmarks | Prefer the clear version |
| Is it a startup/teardown/admin-only path? | Almost never worth optimizing | Leave it alone |

## Severity Guidance

- **P1:** N+1 queries or quadratic work on a real data path; blocking the event loop in request handling; an unbounded leak in a long-running process.
- **P2:** missing caching or eager loading with a clear, repeated cost; avoidable copies of large data.
- **P3–P4:** small constant-factor gains. Report them only if they are on a proven hot path.

## When Not to Flag

- Startup, teardown, admin-only, or one-time code.
- Small, fixed-size data.
- Micro-optimizations with no measurement and no clear hot path.
- Code outside the change.
