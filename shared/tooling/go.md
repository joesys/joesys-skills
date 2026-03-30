# Go Tooling Profile

Tools for Go projects. Read this file alongside `shared/tooling/general.md`. All tools follow the safety rules, detection flow, and execution protocol defined in `shared/tooling-registry.md`.

---

## 1. Tools

### go vet

| Field | Value |
|:--|:--|
| **Category** | Static Analyzer |
| **Tier** | 1 |
| **Detection** | Always available with the Go toolchain — no config file required |
| **Availability** | `which go` (Unix) / `where go` (Windows) |
| **Report-only invocation** | `go vet ./...` |
| **Scope-to-files** | Pass a package path: `go vet ./path/to/package` — operates on packages, not individual files |
| **Output format** | Text diagnostics to stderr; one finding per line as `file:line: message` |
| **Recommendation** | Best-in-class built-in analyzer. Catches real bugs: incorrect format strings, unreachable code, misuse of sync primitives, suspicious composite literals. Zero configuration. Does not modify files. Run as the first check on every Go project. |

---

### staticcheck

| Field | Value |
|:--|:--|
| **Category** | Static Analyzer |
| **Tier** | 1 |
| **Detection** | `staticcheck.conf` (rare). Check binary availability. |
| **Availability** | `which staticcheck` (Unix) / `where staticcheck` (Windows) |
| **Report-only invocation** | `staticcheck -f json ./...` |
| **Scope-to-files** | Pass a package path as a positional argument: `staticcheck -f json ./path/to/package` |
| **Output format** | JSON lines (one JSON object per line); each object contains `code`, `severity`, `message`, `location.file`, `location.line` |
| **Recommendation** | Best-in-class third-party static analyzer for Go. Goes significantly deeper than `go vet` — detects deprecated API usage, incorrect time.Duration arithmetic, unreachable code after returns, and hundreds of additional checks. Does not modify files. |

---

### golangci-lint

| Field | Value |
|:--|:--|
| **Category** | Meta-linter |
| **Tier** | 2 |
| **Detection** | `.golangci.yml`, `.golangci.yaml`, `.golangci.toml`, `.golangci.json` |
| **Availability** | `which golangci-lint` (Unix) / `where golangci-lint` (Windows) |
| **Report-only invocation** | `golangci-lint run --out-format json ./...` — NEVER pass `--fix` |
| **Scope-to-files** | Pass a package path as a positional argument: `golangci-lint run --out-format json ./path/to/package` |
| **Output format** | JSON object with an `Issues` array; each issue contains `Text`, `Severity`, `Pos.Filename`, `Pos.Line`, `FromLinter` |
| **Recommendation** | Popular OSS meta-linter that aggregates 100+ Go linters (including staticcheck, errcheck, govet, gosimple) in a single run. Highly configurable via its config file. Does not modify files unless `--fix` is passed — never pass `--fix`. |

---

### gofmt

⚠️ DANGER: auto-modifies — NEVER pass `-w`

| Field | Value |
|:--|:--|
| **Category** | Formatter |
| **Tier** | 3 |
| **Detection** | Always available with the Go toolchain — no config file required |
| **Availability** | `which gofmt` (Unix) / `where gofmt` (Windows) |
| **Report-only invocation** | `gofmt -l {source_paths}` |
| **Scope-to-files** | Pass file or directory paths as positional arguments |
| **Output format** | Lists the filenames of files that need formatting, one per line; exits 0 whether or not files need formatting |
| **Recommendation** | Best-in-class built-in formatter. The Go standard — all idiomatic Go code is gofmt-compliant. **CRITICAL:** `-w` writes changes in place and must never be passed. Use `-l` to report files needing formatting without modifying them. |

---

### goimports

⚠️ DANGER: auto-modifies — NEVER pass `-w`

| Field | Value |
|:--|:--|
| **Category** | Formatter / import management |
| **Tier** | 3 |
| **Detection** | Check binary availability — no config file |
| **Availability** | `which goimports` (Unix) / `where goimports` (Windows) |
| **Report-only invocation** | `goimports -l {source_paths}` |
| **Scope-to-files** | Pass file or directory paths as positional arguments |
| **Output format** | Lists the filenames of files that need formatting or import changes, one per line |
| **Recommendation** | Popular OSS superset of gofmt — applies all gofmt formatting and additionally adds missing imports and removes unused ones. **CRITICAL:** `-w` writes changes in place and must never be passed. Use `-l` to report files needing changes without modifying them. |

---

### gosec

| Field | Value |
|:--|:--|
| **Category** | Security Scanner |
| **Tier** | 4 |
| **Detection** | Check binary availability, or `gosec` referenced in CI config |
| **Availability** | `which gosec` (Unix) / `where gosec` (Windows) |
| **Report-only invocation** | `gosec -fmt json -quiet ./...` |
| **Scope-to-files** | Pass a package path as a positional argument: `gosec -fmt json -quiet ./path/to/package` |
| **Output format** | JSON object with an `Issues` array; each issue contains `rule_id`, `severity`, `confidence`, `details`, `file`, `line` |
| **Recommendation** | Popular OSS SAST tool for Go. Detects hardcoded credentials, SQL injection, command injection, insecure TLS config, unsafe use of `math/rand`, and other common Go-specific security pitfalls. Does not modify files. |

---

### govulncheck

| Field | Value |
|:--|:--|
| **Category** | Security Scanner / dependency vulnerability analysis |
| **Tier** | 4 |
| **Detection** | `go.sum` required. Check binary availability. |
| **Availability** | `which govulncheck` (Unix) / `where govulncheck` (Windows) |
| **Report-only invocation** | `govulncheck -json ./...` |
| **Scope-to-files** | N/A — scans the full dependency tree and call graphs; does not operate on individual files or packages |
| **Output format** | JSON with vulnerability entries; each entry contains `osv` (CVE data), `modules`, `packages`, and `callstacks` showing reachable vulnerable code paths |
| **Recommendation** | Best-in-class official Go vulnerability scanner from the Go team. Cross-references the Go vulnerability database against your exact dependency versions and uses call graph analysis to report only vulnerabilities reachable from your code — eliminates false positives from transitive-only dependencies. Does not modify files. |

---

## 2. Build-Integrated Analysis Patterns

These patterns indicate that static analysis is already woven into the project's development workflow. The orchestrator detects them during **Step 5 — Detect Build-Integrated Analysis** and records them for grading.

| Pattern | Location | Signal |
|:--|:--|:--|
| `go vet` in build targets | `Makefile` | Vet integrated into build pipeline |
| `golangci-lint run` in build targets | `Makefile` | Meta-linter integrated into build pipeline |
| `gofmt -l` or `goimports -l` in build targets | `Makefile` | Formatter check integrated into build pipeline |
| `go vet`, `golangci-lint`, or `gofmt` steps | `.github/workflows/*.yml`, `.gitlab-ci.yml`, etc. | Static analysis enforced in CI |
| `//go:generate` directives | `*.go` source files | Signals build maturity and automated code generation in the workflow |
| `golangci-lint` or Go tool hooks | `.pre-commit-config.yaml` | Analysis enforced at commit time |

---

## 3. Gap Analysis

When the orchestrator identifies missing tooling categories, recommend alternatives using this table.

| If Missing | Best-in-Class | Popular OSS |
|:--|:--|:--|
| Only `go vet` (no deeper static analysis) | **staticcheck** — significantly deeper analysis, 150+ checks, official Go tool | **golangci-lint** — aggregates 100+ linters including staticcheck in one tool |
| No meta-linter | — | **golangci-lint** — aggregates staticcheck, errcheck, govet, and 100+ more linters |
| No formatter check | **gofmt** — built-in, zero-config, the Go standard | **goimports** — superset of gofmt; also manages import blocks |
| No security scanner | **govulncheck** — official, call-graph-aware, zero false positives on unreachable vulns | **gosec** — SAST patterns for Go-specific security pitfalls |
