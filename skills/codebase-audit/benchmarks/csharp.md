# C# Benchmarks

C#-specific quality thresholds aligned with .NET ecosystem standards.

## Complexity

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Cyclomatic complexity (avg) | ≤10 | Good | NDepend defaults [^1] |
| Cyclomatic complexity (max) | ≤20 | Acceptable | Visual Studio code metrics [^2] |

## Size & Style

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Function length (median) | ≤30 lines | Good | .NET coding conventions [^3] |
| File length (one class per file) | ≤400 lines | Good | .NET convention [^3] |
| Nesting depth | ≤4 | Good | NDepend defaults [^1] |

## Testing

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Test framework | xUnit, NUnit, or MSTest | Standard | .NET ecosystem [^4] |
| Test-to-source ratio | ≥0.8 | Good | Industry standard |

## Dependencies

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| dotnet audit clean | 0 vulnerabilities | Required | dotnet list package --vulnerable [^4] |

## References

[^1]: NDepend, "Code Quality Metrics," ndepend.com
[^2]: Microsoft, "Code Metrics Values," docs.microsoft.com/en-us/visualstudio/code-quality/code-metrics-values
[^3]: Microsoft, ".NET Coding Conventions," docs.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions
[^4]: Microsoft, ".NET Documentation," docs.microsoft.com/en-us/dotnet/
