# Clean Code Principles

## Quick Diagnostic Guide

| Symptom | Likely Principle |
|---|---|
| Function does too many things or has many parameters | Small Functions |
| Deep nesting (3+ levels of indentation) | Guard Clauses |
| Hard to understand what a block of code does at a glance | Cognitive Load |
| Mixing orchestration logic with low-level details | SLAP |
| Cryptic variable/function names or magic numbers | Self-Documenting Code |
| Comments just restate the code | Documentation Discipline |
| Abstractions, interfaces, or features that nothing uses yet | YAGNI |
| Over-engineered solution for a simple problem | KISS |
| Function has surprising side effects or inconsistent returns | Principle of Least Surprise |
| Code works but feels clunky, verbose, or brute-forced | Elegance |

## Principle Tensions

| Tension | Guidance |
|---|---|
| **KISS vs. Small Functions** | Extracting functions adds indirection. Extract only when the extracted piece has a clear name and is called from multiple places, or when the original function mixes abstraction levels. Do not create trivial one-liner wrappers. |
| **YAGNI vs. Extensibility** | Build only what is needed today. If a second concrete case appears, refactor then. Premature abstraction is more costly than a later refactor. |
| **Self-Documenting Code vs. Documentation Discipline** | Good names reduce the need for comments, but they cannot explain *why* a business rule exists or *why* a non-obvious approach was chosen. Use comments for rationale, not narration. |
| **Small Functions vs. Cognitive Load** | Too many tiny functions force the reader to jump around. If the extraction does not reduce cognitive load, it increases it. Inline trivial helpers. |
| **Guard Clauses vs. SLAP** | Guard clauses are low-level checks. Placing them at the top of a high-level orchestrator can break SLAP. Consider validating in a dedicated validation function. |
| **Elegance vs. KISS** | Elegant code is minimal, but cleverness without clarity is not elegant. If a teammate cannot understand the code in 30 seconds, choose the plainer version. |

---

## 1. KISS — Keep It Simple, Stupid

Prefer the simplest solution that solves the actual problem. Every layer of abstraction,
every design pattern, and every indirection has a cost: it must be read, understood, and
maintained. Add complexity only when a concrete requirement demands it.

### ❌ Wrong

```python
from abc import ABC, abstractmethod


class OperationInterface(ABC):
    @abstractmethod
    def execute(self, a: float, b: float) -> float: ...


class Addition(OperationInterface):
    def execute(self, a: float, b: float) -> float:
        return a + b


class Subtraction(OperationInterface):
    def execute(self, a: float, b: float) -> float:
        return a - b


class OperationFactory:
    _operations = {"add": Addition, "sub": Subtraction}

    @classmethod
    def create(cls, name: str) -> OperationInterface:
        return cls._operations[name]()


def calculate(op: str, a: float, b: float) -> float:
    return OperationFactory.create(op).execute(a, b)
```

### ✅ Correct

```python
def calculate(op: str, a: float, b: float) -> float:
    if op == "add":
        return a + b
    elif op == "sub":
        return a - b
    else:
        raise ValueError(f"Unknown operation: {op}")
```

**Key points:** Avoid premature abstraction. Interfaces, factories, and registries are justified when there are many variants or when third-party plugins must extend behaviour — not for two arithmetic operations.

---

## 2. YAGNI — You Aren't Gonna Need It

Do not build features, abstractions, or extension points until a real requirement demands
them. Speculative code costs time to write, time to read, and time to maintain — and it
is often wrong when the real need finally arrives.

### ❌ Wrong

```python
from abc import ABC, abstractmethod


class DataExporter(ABC):
    @abstractmethod
    def export(self, data: list[dict]) -> str: ...

    @abstractmethod
    def get_file_extension(self) -> str: ...


class JSONExporter(DataExporter):
    def export(self, data: list[dict]) -> str:
        import json
        return json.dumps(data, indent=2)

    def get_file_extension(self) -> str:
        return ".json"


# CSVExporter, XMLExporter — "we might need them later"
```

### ✅ Correct

```python
import json


def export_to_json(data: list[dict]) -> str:
    return json.dumps(data, indent=2)
```

**Key points:** When a second export format is actually needed, refactor at that point. An ABC with a single concrete subclass is a premature abstraction that adds files, indirection, and maintenance burden for zero benefit.

---

## 3. Small Functions — Short, Focused, One Purpose

Each function should do one thing and do it well. A function that fits on a screen
(roughly 20 lines of logic) is easier to name, test, and reason about. However, extraction
must add clarity — do not create trivial wrappers that merely rename a built-in.

### ❌ Wrong

```python
def is_empty(items: list) -> bool:
    """Unnecessary wrapper — adds indirection without insight."""
    return len(items) == 0


def has_elements(items: list) -> bool:
    """Another wrapper that obscures rather than clarifies."""
    return len(items) > 0
```

### ✅ Correct

```python
def get_active_users(users: list[dict]) -> list[dict]:
    """Meaningful extraction — encapsulates a domain concept."""
    return [
        user for user in users
        if user["is_active"] and not user.get("is_suspended")
    ]


def send_digest(users: list[dict], digest: str) -> None:
    active = get_active_users(users)
    for user in active:
        send_email(user["email"], digest)
```

**Key points:** Extract when the extracted function encapsulates a domain concept, is reused, or makes the caller easier to read. Do not extract one-liners that merely rename a language primitive.

---

## 4. Guard Clauses — Exit Early for Invalid States

Return or raise at the top of a function for invalid inputs and edge cases. This
eliminates deep nesting (the arrow anti-pattern) and keeps the main logic at the
shallowest indentation level, making it easier to read and modify.

### ❌ Wrong

```python
def process_order(order: dict) -> str:
    if order is not None:
        if order.get("status") == "pending":
            if order.get("items"):
                total = sum(item["price"] for item in order["items"])
                if total > 0:
                    return f"Processed ${total:.2f}"
                else:
                    return "Error: empty total"
            else:
                return "Error: no items"
        else:
            return "Error: not pending"
    else:
        return "Error: no order"
```

### ✅ Correct

```python
def process_order(order: dict) -> str:
    if order is None:
        return "Error: no order"
    if order.get("status") != "pending":
        return "Error: not pending"
    if not order.get("items"):
        return "Error: no items"

    total = sum(item["price"] for item in order["items"])
    if total <= 0:
        return "Error: empty total"

    return f"Processed ${total:.2f}"
```

**Key points:** Each guard clause handles one invalid state and exits. The happy path flows straight down at the leftmost indentation. Maximum nesting depth drops from 4 to 1.

---

## 5. Cognitive Load — Reduce Mental Effort

Every piece of code a developer reads consumes working memory. Compound boolean
expressions, implicit state changes, and dense one-liners force the reader to mentally
simulate the code to understand it. Reduce load by naming intermediate results and
breaking complex expressions into labelled steps.

### ❌ Wrong

```python
def should_send_reminder(user: dict) -> bool:
    return (user["is_active"] and not user.get("is_suspended")
            and user.get("last_login") is not None
            and (datetime.now() - user["last_login"]).days > 30
            and user.get("email_opt_in", False))
```

### ✅ Correct

```python
def should_send_reminder(user: dict) -> bool:
    is_eligible = user["is_active"] and not user.get("is_suspended")
    has_logged_in = user.get("last_login") is not None
    is_inactive = has_logged_in and (datetime.now() - user["last_login"]).days > 30
    wants_email = user.get("email_opt_in", False)

    return is_eligible and is_inactive and wants_email
```

**Key points:** Named booleans act as inline documentation. Each variable answers one question. The final return reads almost like English. Debugging is easier because each condition can be inspected individually.

---

## 6. SLAP — Single Level of Abstraction Principle

Every statement in a function should operate at the same level of abstraction. Mixing
high-level orchestration (`validate`, `save`, `notify`) with low-level details
(`line.split(",")[3].strip()`) forces the reader to constantly shift mental gears.

### ❌ Wrong

```python
def process_csv_report(path: str) -> None:
    with open(path) as f:
        lines = f.readlines()
    headers = lines[0].strip().split(",")
    records = []
    for line in lines[1:]:
        parts = line.strip().split(",")
        record = dict(zip(headers, parts))
        record["total"] = float(record["qty"]) * float(record["price"])
        records.append(record)

    valid = [r for r in records if r["total"] > 0]
    report = {"count": len(valid), "sum": sum(r["total"] for r in valid)}

    with open("report.json", "w") as f:
        json.dump(report, f)
    send_email("team@example.com", "Report ready", json.dumps(report))
```

### ✅ Correct

```python
def process_csv_report(path: str) -> None:
    records = parse_csv(path)
    enriched = compute_totals(records)
    valid = filter_valid(enriched)
    report = build_summary(valid)
    save_report(report)
    notify_team(report)


def parse_csv(path: str) -> list[dict]:
    with open(path) as f:
        lines = f.readlines()
    headers = lines[0].strip().split(",")
    return [dict(zip(headers, line.strip().split(","))) for line in lines[1:]]


def compute_totals(records: list[dict]) -> list[dict]:
    for record in records:
        record["total"] = float(record["qty"]) * float(record["price"])
    return records
```

**Key points:** The top-level function reads as a recipe — each step is one verb at the same abstraction level. Low-level parsing, filtering, and I/O live in dedicated helpers. Each helper can be understood, tested, and modified independently.

---

## 7. Self-Documenting Code — Names Reveal Purpose

Choose names that express intent so readers never have to guess. Replace magic numbers
with named constants. If understanding a function requires reading its body, the name is
wrong.

### ❌ Wrong

```python
def proc(d, w):
    t = 0
    for day in d:
        h = day["hours"]
        if h > 8:
            t += 8 + (h - 8) * 1.5
        else:
            t += h
    return t * w
```

### ✅ Correct

```python
STANDARD_HOURS_PER_DAY = 8
OVERTIME_MULTIPLIER = 1.5


def calculate_billable_hours(timesheets: list[dict], hourly_rate: float) -> float:
    total_hours = 0.0
    for day in timesheets:
        worked = day["hours"]
        if worked > STANDARD_HOURS_PER_DAY:
            overtime = (worked - STANDARD_HOURS_PER_DAY) * OVERTIME_MULTIPLIER
            total_hours += STANDARD_HOURS_PER_DAY + overtime
        else:
            total_hours += worked
    return total_hours * hourly_rate
```

**Key points:** `proc`, `d`, `w`, `t`, `h` communicate nothing. `calculate_billable_hours`, `timesheets`, `hourly_rate`, `OVERTIME_MULTIPLIER` make the business logic self-evident. Magic numbers like `8` and `1.5` become searchable, reviewable constants.

---

## 8. Documentation Discipline — Code Tells How, Comments Tell Why

Comments should explain *why* a decision was made — the business rule, the constraint,
the workaround — not *what* the code does. If the code is unclear enough to need a
"what" comment, improve the code first. Redundant comments rot faster than no comments.

### ❌ Wrong

```python
# Get the user
user = get_user(user_id)

# Check if user is active
if user.is_active:
    # Calculate the discount
    discount = calculate_discount(user)
    # Apply the discount
    total = apply_discount(order, discount)
```

### ✅ Correct

```python
user = get_user(user_id)

if user.is_active:
    # Business rule: loyalty discount applies only to users who joined
    # before the 2023 pricing restructure (see JIRA-4521).
    discount = calculate_discount(user)
    total = apply_discount(order, discount)
```

**Key points:** Parrot comments (`# Get the user` above `get_user()`) add noise and maintenance cost. Good comments explain business rationale, non-obvious constraints, or the reason a workaround exists. They answer "why is this here?" not "what does this line do?"

---

## 9. Elegance — Beauty Through Insight and Minimality

Elegant code solves a problem with the minimum necessary mechanism, reveals the
structure of the problem domain, and leaves the reader thinking "of course, that's
how it should be done." It is not cleverness — it is clarity distilled.

**Criteria for elegance:**

| Criterion | Question to Ask |
|---|---|
| **Minimality** | Can anything be removed without losing correctness? |
| **Accomplishment** | Does it fully solve the stated problem? |
| **Modesty** | Does it avoid showing off? Would a junior developer follow it? |
| **Revelation** | Does it illuminate the problem's structure? |

### ❌ Wrong

```python
def flatten(nested):
    result = []
    stack = list(reversed(nested))
    while stack:
        item = stack.pop()
        if isinstance(item, list):
            stack.extend(reversed(item))
        else:
            result.append(item)
    return result
```

### ✅ Correct

```python
def flatten(nested: list) -> list:
    items = []
    for element in nested:
        if isinstance(element, list):
            items.extend(flatten(element))
        else:
            items.append(element)
    return items
```

**Key points:** The recursive version mirrors the recursive structure of the data — nested lists contain either items or more nested lists. The stack-based version works but hides that insight behind manual stack management and reversed ordering. Elegant code matches the shape of the problem.

---

## 10. Principle of Least Surprise — Behave as Users Expect

A function should do what its name promises, nothing more, nothing less. No hidden side
effects, no inconsistent return types, no silent failures. When a developer reads a
function's signature, their prediction of its behaviour should be correct.

### ❌ Wrong

```python
def get_user_name(user_id: int) -> str:
    user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
    # Hidden side effect: logging unrelated analytics
    analytics.track("user_lookup", user_id)
    # Hidden side effect: mutating global state
    global last_accessed_user
    last_accessed_user = user_id
    if user is None:
        return None  # Inconsistent: signature says str, returns None
    return user["name"]
```

### ✅ Correct

```python
def get_user_name(user_id: int) -> str | None:
    """Return the user's display name, or None if not found."""
    user = db.query("SELECT name FROM users WHERE id = %s", (user_id,))
    if user is None:
        return None
    return user["name"]


def track_user_lookup(user_id: int) -> None:
    """Explicitly separated side effect — caller decides when to track."""
    analytics.track("user_lookup", user_id)
```

**Key points:** `get_` implies a pure read — do not smuggle writes, tracking, or global mutation into it. Return type must match the signature (use `str | None` if `None` is possible). Side effects belong in separate, explicitly named functions so callers can compose behaviour predictably.
