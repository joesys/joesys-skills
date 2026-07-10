# Correctness Principles

## Quick Diagnostic Guide

| Symptom | Likely Category |
|---|---|
| `IndexError` or unexpected slice results | Off-by-One Errors |
| `AttributeError: 'NoneType' has no attribute` | Null/Undefined Handling |
| Condition fires when it should not (or vice versa) | Boolean Logic Errors |
| Crash on empty input, zero, negative number, or Unicode | Edge Cases |
| Intermittent, non-reproducible bug that vanishes under debugger | Race Conditions & Concurrency |
| Function returns wrong value despite correct logic in body | Incorrect Return Values |
| Data mysteriously changes, or stale value served after update | State Management Bugs |
| Exception swallowed silently, or wrong exception caught | Error Handling Gaps |

## Common Bug Detection Heuristics

Use these heuristics as a first-pass scan when reviewing code for correctness:

| Heuristic | What to Look For |
|---|---|
| **Boundary smell** | Any `+1`, `-1`, `len(x)`, `range(...)`, slice notation — verify the bounds manually |
| **None path** | Every `.attribute` access or `[key]` lookup — can the object be `None`? Can the key be missing? |
| **Negation smell** | `not`, `!=`, `and`/`or` chains — mentally negate the condition and check if the inverted behavior is correct |
| **Empty collection smell** | `items[0]`, `min(items)`, `sum(x)/len(x)` — what happens when the collection has zero elements? |
| **Shared reference smell** | Mutable default arguments, global state, objects passed by reference — who else holds a reference? |
| **Silent None return** | Any function that lacks a `return` in some branch — Python returns `None` implicitly |
| **Broad except smell** | `except Exception`, `except:`, `except BaseException` — is the caught type too wide? |
| **Check-then-act smell** | `if file_exists(x): open(x)` — can the state change between the check and the action? |

---

## 1. Off-by-One Errors — The Most Common Bug in Programming

An off-by-one error (OBOE) occurs when a loop iterates one time too many or too few, an
index is one position off, or a boundary condition is `<` when it should be `<=`. These
bugs are pervasive because humans think in terms of counts (1-based) while most programming
languages use 0-based indexing.

**Common in:** loop bounds, string slicing, pagination (`page * size` vs. `(page - 1) * size`), fence-post problems (N items need N-1 separators), array indexing.

### ❌ Wrong

```python
def get_elements_in_range(arr: list[int], start: int, end: int) -> list[int]:
    """Return elements from index start to end, inclusive."""
    result = []
    for i in range(start, end):  # Bug: excludes 'end', should be end + 1
        result.append(arr[i])
    return result

def paginate(items: list, page: int, page_size: int) -> list:
    """Get a page of items (1-based page number)."""
    offset = page * page_size  # Bug: page 1 skips first page_size items
    return items[offset:offset + page_size]

def process_all(data: list[str]) -> list[str]:
    for i in range(len(data) + 1):  # Bug: IndexError on last iteration
        data[i] = data[i].upper()
    return data
```

### ✅ Correct

```python
def get_elements_in_range(arr: list[int], start: int, end: int) -> list[int]:
    """Return elements from index start to end, inclusive."""
    return arr[start:end + 1]  # Slice end is exclusive, so +1 for inclusive

def paginate(items: list, page: int, page_size: int) -> list:
    """Get a page of items (1-based page number)."""
    if page < 1:
        raise ValueError(f"Page must be >= 1, got {page}")
    offset = (page - 1) * page_size  # Page 1 → offset 0
    return items[offset:offset + page_size]

def process_all(data: list[str]) -> list[str]:
    # Prefer enumerate or direct iteration — no index math, no OBOE possible
    return [item.upper() for item in data]
```

**Key points:** Prefer `enumerate()`, `zip()`, and list comprehensions over manual index arithmetic — they eliminate OBOEs entirely. When index math is unavoidable, verify bounds by substituting the first and last valid values mentally.

---

## 2. Null/Undefined Handling — The Billion-Dollar Mistake

`None` in Python (and `null` in other languages) represents the absence of a value, but
code that accesses attributes or methods on `None` crashes immediately. The danger is that
`None` can propagate silently through a system before finally causing an error far from its
origin, making debugging difficult.

**Common in:** chained attribute access (`user.profile.address`), `.get()` results consumed without null check, functions that return `None` on failure, optional fields in API responses.

### ❌ Wrong

```python
def get_user_city(user: dict) -> str:
    # Crashes if 'profile' or 'address' is missing or None
    return user["profile"]["address"]["city"].lower()

def find_user(db, user_id: int):
    result = db.query("SELECT * FROM users WHERE id = %s", (user_id,))
    # Returns None if no rows — caller will crash when accessing .name
    if result:
        return result[0]

def format_name(user) -> str:
    # No check: crashes with AttributeError if user.name is None
    return user.name.strip().title()
```

### ✅ Correct

```python
from typing import Optional

def get_user_city(user: dict) -> Optional[str]:
    """Safely navigate nested dicts, returning None if any key is missing."""
    profile = user.get("profile") or {}
    address = profile.get("address") or {}
    city = address.get("city")
    return city.lower() if city else None

def find_user(db, user_id: int) -> dict:
    """Raise explicitly when user not found — never return None silently."""
    result = db.query("SELECT * FROM users WHERE id = %s", (user_id,))
    if not result:
        raise UserNotFoundError(f"No user with id {user_id}")
    return result[0]

def format_name(user) -> str:
    """Guard against None before accessing attributes."""
    if user.name is None:
        raise ValueError("User name must not be None")
    return user.name.strip().title()
```

**Key points:** Guard against `None` at the point of access. When a function cannot produce a meaningful result, raise an exception rather than returning `None` silently. Use type hints (`Optional[X]`) to document which values may be `None`.

---

## 3. Boolean Logic Errors — When Conditions Lie

Boolean logic errors occur when a condition does not express the programmer's actual intent.
These bugs are insidious because the code reads plausibly but evaluates differently. De
Morgan's law violations, inverted conditions, and operator precedence mistakes are the most
frequent causes.

**Common in:** De Morgan confusion (`not a and not b` vs. `not (a or b)`), inverted conditions, operator precedence traps (`a or b and c` evaluates as `a or (b and c)`), wrong comparison operators.

### ❌ Wrong

```python
def should_send_notification(user) -> bool:
    # Intent: send notification if user is NOT (active AND subscribed)
    # Bug: De Morgan — this checks if user is (inactive AND unsubscribed)
    if not user.is_active and not user.is_subscribed:
        return True
    return False

def can_access_resource(user, resource) -> bool:
    # Intent: (admin OR owner) AND resource is not locked
    # Bug: precedence — `and` binds tighter, so admin bypasses the lock check
    if user.is_admin or user.id == resource.owner_id and not resource.is_locked:
        return True
    return False

def filter_invalid_entries(entries: list[dict]) -> list[dict]:
    # Intent: remove entries where status is "deleted" or "archived"
    # Bug: inverted condition — this KEEPS deleted and archived entries
    return [e for e in entries if e["status"] == "deleted" or e["status"] == "archived"]
```

### ✅ Correct

```python
def should_send_notification(user) -> bool:
    """Send notification if user is NOT (active AND subscribed)."""
    is_fully_opted_in = user.is_active and user.is_subscribed
    return not is_fully_opted_in

def can_access_resource(user, resource) -> bool:
    """Access allowed if (admin OR owner) AND resource is not locked."""
    has_permission = user.is_admin or user.id == resource.owner_id
    is_accessible = not resource.is_locked
    return has_permission and is_accessible

def filter_invalid_entries(entries: list[dict]) -> list[dict]:
    """Remove entries that are deleted or archived."""
    excluded_statuses = {"deleted", "archived"}
    return [e for e in entries if e["status"] not in excluded_statuses]
```

**Key points:** Extract complex boolean expressions into named variables — `is_fully_opted_in` is self-documenting where `not a and not b` is ambiguous. Use explicit parentheses to clarify operator precedence. When in doubt, build a truth table to verify the condition matches intent.

---

## 4. Edge Cases — The Inputs Nobody Thought About

Edge case bugs occur when code works correctly for typical inputs but fails at boundary
values: zero, empty collections, negative numbers, extremely large values, empty strings,
or Unicode. These are not exotic scenarios — they are the first thing an attacker or a
production dataset will exercise.

**Common in:** empty collections (`items[0]`, `sum(x)/len(x)`), zero/negative numbers (division, modulo, negative index wrap-around), empty strings (`"".split("/")[1]`), Unicode (`len("cafe\u0301")` is 5 not 4), very large inputs.

### ❌ Wrong

```python
def average(values: list[float]) -> float:
    # Bug: ZeroDivisionError when values is empty
    return sum(values) / len(values)

def get_first_element(items: list) -> object:
    # Bug: IndexError when items is empty
    return items[0]

def calculate_discount(price: float, quantity: int) -> float:
    # Bug: no guard for zero or negative quantity
    per_unit = price / quantity
    if quantity > 10:
        return per_unit * 0.9 * quantity
    return price

def parse_path(filepath: str) -> str:
    """Extract directory from path."""
    return filepath.split("/")[1]  # Bug: IndexError on "file.txt" (no separator)
```

### ✅ Correct

```python
from typing import Optional

def average(values: list[float]) -> Optional[float]:
    """Return the arithmetic mean, or None if the list is empty."""
    if not values:
        return None
    return sum(values) / len(values)

def get_first_element(items: list, default=None):
    """Return first element, or default if empty."""
    return items[0] if items else default

def calculate_discount(price: float, quantity: int) -> float:
    """Calculate total price with bulk discount."""
    if quantity <= 0:
        raise ValueError(f"Quantity must be positive, got {quantity}")
    if price < 0:
        raise ValueError(f"Price must be non-negative, got {price}")
    total = price * quantity
    if quantity > 10:
        total *= 0.9  # 10% bulk discount
    return total

def parse_path(filepath: str) -> str:
    """Extract filename from a path string safely."""
    if not filepath:
        raise ValueError("File path must not be empty")
    return os.path.basename(filepath)  # Handles edge cases: no separator, trailing slash
```

**Key points:** Handle boundary values at function entry with guard clauses. Test with: empty collection, single element, zero, negative, empty string, `None`. Prefer library functions (`os.path.basename`) over manual parsing — they handle edge cases you will forget.

---

## 5. Race Conditions & Concurrency — When Timing Is the Bug

A race condition occurs when the correctness of a program depends on the relative timing
of operations. The most common form is check-then-act (TOCTOU — Time of Check to Time of
Use): you check a condition, then act on it, but the condition changes between the check
and the action.

**Common in:** check-then-act (TOCTOU — `if file_exists(x): open(x)`), shared mutable state without locks, lazy initialization races, non-atomic read-modify-write sequences.

### ❌ Wrong

```python
import os, threading

# TOCTOU: file can be deleted between check and use
def read_config(path: str) -> str:
    if os.path.exists(path):  # Check
        with open(path) as f:  # Act — file may no longer exist
            return f.read()
    return ""

# Shared mutable state without synchronization
class Counter:
    def __init__(self):
        self.count = 0

    def increment(self):
        # Not atomic: read, add, write can interleave across threads
        self.count += 1
# Two threads calling counter.increment() 100k times each
# Result is non-deterministic, almost always < 200_000
```

### ✅ Correct

```python
import threading
from pathlib import Path

# EAFP: try the operation directly, handle failure
def read_config(path: str) -> str:
    try:
        return Path(path).read_text()
    except FileNotFoundError:
        return ""

# Thread-safe counter using a lock
class Counter:
    def __init__(self):
        self._count = 0
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:
            self._count += 1

    @property
    def count(self) -> int:
        with self._lock:
            return self._count
```

**Key points:** Replace check-then-act with EAFP (try the operation, catch the exception). Protect shared mutable state with locks, or eliminate sharing via message-passing (queues) or immutable data. `+=` is not atomic in Python even with the GIL.

---

## 6. Incorrect Return Values — The Function That Lies

An incorrect return value bug occurs when a function's return value does not match what the
caller expects. This happens through variable shadowing, missing return statements in
conditional branches (which silently return `None`), or accidentally returning the input
instead of the transformed result.

**Common in:** missing `return` in a conditional branch (implicit `None`), variable shadowing, returning input instead of output (typo), inconsistent return types across branches.

### ❌ Wrong

```python
def classify_age(age: int) -> str:
    if age < 13:
        return "child"
    elif age < 20:
        return "teenager"
    elif age < 65:
        return "adult"
    # Bug: no return for age >= 65 — implicitly returns None
    # Caller doing classify_age(70).upper() will crash

def transform_data(data: list[dict]) -> list[dict]:
    result = []
    for item in data:
        result.append({
            "name": item["name"].upper(),
            "value": item["value"] * 2,
        })
    return data  # Bug: returns original input, not transformed result
```

### ✅ Correct

```python
def classify_age(age: int) -> str:
    """Classify age into a life stage. All branches return explicitly."""
    if age < 0:
        raise ValueError(f"Age cannot be negative, got {age}")
    if age < 13:
        return "child"
    if age < 20:
        return "teenager"
    if age < 65:
        return "adult"
    return "senior"  # Explicit return for the final case

def transform_data(data: list[dict]) -> list[dict]:
    """Transform data — return the result, not the input."""
    result = []
    for item in data:
        result.append({
            "name": item["name"].upper(),
            "value": item["value"] * 2,
        })
    return result  # Correct: returns the transformed list
```

**Key points:** Every code path must have an explicit `return` — use linters (`mypy --warn-return-any`, `pylint`) to catch implicit `None` returns. Use distinct variable names to prevent shadowing. When a built-in exists (`max`, `min`, `sorted`), use it instead of reimplementing.

---

## 7. State Management Bugs — When Data Has a Mind of Its Own

State management bugs occur when the program's in-memory data diverges from its expected
value. This happens through accidental mutation of shared objects, stale cached values, and
incorrect initialization order. These bugs are especially difficult to diagnose because the
corruption often occurs far from where the symptom appears.

**Common in:** mutable default arguments (`def f(items=[])`), aliased mutation (modifying a passed-in list), stale cached values, wrong initialization order in `__init__`, global mutable state.

### ❌ Wrong

```python
def add_item(item: str, items: list = []) -> list:
    # Bug: mutable default — the same list is reused across all calls
    items.append(item)
    return items
# add_item("a") → ["a"]
# add_item("b") → ["a", "b"]  — surprise! "a" is still there

class UserService:
    def __init__(self, db):
        # Bug: initialization order — using self._cache before it's defined
        self._load_users()  # Calls method that uses self._cache
        self._cache = {}    # Too late — _load_users already failed

    def _load_users(self):
        self._cache["users"] = self._db.get_all_users()  # AttributeError

def process_records(records: list[dict]) -> list[dict]:
    """Add a 'processed' flag to each record."""
    for record in records:
        record["processed"] = True  # Bug: mutates the caller's data
    return records
```

### ✅ Correct

```python
from typing import Optional

def add_item(item: str, items: Optional[list] = None) -> list:
    """Use None sentinel for mutable defaults."""
    if items is None:
        items = []
    items.append(item)
    return items

class UserService:
    def __init__(self, db):
        self._db = db
        self._cache: dict = {}    # Initialize BEFORE use
        self._load_users()        # Now self._cache exists

    def _load_users(self):
        self._cache["users"] = self._db.get_all_users()

def process_records(records: list[dict]) -> list[dict]:
    """Return new list with 'processed' flag — do not mutate input."""
    return [{**record, "processed": True} for record in records]
```

**Key points:** Never use mutable objects (`list`, `dict`, `set`) as default arguments — use `None` and create a fresh instance inside the function. Decide explicitly whether a function mutates in place (document it) or returns a copy. Initialize all attributes in `__init__` before calling methods.

---

## 8. Error Handling Gaps — When Failures Fall Through the Cracks

Error handling gaps occur when code catches exceptions too broadly, swallows them silently,
catches the wrong type, or fails to preserve error context. The result is that failures
become invisible or untraceable — the system continues in a corrupt state, or the error
message tells you nothing about the root cause.

**Common in:** bare `except: pass` (invisible failures), catching `Exception` too broadly, catching the wrong exception type, missing `from exc` error chaining, partial operations without rollback.

### ❌ Wrong

```python
import json

def load_config(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except:  # Bug: catches EVERYTHING — KeyboardInterrupt, SystemExit, MemoryError
        pass  # Bug: silently returns None — caller has no idea config failed to load

def transfer_funds(from_acct, to_acct, amount: float) -> None:
    try:
        from_acct.debit(amount)
        to_acct.credit(amount)  # If credit fails, debit is not rolled back
    except Exception as e:
        print(f"Transfer failed: {e}")  # Swallowed — caller thinks it succeeded

def parse_user_input(data: str) -> dict:
    try:
        return json.loads(data)
    except ValueError:  # Bug: too broad — catches unrelated errors too
        return {}  # Caller gets empty dict — indistinguishable from valid empty input
```

### ✅ Correct

```python
import json
import logging

logger = logging.getLogger(__name__)

def load_config(path: str) -> dict:
    """Load configuration — fail explicitly if the file is missing or malformed."""
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        raise ConfigError(f"Config file not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path}: {exc}") from exc

def transfer_funds(from_acct, to_acct, amount: float) -> None:
    """Transfer with rollback on failure."""
    from_acct.debit(amount)
    try:
        to_acct.credit(amount)
    except Exception:
        # Roll back the debit before re-raising
        from_acct.credit(amount)
        raise  # Preserve original exception and traceback

def parse_user_input(data: str) -> dict:
    """Parse JSON input — raise on invalid data with chained context."""
    try:
        result = json.loads(data)
    except json.JSONDecodeError as exc:
        raise InvalidInputError(f"Expected valid JSON, got {data[:100]!r}") from exc
    if not isinstance(result, dict):
        raise InvalidInputError(f"Expected JSON object, got {type(result).__name__}")
    return result
```

**Key points:** Catch the most specific exception type — `json.JSONDecodeError`, not `Exception`. Never use bare `except: pass`. Use `raise ... from exc` to chain exceptions and preserve the original traceback. When multi-step operations can partially fail, implement rollback or use transactions.

---

## Summary: Correctness Review Checklist

| # | Category | Key Question |
|---|---|---|
| 1 | Off-by-One Errors | Are loop bounds and slice indices correct at both ends? |
| 2 | Null/Undefined Handling | Can any variable be `None` at the point of access? |
| 3 | Boolean Logic Errors | Does the condition express the actual intent? (Test by negation.) |
| 4 | Edge Cases | What happens with zero, empty, negative, or very large inputs? |
| 5 | Race Conditions | Can state change between a check and the subsequent action? |
| 6 | Incorrect Return Values | Does every code path return the correct value of the correct type? |
| 7 | State Management | Is mutable state copied, not aliased? Are defaults immutable? |
| 8 | Error Handling Gaps | Are exceptions specific, chained, and never swallowed? |
