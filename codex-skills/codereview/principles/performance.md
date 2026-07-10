# Performance Principles

## Quick Diagnostic Guide

| Symptom | Likely Principle |
|---|---|
| Nested loops searching or matching across two collections | Algorithm Complexity |
| One database query per item in a loop | N+1 Queries |
| String concatenation with `+=` inside a loop | Unnecessary Allocations/Copies |
| `time.sleep()` or `requests.get()` inside an `async def` | Blocking I/O in Async Contexts |
| Same expensive computation repeated on every request | Missing Caching |
| File handles opened but never closed, unbounded list growth | Memory Leaks / Resource Management |
| Loading an entire table when only 10 rows are displayed | Lazy vs. Eager Loading |
| Optimizing code that runs once at startup | Premature vs. Legitimate Optimization |

## Principle Tensions

| Tension | Guidance |
|---|---|
| **Caching vs. Correctness** | Caching stale data is worse than recomputing. Always define an invalidation strategy before adding a cache. If you cannot articulate when the cache becomes stale, do not cache. |
| **Lazy Loading vs. N+1 Queries** | Lazy loading avoids fetching unused data but can trigger N+1 queries when you iterate. Use eager loading when you know you will access all related objects; use lazy loading when most calls never touch the relation. |
| **Readability vs. Performance** | A readable O(n^2) solution is fine for small n. Only replace it with a harder-to-read O(n) solution when profiling shows the readable version is a bottleneck. Comment the optimization so future readers know why. |
| **Pre-allocation vs. YAGNI** | Pre-allocating buffers or pools adds complexity. Do it only when allocation cost is measured and significant — not because it "might be faster." |
| **Async vs. Simplicity** | Async code is harder to read, debug, and test. Use it when I/O concurrency is a proven requirement, not as a default architectural choice. |
| **Eager Optimization vs. Profiling First** | Never optimize without evidence. A profiler tells you where time is actually spent. Intuition about bottlenecks is wrong more often than right. |

---

## 1. Algorithm Complexity — Choose the Right Data Structure

The single highest-impact performance decision is algorithmic. Moving from O(n^2) to O(n) or O(1)
is not premature optimization — it is choosing the correct tool. When you see nested iteration over
a collection to find matches, a set or dictionary lookup almost always eliminates the inner loop.

### ❌ Wrong

```python
def find_common_users(active_users: list[str], premium_users: list[str]) -> list[str]:
    """O(n * m) — scans premium_users for every active user."""
    common = []
    for user in active_users:
        for premium in premium_users:
            if user == premium:
                common.append(user)
                break
    return common
```

### ✅ Correct

```python
def find_common_users(active_users: list[str], premium_users: list[str]) -> list[str]:
    """O(n + m) — set lookup is O(1) per check."""
    premium_set = set(premium_users)
    return [user for user in active_users if user in premium_set]
```

**When to care:** Large collections (thousands+ elements), hot paths called per-request, or any
code inside a loop that itself runs many times. For a list of 10 items, the nested loop is fine.

**Key points:**
- Nested loops over two collections are almost always replaceable with set/dict lookups.
- `in` on a list is O(n); `in` on a set is O(1).
- Sorting + binary search (O(n log n)) beats nested loops but loses to hash-based lookups.
- If you need both membership testing and ordering, use a sorted container or combine structures.

---

## 2. N+1 Queries — Batch Your Database Access

An N+1 query occurs when code issues one query to fetch a list of N items, then issues N additional
queries to fetch related data for each item. This turns a constant number of round-trips into a
linear number, and network latency dominates execution time.

### ❌ Wrong

```python
# SQLAlchemy — lazy loading triggers one SELECT per order
def get_order_summaries(session: Session) -> list[dict]:
    orders = session.query(Order).all()  # 1 query
    return [
        {
            "id": order.id,
            "customer": order.customer.name,  # +1 query per order
            "items": len(order.items),         # +1 query per order
        }
        for order in orders
    ]
```

### ✅ Correct

```python
# SQLAlchemy — eager loading with joinedload
from sqlalchemy.orm import joinedload

def get_order_summaries(session: Session) -> list[dict]:
    orders = (
        session.query(Order)
        .options(joinedload(Order.customer), joinedload(Order.items))
        .all()
    )  # 1 query with JOINs
    return [
        {
            "id": order.id,
            "customer": order.customer.name,
            "items": len(order.items),
        }
        for order in orders
    ]


# Django — select_related for FK, prefetch_related for M2M
def get_order_summaries() -> list[dict]:
    orders = Order.objects.select_related("customer").prefetch_related("items").all()
    return [
        {
            "id": order.id,
            "customer": order.customer.name,
            "items": order.items.count(),
        }
        for order in orders
    ]
```

**When to care:** Always. N+1 queries are never acceptable in production code. Even for small N,
they establish a pattern that scales catastrophically. Catch them in code review, not in production.

**Key points:**
- Use `joinedload` / `subqueryload` (SQLAlchemy), `select_related` / `prefetch_related` (Django).
- For raw SQL, use JOINs or `WHERE id IN (...)` instead of per-row SELECTs.
- Enable query logging in development to spot N+1 patterns early.
- Pagination does not fix N+1 — it just caps N per page.

---

## 3. Unnecessary Allocations/Copies — Avoid Wasteful Object Creation

Creating objects costs CPU and memory. In tight loops, unnecessary allocations dominate runtime.
String concatenation with `+=` is the classic example: each concatenation creates a new string
object and copies all previous content, turning an O(n) operation into O(n^2).

### ❌ Wrong

```python
def build_report(records: list[dict]) -> str:
    """O(n^2) — each += copies the entire string so far."""
    report = ""
    for record in records:
        report += f"Name: {record['name']}, Score: {record['score']}\n"
    return report


def process_large_file(path: str) -> list[str]:
    """Loads entire file into memory, then creates a second copy as a list."""
    with open(path) as f:
        content = f.read()
    return content.splitlines()
```

### ✅ Correct

```python
def build_report(records: list[dict]) -> str:
    """O(n) — join allocates once."""
    lines = [f"Name: {record['name']}, Score: {record['score']}" for record in records]
    return "\n".join(lines)


def process_large_file(path: str):
    """Yields one line at a time — constant memory regardless of file size."""
    with open(path) as f:
        for line in f:
            yield line.rstrip("\n")
```

**When to care:** Loops with hundreds or more iterations, large file processing, or any path where
allocation shows up in profiling. For building a string from 5 items, `+=` is perfectly fine.

**Key points:**
- Use `"".join()` instead of `+=` in loops for string building.
- Use generators (`yield`) instead of lists when the consumer processes items one at a time.
- Pre-allocate lists with a known size when appropriate: `[None] * n` beats repeated `.append()`.
- Avoid creating temporary objects (dicts, dataclasses) inside tight loops when a tuple suffices.

---

## 4. Blocking I/O in Async Contexts — Never Block the Event Loop

In async code, the event loop is single-threaded. A blocking call (synchronous I/O, `time.sleep()`,
CPU-heavy computation) freezes the entire loop, stalling all concurrent tasks. This defeats the
purpose of async and causes latency spikes across unrelated requests.

### ❌ Wrong

```python
import asyncio
import time
import requests


async def fetch_and_wait(url: str) -> str:
    time.sleep(2)                        # blocks the entire event loop for 2 seconds
    response = requests.get(url)         # blocks again — no other coroutine can run
    return response.text


async def main():
    # These run SEQUENTIALLY because each one blocks the loop
    results = await asyncio.gather(
        fetch_and_wait("https://api.example.com/a"),
        fetch_and_wait("https://api.example.com/b"),
    )
```

### ✅ Correct

```python
import asyncio
import httpx


async def fetch_and_wait(url: str) -> str:
    await asyncio.sleep(2)               # yields control — other coroutines run during the wait
    async with httpx.AsyncClient() as client:
        response = await client.get(url) # non-blocking I/O
    return response.text


async def main():
    # These run CONCURRENTLY — total time ~2s, not ~4s
    results = await asyncio.gather(
        fetch_and_wait("https://api.example.com/a"),
        fetch_and_wait("https://api.example.com/b"),
    )
```

**When to care:** Any codebase using `asyncio`, FastAPI, Starlette, or other async frameworks.
If you are writing synchronous Flask or Django views, blocking I/O is expected and this does
not apply.

**Key points:**
- `time.sleep()` blocks; `await asyncio.sleep()` yields.
- `requests` is synchronous; use `httpx` or `aiohttp` in async code.
- For unavoidable sync calls, offload to a thread: `await asyncio.to_thread(sync_function)`.
- CPU-bound work in async code should use `ProcessPoolExecutor`, not threads.

---

## 5. Missing Caching — Do Not Recompute What Has Not Changed

When a function produces the same result for the same inputs and the computation is expensive,
cache it. Network calls, database queries, complex calculations, and file parsing are all
candidates. But caching is not free — it trades memory for speed and introduces a staleness risk.

### ❌ Wrong

```python
def get_user_permissions(user_id: int) -> set[str]:
    """Hits the database on every single call, even within the same request."""
    user = db.query(User).get(user_id)
    roles = db.query(Role).filter(Role.user_id == user_id).all()
    return {perm for role in roles for perm in role.permissions}


# Called 15 times per request with the same user_id
```

### ✅ Correct

```python
import functools

@functools.lru_cache(maxsize=256)
def get_user_permissions(user_id: int) -> frozenset[str]:
    """Cached — subsequent calls with the same user_id skip the database."""
    user = db.query(User).get(user_id)
    roles = db.query(Role).filter(Role.user_id == user_id).all()
    return frozenset(perm for role in roles for perm in role.permissions)


# For request-scoped caching, use a dict on the request object:
def get_user_permissions_request_scoped(request, user_id: int) -> set[str]:
    cache_key = f"perms:{user_id}"
    if cache_key not in request.state.cache:
        request.state.cache[cache_key] = _fetch_permissions(user_id)
    return request.state.cache[cache_key]
```

**When to care:** Functions called repeatedly with the same arguments within a request or process
lifetime. Expensive computations (>10ms) that produce deterministic results.

**When NOT to cache:**
- **Frequently changing data** — stale cache causes bugs harder to debug than slow queries.
- **Security-sensitive data** — cached auth tokens or permissions can outlive revocation.
- **Large result sets** — caching 10,000 ORM objects consumes memory without proportional benefit.
- **Non-deterministic functions** — caching `random()` or `datetime.now()` is always a bug.

**Key points:**
- `@functools.lru_cache` for pure functions with hashable arguments.
- Use `@functools.cache` (Python 3.9+) for unbounded caching of truly stable data.
- For distributed systems, use Redis or Memcached with explicit TTLs.
- Always define an invalidation strategy alongside the caching strategy.

---

## 6. Memory Leaks / Resource Management — Clean Up After Yourself

In garbage-collected languages, "memory leak" usually means retaining references longer than
necessary — growing lists without bounds, event listeners never removed, or file handles never
closed. These degrade performance gradually, making them hard to catch in testing but devastating
in production.

### ❌ Wrong

```python
class EventProcessor:
    def __init__(self):
        self.history = []  # grows without bound

    def process(self, event: dict) -> None:
        self.history.append(event)  # never trimmed — OOM after hours/days
        self._handle(event)


def read_all_configs(paths: list[str]) -> list[dict]:
    configs = []
    for path in paths:
        f = open(path)       # file handle never closed
        configs.append(json.load(f))
    return configs
```

### ✅ Correct

```python
from collections import deque


class EventProcessor:
    def __init__(self, max_history: int = 1000):
        self.history = deque(maxlen=max_history)  # bounded — oldest items auto-evicted

    def process(self, event: dict) -> None:
        self.history.append(event)
        self._handle(event)


def read_all_configs(paths: list[str]) -> list[dict]:
    configs = []
    for path in paths:
        with open(path) as f:  # context manager guarantees closure
            configs.append(json.load(f))
    return configs
```

**When to care:** Long-running processes (servers, workers, daemons). Batch jobs processing large
datasets. Any code that accumulates state over time.

**Key points:**
- Use context managers (`with`) for files, connections, locks, and transactions.
- Bound collections with `deque(maxlen=...)` or explicit eviction.
- Watch for closures and callbacks that capture references to large objects.
- Use `weakref` when observers should not prevent garbage collection.
- Profile memory with `tracemalloc` or `objgraph` when leaks are suspected.

---

## 7. Lazy vs. Eager Loading — Load Only What You Need, When You Need It

Eager loading fetches everything upfront; lazy loading defers fetching until access. Neither is
universally better. Eager loading avoids N+1 queries but wastes resources when data goes unused.
Lazy loading saves resources but can trigger unexpected I/O at inconvenient times.

### ❌ Wrong

```python
def get_user_dashboard(user_id: int) -> dict:
    """Loads ALL orders — even though the dashboard shows only the 5 most recent."""
    user = db.query(User).get(user_id)
    all_orders = db.query(Order).filter(Order.user_id == user_id).all()  # could be 50,000 rows
    return {
        "user": user.name,
        "recent_orders": all_orders[:5],
        "total_orders": len(all_orders),
    }
```

### ✅ Correct

```python
def get_user_dashboard(user_id: int) -> dict:
    """Loads only what is displayed — count via SQL, recent via LIMIT."""
    user = db.query(User).get(user_id)
    recent_orders = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .limit(5)
        .all()
    )
    total_orders = (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .count()
    )
    return {
        "user": user.name,
        "recent_orders": recent_orders,
        "total_orders": total_orders,
    }
```

**When to care:** Any query that can return an unbounded number of rows. API endpoints that display
paginated data. Reports that aggregate over large datasets.

**Key points:**
- Use `LIMIT`/`OFFSET` or keyset pagination to avoid loading full tables.
- Use SQL aggregates (`COUNT`, `SUM`, `AVG`) instead of loading rows and computing in Python.
- Generators and iterators are the in-memory equivalent of lazy loading.
- Beware of lazy loading in ORMs — it saves memory but may trigger N+1 (see Principle 2).

---

## 8. Premature vs. Legitimate Optimization — Know When to Care

"Premature optimization is the root of all evil" is the most misquoted line in computer science.
Knuth's full quote advocates against optimizing *small efficiencies* without measurement — not
against thinking about performance at all. Choosing the right algorithm, avoiding N+1 queries, and
not blocking the event loop are not premature optimizations. They are basic competence.

### ❌ Wrong — Premature Optimization

```python
# Micro-optimizing startup code that runs once
config = {}
keys = ("host", "port", "debug")
# Using tuple instead of list "because tuples are faster"
for i in range(len(keys)):  # range(len()) "to avoid iterator overhead"
    config[keys[i]] = os.environ.get(keys[i])

# Replacing readable code with bit manipulation for negligible gain
is_even = not (n & 1)  # instead of: n % 2 == 0
```

### ✅ Correct — Legitimate Optimization

```python
# This function is called 10,000 times per request — optimization is justified
def match_rules(event: dict, rules: list[dict]) -> list[dict]:
    # BEFORE (profiled at 340ms/request):
    # return [r for r in rules if all(event.get(k) == v for k, v in r["conditions"].items())]

    # AFTER (profiled at 12ms/request) — pre-indexed rules by first condition:
    first_key = next(iter(event))
    candidates = rule_index.get((first_key, event[first_key]), [])
    return [r for r in candidates if _matches(event, r)]
```

**Decision framework — should you optimize this code?**

| Question | If Yes | If No |
|---|---|---|
| Is it on a hot path (called per-request, per-event, per-item)? | Consider optimizing | Leave it alone |
| Does it operate on large data (1000+ items)? | Consider optimizing | Leave it alone |
| Has profiling confirmed it is a bottleneck? | Optimize now | Profile first |
| Will the optimization hurt readability? | Document why + add benchmarks | Prefer the clear version |
| Is it a startup/teardown/admin-only path? | Almost never worth optimizing | Leave it alone |

**Key points:**
- Always profile before optimizing. Use `cProfile`, `py-spy`, or `line_profiler`.
- Choosing the right data structure is design, not premature optimization.
- Readable code that is "fast enough" beats clever code that is 5% faster.
- When you do optimize, leave a comment explaining what was slow and what the improvement was.
- Benchmark after optimizing to prove the change had the expected effect.
