# Cross-Language Tooling Profile

Tools and patterns that apply across multiple languages. Read this file alongside the relevant language-specific profile (`shared/tooling/<language>.md`). All tools listed here follow the safety rules, detection flow, and execution protocol defined in `shared/tooling-registry.md`.

---

## 1. Tools

### Semgrep (multi-language)

| Field | Value |
|:--|:--|
| **Category** | Security Scanner / Linter (configurable) |
| **Tier** | 4 (security) or 2 (linting, with custom rules) |
| **Detection** | `.semgrep.yml`, `.semgrep/` directory, `semgrep` in CI config files |
| **Availability** | `which semgrep` (Unix) / `where semgrep` (Windows) |

**Report-only invocation:**

```
semgrep scan --config auto --json --no-autofix --quiet {source_paths}
```

| Flag | Purpose |
|:--|:--|
| `--no-autofix` | **CRITICAL** — prevents source modification |
| `--json` | Structured output for programmatic consumption |
| `--quiet` | Suppresses progress bars and non-essential output |

**Scope-to-files:** Pass file paths as positional arguments after flags.

**Output format:** JSON object with a `results` array. Each result contains:

| Key | Description |
|:--|:--|
| `check_id` | Rule identifier |
| `path` | File path |
| `start.line` | Line number |
| `extra.severity` | Severity level |
| `extra.message` | Human-readable explanation |

**Recommendation:** Best-in-class for multi-language security scanning. Covers 30+ languages with a single tool. Free CLI; paid CI platform (Semgrep Cloud).

---

### SonarQube / SonarCloud

| Field | Value |
|:--|:--|
| **Category** | Linter / Security Scanner (multi-category) |
| **Tier** | 2 / 4 |
| **Detection** | `sonar-project.properties`, `.sonarcloud.properties`, `sonar` in CI config |
| **Availability** | Not a local CLI tool — CI-integrated only. Detect config presence only. |

**Report-only invocation:** N/A (analysis runs in CI or SonarQube server; no local CLI execution).

**Recommendation:** Best-in-class for enterprise CI-integrated analysis. Deep multi-language analysis with quality gates. SonarCloud is free for open source projects.

---

## 2. Build-Integrated Analysis Patterns

These patterns indicate that static analysis is already woven into the project's development workflow. The orchestrator detects them during **Step 5 — Detect Build-Integrated Analysis** and records them for grading.

### Pre-Commit Hooks

**pre-commit framework:**

- **Detection:** `.pre-commit-config.yaml` exists in the repository root.
- **Common hooks to look for:**
  - Python: `ruff`, `black`, `mypy`, `flake8`, `isort`
  - JavaScript/TypeScript: `eslint`, `prettier`
  - C/C++: `clang-format`, `clang-tidy`
  - Rust: `rustfmt`, `clippy`
  - Security: `gitleaks`, `detect-secrets`

**Husky (JS ecosystem):**

- **Detection:** `.husky/` directory exists.
- Typically combined with `lint-staged` for efficient per-commit checks.

**lint-staged:**

- **Detection:** `lint-staged` key in `package.json`, or `.lintstagedrc` / `lint-staged.config.js` file.
- Runs linters/formatters on staged files only — efficient pre-commit strategy.

### CI-Integrated Analysis

Look for tool names and patterns in CI workflow files:

| CI System | Config Location |
|:--|:--|
| GitHub Actions | `.github/workflows/*.yml` |
| GitLab CI | `.gitlab-ci.yml` |
| Jenkins | `Jenkinsfile` |
| CircleCI | `.circleci/config.yml` |

**Patterns to detect:**

| Pattern | Signal |
|:--|:--|
| `sonar` in CI config | SonarQube / SonarCloud integration |
| `codecov` or `coveralls` | Coverage reporting (related quality signal) |
| `dependabot.yml` or `renovate.json` | Automated dependency updates |
| `semgrep` in CI config | Security scanning in pipeline |
| `super-linter` or `megalinter` | Aggregated multi-linter runs |

### Editor Integration

| Marker | Signal |
|:--|:--|
| `.vscode/extensions.json` with linter/formatter extensions | Team-recommended editor tooling |
| `.editorconfig` | Cross-editor formatting consistency |

These are informational signals — they indicate team intent around code quality but do not produce executable findings.

---

## 3. Gap Analysis

When the orchestrator identifies missing tooling categories, recommend alternatives using this table.

| If Missing | Best-in-Class | Popular OSS |
|:--|:--|:--|
| No cross-language security scanner | **Semgrep** — custom rules, 30+ languages, free CLI | -- (Semgrep CLI is already free/OSS) |
| No CI-integrated analysis | **SonarCloud** — free for open source, deep analysis | **Super-Linter** — GitHub Action, aggregates many linters, free |
| No pre-commit hooks | **pre-commit framework** — language-agnostic, huge hook ecosystem | **Husky + lint-staged** — JS ecosystem, simpler setup |
| No dependency update automation | **Renovate** — highly configurable, multi-platform | **Dependabot** — GitHub-native, zero config |
| No secret detection | **GitGuardian** — real-time, paid | **gitleaks** — fast, free, CI-friendly |
