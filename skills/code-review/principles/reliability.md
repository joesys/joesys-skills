# Reliability Principles

## Quick Diagnostic Guide

| Symptom | Likely Principle |
|---|---|
| Error surfaces far from where it originated | Fail-Fast & Defensive Programming |
| Caller passes garbage and function silently proceeds | Design by Contract |
| API rejects valid input over minor formatting | Postel's Law |
| One failing dependency brings down the entire system | Resilience & Graceful Degradation |
| Service account has write access but only reads data | Principle of Least Privilege |
| "Not my code, not my problem" attitude toward messy code | Boy Scout Rule |
| Production failure with no logs, metrics, or traces | Observability & Transparency |

## Principle Tensions

| Tension | Guidance |
|---|---|
| **Fail-Fast vs. Resilience** | Fail-fast on programming errors (wrong types, broken invariants). Be resilient against operational errors (network timeouts, temporary unavailability). The distinction is: can the caller fix it by retrying? |
| **Defensive Programming vs. Design by Contract** | DbC trusts the caller to meet preconditions and crashes hard if they don't. Defensive programming trusts nobody. Use DbC at internal module boundaries; use defensive programming at system edges (APIs, user input, deserialization). |
| **Postel's Law vs. Fail-Fast** | Being liberal in what you accept can mask bugs upstream. Accept reasonable variations (trailing whitespace, mixed case), but reject structurally invalid data. Do not silently coerce `"yes"` into `True` unless that is an explicit, documented feature. |
| **Least Privilege vs. Developer Velocity** | Strict permissions slow down local development. Use broad permissions in dev/test, strict in staging/production. Never relax production permissions to speed up development. |
| **Boy Scout Rule vs. Scope Creep** | Cleaning up code while working on a feature is good. Refactoring an entire module when you were asked to fix a typo is scope creep. Clean the campground, not the forest. |
| **Observability vs. Security** | Logs and traces are essential but can leak secrets. Never log credentials, tokens, PII, or full request bodies. Structured logging with explicit field selection prevents accidental exposure. |

---

## 1. Fail-Fast & Defensive Programming — Detect and Report Errors Immediately

Do not let invalid state propagate through the system. The further an error travels from
its origin, the harder it is to diagnose. Validate inputs at entry, check configuration at
startup, and raise exceptions the moment something is wrong.

**Error type strategies:**

| Error Type | Example | Strategy |
|---|---|---|
| **Precondition violation** | Null argument, negative age | Raise immediately — caller's bug |
| **Transient failure** | Network timeout, lock contention | Retry with backoff — may self-heal |
| **Deterministic failure** | File not found, invalid SQL | Fail with clear message — retrying won't help |
| **Invariant violation** | Negative account balance after debit | Assert — indicates logic bug |

### ❌ Wrong

```python
def transfer_money(from_account: dict, to_account: dict, amount: float) -> dict:
    from_account["balance"] -= amount  # no validation — invalid state propagates
    to_account["balance"] += amount
    if from_account["balance"] < 0:
        print("Warning: negative balance")  # discovered much later, log and continue?!
    return {"from": from_account, "to": to_account}
```

### ✅ Correct

```python
def transfer_money(from_account: dict, to_account: dict, amount: float) -> dict:
    if amount <= 0:
        raise ValueError(f"Transfer amount must be positive, got {amount}")
    if from_account["balance"] < amount:
        raise InsufficientFundsError(
            f"Cannot transfer {amount}: only {from_account['balance']} available"
        )

    from_account["balance"] -= amount
    to_account["balance"] += amount
    assert from_account["balance"] >= 0, "Invariant violated: negative balance after transfer"
    return {"from": from_account, "to": to_account}


def load_config() -> dict:
    """Validate configuration at startup, not at first use."""
    config = _read_config_file()
    required = ["DATABASE_URL", "SECRET_KEY", "REDIS_HOST"]
    missing = [k for k in required if k not in config]
    if missing:
        raise ConfigurationError(f"Missing required config keys: {missing}")
    return config
```

**Key points:** Guard clauses catch precondition violations at the function boundary. The invariant assertion catches logic bugs. Config validation at startup prevents cryptic `KeyError` deep in a request handler.

---

## 2. Design by Contract — Explicit Agreements Between Caller and Routine

Every function has a contract: *preconditions* (what the caller guarantees), *postconditions*
(what the function guarantees back), and *invariants* (what is always true about the
object's state). Making these contracts explicit prevents the ambiguity that causes bugs.

**DbC vs. Defensive Programming:**

| Aspect | Design by Contract | Defensive Programming |
|---|---|---|
| **Trust model** | Trusts caller to meet preconditions | Trusts nobody |
| **On violation** | Crashes (caller's bug) | Handles gracefully |
| **Best for** | Internal module APIs | System boundaries, public APIs |
| **Cost** | Simpler implementation | More code, more branches |

### ❌ Wrong

```python
def calculate_discount(price: float, percentage: float) -> float:
    # No contract — what happens with negative price? 150% discount?
    return price * (percentage / 100)

def apply_bulk_discount(items: list[dict]) -> list[dict]:
    # Caller has no idea what this expects or guarantees
    for item in items:
        if item.get("qty", 0) > 10:
            item["price"] *= 0.9
    return items
```

### ✅ Correct

```python
def calculate_discount(price: float, percentage: float) -> float:
    """Preconditions: price >= 0, 0 <= percentage <= 100.
    Postconditions: 0 <= result <= price."""
    assert price >= 0, f"Precondition: price must be non-negative, got {price}"
    assert 0 <= percentage <= 100, f"Precondition: percentage must be 0-100, got {percentage}"
    result = price * (1 - percentage / 100)
    assert 0 <= result <= price, f"Postcondition: result {result} outside [0, {price}]"
    return result

class ShoppingCart:
    """Invariant: total always equals sum of item prices * quantities."""
    def __init__(self):
        self._items: list[dict] = []
        self._total: float = 0.0

    def add_item(self, name: str, price: float, qty: int) -> None:
        assert price >= 0 and qty > 0, "Precondition: price >= 0, qty > 0"
        self._items.append({"name": name, "price": price, "qty": qty})
        self._total += price * qty
        self._check_invariant()

    def _check_invariant(self) -> None:
        expected = sum(i["price"] * i["qty"] for i in self._items)
        assert abs(self._total - expected) < 0.01, "Invariant violated: total mismatch"
```

**Key points:** Preconditions document what callers must provide. Postconditions document what the function guarantees. Invariants ensure the object is always in a consistent state. Use `assert` for contracts — they can be disabled in production with `python -O` if performance matters.

---

## 3. Postel's Law — Be Conservative in What You Send, Liberal in What You Accept

Also known as the Robustness Principle: produce strict, well-formed output but accept
reasonable variations in input. This makes systems resilient to minor inconsistencies
from upstream sources without sacrificing the quality of downstream data.

**The Tolerant Reader pattern:** When consuming data, ignore fields you don't need and
tolerate minor format variations. Don't break because a response added a new field.

**The dark side:** Taken too far, liberal acceptance causes *specification rot* — producers
never fix their bugs because consumers silently compensate. It can also create security
risks when the system guesses intent from malformed input (e.g., HTML auto-correction
enabling XSS).

### ❌ Wrong

```python
def parse_user_input(data: dict) -> dict:
    # Too strict: rejects valid data over trivial formatting
    if data["role"] != "admin":  # rejects "Admin", "ADMIN", " admin "
        raise ValueError(f"Invalid role: {data['role']}")
    if not isinstance(data["age"], int):  # rejects "25" from form input
        raise ValueError("Age must be integer")
    return data

def generate_api_response(user: dict) -> dict:
    # Too liberal in output: inconsistent, sloppy
    return {
        "Name": user.get("name", ""),    # inconsistent casing
        "age": user.get("age"),           # might be None, string, or int
        "extra_debug_info": user,         # leaks internal structure
    }
```

### ✅ Correct

```python
def parse_user_input(data: dict) -> dict:
    """Liberal in acceptance: tolerate reasonable variations."""
    role = str(data.get("role", "")).strip().lower()
    if role not in {"admin", "user", "viewer"}:
        raise ValueError(f"Invalid role: {data.get('role')!r}")

    try:
        age = int(data["age"])  # accept "25" or 25
    except (KeyError, ValueError, TypeError) as exc:
        raise ValueError(f"Age must be a valid integer, got {data.get('age')!r}") from exc
    if age < 0 or age > 150:
        raise ValueError(f"Age out of range: {age}")
    return {"role": role, "age": age}

def generate_api_response(user: dict) -> dict:
    """Conservative in output: strict, predictable format."""
    return {"name": str(user["name"]), "age": int(user["age"]), "role": str(user["role"])}
```

**Key points:** Input parsing normalizes whitespace and casing (liberal), but still rejects structurally invalid data. Output is strict: consistent key casing, explicit types, no extra fields. The balanced approach accepts reasonable variations without silently swallowing garbage.

---

## 4. Resilience & Graceful Degradation — Continue Operating Despite Partial Failures

A resilient system continues to provide value even when some components fail. Rather than
crashing entirely when a dependency is unavailable, degrade gracefully: serve cached data,
skip non-critical features, or return partial results with a clear indication of what's
missing.

**Key patterns:**

| Pattern | Purpose | Example |
|---|---|---|
| **Exponential backoff with jitter** | Prevent thundering herd on retries | `delay = min(base * 2^attempt + random(), max_delay)` |
| **Circuit breaker** | Stop calling a failing service | After N failures, short-circuit for a cooldown period |
| **Cascading fallback** | Degrade through multiple tiers | Cache → stale cache → default → error |

### ❌ Wrong

```python
def get_product_details(product_id: str) -> dict:
    """No resilience: one failure kills the entire response."""
    product = catalog_service.get(product_id)  # if this times out, everything dies
    reviews = review_service.get(product_id)   # no timeout, blocks forever
    price = pricing_service.get(product_id)    # no fallback
    return {"product": product, "reviews": reviews, "price": price}

def fetch_with_retry(url: str) -> dict:
    """Naive retry: hammers the failing service."""
    for _ in range(10):
        try:
            return requests.get(url, timeout=30).json()
        except Exception:
            time.sleep(1)  # fixed delay, no backoff, no jitter
    raise RuntimeError("Failed after 10 retries")
```

### ✅ Correct

```python
import random, time


def fetch_with_backoff(url: str, max_retries: int = 4, base_delay: float = 0.5) -> dict:
    """Retry with exponential backoff and jitter."""
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            if attempt == max_retries - 1:
                raise
            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), 30)
            time.sleep(delay)


def get_product_details(product_id: str) -> dict:
    """Graceful degradation: partial results beat no results."""
    product = catalog_service.get(product_id)  # critical — let this fail

    try:  # non-critical: degrade gracefully
        reviews = review_service.get(product_id, timeout=2)
    except ServiceUnavailableError:
        reviews = cache.get(f"reviews:{product_id}", default=[])

    try:
        price = pricing_service.get(product_id, timeout=2)
    except ServiceUnavailableError:
        price = product.get("list_price")  # fallback to catalog price

    return {
        "product": product, "reviews": reviews, "price": price,
        "degraded": reviews == [] or price == product.get("list_price"),
    }
```

**Key points:** Exponential backoff with jitter prevents thundering herds. Non-critical dependencies degrade to cached data or defaults instead of killing the entire response. The `degraded` flag tells the caller that the response is partial, maintaining transparency.

---

## 5. Principle of Least Privilege — Minimum Permissions Necessary

Every component — user, service, process, database connection — should operate with the
minimum set of permissions needed to accomplish its task, and only for the duration required.
Excessive privilege turns small bugs into large security incidents.

### ❌ Wrong

```python
def read_user_profile(user_id: str) -> dict:
    # Full admin connection — can DROP tables, read all schemas
    conn = psycopg2.connect(
        host="db.prod.internal",
        user="admin",           # superuser!
        password=ADMIN_PASSWORD,
        dbname="production",
    )
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    return dict(cursor.fetchone())

# IAM policy: full access to everything
s3_policy = {"Effect": "Allow", "Action": "s3:*", "Resource": "*"}
```

### ✅ Correct

```python
def read_user_profile(user_id: str) -> dict:
    """Uses a read-only connection scoped to needed columns."""
    conn = psycopg2.connect(
        host="db.prod.internal",
        user="app_readonly",        # read-only role
        password=READONLY_PASSWORD,
        dbname="production",
    )
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users WHERE id = %s", (user_id,))
    return dict(cursor.fetchone())

# IAM policy: only what's needed, only where it's needed
s3_read_policy = {
    "Effect": "Allow",
    "Action": ["s3:GetObject"],             # read only
    "Resource": "arn:aws:s3:::my-bucket/*",  # one bucket only
}

# Write access is a separate role, scoped to a prefix
s3_write_policy = {
    "Effect": "Allow",
    "Action": ["s3:PutObject"],
    "Resource": "arn:aws:s3:::my-bucket/reports/*",
}
```

**Key points:** The read path uses a read-only database user. IAM policies scope actions (`GetObject` vs `s3:*`) and resources (specific bucket vs `*`). Write access is a separate role scoped to a prefix. If the read-only connection is compromised, the attacker cannot modify or delete data.

---

## 6. Boy Scout Rule — Leave Code Better Than You Found It

When you touch a file to add a feature or fix a bug, leave it a little cleaner than you
found it. Rename a misleading variable, extract a confusing conditional, add a missing
type hint. Small, incremental improvements compound over time and prevent codebase decay.

**Clean the campground, not the forest:** The rule applies to code you are already
modifying, not to unrelated files. A drive-by cleanup of an entire module when you were
asked to fix a one-line bug is scope creep that introduces risk and muddies the diff.

### ❌ Wrong

```python
# You need to add email validation to this function.
# The existing code is messy, but you just add your feature on top.
def reg(d):
    # not my problem that this is unreadable
    u = d["u"]
    p = d["p"]
    e = d["e"]
    if len(p) < 8:
        return {"ok": False, "msg": "bad pw"}
    # your new feature bolted on
    if "@" not in e:
        return {"ok": False, "msg": "bad email"}
    db.execute("INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
               (u, p, e))
    return {"ok": True}
```

### ✅ Correct

```python
# You clean up what you touch while adding the email validation.
def register_user(data: dict) -> dict:
    username = data["username"]         # renamed from 'u'
    password = data["password"]         # renamed from 'p'
    email = data["email"]              # renamed from 'e'

    if len(password) < 8:
        return {"ok": False, "msg": "Password must be at least 8 characters"}

    if "@" not in email:               # your new feature
        return {"ok": False, "msg": "Invalid email address"}

    db.execute(
        "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)",
        (username, password, email),
    )
    return {"ok": True}
```

**Key points:** You were going to modify this function anyway, so renaming variables and improving the error message costs almost nothing. The function name, parameter names, and error messages are all clearer. You did not refactor the entire module — just the code you were already touching.

---

## 7. Observability & Transparency — Understand What Systems Do in Production

Code that cannot be observed in production is code that cannot be debugged, tuned, or
trusted. Build observability in from the start: structured logs for events, metrics for
trends, and traces for request flow. The goal is to answer "what is happening and why?"
from outside the process.

**Three pillars:**

| Pillar | Purpose | Key Practice |
|---|---|---|
| **Logs** | Record discrete events | Structured (JSON), with correlation IDs |
| **Metrics** | Track aggregate trends | Counters, gauges, histograms (latency, error rate) |
| **Traces** | Follow a request across services | Distributed trace IDs propagated in headers |

**Anti-patterns:**

| Anti-Pattern | Problem |
|---|---|
| Silent failure | `except: pass` — errors vanish without trace |
| Opaque errors | `raise Exception("Error")` — no context, no cause |
| Logging secrets | `logger.info(f"Auth: {token}")` — credentials in plaintext |
| Print debugging | `print("here")` — no severity, no structure, no rotation |
| Log everything | Gigabytes of noise drown real signals |

### ❌ Wrong

```python
def process_payment(order_id: str, amount: float) -> bool:
    try:
        result = payment_gateway.charge(amount)
        return True
    except Exception:
        return False  # silent failure: nobody knows this failed or why

def authenticate(request) -> dict:
    token = request.headers.get("Authorization")
    print(f"DEBUG: auth token = {token}")  # logging secrets in plaintext
    user = verify_token(token)
    if not user:
        raise Exception("Auth failed")  # opaque: no context for debugging
    return user
```

### ✅ Correct

```python
import logging
import time

logger = logging.getLogger(__name__)


def process_payment(order_id: str, amount: float) -> bool:
    start = time.monotonic()
    try:
        result = payment_gateway.charge(amount)
        duration_ms = (time.monotonic() - start) * 1000
        logger.info("Payment processed", extra={
            "order_id": order_id, "amount": amount,
            "charge_id": result.charge_id, "duration_ms": round(duration_ms, 2),
        })
        PAYMENT_COUNTER.labels(status="success").inc()
        return True
    except PaymentGatewayError as exc:
        logger.error("Payment failed", extra={
            "order_id": order_id, "error_type": type(exc).__name__,
            "error_message": str(exc),
        })
        PAYMENT_COUNTER.labels(status="failure").inc()
        raise


def authenticate(request) -> dict:
    token = request.headers.get("Authorization")
    # Log presence, not value — never log secrets
    logger.debug("Auth attempt", extra={
        "has_token": token is not None,
        "token_prefix": token[:8] + "..." if token else None,
    })
    user = verify_token(token)
    if not user:
        logger.warning("Auth failed", extra={"ip": request.remote_addr})
        raise AuthenticationError(f"Invalid or expired token from {request.remote_addr}")
    return user
```

**Key points:** Structured logging (`extra={}`) enables machine parsing and filtering. Metrics (counters, histograms) enable dashboards and alerts. Secrets are never logged — only presence and a safe prefix. Errors include context (order ID, IP, duration) so on-call engineers can diagnose without reproducing locally.

---

## When to Relax Rules

| Principle | Relax When | Example |
|---|---|---|
| **Fail-Fast** | Batch processing where partial results are valuable | Log the error, skip the bad record, continue processing |
| **Design by Contract** | Performance-critical inner loops where assertions add overhead | Disable with `python -O` after thorough testing |
| **Postel's Law** | Security-sensitive input (auth tokens, SQL, HTML) | Reject anything that doesn't match the exact expected format |
| **Resilience** | Data integrity operations where partial results are dangerous | Financial transactions must be all-or-nothing, not degraded |
| **Least Privilege** | Local development and prototyping | Use broader permissions locally, but never deploy them to production |
| **Boy Scout Rule** | Under tight deadline with no test coverage | Don't refactor code you can't verify — note it as tech debt instead |
| **Observability** | Extremely hot paths where logging adds latency | Sample logs (1 in 1000) instead of logging every event |
