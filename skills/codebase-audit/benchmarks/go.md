# Go Benchmarks

Go-specific quality thresholds. Go's error handling idiom affects complexity baselines.

## Complexity

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Cyclomatic complexity (avg) | ≤12 | Good | Adjusted +3 for error handling [^1] |
| Cyclomatic complexity (max) | ≤20 | Acceptable | golangci-lint defaults [^2] |

## Size & Style

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Function length (median) | ≤40 lines | Good | Convention — no single authoritative source |
| File length | ≤600 lines | Good | Convention — no single authoritative source |
| Nesting depth | ≤4 | Good | Convention — no single authoritative source |
| Line length | ≤120 chars | Good | Convention — no single authoritative source |

## Testing

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Test runner | `go test ./...` | Standard | Built-in [^4] |
| Test-to-source ratio | ≥0.7 | Good | Convention — no single authoritative source |
| Table-driven tests | Present | Expected | Go testing convention [^4] |

## Dependencies

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| govulncheck clean | 0 vulnerabilities | Required | govulncheck [^5] |
| go.sum present | Present | Required | Go modules [^4] |

## Story Readability

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Exported function GoDoc coverage | 100% | Good | Go Doc Comments [^3] |

## References

[^1]: Go idiomatic error handling adds ~3 CC per function via `if err != nil` patterns
[^2]: golangci-lint, "Linters," golangci-lint.run
[^3]: Go Doc Comments, go.dev/doc/comment — "Every exported (capitalized) name should have a doc comment."
[^4]: The Go Programming Language, go.dev/doc/
[^5]: govulncheck, "Check for Known Vulnerabilities," pkg.go.dev/golang.org/x/vuln/cmd/govulncheck
