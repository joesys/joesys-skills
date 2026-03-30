# C++ Tooling Profile

Tools and patterns for C and C++ projects. Read this file alongside `shared/tooling/general.md`. All tools listed here follow the safety rules, detection flow, and execution protocol defined in `shared/tooling-registry.md`.

---

## 1. Tools

### clang-tidy

| Field | Value |
|:--|:--|
| **Category** | Static Analyzer |
| **Tier** | 1 |
| **Detection** | `.clang-tidy` file in the repository root or any parent directory |
| **Availability** | `which clang-tidy` (Unix) / `where clang-tidy` (Windows) |

**Report-only invocation:**

```
clang-tidy -p {build_dir} --quiet {files}
```

| Flag | Purpose |
|:--|:--|
| `-p {build_dir}` | Path to the directory containing `compile_commands.json` |
| `--quiet` | Suppresses informational messages; only findings are emitted |

> **NEVER** pass `--fix` or `--fix-errors` — either flag rewrites source files in place.

**Scope-to-files:** Pass file paths as positional arguments after all flags. Limit to the files under review to avoid full-project analysis overhead.

**Output format:** Plain text, one finding per line:

```
{file}:{line}:{col}: {severity}: {message} [{check-name}]
```

**Recommendation:** Best-in-class C++ static analyzer. Integrates with `compile_commands.json` for accurate, whole-translation-unit analysis. Covers a wide range of checks (bugprone, clang-analyzer, cppcoreguidelines, modernize, performance, readability). Pairs well with `CMAKE_CXX_CLANG_TIDY` for build-integrated runs.

---

### cppcheck

| Field | Value |
|:--|:--|
| **Category** | Static Analyzer |
| **Tier** | 1 |
| **Detection** | `.cppcheck` file, `cppcheck.cfg`, or `cppcheck` referenced in CI config / `Makefile` / `CMakeLists.txt` |
| **Availability** | `which cppcheck` (Unix) / `where cppcheck` (Windows) |

**Report-only invocation:**

```
cppcheck --enable=all --suppress=missingIncludeSystem --error-exitcode=0 --quiet {source_paths}
```

| Flag | Purpose |
|:--|:--|
| `--enable=all` | Enables all check categories (style, performance, portability, information) |
| `--suppress=missingIncludeSystem` | Silences noise from missing system headers |
| `--error-exitcode=0` | Always exits 0 — prevents findings from being treated as tool failure |
| `--quiet` | Suppresses progress output; emits only findings |

**Scope-to-files:** Pass file paths or directory paths as positional arguments. Directories are scanned recursively.

**Output format:** Plain text, one finding per line:

```
{file}:{line}: {severity}: {message} [{id}]
```

**Recommendation:** Popular OSS static analyzer with no dependency on a compilation database — useful when `compile_commands.json` is absent. Less precise than clang-tidy for complex template code but fast and easy to integrate. Good complement to clang-tidy.

---

### clang-format

> ⚠️ **DANGER: auto-modifies** — without `--dry-run`, `clang-format` rewrites files in place. **Always** pass `--dry-run --Werror` for report-only use.

| Field | Value |
|:--|:--|
| **Category** | Formatter |
| **Tier** | 3 |
| **Detection** | `.clang-format` or `_clang-format` file in the repository root or any parent directory |
| **Availability** | `which clang-format` (Unix) / `where clang-format` (Windows) |

**Report-only invocation:**

```
clang-format --dry-run --Werror {files}
```

| Flag | Purpose |
|:--|:--|
| `--dry-run` | **CRITICAL** — performs formatting check without modifying any file |
| `--Werror` | Exits non-zero if any file would be reformatted; enables diff detection |

**Scope-to-files:** Pass file paths as positional arguments. Does not accept directory paths — enumerate files explicitly.

**Output format:** Plain text warnings when files deviate from the configured style:

```
{file}:{line}:{col}: warning: code should be clang-formatted [-Wclang-format-violations]
```

**Recommendation:** Best-in-class C/C++ formatter. Deterministic output governed by `.clang-format` configuration. Strongly prefer enforcing it in CI and pre-commit hooks to keep diffs clean.

---

### Semgrep C++ rules

> ⚠️ **DANGER: auto-modifies** — Semgrep rules may include autofixes. **Always** pass `--no-autofix`. **Never** omit it.

| Field | Value |
|:--|:--|
| **Category** | Security Scanner |
| **Tier** | 4 |
| **Detection** | `.semgrep.yml`, `.semgrep/` directory, or `semgrep` referenced in CI config |
| **Availability** | `which semgrep` (Unix) / `where semgrep` (Windows) |

**Report-only invocation:**

```
semgrep scan --config auto --lang cpp --json --no-autofix --quiet {source_paths}
```

| Flag | Purpose |
|:--|:--|
| `--config auto` | Uses Semgrep's curated rule registry for C++ |
| `--lang cpp` | Restricts analysis to C/C++ files |
| `--json` | Structured output for programmatic consumption |
| `--no-autofix` | **CRITICAL** — prevents any source modification |
| `--quiet` | Suppresses progress bars and non-essential output |

**Scope-to-files:** Pass file or directory paths as positional arguments.

**Output format:** JSON object with a `results` array. Each result contains:

| Key | Description |
|:--|:--|
| `check_id` | Rule identifier |
| `path` | File path |
| `start.line` | Line number |
| `extra.severity` | Severity level |
| `extra.message` | Human-readable explanation |

**Recommendation:** Best-in-class for C++ security pattern scanning. Detects memory safety issues, injection patterns, use-after-free risks, and insecure API usage. Free CLI; paid CI platform (Semgrep Cloud).

---

### Flawfinder

| Field | Value |
|:--|:--|
| **Category** | Security Scanner |
| **Tier** | 4 |
| **Detection** | `flawfinder` referenced in CI config, `Makefile`, or no config file required — presence of the binary is sufficient |
| **Availability** | `which flawfinder` (Unix) / `where flawfinder` (Windows) |

**Report-only invocation:**

```
flawfinder --columns --context --quiet {source_paths}
```

| Flag | Purpose |
|:--|:--|
| `--columns` | Includes column numbers in output for precise location |
| `--context` | Shows the source line containing the finding |
| `--quiet` | Suppresses the summary header and progress output |

Flawfinder does **not** modify files — no additional safety flags are required.

**Scope-to-files:** Pass file or directory paths as positional arguments. Directories are scanned recursively.

**Output format:** Plain text, one finding per block:

```
{file}:{line}:{col}: [{risk-level}] (CWE-{id}) {function}: {message}
  {source-context-line}
```

Risk levels range from 0 (informational) to 5 (highest risk).

**Recommendation:** Popular OSS security scanner. Fast, zero-configuration, and focused on identifying calls to dangerous C/C++ functions (e.g., `strcpy`, `sprintf`, `gets`). Lower precision than Semgrep but a useful quick-scan complement. Good for teams that cannot run Semgrep.

---

## 2. Build-Integrated Analysis

These patterns indicate that analysis is already woven into the project's build system or CI pipeline. Detect them during **Step 5 — Detect Build-Integrated Analysis** and record them for grading.

| Pattern | Location | Signal |
|:--|:--|:--|
| `-Wall -Werror` | `CMakeLists.txt`, `Makefile`, `meson.build` | Compiler warnings treated as errors — baseline quality gate |
| `-Wextra -Wpedantic` | `CMakeLists.txt`, `Makefile`, `meson.build` | Extended warnings enabled — stronger correctness enforcement |
| `-fsanitize=address,undefined` | `CMakeLists.txt`, `Makefile`, `meson.build` | AddressSanitizer + UBSan enabled — runtime bug detection |
| `-fsanitize=thread` | `CMakeLists.txt`, `Makefile`, `meson.build` | ThreadSanitizer enabled — data race detection |
| `CMAKE_CXX_CLANG_TIDY` | `CMakeLists.txt` | clang-tidy runs on every compilation unit during build |
| `CMAKE_CXX_CPPCHECK` | `CMakeLists.txt` | cppcheck runs on every compilation unit during build |
| `CMAKE_CXX_INCLUDE_WHAT_YOU_USE` | `CMakeLists.txt` | include-what-you-use enforced at build time |
| `clang-analyzer` or `scan-build` | CI config | Clang static analyzer runs in CI pipeline |
| `CMAKE_EXPORT_COMPILE_COMMANDS ON` | `CMakeLists.txt` | `compile_commands.json` generated — required for accurate clang-tidy analysis |

---

## 3. Gap Analysis

When the orchestrator identifies missing tooling categories, recommend alternatives using this table.

| If Missing | Best-in-Class | Popular OSS |
|:--|:--|:--|
| No static analyzer | **clang-tidy** — deep, accurate, integrates with CMake | **cppcheck** — fast, zero-config, no compilation database required |
| No formatter | **clang-format** — deterministic, widely adopted | — (clang-format is already free/OSS) |
| No security scanner | **Semgrep** — broad rule coverage, active rule registry | **Flawfinder** — fast, zero-config, focuses on dangerous API calls |
| No compiler hardening | Add `-Wall -Werror -Wextra` + `-fsanitize=address,undefined` to build flags | — |
| No compilation database | Set `CMAKE_EXPORT_COMPILE_COMMANDS ON` in `CMakeLists.txt` | — |
