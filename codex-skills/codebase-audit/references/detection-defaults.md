# Codebase Audit — Detection Defaults

Auto-detection rules for language, paths, test runners, and polyglot repos. Values in `.codex/audit.yaml` always override auto-detected defaults.

## Language Detection (Marker Files)

Check in priority order — first match wins:

| Marker | Language |
|---|---|
| `project.godot` | GDScript |
| `Cargo.toml` | Rust |
| `go.mod` | Go |
| `*.sln` or `*.csproj` | C# |
| `CMakeLists.txt` + `.cpp`/`.cc`/`.h` files | C++ |
| `pyproject.toml` / `setup.py` / `requirements.txt` | Python |
| `package.json` (with `.ts` files) | TypeScript |
| `package.json` (without `.ts` files) | JavaScript |
| Fallback | Count file extensions, pick dominant |

---

## Language Defaults

| Language | Extension | Test Runner |
|---|---|---|
| Python | .py | pytest |
| TypeScript | .ts | jest/vitest |
| JavaScript | .js | jest/vitest |
| Rust | .rs | cargo test |
| Go | .go | go test ./... |
| C++ | .cpp | ctest/gtest |
| C# | .cs | dotnet test |
| GDScript | .gd | gdUnit4 |

---

## Path Auto-Detection

### Source Paths

Check for `src/`, `lib/`, `app/` — use all found. Fall back to project root if none exist.

For monorepos: also check `packages/*/src/`, `backend/`, `frontend/`, `services/*/`.

### Test Paths

Check for `tests/`, `test/`, `__tests__/`, `spec/` — including within source roots.

### Auto-Excluded Directories

Always excluded (in addition to config `paths.exclude`):
`vendor/`, `node_modules/`, `dist/`, `build/`, `__pycache__/`, `.git/`, and patterns from `.gitignore`.

---

## Polyglot Detection

Count file extensions across detected source paths. Any secondary language >10% of source files → add to `language.additional`.

For polyglot repos:
- Helper scripts run once per language
- Benchmarks loaded for each language
- Metrics grouped by language where they differ

---

## Test Runner Detection

Detection order:

1. Check framework config files: `pytest.ini`, `jest.config.*`, `vitest.config.*`, `.mocharc.*`, `phpunit.xml`
2. Check `package.json` → `scripts.test`
3. Fall back to language default (see Language Defaults table)
4. If ambiguous, ask user

---

## Config File Format

Read `.codex/audit.yaml` (or `.yml`) from project root. All fields are optional — auto-detected defaults fill gaps.

```yaml
# .codex/audit.yaml — all fields optional
project:
  name: "My Project"           # auto: from package.json, Cargo.toml, etc.
  engine: "Godot 4.6"          # auto: from project.godot, or omitted

paths:
  source:                      # auto: detected from project structure
    - "src/"
  tests:
    - "tests/"
  exclude:                     # globs to skip in all measurements
    - "vendor/"
    - "node_modules/"

language:
  primary: "python"            # auto: from dominant file extension
  additional: ["typescript"]   # auto: if >10% of source files
  extension: ".py"

testing:
  runner: "pytest --tb=short"
  timeout: 60000

architecture:
  boundaries: []               # {name, pattern, path, expected} rules

criteria_priority: []          # pin top N criteria priorities
```

Merge order: `auto-detected defaults ← config overrides` — config always wins where specified.
