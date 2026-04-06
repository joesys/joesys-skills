# Story-Readability Principle

> Single source of truth for the story-readability code review system.
> Consumed by: `/readability-review`, `/code-review` (domain 7), `/codebase-audit` (criterion 12).

---

## Philosophy

Code should read like a story. A stranger should read the code and understand the intent without comments — no clever tricks, no dense one-liners, no guesswork.

### Gold-Standard Example

```cpp
auto process_dawn_phase(World& world) -> void {
    collect_night_rewards(world);
    transfer_grace_to_hero(world);
    heal_injured_agents(world);
    process_immigration(world);
    generate_journal_entry(world);
}
```

Each line is a sentence. The function is a paragraph. The reader knows what happens at dawn without reading any implementation. This philosophy extends beyond the absence of code smells — it asks: **does this code tell a coherent story?**

---

## The 8 Dimensions

| # | Dimension | Weight | What It Measures |
|---|-----------|--------|------------------|
| 1 | Narrative Flow | 20% | Does a function read top-to-bottom as a sequence of clear steps? Are logical phases separated by paragraph spacing? Do paired operations (begin/end, open/close) appear symmetrically? |
| 2 | Naming as Intent | 15% | Do names reveal *what* and *why* without needing to read the body? Are enums used over bools at call sites? Are call sites self-documenting? |
| 3 | Cognitive Chunking | 15% | Are logical phases of a function extracted into named steps, even when the extraction doesn't reduce complexity or duplication? Can a reader see the story's chapters at a glance? |
| 4 | Abstraction Consistency (SLAP) | 14% | Does each function operate at a single level of abstraction? Does the orchestrator avoid mixing high-level steps with low-level details? |
| 5 | Function Focus | 10% | One function, one job. Short enough to hold in your head (~20 lines of logic). Extraction adds clarity, not just indirection. |
| 6 | Structural Clarity | 10% | Flat control flow. Guard clauses and early returns for invalid states. Minimal nesting. No arrow anti-patterns. |
| 7 | Documentation Quality | 10% | Comments explain *why*, not *what*. No parrot comments. Business rationale and non-obvious constraints are documented. |
| 8 | No Clever Tricks | 6% | Absence of dense one-liners, bitwise hacks, ternary chains, negation puzzles, and obscure idioms. |

> **Note:** The top 4 dimensions carry 64% of the total weight. Weights are defaults — customizable via user preferences.

---

## Sub-Signals per Dimension

### Narrative Flow
- **Paragraph spacing** — blank lines between logical phases
- **Symmetry** — paired operations (begin/end, open/close, acquire/release) appear in matching structure
- **Temporal ordering** — steps appear in the order they logically occur

### Naming as Intent
- **Enums over bools** — eliminate boolean blindness at call sites
- **Self-documenting call sites** — arguments read like prose without jumping to the signature

### Cognitive Chunking
- **Named extraction** — logical phases pulled into named helpers even when it doesn't reduce duplication
- **Chapter visibility** — a reader can see the story's structure at a glance from the orchestrator

### Abstraction Consistency (SLAP)
- **Single level** — every line in a function operates at the same abstraction level
- **No level mixing** — orchestrators delegate details, never inline them

### Function Focus
- **One responsibility** — each function does exactly one thing
- **Size discipline** — roughly 20 lines of logic; extraction adds clarity, not just indirection

### Structural Clarity
- **Early returns** — guard clauses handle invalid states at the top
- **Happy path at shallowest indentation** — the main logic is never buried in nesting
- **Flat control flow** — no arrow anti-patterns

### Documentation Quality
- **Why, not what** — comments explain business rationale and non-obvious constraints
- **No parrot comments** — never restate what the code already says

### No Clever Tricks
- **Negation avoidance** — no double-negative conditions
- **No dense compound expressions** — break complex conditions into named booleans
- **No obscure idioms** — prefer readable constructs over clever shortcuts

---

## Calibration Examples

Each dimension is illustrated at three score bands: **9-10** (excellent), **5-6** (mediocre), and **2-3** (poor). Subagents MUST use these as anchors when scoring.

### Dimension 1 — Narrative Flow

**Score 9-10:** Three phases separated by paragraph spacing, temporal ordering correct.

```python
def deploy_release(release):
    # Phase 1: Prepare
    validate_release_artifacts(release)
    snapshot_current_state(release.target)
    notify_team_deploy_starting(release)

    # Phase 2: Execute
    stop_traffic(release.target)
    swap_binaries(release)
    run_smoke_tests(release.target)
    resume_traffic(release.target)

    # Phase 3: Confirm
    verify_health_checks(release.target)
    tag_release_as_deployed(release)
    notify_team_deploy_complete(release)
```

**Score 5-6:** Same steps but no paragraph spacing — phases blur together.

```python
def deploy_release(release):
    validate_release_artifacts(release)
    snapshot_current_state(release.target)
    notify_team_deploy_starting(release)
    stop_traffic(release.target)
    swap_binaries(release)
    run_smoke_tests(release.target)
    resume_traffic(release.target)
    verify_health_checks(release.target)
    tag_release_as_deployed(release)
    notify_team_deploy_complete(release)
```

**Score 2-3:** Temporal ordering scrambled — notify before deploy, validate after rollout.

```python
def deploy_release(release):
    notify_team_deploy_complete(release)
    swap_binaries(release)
    resume_traffic(release.target)
    validate_release_artifacts(release)
    tag_release_as_deployed(release)
    stop_traffic(release.target)
    snapshot_current_state(release.target)
    run_smoke_tests(release.target)
    verify_health_checks(release.target)
    notify_team_deploy_starting(release)
```

---

### Dimension 2 — Naming as Intent

**Score 9-10:** Every argument reads like prose.

```cpp
recruit_settler(world, SettlerClass::farmer, Loyalty::high);
```

**Score 5-6:** Function name clear but call site opaque.

```cpp
recruit_settler(world, "farmer", true);
```

**Score 2-3:** Single-letter vars, abbreviated names, magic numbers.

```cpp
rec(w, 2, true);
```

---

### Dimension 3 — Cognitive Chunking

**Score 9-10:** Two phases (validate then construct) visible at a glance.

```cpp
auto make_world_config(int width, int height, Biome biome) -> WorldConfig {
    validate_map_dimensions(width, height);

    return WorldConfig{
        .map   = generate_map(width, height, biome),
        .rules = load_default_rules(),
        .seed  = generate_random_seed(),
    };
}

auto validate_map_dimensions(int width, int height) -> void {
    if (width < MIN_MAP_SIZE || width > MAX_MAP_SIZE)
        throw InvalidDimension{"width", width};
    if (height < MIN_MAP_SIZE || height > MAX_MAP_SIZE)
        throw InvalidDimension{"height", height};
    if (width * height > MAX_TILE_COUNT)
        throw MapTooLarge{width, height};
}
```

**Score 5-6:** Correct but validation inlined — phases not chunked.

```cpp
auto make_world_config(int width, int height, Biome biome) -> WorldConfig {
    if (width < MIN_MAP_SIZE || width > MAX_MAP_SIZE)
        throw InvalidDimension{"width", width};
    if (height < MIN_MAP_SIZE || height > MAX_MAP_SIZE)
        throw InvalidDimension{"height", height};
    if (width * height > MAX_TILE_COUNT)
        throw MapTooLarge{width, height};

    return WorldConfig{
        .map   = generate_map(width, height, biome),
        .rules = load_default_rules(),
        .seed  = generate_random_seed(),
    };
}
```

**Score 2-3:** Dense one-liners, abbreviated parameters, no visual separation.

```cpp
auto mkwc(int w, int h, Biome b) -> WorldConfig {
    if(w<1||w>512||h<1||h>512||w*h>65536) throw std::runtime_error("bad");
    return WorldConfig{generate_map(w,h,b),load_default_rules(),generate_random_seed()};
}
```

---

### Dimension 4 — Abstraction Consistency (SLAP)

**Score 9-10:** All lines at the same abstraction level.

```python
def generate_monthly_report(month, year):
    data = fetch_monthly_data(month, year)
    metrics = compute_summary_metrics(data)
    charts = render_charts(metrics)
    document = assemble_report(metrics, charts)
    deliver_report(document)
```

**Score 5-6:** Drops into HTML string concatenation midway — two abstraction levels.

```python
def generate_monthly_report(month, year):
    data = fetch_monthly_data(month, year)
    metrics = compute_summary_metrics(data)
    charts = render_charts(metrics)

    html = "<html><body>"
    html += f"<h1>Report for {month}/{year}</h1>"
    for key, value in metrics.items():
        html += f"<tr><td>{key}</td><td>{value}</td></tr>"
    html += "</body></html>"

    deliver_report(html)
```

**Score 2-3:** DB cursors, raw SQL, arithmetic, HTML, SMTP all in one function — every line at a different level.

```python
def generate_monthly_report(month, year):
    conn = psycopg2.connect(host="db.prod", dbname="analytics")
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM sales WHERE month={month} AND year={year}")
    rows = cur.fetchall()
    total = sum(r[3] * r[4] - r[5] for r in rows)
    avg = total / len(rows) if rows else 0
    html = "<html><body><h1>Report</h1>"
    html += f"<p>Total: ${total:.2f}, Avg: ${avg:.2f}</p>"
    for r in rows:
        html += f"<tr><td>{r[0]}</td><td>{r[3]*r[4]-r[5]:.2f}</td></tr>"
    html += "</body></html>"
    smtp = smtplib.SMTP("mail.prod")
    msg = MIMEText(html, "html")
    msg["Subject"] = f"Monthly Report {month}/{year}"
    smtp.send_message(msg)
    conn.close()
```

---

### Dimension 5 — Function Focus

**Score 9-10:** Each function does one thing. Caller reads as a sequence of named steps. Each function is 20 lines or fewer.

```python
def onboard_new_employee(employee):
    create_account(employee)
    assign_default_permissions(employee)
    provision_workstation(employee)
    schedule_orientation(employee)
    send_welcome_email(employee)

def create_account(employee):
    validate_employee_info(employee)
    account = Account(
        username=generate_username(employee),
        email=employee.work_email,
        department=employee.department,
    )
    save_account(account)
    return account
```

**Score 5-6:** Functions mostly focused but 30-40 lines with extractable phases.

```python
def onboard_new_employee(employee):
    # Account creation (could be extracted)
    if not employee.email:
        raise ValueError("Email required")
    username = f"{employee.first_name[0]}{employee.last_name}".lower()
    if account_exists(username):
        username += str(random.randint(100, 999))
    account = Account(username=username, email=employee.email)
    db.save(account)

    # Permissions (could be extracted)
    perms = get_default_permissions(employee.department)
    for perm in perms:
        grant_permission(account, perm)

    # Notification (could be extracted)
    send_welcome_email(employee)
    schedule_orientation(employee)
```

**Score 2-3:** God function, 100+ lines, multiple responsibilities interleaved.

```python
def onboard_new_employee(employee):
    # 100+ lines mixing account creation, LDAP lookups, permission
    # assignment, workstation imaging, badge printing, orientation
    # scheduling, payroll enrollment, benefits selection, parking
    # assignment, email setup, Slack invitation, and welcome email
    # — all in a single function with deeply nested conditionals.
    ...
```

---

### Dimension 6 — Structural Clarity

**Score 9-10:** Guards at top, happy path at bottom, flat control flow.

```python
def process_order(order):
    if not order:
        raise InvalidOrder("Order is empty")
    if order.is_cancelled:
        return CancelledResult(order.id)
    if not order.has_payment:
        return PendingPayment(order.id)

    items = reserve_inventory(order.items)
    charge = process_payment(order.payment)
    shipment = create_shipment(items, order.address)
    return OrderConfirmation(order.id, charge, shipment)
```

**Score 2-3:** Arrow anti-pattern — nested if/else burying happy path at deepest nesting.

```python
def process_order(order):
    if order:
        if not order.is_cancelled:
            if order.has_payment:
                items = reserve_inventory(order.items)
                if items:
                    charge = process_payment(order.payment)
                    if charge.success:
                        shipment = create_shipment(items, order.address)
                        if shipment:
                            return OrderConfirmation(order.id, charge, shipment)
                        else:
                            return ShipmentFailed(order.id)
                    else:
                        return PaymentFailed(order.id)
                else:
                    return OutOfStock(order.id)
            else:
                return PendingPayment(order.id)
        else:
            return CancelledResult(order.id)
    else:
        raise InvalidOrder("Order is empty")
```

---

### Dimension 7 — Documentation Quality

**Score 9-10:** Comment explains a business rule not visible in the code.

```python
def calculate_discount(customer, order):
    # Customers who joined before 2020 get legacy loyalty pricing
    # per agreement with VP Sales — see JIRA-4521 for context.
    if customer.join_date < date(2020, 1, 1):
        return apply_legacy_discount(order, rate=0.15)

    return apply_standard_discount(order)
```

**Score 2-3:** Parrot comments that restate what the code already says.

```python
def calculate_discount(customer, order):
    # Get the customer
    customer = get_customer(customer.id)
    # Get the order
    order = get_order(order.id)
    # Calculate the discount
    discount = order.total * 0.1
    # Return the discount
    return discount
```

---

### Dimension 8 — No Clever Tricks

**Score 9-10:** Reads like English.

```python
if user.is_eligible and user.wants_notifications:
    send_notification(user)
```

**Score 2-3:** Double negation, bitwise flag, unreadable.

```python
if not (not user.excluded or user.opt_out) and (user.flags & 0x04):
    send_notification(user)
```

---

## Scoring Protocol

### Per-Dimension Scoring

Each dimension is scored on a **1-10** scale using the calibration examples above as anchors.

### Weighted Aggregation

Compute the total score out of 100:

```
total = sum((dimension_score / 10) * weight_points for each dimension)
```

Where `weight_points` is the weight percentage applied directly (e.g., Narrative Flow at 20% contributes up to 20 points).

**Example:** If Narrative Flow scores 8/10, it contributes `(8/10) * 20 = 16` points.

### Grade Mapping

| Score Range | Grade |
|-------------|-------|
| 95 - 100 | A+ |
| 88 - 94 | A |
| 80 - 87 | B+ |
| 72 - 79 | B |
| 64 - 71 | C+ |
| 56 - 63 | C |
| 45 - 55 | D |
| 0 - 44 | F |

---

## Language-Aware Notes

The 8 dimensions are language-agnostic, but each language has idioms that affect scoring. Apply these adjustments when reviewing code in the corresponding language.

### C++
- No universal formatter. Paragraph spacing is a conscious authorial choice — reward it.
- Template metaprogramming can violate No Clever Tricks even when idiomatic.
- Trailing return types (`auto foo() -> int`) are idiomatic and do not hurt readability.
- Designated initializers (`.field = value`) improve Naming as Intent — reward their use.

### Python
- List comprehensions are idiomatic unless nested. Nested comprehensions often violate No Clever Tricks.
- PEP 8 enforces some Structural Clarity by convention.
- Type hints are part of the story — their presence improves Naming as Intent.

### Go
- `gofmt` enforces formatting uniformly. Do not score paragraph spacing since the formatter controls it.
- Short variable names in short scopes (`i`, `r`, `ctx`) are idiomatic — do not penalize in tight loops.
- Exported symbols need GoDoc comments — score under Documentation Quality.

### Rust
- Pattern matching (`match`) is idiomatic and often improves Narrative Flow.
- The `?` operator improves Narrative Flow by eliminating nested error checks.
- Lifetime annotations (`'a`) can hurt flow — do not penalize when necessary, but reward when avoided via elision.

### TypeScript
- `any` breaks Naming as Intent. Penalize its use when a concrete type is feasible.
- Prefer explicit types when they aid readability, even when inference would work.

### JavaScript
- Same guidance as TypeScript, minus the type system.
- Prototype chains and non-obvious `this` binding can qualify as Clever Tricks.

### C#
- LINQ is idiomatic and improves Narrative Flow when used for data transformations.
- `var` is acceptable when the type is obvious from the right-hand side.
- `async/await` follows the same Narrative Flow principles — the async version should read like the sync version.

### GDScript
- Signal/slot connections are idiomatic Godot patterns — not cryptic.
- `_ready()`, `_process()`, `_physics_process()` are Godot lifecycle conventions — do not penalize as unclear naming.
