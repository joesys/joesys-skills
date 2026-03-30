# GDScript Tooling Profile

Tools for GDScript (Godot Engine) projects. Read this file alongside `shared/tooling/general.md`. All tools follow the safety rules, detection flow, and execution protocol defined in `shared/tooling-registry.md`.

> **Note:** GDScript has significantly more limited tooling compared to mainstream languages. The ecosystem has no dedicated type checker, no security scanner, and only one mature third-party static analysis suite. The primary — and effectively only — option for both linting and formatting is **gdtoolkit**, installed via `pip install gdtoolkit`.

---

## 1. Tools

### gdlint (gdtoolkit)

| Field | Value |
|:--|:--|
| **Category** | Linter |
| **Tier** | 2 |
| **Detection** | `.gdlintrc` file in the repository root, or `gdtoolkit` listed in `requirements.txt` / `pyproject.toml` |
| **Availability** | `which gdlint` (Unix) / `where gdlint` (Windows) |
| **Report-only invocation** | `gdlint {source_paths}` — does not modify files |
| **Scope-to-files** | Pass individual `.gd` file paths as positional arguments: `gdlint src/player.gd src/enemy.gd` |
| **Output format** | Text diagnostics, one per line: `file:line: Error: message (rule-name)` — exits 1 if any violations are found, 0 if clean |
| **Recommendation** | Best-in-class GDScript linter — it is the only production-ready option available. Part of the gdtoolkit suite. Enforces naming conventions, structural rules, and style guidelines. Install via `pip install gdtoolkit`. Does not modify files. |

---

### gdformat (gdtoolkit)

> ⚠️ **DANGER: auto-modifies** — `gdformat` rewrites `.gd` files in place when run without `--check`. **NEVER** omit `--check` during analysis.

| Field | Value |
|:--|:--|
| **Category** | Formatter |
| **Tier** | 3 |
| **Detection** | `.gdformatrc` file in the repository root, or `gdtoolkit` listed in `requirements.txt` / `pyproject.toml` (same package as gdlint) |
| **Availability** | `which gdformat` (Unix) / `where gdformat` (Windows) |
| **Report-only invocation** | `gdformat --check {source_paths}` — **WITHOUT** `--check`, rewrites files in place |
| **Scope-to-files** | Pass individual `.gd` file paths as positional arguments: `gdformat --check src/player.gd src/enemy.gd` |
| **Output format** | Lists files that would be reformatted, one per line — exits 1 if any files need reformatting, 0 if all files are already formatted |
| **Recommendation** | Best-in-class GDScript formatter — it is the only production-ready option available. Part of the gdtoolkit suite. Install via `pip install gdtoolkit`. **CRITICAL:** omitting `--check` causes in-place file rewrites with no confirmation prompt. |

---

## 2. Build-Integrated Analysis Patterns

These patterns indicate that static analysis is already woven into the project's development workflow. The orchestrator detects them during **Step 5 — Detect Build-Integrated Analysis** and records them for grading.

| Pattern | Location | Signal |
|:--|:--|:--|
| `gdlint` or `gdformat` command | CI workflow files (`.github/workflows/*.yml`, etc.) | Analysis enforced in CI pipeline |
| `gdlint` or `gdformat` target | `Makefile` | Analysis available as a make target |
| `gdtoolkit` | `requirements.txt` / `pyproject.toml` | Tooling declared as a project dependency |
| `GDScript/` editor settings | `project.godot` | Godot editor-level script settings — limited relevance to static analysis |

---

## 3. Gap Analysis

When the orchestrator identifies missing tooling categories, recommend alternatives using this table.

| If Missing | Best-in-Class | Popular OSS |
|:--|:--|:--|
| No linter | **gdlint** from gdtoolkit (`pip install gdtoolkit`) — the only GDScript linter | — (no alternative exists) |
| No formatter | **gdformat** from gdtoolkit (`pip install gdtoolkit`) — the only GDScript formatter | — (no alternative exists) |
| No security scanner | N/A — no dedicated GDScript security scanner exists. Rely on AI analysis. | — |
