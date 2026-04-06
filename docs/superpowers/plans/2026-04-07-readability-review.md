# Readability Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a story-readability code review system with three integration points: standalone `/readability-review` skill, 7th domain in `code-review`, and 12th criterion in `codebase-audit`.

**Architecture:** A single shared principle file (`shared/story-readability.md`) defines 8 weighted dimensions of narrative code quality. Three consumers read it: a standalone skill with numeric scoring and fix dispatch, a new subagent in the existing code-review pipeline, and a new criterion in the codebase-audit pipeline. Preferences are customizable per-project via the shared skill-context system.

**Tech Stack:** Markdown skill files, Claude Code plugin system (plugin.json/marketplace.json), Agent tool for subagent dispatch, shared infrastructure (`shared/review-common.md`, `shared/skill-context.md`).

---

## File Structure

### New Files

| File | Responsibility |
|---|---|
| `shared/story-readability.md` | Core principle file — philosophy, 8 dimensions with weights, calibration examples, scoring protocol, language-aware notes. Single source of truth. |
| `skills/readability-review/SKILL.md` | Standalone skill — invocation parsing, scope resolution, single-subagent analysis, 3-layer report output, fix dispatch, preferences integration. |
| `skills/codebase-audit/principles/story-readability.md` | Thin criterion wrapper — references shared file, adds audit-specific grading rubric and measurement guidance. |

### Modified Files

| File | Change Summary |
|---|---|
| `skills/code-review/SKILL.md` | Add 7th subagent to roster, update dispatch count (6→7, 7→8 with cross-model), add deduplication note for Clean Code overlap, update failure handling counts. |
| `skills/codebase-audit/SKILL.md` | Add `story-readability` to valid criterion names, add agent mapping, update console display, update criterion count references. |
| `skills/codebase-audit/benchmarks/general.md` | Add Story Readability section with cross-language narrative benchmarks. |
| `skills/codebase-audit/benchmarks/cpp.md` | Add Story Readability section with C++-specific benchmarks. |
| `skills/codebase-audit/benchmarks/python.md` | Add Story Readability section with Python-specific benchmarks. |
| `skills/codebase-audit/benchmarks/typescript.md` | Add Story Readability section with TypeScript-specific benchmarks. |
| `skills/codebase-audit/benchmarks/rust.md` | Add Story Readability section with Rust-specific benchmarks. |
| `skills/codebase-audit/benchmarks/go.md` | Add Story Readability section with Go-specific benchmarks. |
| `skills/codebase-audit/benchmarks/javascript.md` | Add Story Readability section with JavaScript-specific benchmarks. |
| `skills/codebase-audit/benchmarks/csharp.md` | Add Story Readability section with C#-specific benchmarks. |
| `skills/codebase-audit/benchmarks/gdscript.md` | Add Story Readability section with GDScript-specific benchmarks. |
| `skills/codebase-audit/references/agent-prompts.md` | Update author agent prompt to read 12 principle files (add story-readability.md). |
| `skills/codebase-audit/references/output-schemas.md` | Add `story_readability` to metrics.json schema. |
| `skills/codebase-audit/templates/analysis-template.md` | Update criterion count reference from 11 to 12. |
| `.claude-plugin/plugin.json` | Add `readability-review` keyword, bump version. |
| `.claude-plugin/marketplace.json` | Update description to mention readability review, bump version. |

---

### Task 1: Create Core Principle File — `shared/story-readability.md`

**Files:**
- Create: `shared/story-readability.md`

This is the foundation everything else depends on. It defines the 8 dimensions, weights, scoring protocol, calibration examples, and language-aware notes.

- [ ] **Step 1: Write the philosophy and dimension definitions**

Create `shared/story-readability.md` with the following content:

```markdown
# Story Readability

Code should read like a story. Short functions. Self-documenting names. Each function reads like a narrative of what it does:

```cpp
auto process_dawn_phase(World& world) -> void {
    collect_night_rewards(world);
    transfer_grace_to_hero(world);
    heal_injured_agents(world);
    process_immigration(world);
    generate_journal_entry(world);
}
```

No clever tricks. No dense one-liners. A stranger should read the code and understand the intent without comments.

This philosophy extends beyond absence of code smells. It asks: **does this code tell a coherent story?** Can a new developer scan a function and immediately understand its narrative — the beginning, the middle, the end — without diving into implementation details?

---

## The 8 Dimensions

### Default Weights

| # | Dimension | Weight | What It Measures |
|---|---|---|---|
| 1 | Narrative Flow | 20% | Does a function read top-to-bottom as a sequence of clear steps? Are logical phases separated by paragraph spacing? Do paired operations (begin/end, open/close) appear symmetrically? |
| 2 | Naming as Intent | 15% | Do names reveal *what* and *why* without needing to read the body? Are enums used over bools at call sites? Are call sites self-documenting? |
| 3 | Cognitive Chunking | 15% | Are logical phases of a function extracted into named steps, even when the extraction doesn't reduce complexity or duplication? Can a reader see the story's chapters at a glance? |
| 4 | Abstraction Consistency (SLAP) | 14% | Does each function operate at a single level of abstraction? Does the orchestrator avoid mixing high-level steps with low-level details? |
| 5 | Function Focus | 10% | One function, one job. Short enough to hold in your head (~20 lines of logic). Extraction adds clarity, not just indirection. |
| 6 | Structural Clarity | 10% | Flat control flow. Guard clauses and early returns for invalid states. Minimal nesting. No arrow anti-patterns. |
| 7 | Documentation Quality | 10% | Comments explain *why*, not *what*. No parrot comments. Business rationale and non-obvious constraints are documented. |
| 8 | No Clever Tricks | 6% | Absence of dense one-liners, bitwise hacks, ternary chains, negation puzzles (`!is_not_excluded`), and obscure idioms. A stranger can follow the logic without comments. |

**Total:** 100%. Top 4 dimensions (Narrative Flow, Naming, Cognitive Chunking, Abstraction Consistency) carry 64%.

These weights are defaults. Users can override them per-project via `.claude/skill-context/readability-review.md`.

---

## Dimension Details & Calibration

### 1. Narrative Flow (20%)

A function should read like a paragraph in a well-written book. Each step follows naturally from the last. Logical phases are visually separated. The reader never has to jump around to understand the sequence.

**Sub-signals:**
- **Paragraph spacing** — blank lines between logical phases, like paragraphs in prose
- **Symmetry** — paired operations (begin/end, open/close, acquire/release) appear together
- **Temporal ordering** — steps appear in the order they conceptually happen

#### Score 9–10: Exemplary

```python
def deploy_release(release, environment):
    validate_release_artifacts(release)
    run_pre_deploy_checks(environment)

    create_deployment_snapshot(environment)
    apply_database_migrations(release)
    roll_out_services(release, environment)

    verify_health_checks(environment)
    notify_team(release, environment)
```

Three clear phases (prepare → execute → confirm), separated by paragraph spacing. Temporal ordering matches the real deployment sequence. Symmetry: snapshot before changes, verify after.

#### Score 5–6: Adequate

```python
def deploy_release(release, environment):
    validate_release_artifacts(release)
    run_pre_deploy_checks(environment)
    create_deployment_snapshot(environment)
    apply_database_migrations(release)
    roll_out_services(release, environment)
    verify_health_checks(environment)
    notify_team(release, environment)
```

Same steps, but no paragraph spacing. The three phases blur together. A reader has to mentally group the steps.

#### Score 2–3: Poor

```python
def deploy_release(release, environment):
    notify_team(release, environment)  # notify first for visibility
    roll_out_services(release, environment)
    apply_database_migrations(release)
    validate_release_artifacts(release)
    create_deployment_snapshot(environment)
    verify_health_checks(environment)
    run_pre_deploy_checks(environment)
```

Temporal ordering is scrambled. Notification happens before deployment. Validation happens after rollout. The "story" makes no sense.

---

### 2. Naming as Intent (15%)

Names are the vocabulary of the story. A function call should read like a sentence. A variable should answer "what is this?" without needing to read its assignment. Call sites should be self-documenting.

**Sub-signals:**
- **Enums over bools** — `AgentRole::warrior` over `true` (boolean blindness)
- **Self-documenting call sites** — reading a function call tells you what it does without checking the signature

#### Score 9–10: Exemplary

```cpp
auto settler = recruit_settler(world, SettlerClass::farmer, Loyalty::high);
assign_to_village(settler, target_village, HousingPriority::immediate);
```

Every argument reads like prose. No guessing what `true` or `3` means.

#### Score 5–6: Adequate

```cpp
auto settler = recruit_settler(world, "farmer", true);
assign_to_village(settler, target_village, 1);
```

Function names are clear, but call sites are opaque. What does `true` mean? What is `1`?

#### Score 2–3: Poor

```cpp
auto s = rec(w, 2, true);
atv(s, tv, 1);
```

Single-letter variables, abbreviated function names, magic numbers. Nothing is readable.

---

### 3. Cognitive Chunking (15%)

Are logical phases of a function extracted into named steps, even when the extraction doesn't reduce complexity or duplication? The goal is *scannability* — a reader should see the story's chapters at a glance, without mentally parsing where one phase ends and the next begins.

This is distinct from Function Focus (which is about length) and Abstraction Consistency (which is about mixing levels). Cognitive Chunking says: even if a function is only 25 lines, if it contains two distinct *phases*, those phases should be named and separated.

#### Score 9–10: Exemplary

```cpp
auto make_world_config(uint64_t master_seed,
                       int32_t map_width,
                       int32_t map_height,
                       std::string initial_building) -> std::expected<WorldConfig, ConfigError>
{
    auto validation = validate_map_dimensions(map_width, map_height);
    if (!validation) {
        return std::unexpected(validation.error());
    }

    return WorldConfig{
        .master_seed = master_seed,
        .map_width = map_width,
        .map_height = map_height,
        .initial_building = std::move(initial_building),
    };
}
```

Two phases (validate → construct) are immediately visible. The reader can skip `validate_map_dimensions` and see the story: "validate, then build."

#### Score 5–6: Adequate

```cpp
auto make_world_config(uint64_t master_seed,
                       int32_t map_width,
                       int32_t map_height,
                       std::string initial_building) -> std::expected<WorldConfig, ConfigError>
{
    if (map_width <= 0) {
        return std::unexpected(ConfigError{/* ... */});
    }
    if (map_height <= 0) {
        return std::unexpected(ConfigError{/* ... */});
    }
    if (map_width > WorldConfig::max_map_dimension) {
        return std::unexpected(ConfigError{/* ... */});
    }
    if (map_height > WorldConfig::max_map_dimension) {
        return std::unexpected(ConfigError{/* ... */});
    }

    return WorldConfig{
        .master_seed = master_seed,
        .map_width = map_width,
        .map_height = map_height,
        .initial_building = std::move(initial_building),
    };
}
```

Correct code, but the validation and construction phases aren't chunked. A reader must scan all the guard clauses to understand "this is the validation part."

#### Score 2–3: Poor

```cpp
auto make_world_config(uint64_t seed, int32_t w, int32_t h, std::string b)
    -> std::expected<WorldConfig, ConfigError>
{
    if (w <= 0) return std::unexpected(ConfigError{/* ... */});
    if (h <= 0) return std::unexpected(ConfigError{/* ... */});
    if (w > WorldConfig::max_map_dimension) return std::unexpected(ConfigError{/* ... */});
    if (h > WorldConfig::max_map_dimension) return std::unexpected(ConfigError{/* ... */});
    return WorldConfig{seed, w, h, std::move(b)};
}
```

Dense one-liners, abbreviated parameters, no visual separation. The function compresses everything into a block of similar-looking lines.

---

### 4. Abstraction Consistency — SLAP (14%)

Every statement in a function should operate at the same level of abstraction. Mixing high-level orchestration with low-level details forces the reader to constantly shift mental gears.

#### Score 9–10: Exemplary

```python
def generate_monthly_report(company, month):
    transactions = fetch_transactions(company, month)
    summary = compute_financial_summary(transactions)
    charts = render_charts(summary)
    report = assemble_report(summary, charts)
    deliver_report(report, company.stakeholders)
```

Every line is at the same level: fetch, compute, render, assemble, deliver. No line drops down into SQL queries or pixel math.

#### Score 5–6: Adequate

```python
def generate_monthly_report(company, month):
    transactions = fetch_transactions(company, month)
    summary = compute_financial_summary(transactions)
    charts = render_charts(summary)

    html = f"<html><body><h1>{company.name} - {month}</h1>"
    html += summary.to_html()
    for chart in charts:
        html += f'<img src="{chart.path}" />'
    html += "</body></html>"

    send_email(company.stakeholders, "Monthly Report", html)
```

Starts at a high level (fetch, compute, render) then drops into HTML string concatenation. Two abstraction levels in one function.

#### Score 2–3: Poor

```python
def generate_monthly_report(company, month):
    conn = psycopg2.connect(os.environ["DB_URL"])
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM transactions WHERE company_id={company.id} AND month='{month}'")
    rows = cur.fetchall()
    total = sum(r[3] for r in rows)
    avg = total / len(rows) if rows else 0
    html = f"<html><body><h1>{company.name}</h1><p>Total: {total}, Avg: {avg}</p></body></html>"
    smtp = smtplib.SMTP("mail.example.com")
    smtp.sendmail("reports@example.com", [s.email for s in company.stakeholders], html)
```

Database cursors, raw SQL, arithmetic, HTML construction, and SMTP all in one function. Every line is at a different abstraction level.

---

### 5. Function Focus (10%)

One function, one job. Short enough to hold in your head (~20 lines of logic). Extraction must add clarity — do not create trivial wrappers that merely rename a built-in.

#### Score 9–10: Exemplary

Each function does one thing. The caller reads as a sequence of named steps. No function exceeds ~20 lines of logic.

#### Score 5–6: Adequate

Functions are mostly focused but some handle 2-3 related concerns. Lengths around 30-40 lines. Extractable phases exist but aren't split out.

#### Score 2–3: Poor

God functions spanning 100+ lines. Multiple responsibilities interleaved. Impossible to name the function accurately because it does too many things.

---

### 6. Structural Clarity (10%)

Flat control flow. Guard clauses at the top. Early returns for invalid states. The happy path flows straight down at the shallowest indentation level.

**Sub-signals:**
- **Early returns** — test for the invalid state and exit, rather than wrapping the happy path in a conditional
- **Guard clauses** — at the top of the function, before the main logic
- **Minimal nesting** — no more than 2-3 levels of indentation in the main logic

#### Score 9–10: Exemplary

```python
def process_order(order):
    if order is None:
        return Error("no order")
    if order.status != "pending":
        return Error("not pending")
    if not order.items:
        return Error("no items")

    total = compute_total(order.items)
    return Receipt(order, total)
```

Guards at top, happy path at bottom, flat.

#### Score 2–3: Poor

```python
def process_order(order):
    if order is not None:
        if order.status == "pending":
            if order.items:
                total = compute_total(order.items)
                return Receipt(order, total)
            else:
                return Error("no items")
        else:
            return Error("not pending")
    else:
        return Error("no order")
```

Arrow anti-pattern. Happy path buried at deepest nesting.

---

### 7. Documentation Quality (10%)

Comments should explain *why* a decision was made, not *what* the code does. No parrot comments. Business rationale, non-obvious constraints, and workaround context are documented.

#### Score 9–10: Exemplary

```python
# Business rule: loyalty discount applies only to customers who joined
# before the 2023 pricing restructure (see JIRA-4521).
discount = calculate_loyalty_discount(customer)
```

Comment explains the business rule that isn't visible in the code.

#### Score 2–3: Poor

```python
# Get the user
user = get_user(user_id)
# Check if active
if user.is_active:
    # Calculate discount
    discount = calculate_discount(user)
```

Every comment restates the code. No value added. Maintenance cost increased.

---

### 8. No Clever Tricks (6%)

A stranger should be able to follow the logic without documentation. No dense one-liners. No bitwise hacks for non-bitwise problems. No chained ternaries. No double-negative conditions.

**Sub-signals:**
- **Negation avoidance** — `if (is_eligible)` over `if (!is_not_excluded)`
- **No double-negative conditions**
- **No dense compound expressions** that require mental simulation

#### Score 9–10: Exemplary

```python
if user.is_eligible and user.wants_notifications:
    send_notification(user)
```

Reads like English. No mental gymnastics.

#### Score 2–3: Poor

```python
if not (not user.excluded or user.opt_out) and (user.flags & 0x04):
    send_notification(user)
```

Double negation, bitwise flag check, compound boolean. Requires pen and paper to evaluate.

---

## Scoring Protocol

### Per-Dimension Scoring

Each dimension is scored 1–10, anchored by the calibration examples above:

| Score Range | Meaning |
|---|---|
| 9–10 | Exemplary — code reads like well-written prose |
| 7–8 | Good — story is clear with minor rough spots |
| 5–6 | Adequate — readable but doesn't flow naturally |
| 3–4 | Poor — requires effort to follow the narrative |
| 1–2 | Unreadable — no narrative structure discernible |

### Weighted Aggregation

Each dimension contributes `(score / 10) * weight_points` to the total, where `weight_points` is the weight expressed as points out of 100 (e.g., 20% = 20 points). A dimension scored 8/10 with weight 20% contributes `(8/10) * 20 = 16`. A perfect 10/10 across all dimensions yields 100.

### Grade Mapping

| Score | Grade |
|---|---|
| 95–100 | A+ |
| 88–94 | A |
| 80–87 | B+ |
| 72–79 | B |
| 64–71 | C+ |
| 56–63 | C |
| 45–55 | D |
| 0–44 | F |

---

## Language-Aware Notes

The dimensions are universal. How they manifest differs by language.

- **C++:** No universal formatter. Paragraph spacing is a conscious choice. Template metaprogramming can violate "No Clever Tricks" — flag when simpler alternatives exist. Trailing return types (`auto f() -> T`) are idiomatic, not clever. Designated initializers (`.field = value`) improve Naming as Intent at call sites.
- **Python:** List comprehensions are idiomatic, not clever — unless nested. PEP 8 enforces some structural clarity. `black` / `ruff` handle formatting; story readability focuses on what formatters can't fix. Type hints are part of the story — they document intent.
- **Go:** `gofmt` enforces formatting. Short variable names in short scopes are idiomatic (not a naming violation). Exported symbols need GoDoc comments. Error handling via `if err != nil` is structural — judge by how well the happy path reads around it, not by the pattern itself.
- **Rust:** Pattern matching is idiomatic, not clever. `rustfmt` handles formatting. Lifetime annotations can hurt narrative flow — flag excessive lifetime complexity. The `?` operator improves narrative flow by reducing error-handling noise.
- **TypeScript:** `any` usage breaks "Naming as Intent" — types are part of the story. Prefer explicit types over inference when it aids readability. Template literal types can be clever — flag when simpler alternatives exist.
- **JavaScript:** Same as TypeScript minus the type system. Prototype chains and `this` binding can be clever tricks. Prefer class syntax or plain functions.
- **C#:** LINQ expressions are idiomatic. `var` is acceptable when the type is obvious from the right-hand side. Async/await patterns should follow the same narrative flow principles.
- **GDScript:** Signal/slot patterns are idiomatic. `_ready()`, `_process()`, `_physics_process()` are Godot conventions — don't flag as cryptic names. `@export` and `@onready` annotations are idiomatic.
```

- [ ] **Step 2: Verify the file was created correctly**

Run: `wc -l shared/story-readability.md`
Expected: ~350-400 lines

- [ ] **Step 3: Commit**

```bash
git add shared/story-readability.md
git commit -m "feat(shared): add story-readability principle file — 8 dimensions with calibration examples"
```

---

### Task 2: Create Standalone `/readability-review` Skill

**Files:**
- Create: `skills/readability-review/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

Create `skills/readability-review/SKILL.md` with the following content:

```markdown
---
name: readability-review
version: "1.0.0"
description: "Use when the user invokes /readability-review to grade code on 8 story-readability dimensions with numeric scoring (0-100), letter grades, and concrete before/after refactoring suggestions."
---

# Readability Review Skill

Grade code on how well it "reads like a story" using 8 weighted dimensions. Produces a numeric score (0-100) mapped to a letter grade, with thematic findings and file-by-file breakdown including concrete refactoring suggestions.

## Invocation

Parse the user's `/readability-review` arguments to determine mode and scope:

| Invocation | Mode | Scope |
|---|---|---|
| `/readability-review` | Branch diff (default) | Current branch vs. fork point |
| `/readability-review src/utils/` | Directory scan | All files recursively in specified directory |
| `/readability-review --file src/main.cpp` | Single file | One specific file |
| `/readability-review --pr 123` | PR review | Files changed in a GitHub PR |
| `/readability-review --commit abc123` | Commit review | Files changed in a specific commit |
| `/readability-review --min-score 70` | Score filter | Combinable with any mode — only show files below threshold |

Arguments are combinable. Examples:
- `/readability-review --pr 42 --min-score 60` — review PR #42, only show files scoring below 60
- `/readability-review src/world/ --min-score 70` — scan directory, only flag files below 70

If the invocation is ambiguous or the argument is unrecognizable, ask the user to clarify before proceeding.

---

## Phase 0: Scope Resolution

### 0.1 Load User Preferences

Read `shared/skill-context.md` for the full protocol. In brief:

1. Read `.claude/skill-context/preferences.md` — if missing, invoke `/preferences` (streamlined).
2. Read `.claude/skill-context/readability-review.md` (if it exists) for skill-specific preferences.

**How preferences shape this skill:**

| Preference | Effect on Readability Review |
|---|---|
| Detail level: concise | Shorter findings, fewer calibration references |
| Detail level: detailed | Include dimension philosophy, explain scoring rationale |
| Assumed knowledge: beginner | Explain what each dimension means and why it matters |
| Assumed knowledge: expert | Skip dimension explanations, focus on specific findings |
| Skill-specific: custom weights | Override default dimension weights from `shared/story-readability.md` |
| Skill-specific: min-score default | Override the default `--min-score` threshold |

Pass relevant preferences to the analysis subagent in Phase 1.

### 0.2 Base Branch Detection

Read `shared/review-common.md` § Base Branch Detection.

### 0.3 File Gathering

Read `shared/review-common.md` § File Gathering.

### 0.4 Content Loading

Read the **full content** of every file in scope — not just the diff. Story readability requires function-level context to assess narrative flow, abstraction consistency, and cognitive chunking. A diff alone cannot reveal whether a function tells a coherent story.

Also capture the **diff itself** if in branch-diff or PR mode, so the subagent can focus analysis on what actually changed while having full files for context.

### 0.5 Target Language Detection

Read `shared/review-common.md` § Target Language Detection.

---

## Phase 1: Analysis

Dispatch a **single subagent** via the Agent tool with `model: "opus"`.

No cross-model dispatch — story readability grading is calibrated to the principle file's specific taste and calibration examples. A second model without that calibration would score against a different standard.

No static analysis tooling — this is a qualitative, judgment-based review.

### Subagent Prompt

```
You are a senior code readability reviewer specializing in narrative code quality.

## Instructions
1. Read the principle file at: shared/story-readability.md
   (This file is relative to the project root — find and read it first.)
2. For each file, score all 8 dimensions on a 1-10 scale using the calibration
   examples as anchors.
3. Compute the weighted score per file using the weights in the principle file
   (or custom weights if provided below).
4. For each finding (any dimension scoring 7 or below), provide a concrete
   before/after refactoring suggestion in <TARGET_LANGUAGE>.
5. All code examples MUST be in <TARGET_LANGUAGE>.

{IF_CUSTOM_WEIGHTS}
## Custom Dimension Weights
Use these weights instead of the defaults in the principle file:
{CUSTOM_WEIGHTS}
{END_IF}

## User Preferences
{PREFERENCES}

## Files Under Review
<FILES_CONTENT>

{IF_DIFF_AVAILABLE}
## Diff Context
<DIFF_CONTENT>
Focus analysis on changed code, but use the full file for context.
{END_IF}

## Output Format

For EACH file, output:

### <filename>

**Dimension Scores:**
| # | Dimension | Score | Key Observation |
|---|---|---|---|
| 1 | Narrative Flow | X/10 | Brief note |
| 2 | Naming as Intent | X/10 | Brief note |
| 3 | Cognitive Chunking | X/10 | Brief note |
| 4 | Abstraction Consistency | X/10 | Brief note |
| 5 | Function Focus | X/10 | Brief note |
| 6 | Structural Clarity | X/10 | Brief note |
| 7 | Documentation Quality | X/10 | Brief note |
| 8 | No Clever Tricks | X/10 | Brief note |

**Weighted Score:** XX/100 (Grade)

**Findings:**

For each dimension scoring 7 or below:

#### [Dimension Name] — [Specific Issue]
**Score impact**: What this dimension scored and why
**Location**: `file.ext:line_number`
**Before**:
(code block in target language)
**After**:
(code block in target language)
**Why this improves the story**: Explanation of how the refactoring makes the code read better

If a file scores 8+ on all dimensions, output:
"All dimensions score well. This file reads like a clear story."
```

### Large Scope Handling

If the file list exceeds **30 files**, batch them into groups of roughly 15. Process batches sequentially — dispatch one subagent per batch. Aggregate scores across all batches for the final report.

---

## Phase 2: Report

Present the synthesized report in three layers.

### Layer 1: Scorecard

Print a summary table directly in the conversation:

```
╔═══════════════════════════════════════════════════╗
║  READABILITY REVIEW — {scope}                     ║
║  {Language} · {N} files · {Date}                  ║
╠═══════════════════════════════════════════════════╣
║  Story Score: {score}/100 ({grade})               ║
╠═══════════════════════════════════════════════════╣
║  #  Dimension              Score  Weight  Grade   ║
║  ── ────────────────────── ────── ─────── ─────── ║
║  1  Narrative Flow         {s}/10  20%    {grade} ║
║  2  Naming as Intent       {s}/10  15%    {grade} ║
║  3  Cognitive Chunking     {s}/10  15%    {grade} ║
║  4  Abstraction Consistency{s}/10  14%    {grade} ║
║  5  Function Focus         {s}/10  10%    {grade} ║
║  6  Structural Clarity     {s}/10  10%    {grade} ║
║  7  Documentation Quality  {s}/10  10%    {grade} ║
║  8  No Clever Tricks       {s}/10   6%    {grade} ║
╠═══════════════════════════════════════════════════╣
║  Top opportunity: {dimension} in {file}           ║
║  Strongest: {dimension} across {scope}            ║
╚═══════════════════════════════════════════════════╝
```

Dimension scores are averaged across all files (weighted by file LOC if files vary significantly in size). Individual dimension grades use the same grade mapping as overall.

If `--min-score` was specified, note how many files were filtered out: "Showing {N} of {M} files (filtered by --min-score {threshold})."

### Layer 2: Findings Summary

A few paragraphs describing thematic patterns:
- What's working well across the codebase
- What recurring issues drag the score down
- The highest-impact improvements (which dimensions, which files)
- Any patterns that span multiple files (e.g., "boolean blindness is endemic in the API layer")

### Layer 3: File-by-File Breakdown

For each file (ordered by score ascending — worst first):

```
### {filename} — {score}/100 ({grade})

| Dimension | Score |
|---|---|
| Narrative Flow | {s}/10 |
| ... | ... |

**Findings:**

#### [Dimension] — [Issue]
**Location**: `file:line`
**Before**: (code)
**After**: (code)
**Why this improves the story**: ...
```

If `--min-score` was specified, only files below the threshold appear in this section.

---

## Phase 3: Fix Offer

After the report:

> "Want me to refactor to improve the story score? I can fix all findings, or you can pick specific files or dimensions."

Wait for the user's response:

- **"All"** or **"fix all"**: Dispatch fix agents for all findings
- **Specific files**: "Fix src/world.cpp and src/agent.cpp"
- **Specific dimensions**: "Fix all Cognitive Chunking issues"
- **"No"**: End the review

### Fix Dispatch

- Group fixes by **file independence** — fixes in unrelated files can be dispatched in parallel via the Agent tool
- Fixes in the **same file** must be applied sequentially to avoid conflicts
- Each fix agent receives: the finding details (dimension, location, before/after, reasoning) and applies the refactoring using the Edit tool
- Fix agents must verify the before-code still matches (code may have shifted since analysis)
- Always spawn fix agents with `model: "opus"`

### Post-Fix Summary

After fixes are applied:
- List of files modified with a brief description of each change
- Number of findings addressed vs. total findings
- Estimated score improvement (qualitative — "expect +8-12 points based on the refactoring")
- Suggest re-running `/readability-review` to verify the improvement

---

## First Run Behavior

On first invocation, if `.claude/skill-context/readability-review.md` does not exist:

1. Use default weights from `shared/story-readability.md`
2. After the report, ask: "These are the default dimension weights. Want to customize them for this project?"
3. If yes, write to `.claude/skill-context/readability-review.md` with the user's preferred weights
4. If no, proceed — defaults apply until explicitly changed via `/preferences readability-review`

---

## Guardrails

Read `shared/review-common.md` § Shared Guardrails for the base constraints.

Additional readability-review-specific guardrails:

1. **Calibration-anchored scoring**: Every score must be justifiable by reference to the calibration examples in the principle file. Do not assign scores based on vibes.
2. **Language-aware judgment**: Consult the Language-Aware Notes section of the principle file. Idiomatic patterns in the target language are not violations (e.g., list comprehensions in Python, `?` operator in Rust).
3. **Before/after required**: Every finding must include a concrete refactoring suggestion with before/after code. Vague advice ("improve naming") is not acceptable.
4. **No severity inflation**: Story readability concerns are maintainability improvements. Do not frame them as critical bugs or security issues.
5. **Context matters**: Test code follows different standards. Prefer DAMP over DRY in tests. Prototype code may intentionally sacrifice readability for speed.

---

## Error Handling

Read `shared/review-common.md` § Shared Error Handling for common errors.

Additional readability-review-specific errors:

| Error | Action |
|---|---|
| Analysis subagent fails | Report: "Analysis failed — could not complete readability review. Please try again." |
| No files in scope | "No files found in the specified scope. Check the path and try again." |
| All files above --min-score | "All {N} files score above {threshold}. No findings to report." |
| Fix agent fails | Report which fixes failed, suggest manual application. |
```

- [ ] **Step 2: Verify the directory and file exist**

Run: `ls -la skills/readability-review/`
Expected: `SKILL.md` present

- [ ] **Step 3: Commit**

```bash
git add skills/readability-review/SKILL.md
git commit -m "feat(skills): add standalone /readability-review skill — 8-dimension story grading"
```

---

### Task 3: Create `codebase-audit` Criterion Principle File

**Files:**
- Create: `skills/codebase-audit/principles/story-readability.md`

- [ ] **Step 1: Write the thin criterion definition**

Create `skills/codebase-audit/principles/story-readability.md`:

```markdown
# Story Readability

## Definition

Story Readability measures how well code reads as a coherent narrative. It goes beyond mechanical readability (naming conventions, comment density, nesting depth) to assess whether a developer can scan a function and immediately understand its story — the beginning, middle, and end — without diving into implementation details.

This criterion is separate from Readability (criterion 7), which measures mechanical parsing ease. Story Readability measures narrative quality.

## Core Reference

Read `shared/story-readability.md` for the full dimension definitions, weights, calibration examples, and scoring protocol. This file adds audit-specific measurement guidance and grading rubric.

## Concrete Signals

**Positive signals:**
- Functions read as sequences of named, well-ordered steps
- Paragraph spacing separates logical phases
- Call sites are self-documenting (enums over bools, descriptive arguments)
- Logical phases are extracted into named chunks even without duplication
- Each function operates at a single level of abstraction
- Guard clauses and early returns keep the happy path flat
- Comments explain business rationale, not code mechanics

**Negative signals:**
- Functions mix high-level orchestration with low-level details
- No visual separation between logical phases
- Boolean blindness at call sites (`spawn(world, true, false, true)`)
- Long functions with multiple interleaved responsibilities
- Deep nesting burying the happy path
- Parrot comments that restate what the code does
- Dense one-liners, double negatives, chained ternaries

## Measurement Guidance

| Metric | How to Measure | Source |
|---|---|---|
| Narrative flow score | Qualitative assessment of function-level story structure | Author agent + `shared/story-readability.md` calibration |
| Naming intent score | Check for boolean blindness, self-documenting call sites | Author agent qualitative |
| Cognitive chunking score | Check if multi-phase functions are extracted into named steps | Author agent qualitative |
| Abstraction consistency | Check for SLAP violations — mixed abstraction levels | Author agent qualitative |
| Average function length | Quantitative — shorter functions correlate with focus | `compute_structure.py` |
| Max nesting depth | Quantitative — deep nesting hurts structural clarity | `compute_structure.py` |
| Comment quality ratio | Qualitative — % of comments that explain "why" vs "what" | Author agent qualitative |

**Quantitative floor:** The Structural and Quality agent metrics constrain the qualitative scores:

| Quantitative Signal | Dimension Cap |
|---|---|
| Average function length > 50 lines | Function Focus capped at 4/10 |
| Max nesting depth > 6 | Structural Clarity capped at 4/10 |
| Comment density < 2% | Documentation Quality capped at 5/10 |
| Naming convention violations > 20% of identifiers | Naming as Intent capped at 5/10 |

## Grading Rubric

| Grade | Criteria |
|---|---|
| A+ | Exemplary narrative quality. Functions read like well-written prose. All 8 dimensions score 9+. Calibration: comparable to the `process_dawn_phase` gold standard. |
| A | Strong narrative structure. Most functions tell clear stories. Minor rough spots in 1-2 dimensions. Weighted score 88-94. |
| B | Generally readable with identifiable narrative structure. Some functions mix abstraction levels or lack cognitive chunking. Weighted score 72-87. |
| C | Mixed quality. Some modules tell clear stories, others require effort to follow. Weighted score 56-71. |
| D | Poor narrative structure. Functions frequently mix concerns, naming is inconsistent, minimal chunking. Weighted score 45-55. |
| F | No discernible narrative structure. Dense, monolithic functions. Cryptic naming. No documentation. Weighted score below 45. |

## Language-Aware Notes

See `shared/story-readability.md` § Language-Aware Notes for per-language guidance on what's idiomatic vs. what's a narrative violation.
```

- [ ] **Step 2: Verify the file exists**

Run: `ls -la skills/codebase-audit/principles/story-readability.md`
Expected: file present

- [ ] **Step 3: Commit**

```bash
git add skills/codebase-audit/principles/story-readability.md
git commit -m "feat(codebase-audit): add story-readability criterion principle file"
```

---

### Task 4: Integrate into `code-review` — Add 7th Subagent

**Files:**
- Modify: `skills/code-review/SKILL.md:97-178` (Phase 2 section)
- Modify: `skills/code-review/SKILL.md:232` (failure handling reference)

- [ ] **Step 1: Update Phase 2 header and subagent roster**

In `skills/code-review/SKILL.md`, find:

```markdown
## Phase 2: Parallel Analysis

Dispatch **6 subagents simultaneously** via the Agent tool — all 6 in a single response (6 parallel Agent tool calls). Each subagent is a domain expert that analyzes the code against one principle set.

### Subagent Roster

| # | Domain | Principle File |
|---|---|---|
| 1 | Clean Code | `principles/clean-code.md` |
| 2 | Architecture | `principles/architecture.md` |
| 3 | Reliability | `principles/reliability.md` |
| 4 | Security | `principles/security.md` |
| 5 | Performance | `principles/performance.md` |
| 6 | Correctness | `principles/correctness.md` |
```

Replace with:

```markdown
## Phase 2: Parallel Analysis

Dispatch **7 subagents simultaneously** via the Agent tool — all 7 in a single response (7 parallel Agent tool calls). Each subagent is a domain expert that analyzes the code against one principle set.

### Subagent Roster

| # | Domain | Principle File |
|---|---|---|
| 1 | Clean Code | `principles/clean-code.md` |
| 2 | Architecture | `principles/architecture.md` |
| 3 | Reliability | `principles/reliability.md` |
| 4 | Security | `principles/security.md` |
| 5 | Performance | `principles/performance.md` |
| 6 | Correctness | `principles/correctness.md` |
| 7 | Story Readability | `shared/story-readability.md` |
```

- [ ] **Step 2: Update subagent prompt template note**

In `skills/code-review/SKILL.md`, find:

```markdown
Each subagent receives a prompt structured as follows. Adjust `<DOMAIN>` and `<PRINCIPLE_FILE>` per agent:
```

Add after the closing ``` of the prompt template block (after the line `Always spawn subagents with `model: "opus"` to ensure high-quality analysis.`):

```markdown

#### Story Readability Subagent Adjustments

The Story Readability subagent (domain 7) uses the same prompt template as the other 6, with two adjustments:

1. **Additional output:** In addition to the standard violation format, the Story Readability subagent outputs per-dimension scores (1–10) for each file reviewed. These scores follow the scoring protocol defined in `shared/story-readability.md`.
2. **Severity calibration:** Story readability findings naturally cluster at P2–P4. The subagent does not artificially inflate severity — narrative concerns are maintainability issues, not critical bugs. Typical mapping:
   - P2: Functions that actively mislead (e.g., a function named `validate` that also mutates state)
   - P3: Functions that don't read as stories but aren't misleading (e.g., missing cognitive chunking, mixed abstraction levels)
   - P4: Minor narrative polish (e.g., paragraph spacing, slight naming improvements)
```

- [ ] **Step 3: Update cross-model dispatch count**

In `skills/code-review/SKILL.md`, find:

```markdown
In addition to the 6 domain subagents, dispatch a cross-model review request in the **same parallel batch** — all 7 invocations (6 subagents + 1 cross-model CLI) launch simultaneously in a single response.
```

Replace with:

```markdown
In addition to the 7 domain subagents, dispatch a cross-model review request in the **same parallel batch** — all 8 invocations (7 subagents + 1 cross-model CLI) launch simultaneously in a single response.
```

- [ ] **Step 4: Update failure handling**

In `skills/code-review/SKILL.md`, find:

```markdown
If cross-model dispatch fails, the review continues with the 6 domain subagents only. Note in the report header: "Cross-model review unavailable; results are from domain subagents only."
```

Replace with:

```markdown
If cross-model dispatch fails, the review continues with the 7 domain subagents only. Note in the report header: "Cross-model review unavailable; results are from domain subagents only."
```

- [ ] **Step 5: Add deduplication note for Clean Code overlap**

In `skills/code-review/SKILL.md`, find the section `### 3.2 Deduplicate`. At the end of the deduplication heuristics list (after the line `- Different files + same pattern = not duplicates (each gets its own finding)`), add:

```markdown

**Clean Code / Story Readability overlap:**
When the Clean Code subagent and Story Readability subagent flag the same location (e.g., both flag a SLAP violation or naming issue), merge them into a single finding. Keep the Story Readability framing (richer narrative context) and credit both domains: "Flagged by: Clean Code, Story Readability."
```

- [ ] **Step 6: Update error handling table**

In `skills/code-review/SKILL.md`, find:

```markdown
| One or more subagents fail | Continue with remaining results; note which domain was not analyzed in the report header. |
```

No change needed — this already covers N subagents generically.

- [ ] **Step 7: Verify changes**

Run: `grep -n "7 subagents\|Story Readability\|8 invocations\|7 domain" skills/code-review/SKILL.md`
Expected: matches on the updated lines

- [ ] **Step 8: Commit**

```bash
git add skills/code-review/SKILL.md
git commit -m "feat(code-review): add Story Readability as 7th domain subagent"
```

---

### Task 5: Integrate into `codebase-audit` — Add 12th Criterion

**Files:**
- Modify: `skills/codebase-audit/SKILL.md:42-57` (valid criterion names)
- Modify: `skills/codebase-audit/SKILL.md:114-131` (scoped invocations / agent mapping)
- Modify: `skills/codebase-audit/SKILL.md:209-228` (console display)

- [ ] **Step 1: Add story-readability to valid criterion names**

In `skills/codebase-audit/SKILL.md`, find:

```markdown
| `security` | 11. Security | Core |
| `velocity` | 12. Development Velocity | Extended |
```

Replace with:

```markdown
| `security` | 11. Security | Core |
| `story-readability` | 12. Story Readability | Core |
| `velocity` | 13. Development Velocity | Extended |
```

- [ ] **Step 2: Update parsing rules**

In `skills/codebase-audit/SKILL.md`, find:

```markdown
- **Everything else:** Treated as criterion names, validated against the 12 valid names
```

Replace with:

```markdown
- **Everything else:** Treated as criterion names, validated against the 13 valid names
```

- [ ] **Step 3: Add agent mapping for story-readability**

In `skills/codebase-audit/SKILL.md`, find:

```markdown
| Security | Architecture, Quality |
| Velocity | Git/Velocity |
```

Replace with:

```markdown
| Security | Architecture, Quality |
| Story Readability | Structural, Quality |
| Velocity | Git/Velocity |
```

- [ ] **Step 4: Update console display template**

In `skills/codebase-audit/SKILL.md`, find:

```markdown
║  ...                                                       ║
║  ── ──────────────── ────── ────────────────── ─────────── ║
║  12 Velocity           —    +2.1k lines/30d    —           ║
```

Replace with:

```markdown
║  ...                                                       ║
║  12 Story Readability  B+   Narr: 8, Chunk: 6 ≥ 7 avg     ║
║  ── ──────────────── ────── ────────────────── ─────────── ║
║  13 Velocity           —    +2.1k lines/30d    —           ║
```

- [ ] **Step 5: Verify changes**

Run: `grep -n "story-readability\|Story Readability\|13 valid\|13.*Velocity" skills/codebase-audit/SKILL.md`
Expected: matches on updated lines

- [ ] **Step 6: Commit**

```bash
git add skills/codebase-audit/SKILL.md
git commit -m "feat(codebase-audit): add Story Readability as 12th core criterion"
```

---

### Task 6: Update `codebase-audit` Agent Prompts and Output Schemas

**Files:**
- Modify: `skills/codebase-audit/references/agent-prompts.md:473-476` (author agent principle list)
- Modify: `skills/codebase-audit/references/output-schemas.md` (metrics.json schema)
- Modify: `skills/codebase-audit/templates/analysis-template.md:24-31` (criteria priority table)

- [ ] **Step 1: Update author agent principle file list**

In `skills/codebase-audit/references/agent-prompts.md`, find:

```markdown
## Principle Files
Read ALL 11 principle files from `skills/codebase-audit/principles/`:
maintainability.md, evolvability.md, correctness.md, testability.md, reliability.md,
performance.md, readability.md, modularity.md, consistency.md, operability.md, security.md
```

Replace with:

```markdown
## Principle Files
Read ALL 12 principle files from `skills/codebase-audit/principles/`:
maintainability.md, evolvability.md, correctness.md, testability.md, reliability.md,
performance.md, readability.md, modularity.md, consistency.md, operability.md, security.md,
story-readability.md

For Story Readability, also read `shared/story-readability.md` for the full dimension
definitions, calibration examples, and scoring protocol. The principle file at
`skills/codebase-audit/principles/story-readability.md` provides audit-specific guidance
including the quantitative floor constraints and grading rubric.
```

- [ ] **Step 2: Update author agent instructions**

In `skills/codebase-audit/references/agent-prompts.md`, find:

```markdown
1. **Assign priority ranks and weights** to all 11 criteria based on your language + domain expertise. Show your reasoning in the "Criteria Priority Rationale" section.
```

Replace with:

```markdown
1. **Assign priority ranks and weights** to all 12 criteria based on your language + domain expertise. Show your reasoning in the "Criteria Priority Rationale" section.

   **Story Readability scoring:** This criterion uses hybrid scoring:
   - Use quantitative metrics from the Structural and Quality agents as a floor (see `principles/story-readability.md` § Quantitative floor)
   - Sample 5-10 representative files and score each of the 8 dimensions using the calibration examples in `shared/story-readability.md`
   - Compute the weighted average across sampled files
   - Report confidence as `medium` by default (qualitative-heavy). Only `high` if quantitative metrics strongly corroborate the qualitative assessment.
```

- [ ] **Step 3: Add story_readability to metrics.json schema**

In `skills/codebase-audit/references/output-schemas.md`, find the `"criteria"` block inside the metrics.json schema. After the closing `}` of the `"maintainability"` example entry (which ends around the line `"assessment": "good"`), add a comment noting that `story_readability` follows the same structure but with dimension-specific metrics:

Find:

```json
    "criteria": {
    "maintainability": {
```

This is an example entry — the implementer populates all criteria using this pattern. No schema change needed to the JSON structure itself, since all criteria follow the same schema. However, add a note after the Schema Notes section.

In `skills/codebase-audit/references/output-schemas.md`, find:

```markdown
- `audit_scope` captures what was measured and how — used for delta comparability checks.
- After Phase 4 completes: **rewrite metrics.json and metrics.md** with final ranks, weights, and adjusted overall grade.
```

Add after:

```markdown
- `story_readability` criterion uses dimension-specific metrics: `narrative_flow`, `naming_as_intent`, `cognitive_chunking`, `abstraction_consistency`, `function_focus`, `structural_clarity`, `documentation_quality`, `no_clever_tricks` — each with `value` (1-10), `weight` (percentage), and `assessment`. The `weighted_score` field holds the composite 0-100 score.
```

- [ ] **Step 4: Update analysis template criterion count**

In `skills/codebase-audit/templates/analysis-template.md`, find:

```markdown
| #11 | {Criterion} | Low | {Rationale} |
```

Replace with:

```markdown
| #11 | {Criterion} | Low | {Rationale} |
| #12 | {Criterion} | Low | {Rationale} |
```

- [ ] **Step 5: Commit**

```bash
git add skills/codebase-audit/references/agent-prompts.md skills/codebase-audit/references/output-schemas.md skills/codebase-audit/templates/analysis-template.md
git commit -m "feat(codebase-audit): update agent prompts, schemas, and template for Story Readability"
```

---

### Task 7: Add Story Readability Benchmarks to All Language Files

**Files:**
- Modify: `skills/codebase-audit/benchmarks/general.md`
- Modify: `skills/codebase-audit/benchmarks/cpp.md`
- Modify: `skills/codebase-audit/benchmarks/python.md`
- Modify: `skills/codebase-audit/benchmarks/typescript.md`
- Modify: `skills/codebase-audit/benchmarks/rust.md`
- Modify: `skills/codebase-audit/benchmarks/go.md`
- Modify: `skills/codebase-audit/benchmarks/javascript.md`
- Modify: `skills/codebase-audit/benchmarks/csharp.md`
- Modify: `skills/codebase-audit/benchmarks/gdscript.md`

- [ ] **Step 1: Add Story Readability section to `general.md`**

In `skills/codebase-audit/benchmarks/general.md`, add before the `## References` section:

```markdown
## Story Readability

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Weighted story score (8 dimensions) | ≥ 88 | Good (A) | Calibrated to shared/story-readability.md |
| Weighted story score (8 dimensions) | ≥ 72 | Acceptable (B) | Calibrated to shared/story-readability.md |
| Average function length (narrative proxy) | ≤ 20 lines | Good | Clean Code, Robert C. Martin [^3] |
| Max nesting depth (structural clarity proxy) | ≤ 3 | Good | Linux kernel coding standard [^5] |
```

- [ ] **Step 2: Add Story Readability section to `cpp.md`**

In `skills/codebase-audit/benchmarks/cpp.md`, add before the `## References` section:

```markdown
## Story Readability

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Weighted story score | ≥ 88 | Good (A) | Calibrated to shared/story-readability.md |
| Weighted story score | ≥ 72 | Acceptable (B) | Calibrated to shared/story-readability.md |
| Average function length | ≤ 25 lines | Good | Google C++ Style Guide [^3] |
| Designated initializer usage | Preferred over positional | Good | C++ Core Guidelines [^5] |
```

- [ ] **Step 3: Add Story Readability section to `python.md`**

In `skills/codebase-audit/benchmarks/python.md`, add before the `## References` section:

```markdown
## Story Readability

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Weighted story score | ≥ 88 | Good (A) | Calibrated to shared/story-readability.md |
| Weighted story score | ≥ 72 | Acceptable (B) | Calibrated to shared/story-readability.md |
| Average function length | ≤ 20 lines | Good | PEP 8 consensus [^2] |
| Nested comprehension usage | ≤ 1 level | Good | PEP 8 consensus [^2] |
```

- [ ] **Step 4: Add Story Readability section to remaining language files**

For each of `typescript.md`, `rust.md`, `go.md`, `javascript.md`, `csharp.md`, `gdscript.md` — add before the `## References` section:

```markdown
## Story Readability

| Metric | Threshold | Rating | Source |
|---|---|---|---|
| Weighted story score | ≥ 88 | Good (A) | Calibrated to shared/story-readability.md |
| Weighted story score | ≥ 72 | Acceptable (B) | Calibrated to shared/story-readability.md |
```

Add language-specific rows as appropriate (using existing references in each file):
- **TypeScript:** `| Explicit type annotation (over \`any\`) | ≥ 90% | Good | TypeScript best practices |`
- **Rust:** `| \`?\` operator usage (over manual match) | Preferred | Good | Rust API Guidelines |`
- **Go:** `| Exported function GoDoc coverage | 100% | Good | Effective Go |`
- **JavaScript:** `| Class syntax (over prototype chains) | Preferred | Good | MDN best practices |`
- **C#:** `| LINQ readability (no nested queries) | ≤ 1 level | Good | .NET coding conventions |`
- **GDScript:** `| Signal naming clarity | verb_noun pattern | Good | Godot style guide |`

- [ ] **Step 5: Verify all benchmark files have Story Readability section**

Run: `grep -l "Story Readability" skills/codebase-audit/benchmarks/*.md`
Expected: all 9 benchmark files listed

- [ ] **Step 6: Commit**

```bash
git add skills/codebase-audit/benchmarks/
git commit -m "feat(codebase-audit): add Story Readability benchmarks to all language files"
```

---

### Task 8: Update Plugin Registration

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Update plugin.json**

In `.claude-plugin/plugin.json`, find the `"keywords"` array. Add `"readability-review"` and `"story-readability"` to the array. Also update the version from `"8.0.0"` to `"9.0.0"` (new skill = major version bump per project convention). Update the description to include readability review.

Find:

```json
  "description": "Custom Claude Code skills — multi-model AI delegation, structured git commits, code review, quick review, codebase explanation, codebase quality audit, devlog writing, retrospectives, and markdown export",
  "version": "8.0.0",
```

Replace with:

```json
  "description": "Custom Claude Code skills — multi-model AI delegation, structured git commits, code review, quick review, readability review, codebase explanation, codebase quality audit, devlog writing, retrospectives, and markdown export",
  "version": "9.0.0",
```

Add to keywords array (after `"quick-review"`):

```json
    "readability-review",
    "story-readability",
```

- [ ] **Step 2: Update marketplace.json**

In `.claude-plugin/marketplace.json`, update the version and description:

Find:

```json
      "description": "Custom Claude Code skills — multi-model AI delegation, structured git commits, code review, quick review, codebase explanation, and devlog writing",
      "version": "8.0.0",
```

Replace with:

```json
      "description": "Custom Claude Code skills — multi-model AI delegation, structured git commits, code review, quick review, readability review, codebase explanation, codebase quality audit, devlog writing, retrospectives, and markdown export",
      "version": "9.0.0",
```

Add to tags array (after `"quick-review"`):

```json
        "readability-review",
        "story-readability",
```

- [ ] **Step 3: Verify version bump**

Run: `grep '"version"' .claude-plugin/plugin.json .claude-plugin/marketplace.json`
Expected: both show `"9.0.0"`

- [ ] **Step 4: Commit**

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore(plugin): bump version 8.0.0 → 9.0.0, register /readability-review skill"
```

---

### Task 9: Final Verification

**Files:** (no changes — verification only)

- [ ] **Step 1: Verify all new files exist**

Run:
```bash
ls -la shared/story-readability.md skills/readability-review/SKILL.md skills/codebase-audit/principles/story-readability.md
```
Expected: all 3 files present

- [ ] **Step 2: Verify code-review integration**

Run: `grep -c "Story Readability" skills/code-review/SKILL.md`
Expected: at least 3 matches (roster, prompt adjustment, deduplication note)

- [ ] **Step 3: Verify codebase-audit integration**

Run: `grep -c "story-readability\|Story Readability" skills/codebase-audit/SKILL.md`
Expected: at least 3 matches (criterion name, agent mapping, console display)

- [ ] **Step 4: Verify all benchmark files updated**

Run: `grep -l "Story Readability" skills/codebase-audit/benchmarks/*.md | wc -l`
Expected: 9

- [ ] **Step 5: Verify agent prompts updated**

Run: `grep "story-readability" skills/codebase-audit/references/agent-prompts.md`
Expected: match in the principle file list

- [ ] **Step 6: Verify plugin version**

Run: `grep '"version"' .claude-plugin/plugin.json`
Expected: `"9.0.0"`

- [ ] **Step 7: Run git log to confirm all commits**

Run: `git log --oneline -10`
Expected: 8 commits for tasks 1-8

- [ ] **Step 8: Mark task complete**

All files created, all integrations wired, all verifications pass.
