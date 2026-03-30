# Python Tooling Profile

Tools for Python projects. Read this file alongside `shared/tooling/general.md`. All tools follow the safety rules, detection flow, and execution protocol defined in `shared/tooling-registry.md`.

---

## 1. Tools

### mypy

| Field | Value |
|:--|:--|
| **Category** | Static Analyzer / type checker |
| **Tier** | 1 |
| **Detection** | `mypy.ini`, `.mypy.ini`, `[mypy]` section in `pyproject.toml` or `setup.cfg` |
| **Availability** | `which mypy` (Unix) / `where mypy` (Windows) |
| **Report-only invocation** | `mypy {source_paths} --no-error-summary --no-pretty` |
| **Scope-to-files** | Pass file or directory paths as positional arguments |
| **Output format** | `file:line: severity: message [error-code]` — one finding per line |
| **Recommendation** | Best-in-class Python type checker. Enforces PEP 484 type annotations. Use `--strict` for maximum coverage. Does not modify files. |

---

### pyright

| Field | Value |
|:--|:--|
| **Category** | Static Analyzer / type checker |
| **Tier** | 1 |
| **Detection** | `pyrightconfig.json`, `[tool.pyright]` section in `pyproject.toml` |
| **Availability** | `which pyright` (Unix) / `where pyright` (Windows) |
| **Report-only invocation** | `pyright --outputjson {source_paths}` |
| **Scope-to-files** | Pass file or directory paths as positional arguments |
| **Output format** | JSON object with `generalDiagnostics` and `fileDiagnostics` arrays; each entry contains `file`, `range`, `severity`, `message`, `rule` |
| **Recommendation** | Popular OSS type checker from Microsoft. Pairs well with Pylance in VS Code. Faster than mypy on large codebases. Does not modify files. |

---

### ruff

⚠️ DANGER: auto-modifies — NEVER pass `--fix`

| Field | Value |
|:--|:--|
| **Category** | Linter |
| **Tier** | 2 |
| **Detection** | `ruff.toml`, `[tool.ruff]` or `[tool.ruff.lint]` section in `pyproject.toml` |
| **Availability** | `which ruff` (Unix) / `where ruff` (Windows) |
| **Report-only invocation** | `ruff check --no-fix --output-format json {source_paths}` |
| **Scope-to-files** | Pass file or directory paths as positional arguments |
| **Output format** | JSON array; each entry contains `code`, `message`, `filename`, `location.row`, `location.column` |
| **Recommendation** | Best-in-class Python linter. Replaces flake8, isort, and many pylint rules in a single fast tool. Written in Rust — 10–100× faster than alternatives. **CRITICAL:** omitting `--no-fix` causes in-place file rewrites. |

---

### pylint

| Field | Value |
|:--|:--|
| **Category** | Linter |
| **Tier** | 2 |
| **Detection** | `.pylintrc`, `pylintrc`, `[tool.pylint]` section in `pyproject.toml` or `setup.cfg` |
| **Availability** | `which pylint` (Unix) / `where pylint` (Windows) |
| **Report-only invocation** | `pylint --output-format=json {source_paths}` |
| **Scope-to-files** | Pass file or directory paths as positional arguments |
| **Output format** | JSON array; each entry contains `type`, `message`, `symbol`, `path`, `line`, `column` |
| **Recommendation** | Popular OSS linter with deep semantic analysis. Higher false-positive rate than ruff but catches subtle logic issues. Does not modify files. Consider migrating to ruff for performance. |

---

### flake8

| Field | Value |
|:--|:--|
| **Category** | Linter |
| **Tier** | 2 |
| **Detection** | `.flake8`, `[flake8]` section in `setup.cfg` or `tox.ini` |
| **Availability** | `which flake8` (Unix) / `where flake8` (Windows) |
| **Report-only invocation** | `flake8 --format=json {source_paths}` |
| **Scope-to-files** | Pass file or directory paths as positional arguments |
| **Output format** | JSON object keyed by filename; each entry is an array of findings with `code`, `text`, `row`, `col` |
| **Recommendation** | Legacy linter. Still widely used but superseded by ruff, which is faster and covers a superset of flake8 rules. Recommend migrating to ruff. Does not modify files. |

---

### black

⚠️ DANGER: auto-modifies — ALWAYS pass `--check --diff`

| Field | Value |
|:--|:--|
| **Category** | Formatter |
| **Tier** | 3 |
| **Detection** | `[tool.black]` section in `pyproject.toml`, `.black.toml` |
| **Availability** | `which black` (Unix) / `where black` (Windows) |
| **Report-only invocation** | `black --check --diff {source_paths}` |
| **Scope-to-files** | Pass file or directory paths as positional arguments |
| **Output format** | Text diff showing proposed reformatting; exits 1 if any file would be reformatted, 0 if all files are already formatted |
| **Recommendation** | Best-in-class opinionated Python formatter. Produces deterministic output with minimal configuration. **CRITICAL:** omitting `--check` causes in-place file rewrites. |

---

### isort

⚠️ DANGER: auto-modifies — ALWAYS pass `--check-only --diff`

| Field | Value |
|:--|:--|
| **Category** | Formatter / import sorting |
| **Tier** | 3 |
| **Detection** | `[tool.isort]` section in `pyproject.toml` or `setup.cfg`, `.isort.cfg` |
| **Availability** | `which isort` (Unix) / `where isort` (Windows) |
| **Report-only invocation** | `isort --check-only --diff {source_paths}` |
| **Scope-to-files** | Pass file or directory paths as positional arguments |
| **Output format** | Text diff showing proposed import reordering; exits 1 if any file would be changed, 0 if all imports are already sorted |
| **Recommendation** | Popular OSS import sorter. Note: ruff's `I` rule set replicates isort behavior — consider consolidating if ruff is already in use. **CRITICAL:** omitting `--check-only` causes in-place file rewrites. |

---

### bandit

| Field | Value |
|:--|:--|
| **Category** | Security Scanner |
| **Tier** | 4 |
| **Detection** | `.bandit`, `[tool.bandit]` section in `pyproject.toml` or `setup.cfg`, `bandit.yaml` |
| **Availability** | `which bandit` (Unix) / `where bandit` (Windows) |
| **Report-only invocation** | `bandit -r {source_paths} -f json --quiet` |
| **Scope-to-files** | Pass file or directory paths as positional arguments (`-r` enables recursive directory scanning) |
| **Output format** | JSON object with a `results` array; each entry contains `test_id`, `issue_severity`, `issue_confidence`, `filename`, `line_number`, `issue_text` |
| **Recommendation** | Popular OSS security scanner for Python. Detects common vulnerabilities (SQL injection, hardcoded secrets, insecure crypto, subprocess misuse). Does not modify files. |

---

### Semgrep Python rules

⚠️ DANGER: auto-modifies — NEVER omit `--no-autofix`

| Field | Value |
|:--|:--|
| **Category** | Security Scanner |
| **Tier** | 4 |
| **Detection** | `.semgrep.yml`, `.semgrep/` directory, `semgrep` in CI config files (see `shared/tooling/general.md`) |
| **Availability** | `which semgrep` (Unix) / `where semgrep` (Windows) |
| **Report-only invocation** | `semgrep scan --config auto --lang python --json --no-autofix --quiet {source_paths}` |
| **Scope-to-files** | Pass file or directory paths as positional arguments |
| **Output format** | JSON object with a `results` array; each entry contains `check_id`, `path`, `start.line`, `extra.severity`, `extra.message` |
| **Recommendation** | Best-in-class for Python security scanning. Covers OWASP Top 10, injection flaws, deserialization, and framework-specific issues. Use `--lang python` to restrict to Python rules. **CRITICAL:** omitting `--no-autofix` allows Semgrep to rewrite source files. |

---

## 2. Build-Integrated Analysis Patterns

These patterns indicate that static analysis is already woven into the project's development workflow. The orchestrator detects them during **Step 5 — Detect Build-Integrated Analysis** and records them for grading.

| Pattern | Location | Signal |
|:--|:--|:--|
| `[tool.mypy]` with `strict = true` | `pyproject.toml` | Strict type checking enforced project-wide |
| `[tool.ruff]` or `[tool.ruff.lint]` | `pyproject.toml` | Ruff linting configured project-wide |
| `[tool.black]` | `pyproject.toml` | Black formatting configured project-wide |
| `[testenv]` or `[testenv:lint]` with tool commands | `tox.ini` | Linting integrated into tox test matrix |
| `session` functions running tools | `noxfile.py` | Linting/type-checking integrated into nox sessions |
| `lint`, `format`, or `typecheck` targets | `Makefile` | Analysis available as make targets |
| Python tool hooks (ruff, black, mypy, flake8, isort) | `.pre-commit-config.yaml` | Tools enforced at commit time via pre-commit framework |

---

## 3. Gap Analysis

When the orchestrator identifies missing tooling categories, recommend alternatives using this table.

| If Missing | Best-in-Class | Popular OSS |
|:--|:--|:--|
| No type checker | **mypy** — PEP 484 compliant, widely adopted, configurable strictness | **pyright** — fast, VS Code integration via Pylance |
| No linter | **ruff** — replaces flake8/pylint/isort, 10–100× faster | **pylint** — deep semantic analysis, established rule set |
| No formatter | **black** — opinionated, zero-config, deterministic output | — (black is already free/OSS) |
| No security scanner | **Semgrep** — Python-specific rules, OWASP coverage, free CLI | **bandit** — lightweight, Python-native, CI-friendly |
