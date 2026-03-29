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
| Function length (median) | ≤40 lines | Good | Effective Go [^3] |
| File length | ≤600 lines | Good | Go community convention |
| Nesting depth | ≤4 | Good | Go proverbs [^4] |
| Line length | ≤120 chars | Good | Go community convention |

## Testing

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Test runner | `go test ./...` | Standard | Built-in [^5] |
| Test-to-source ratio | ≥0.7 | Good | Industry standard |
| Table-driven tests | Present | Expected | Go testing convention [^5] |

## Dependencies

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| govulncheck clean | 0 vulnerabilities | Required | govulncheck [^6] |
| go.sum present | Present | Required | Go modules [^5] |

## References

[^1]: Go idiomatic error handling adds ~3 CC per function via `if err != nil` patterns
[^2]: golangci-lint, "Linters," golangci-lint.run
[^3]: Effective Go, go.dev/doc/effective_go
[^4]: Rob Pike, "Go Proverbs," go-proverbs.github.io
[^5]: The Go Programming Language, go.dev/doc/
[^6]: govulncheck, "Check for Known Vulnerabilities," pkg.go.dev/golang.org/x/vuln/cmd/govulncheck
