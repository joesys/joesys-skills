# TypeScript Tooling Profile

Tools specific to TypeScript/JavaScript projects. Read this alongside `shared/tooling/general.md`. All tools follow the safety rules, detection flow, and execution protocol in `shared/tooling-registry.md`.

---

## 1. Tools

### tsc

| Field | Value |
|:--|:--|
| **Category** | Static Analyzer / Type Checker |
| **Tier** | 1 |
| **Detection** | `tsconfig.json` |
| **Availability** | `which tsc` (Unix) / `where tsc` (Windows), or `npx tsc --version` |
| **Report-only invocation** | `npx tsc --noEmit --pretty` |
| **Scope-to-files** | Not supported — tsc always checks the full project based on `tsconfig.json`; individual file arguments bypass config and produce incomplete results |
| **Output format** | `file(line,col): error TSxxxx: message` |
| **Recommendation** | Best-in-class. The authoritative TypeScript type checker. No alternatives exist for type correctness. Enable `"strict": true` in `tsconfig.json` for maximum coverage. |

**`--noEmit` is critical** — it prevents any `.js` / `.d.ts` output files from being written. The command is safe to run anywhere as long as this flag is present.

---

### eslint

> ⚠️ **DANGER: auto-modifies** — `--fix` rewrites source files. **NEVER** pass `--fix`. Always use `--no-fix`.

| Field | Value |
|:--|:--|
| **Category** | Linter |
| **Tier** | 2 |
| **Detection** | `eslint.config.js`, `eslint.config.mjs`, `eslint.config.cjs` (flat config); `.eslintrc`, `.eslintrc.js`, `.eslintrc.cjs`, `.eslintrc.yaml`, `.eslintrc.yml`, `.eslintrc.json` (legacy); `eslintConfig` key in `package.json` |
| **Availability** | `which eslint` (Unix) / `where eslint` (Windows), or `npx eslint --version` |
| **Report-only invocation** | `npx eslint --no-fix --format json {source_paths}` |
| **Scope-to-files** | Pass file or directory paths as positional arguments: `npx eslint --no-fix --format json src/ lib/` |
| **Output format** | JSON array of file result objects. Each object has a `filePath` string and a `messages` array. Each message contains: `ruleId` (string), `severity` (1 = warning, 2 = error), `message` (string), `line` (number), `column` (number). |
| **Recommendation** | Best-in-class. Dominant JavaScript/TypeScript linter with the largest rule and plugin ecosystem. Supports TypeScript-aware rules via `@typescript-eslint`. |

---

### Biome

> ⚠️ **DANGER (format only): auto-modifies** — `biome format` writes files unless `--no-write` / no `--write` is passed. The `lint` subcommand is read-only by default.

| Field | Value |
|:--|:--|
| **Category** | Linter + Formatter |
| **Tier** | 2–3 (Tier 2 as linter, Tier 3 as formatter) |
| **Detection** | `biome.json`, `biome.jsonc` |
| **Availability** | `which biome` (Unix) / `where biome` (Windows), or `npx @biomejs/biome --version` |
| **Report-only invocation** | Lint: `npx @biomejs/biome lint --no-errors-on-unmatched {source_paths}` — read-only by default. Format check: `npx @biomejs/biome format --no-errors-on-unmatched {source_paths}` — **NEVER** pass `--write`. |
| **Scope-to-files** | Pass file or directory paths as positional arguments after the subcommand. |
| **Output format** | Default: human-readable diagnostics to stderr, exit code signals outcome. With `--reporter=json`: JSON object containing a `diagnostics` array with `category`, `severity`, `description`, and `location` (file, span). |
| **Recommendation** | Popular OSS alternative to the eslint + prettier combination. Fast (Rust-based), zero config to start, unified lint+format in one tool. Smaller rule ecosystem than eslint. Good choice for greenfield projects or repos replacing both eslint and prettier. |

---

### prettier

> ⚠️ **DANGER: auto-modifies** — prettier rewrites files when run without `--check`. **NEVER** omit `--check`. **NEVER** pass `--write`.

| Field | Value |
|:--|:--|
| **Category** | Formatter |
| **Tier** | 3 |
| **Detection** | `.prettierrc`, `.prettierrc.js`, `.prettierrc.cjs`, `.prettierrc.mjs`, `.prettierrc.json`, `.prettierrc.yaml`, `.prettierrc.yml`, `.prettierrc.toml`, `prettier.config.js`, `prettier.config.cjs`, `prettier.config.mjs`; `prettier` key in `package.json` |
| **Availability** | `which prettier` (Unix) / `where prettier` (Windows), or `npx prettier --version` |
| **Report-only invocation** | `npx prettier --check {source_paths}` |
| **Scope-to-files** | Pass file or directory paths (or glob patterns) as positional arguments: `npx prettier --check src/ "**/*.ts"` |
| **Output format** | Human-readable list of files that would be reformatted, one per line. Exit code 0 = all files already formatted; exit code 1 = one or more files need formatting. No structured JSON output available. |
| **Recommendation** | Best-in-class formatter. Opinionated and intentionally non-configurable in most respects — this is a feature, not a limitation. Eliminates formatting debates. Works across JS, TS, JSON, CSS, HTML, Markdown, and more. |

---

### Semgrep TypeScript

> ⚠️ **DANGER: auto-modifies** — Semgrep supports autofix rules that rewrite source. **NEVER** omit `--no-autofix`.

| Field | Value |
|:--|:--|
| **Category** | Security Scanner |
| **Tier** | 4 |
| **Detection** | `.semgrep.yml`, `.semgrep/` directory, `semgrep` in CI config files |
| **Availability** | `which semgrep` (Unix) / `where semgrep` (Windows) |
| **Report-only invocation** | `semgrep scan --config auto --lang typescript --json --no-autofix --quiet {source_paths}` |
| **Scope-to-files** | Pass file or directory paths as positional arguments after flags. |
| **Output format** | JSON object with a `results` array. Each result contains: `check_id` (rule), `path` (file), `start.line` (line number), `extra.severity` (severity level), `extra.message` (explanation). |
| **Recommendation** | Best-in-class for security pattern scanning. `--lang typescript` scopes the rule set to TypeScript-aware patterns. Free CLI; paid CI platform (Semgrep Cloud). Use alongside tsc and eslint — Semgrep catches security patterns those tools miss. |

---

## 2. Build-Integrated Analysis Patterns

These patterns indicate that static analysis is woven into the development workflow. Detect them during **Step 5 — Detect Build-Integrated Analysis**.

| Pattern | Location | Signal |
|:--|:--|:--|
| `"strict": true` | `tsconfig.json` | Maximum type-checking coverage enabled |
| `"noEmit": true` | `tsconfig.json` | Type checking without output — safe to run anywhere |
| `tsc --noEmit` in a script | `package.json` → `scripts` | Type check integrated into build/CI |
| `"lint"` script calling eslint | `package.json` → `scripts` | Linting integrated into workflow |
| `"format"` / `"format:check"` script | `package.json` → `scripts` | Formatter check integrated into workflow |
| `lint-staged` key | `package.json` or `.lintstagedrc` | Pre-commit scoped linting on staged files |
| `.husky/` directory | Repository root | Pre-commit hook runner present |
| `eslint` or `biome` in CI workflow | `.github/workflows/*.yml` etc. | Linting enforced in CI pipeline |

---

## 3. Gap Analysis

When detected tooling is absent for a category, recommend using this table.

| If Missing | Best-in-Class | Popular OSS |
|:--|:--|:--|
| No type checking | **tsc** — built-in, enable `"strict": true` + `"noEmit": true` | — (tsc is already free/included) |
| No linter | **eslint** — dominant, huge ecosystem, typescript-eslint support | **Biome** — fast, unified lint+format |
| No formatter | **prettier** — universal, opinionated, zero debate | **Biome** — also formats, one less tool |
| No security scanner | **Semgrep** — TypeScript-aware rules, free CLI | — (Semgrep CLI is already free/OSS) |
