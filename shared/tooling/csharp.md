# C# Tooling Profile

Tools for C# / .NET projects. Read this file alongside `shared/tooling/general.md`. All tools follow the safety rules, detection flow, and execution protocol defined in `shared/tooling-registry.md`.

---

## 1. Tools

### Roslyn Analyzers

| Field | Value |
|:--|:--|
| **Category** | Static Analyzer |
| **Tier** | 1 |
| **Detection** | `<PackageReference Include="Microsoft.CodeAnalysis.NetAnalyzers"` in `.csproj`, or `<EnableNETAnalyzers>true</EnableNETAnalyzers>` in `.csproj` / `Directory.Build.props`. Enabled by default in .NET 5+. |
| **Availability** | Built into `dotnet build`. Verify with `dotnet --version`. |
| **Report-only invocation** | `dotnet build --no-incremental -warnaserror -v quiet` — runs as part of compilation, does not modify source files. |
| **Scope-to-files** | Operates on projects or solutions; pass the `.csproj` or `.sln` path. Cannot be scoped to individual source files. |
| **Output format** | MSBuild format: `file(line,col): warning/error CAXXXX: message` — one finding per line. |
| **Recommendation** | Best-in-class .NET static analyzer. Ships with the .NET SDK — no installation required on .NET 5+. Covers correctness, reliability, performance, security, and API design rules. Does not modify files. |

---

### StyleCop Analyzers

| Field | Value |
|:--|:--|
| **Category** | Linter |
| **Tier** | 2 |
| **Detection** | `<PackageReference Include="StyleCop.Analyzers"` in `.csproj`, or `stylecop.json` in the project root. |
| **Availability** | NuGet package — present when the `<PackageReference>` is in the project. Runs automatically during `dotnet build`. |
| **Report-only invocation** | `dotnet build --no-incremental -warnaserror -v quiet` — StyleCop rules surface as MSBuild warnings/errors during compilation. Does not modify source files. |
| **Scope-to-files** | Operates on projects or solutions; pass the `.csproj` or `.sln` path. Cannot be scoped to individual source files. |
| **Output format** | MSBuild format: `file(line,col): warning SAxxxx: message` — one finding per line. |
| **Recommendation** | Popular OSS style enforcer for C#. Covers naming conventions, layout, ordering, and documentation rules. Complements Roslyn Analyzers. Does not modify files. |

---

### dotnet format

⚠️ DANGER: auto-modifies — ALWAYS pass `--verify-no-changes`

| Field | Value |
|:--|:--|
| **Category** | Formatter |
| **Tier** | 3 |
| **Detection** | `.editorconfig` with C# rules, `.globalconfig`, or `<EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>` in `.csproj` / `Directory.Build.props`. |
| **Availability** | Built into .NET SDK 6+. Verify with `dotnet format --version`. |
| **Report-only invocation** | `dotnet format --verify-no-changes --verbosity diagnostic` — **CRITICAL:** omitting `--verify-no-changes` rewrites source files in place. |
| **Scope-to-files** | `dotnet format --include src/Foo.cs src/Bar.cs --verify-no-changes` — pass space-separated file paths to `--include`. |
| **Output format** | Text listing files that would be changed; exits with code 2 if any formatting changes are needed, 0 if all files are already formatted. |
| **Recommendation** | Best-in-class .NET formatter. Built into the SDK — no installation required. Applies `.editorconfig` and `<EnforceCodeStyleInBuild>` rules. **CRITICAL:** omitting `--verify-no-changes` causes in-place file rewrites. Use `dotnet format --verify-no-changes` in CI. |

---

### Security Code Scan

| Field | Value |
|:--|:--|
| **Category** | Security Scanner |
| **Tier** | 4 |
| **Detection** | `<PackageReference Include="SecurityCodeScan.VS2019"` or `<PackageReference Include="SecurityCodeScan.VS2022"` in `.csproj`. |
| **Availability** | NuGet package — present when the `<PackageReference>` is in the project. Runs automatically during `dotnet build`. |
| **Report-only invocation** | `dotnet build --no-incremental -warnaserror -v quiet` — Security Code Scan rules surface as SCSxxxx warnings/errors during compilation. Does not modify source files. |
| **Scope-to-files** | Operates on projects or solutions; pass the `.csproj` or `.sln` path. Cannot be scoped to individual source files. |
| **Output format** | MSBuild format: `file(line,col): warning SCSxxxx: message` — one finding per line. |
| **Recommendation** | Popular OSS security scanner for C#. Detects OWASP Top 10 vulnerabilities including SQL injection, XSS, path traversal, and insecure deserialization. Based on Roslyn — integrates cleanly with the build pipeline. Does not modify files. |

---

### Semgrep C# rules

⚠️ DANGER: auto-modifies — NEVER omit `--no-autofix`

| Field | Value |
|:--|:--|
| **Category** | Security Scanner |
| **Tier** | 4 |
| **Detection** | `.semgrep.yml`, `.semgrep/` directory, `semgrep` in CI config files (see `shared/tooling/general.md`). |
| **Availability** | `which semgrep` (Unix) / `where semgrep` (Windows) |
| **Report-only invocation** | `semgrep scan --config auto --lang csharp --json --no-autofix --quiet {source_paths}` — **CRITICAL:** omitting `--no-autofix` allows Semgrep to rewrite source files. |
| **Scope-to-files** | Pass file or directory paths as positional arguments. |
| **Output format** | JSON object with a `results` array; each entry contains `check_id`, `path`, `start.line`, `extra.severity`, `extra.message`. |
| **Recommendation** | Best-in-class for C# security scanning. Cross-language rule coverage including OWASP Top 10, injection flaws, and framework-specific issues. Complements build-integrated tools since it scans independently of the build pipeline. **CRITICAL:** omitting `--no-autofix` allows Semgrep to rewrite source files. |

---

## 2. Build-Integrated Analysis Patterns

These patterns indicate that static analysis is already woven into the project's development workflow. The orchestrator detects them during **Step 5 — Detect Build-Integrated Analysis** and records them for grading.

| Pattern | Location | Signal |
|:--|:--|:--|
| `<EnableNETAnalyzers>true</EnableNETAnalyzers>` | `.csproj` / `Directory.Build.props` | Roslyn analyzers explicitly enabled project-wide |
| `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>` | `.csproj` / `Directory.Build.props` | All analyzer warnings promoted to errors — enforced at build time |
| `<EnforceCodeStyleInBuild>true</EnforceCodeStyleInBuild>` | `.csproj` / `Directory.Build.props` | Code style rules enforced during build |
| `<AnalysisLevel>latest-all</AnalysisLevel>` | `.csproj` / `Directory.Build.props` | Opt into all latest analyzer rules |
| `dotnet_diagnostic.*.severity` rules | `.editorconfig` | Fine-grained diagnostic severity overrides |
| `dotnet format --verify-no-changes` | CI config (`.yml` / `.yaml`) | Format check enforced in CI pipeline |
| `dotnet build -warnaserror` | CI config (`.yml` / `.yaml`) | Build warnings treated as errors in CI |

---

## 3. Gap Analysis

When the orchestrator identifies missing tooling categories, recommend alternatives using this table.

| If Missing | Best-in-Class | Popular OSS |
|:--|:--|:--|
| No static analyzer | **Roslyn Analyzers** — free, built into .NET 5+, enable via `<EnableNETAnalyzers>true</EnableNETAnalyzers>` in `Directory.Build.props` | — (Roslyn is already free/OSS) |
| No style enforcement | **StyleCop.Analyzers** — NuGet package, integrates with MSBuild, widely adopted | — (StyleCop.Analyzers is already OSS) |
| No formatter | **dotnet format** — built into .NET SDK 6+, no installation required | — (dotnet format is already free/built-in) |
| No security scanner | **Semgrep** — best-in-class, cross-language, OWASP coverage | **Security Code Scan** — OSS, NuGet package, OWASP-aligned, build-integrated |
