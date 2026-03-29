# C++ Benchmarks

C++ specific quality thresholds. The language's complexity makes stricter standards important.

## Complexity

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Cyclomatic complexity (avg) | ≤10 | Good | MISRA C++ guidelines [^1] |
| Cyclomatic complexity (max) | ≤20 | Acceptable | CppDepend defaults [^2] |

## Size & Style

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Function length (median) | ≤40 lines | Good | Google C++ Style Guide [^3] |
| File length | ≤500 lines | Good | Google C++ Style Guide [^3] |
| Header file length | ≤200 lines | Good | LLVM Coding Standards [^4] |
| Nesting depth | ≤4 | Good | MISRA C++ [^1] |

## Safety

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Smart pointer usage | >80% of heap allocations | Good | C++ Core Guidelines [^5] |
| Raw pointer new/delete | <5% of allocations | Good | C++ Core Guidelines [^5] |

## Testing

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Test framework | Google Test or Catch2 | Standard | Industry convention |
| Test-to-source ratio | ≥0.6 | Good | Industry standard |

## References

[^1]: MISRA C++:2023, "Guidelines for the Use of C++ in Critical Systems"
[^2]: CppDepend, "Code Quality Metrics," cppdepend.com
[^3]: Google, "C++ Style Guide," google.github.io/styleguide/cppguide.html
[^4]: LLVM, "Coding Standards," llvm.org/docs/CodingStandards.html
[^5]: C++ Core Guidelines, isocpp.github.io/CppCoreGuidelines/
