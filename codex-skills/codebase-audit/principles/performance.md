# Performance

## Definition

Performance measures the efficiency of the code in terms of time complexity, space complexity, and resource utilization. This criterion assesses static code patterns — actual runtime profiling is out of scope for v1. Focus is on anti-patterns that are reliably detectable through code analysis.

## Concrete Signals

**Positive signals:**
- Appropriate data structures (sets for membership, dicts for lookup)
- Eager loading of related data in database queries (avoiding N+1)
- Async I/O in async contexts (no blocking calls)
- Caching of expensive computations with invalidation strategy
- Bounded resource consumption (connection pools, bounded queues)
- Lazy/streaming processing for large datasets

**Negative signals:**
- Nested loops doing lookup (O(n²) where O(n) is possible with set/dict)
- N+1 query patterns (one query per item in a loop)
- String concatenation with += in loops (quadratic allocation)
- Blocking I/O in async functions (time.sleep, synchronous HTTP in async)
- Missing caching for repeated expensive operations
- Unbounded in-memory collections growing without limit
- Eager loading of entire tables when only a subset is needed

## Measurement Guidance

| Metric | How to Measure | Source |
|---|---|---|
| Algorithm complexity issues | Identify nested loops over collections | Performance agent |
| N+1 query patterns | Grep for DB queries inside loops | Performance agent |
| Blocking I/O in async | Grep for sync calls inside async functions | Performance agent |
| String concatenation in loops | Grep for += on strings inside loops | Performance agent |
| Missing caching | Identify repeated expensive calls | Performance agent |
| Memory leak patterns | Grep for unbounded growth patterns | Performance agent |

## Grading Rubric

| Grade | Criteria |
|---|---|
| A+ | Zero performance anti-patterns, efficient algorithms throughout, appropriate caching |
| A | No significant anti-patterns, good algorithm choices |
| B | Minor issues (1-2 non-critical anti-patterns), generally efficient |
| C | Several anti-patterns present but not on hot paths |
| D | Performance anti-patterns on hot paths (N+1, O(n²) lookups) |
| F | Critical anti-patterns throughout (blocking async, pervasive N+1, quadratic algorithms) |

## Language-Aware Notes

- **Rust:** Zero-cost abstractions mean iterator chains compile to efficient loops. Focus on algorithmic complexity rather than allocation patterns. `Arc<Mutex<>>` contention is the main concern.
- **Python:** The GIL limits CPU concurrency — async is only beneficial for I/O. List comprehensions are generally faster than equivalent loops. NumPy vectorization matters for data-heavy code.
- **Go:** Goroutine leaks are a performance/reliability concern. Check for goroutines launched without cancellation context.
- **JavaScript/TypeScript:** Event loop blocking is critical in Node.js. Check for synchronous file operations (`readFileSync`) in request paths.
- **C++:** Memory management patterns (smart pointers vs raw) affect both performance and correctness. Cache locality matters for tight loops.
