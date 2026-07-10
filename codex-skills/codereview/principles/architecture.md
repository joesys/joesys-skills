# Architecture Principles

## Quick Diagnostic Guide

| Symptom | Likely Principle |
|---|---|
| Duplicated logic scattered across modules | DRY |
| Same config value defined in multiple places | Single Source of Truth |
| Function mixes DB calls, business rules, and formatting | Separation of Concerns |
| Internal data structures leak through public API | Modularity / Encapsulation |
| Chained accessor calls (`a.b.c.d.do()`) | Law of Demeter |
| Changing one module forces changes in unrelated modules | Orthogonality |
| Hard to test because dependencies are created internally | Dependency Injection |
| Deep inheritance hierarchies with combinatorial explosion | Composition Over Inheritance |
| God class that handles everything | SOLID (SRP) |
| Sensible behavior requires pages of config boilerplate | Convention Over Configuration |
| Method both mutates state and returns a value | Command-Query Separation |
| "Reusable" utility used by exactly one caller | Code Reusability |
| Invalid data propagates far before crashing | Parse, Don't Validate |
| Debugging nightmares caused by mutated shared state | Immutability |
| Retrying an operation causes duplicates or corruption | Idempotency |

## Principle Tensions

| Tension | Guidance |
|---|---|
| **DRY vs. Decoupling** | Merging similar-looking code into one shared function can couple unrelated domains. Prefer duplication over the wrong abstraction — if the code evolves for different reasons, it is not truly duplicated. |
| **Encapsulation vs. Testability** | Hiding everything behind private methods can make unit testing difficult. Expose seams through dependency injection rather than making internals public. |
| **Composition vs. Simplicity** | Composition is more flexible than inheritance but introduces more objects and wiring. For simple, stable hierarchies (e.g., `Exception` subclasses), inheritance is fine. |
| **Modularity vs. Performance** | Deep module boundaries may add overhead. Co-locate hot paths when profiling proves the boundary is the bottleneck — not before. |
| **Immutability vs. Practicality** | Full immutability in Python requires discipline (frozen dataclasses, tuples). Apply it where bugs are likely — shared state, concurrent access — not to every local variable. |
| **SOLID vs. KISS** | Blindly applying all five SOLID principles to a small script creates over-engineering. SOLID shines in large, long-lived codebases where change is frequent. |
| **Dependency Injection vs. Readability** | Injecting every dependency makes constructors noisy. Inject what varies (I/O, config, strategies); hard-code what is stable (standard-library utilities). |

---

## 1. DRY — Don't Repeat Yourself

Every piece of knowledge must have a single, unambiguous, authoritative representation
within a system. DRY targets duplication of *knowledge* — business rules, algorithms,
intent — not textual similarity of code. Two blocks that look alike but change for
different reasons are not DRY violations; merging them creates the wrong abstraction.

**The Rule of Three:** Do not extract a shared abstraction until you have seen the same
pattern in three independent places. Two occurrences may be coincidence; three suggest a
real pattern.

**The Wrong Abstraction (Sandi Metz):** Duplication is far cheaper than the wrong
abstraction. If a shared function accumulates `if`/`else` branches to handle its various
callers, inline it back and let each caller evolve independently.

### ❌ Wrong

```python
def get_user_by_something(identifier: str, by_type: str) -> dict | None:
    """Over-DRY: forces every caller through a branching dispatcher."""
    if by_type == "id":
        return db.query("SELECT * FROM users WHERE id = %s", (int(identifier),))
    elif by_type == "email":
        return db.query("SELECT * FROM users WHERE email = %s", (identifier,))
    elif by_type == "username":
        return db.query("SELECT * FROM users WHERE username = %s", (identifier,))
    else:
        raise ValueError(f"Unknown lookup type: {by_type}")
```

### ✅ Correct

```python
def get_user_by_id(user_id: int) -> dict | None:
    return db.query("SELECT * FROM users WHERE id = %s", (user_id,))

def get_user_by_email(email: str) -> dict | None:
    return db.query("SELECT * FROM users WHERE email = %s", (email,))
```

**Key points:** Each function has a precise name, a typed parameter, and zero branching. The small SQL "duplication" is *not* a DRY violation because each query represents a distinct domain concept that may evolve independently (different joins, indexes, caching).

---

## 2. Single Source of Truth — One Location for Each Piece of Data

Every fact in the system — a configuration value, a business constant, a derived metric —
should be defined in exactly one place. When truth is scattered, copies drift apart and
the system contradicts itself silently.

### ❌ Wrong

```python
# settings.py
MAX_UPLOAD_SIZE = 10 * 1024 * 1024

# validators.py
def validate_upload(file_bytes: bytes) -> bool:
    return len(file_bytes) <= 10 * 1024 * 1024  # duplicated magic number

# api_handler.py
def handle_upload(request):
    if request.content_length > 10485760:  # same number, third location
        return error_response("File too large")
```

### ✅ Correct

```python
# settings.py
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024

# validators.py
from settings import MAX_UPLOAD_SIZE_BYTES

def validate_upload(file_bytes: bytes) -> bool:
    return len(file_bytes) <= MAX_UPLOAD_SIZE_BYTES

# api_handler.py
from settings import MAX_UPLOAD_SIZE_BYTES

def handle_upload(request):
    if request.content_length > MAX_UPLOAD_SIZE_BYTES:
        return error_response("File too large")
```

**Key points:** A single constant in `settings.py` is the authoritative source. Changing the upload limit requires editing one line. No risk of one module silently using a stale value.

---

## 3. Separation of Concerns — One Responsibility per Component

Each module, class, or function should address a single concern. When a function mixes
database access, business logic, presentation, and notification, every change risks
breaking unrelated behaviour and testing requires the entire world to be mocked.

### ❌ Wrong

```python
def process_order(order_data: dict) -> str:
    conn = psycopg2.connect("dbname=shop")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO orders ...", (order_data["customer_id"],))
    order_id = cursor.fetchone()[0]
    conn.commit()

    discount = order_data["total"] * 0.1 if order_data["total"] > 100 else 0
    html = f"<h1>Order #{order_id}</h1><p>Discount: ${discount:.2f}</p>"

    smtplib.SMTP("mail.example.com").sendmail(
        "shop@example.com", order_data["email"], html)
    return html
```

### ✅ Correct

```python
class OrderRepository:
    def __init__(self, conn):
        self._conn = conn

    def save(self, order_data: dict) -> int:
        cursor = self._conn.cursor()
        cursor.execute("INSERT INTO orders ... RETURNING id", (order_data["customer_id"],))
        self._conn.commit()
        return cursor.fetchone()[0]

class OrderService:
    def __init__(self, repo: OrderRepository, notifier: "OrderNotifier"):
        self._repo = repo
        self._notifier = notifier

    def process(self, order_data: dict) -> dict:
        order_id = self._repo.save(order_data)
        discount = order_data["total"] * 0.1 if order_data["total"] > 100 else 0.0
        result = {"order_id": order_id, "discount": discount}
        self._notifier.send_confirmation(order_data["email"], result)
        return result

class OrderPresenter:
    @staticmethod
    def to_html(result: dict) -> str:
        return f'<h1>Order #{result["order_id"]}</h1><p>Discount: ${result["discount"]:.2f}</p>'
```

**Key points:** Repository handles persistence, Service handles business rules, Presenter handles formatting. Each can be tested, replaced, and evolved independently.

---

## 4. Modularity — Independent Components with Hidden Internals

A well-designed module provides a simple, powerful interface while hiding its complexity.
John Ousterhout's distinction: *deep* modules have a small interface relative to their
functionality; *shallow* modules expose nearly as much complexity as they hide.

### ❌ Wrong — Shallow Module

```python
class ShallowConfigReader:
    """Almost zero value added over using a dict directly."""
    def __init__(self):
        self._data = {}

    def set(self, key: str, value: str) -> None:
        self._data[key] = value

    def get(self, key: str) -> str:
        return self._data[key]

    def has(self, key: str) -> bool:
        return key in self._data

    def keys(self) -> list[str]:
        return list(self._data.keys())
```

### ✅ Correct — Deep Module

```python
class Config:
    """Deep module: simple interface, rich functionality hidden inside."""

    def __init__(self, *sources: str):
        self._resolved = self._load_and_merge(sources)

    def get(self, key: str, default: str | None = None, cast: type = str):
        raw = self._resolved.get(key, default)
        if raw is None:
            raise ConfigKeyError(key)
        return cast(raw)

    def _load_and_merge(self, sources: tuple[str, ...]) -> dict:
        """Absorbs complexity: multi-format parsing, merging, env overrides."""
        merged = {}
        for source in sources:
            if source.endswith(".env"):
                merged.update(self._parse_env(source))
            elif source.endswith((".yaml", ".yml")):
                merged.update(self._parse_yaml(source))
            elif source == "ENV":
                merged.update(self._from_environment())
        return merged
```

**Key points:** The shallow module is barely more than a `dict` wrapper. The deep module absorbs real complexity — multi-format parsing, merging, type casting — behind a minimal `Config.get()` interface. Deep modules earn their existence.

---

## 5. Encapsulation — Bundle Data with Behaviour, Hide Internals

An object should own its data and expose behaviour, not raw state. The "Tell, Don't Ask"
principle: tell an object what to do, don't ask for its data and do it yourself. When
external code reaches in to make decisions, it duplicates logic that belongs inside the
object.

### ❌ Wrong — Ask, Then Do

```python
class BankAccount:
    def __init__(self, balance: float):
        self.balance = balance
        self.is_frozen = False

def withdraw(account: BankAccount, amount: float) -> None:
    if account.is_frozen:
        raise ValueError("Account is frozen")
    if account.balance < amount:
        raise ValueError("Insufficient funds")
    account.balance -= amount
```

### ✅ Correct — Tell, Don't Ask

```python
class BankAccount:
    def __init__(self, balance: float):
        self._balance = balance
        self._is_frozen = False

    def withdraw(self, amount: float) -> None:
        if self._is_frozen:
            raise AccountFrozenError()
        if amount > self._balance:
            raise InsufficientFundsError(self._balance, amount)
        self._balance -= amount

    @property
    def balance(self) -> float:
        return self._balance
```

**Key points:** Business rules live inside `BankAccount`, not in external functions. Internal fields are private. If withdrawal rules change (e.g., overdraft protection), only one place needs updating.

---

## 6. Law of Demeter — Only Talk to Immediate Friends

A method should only call methods on: itself, its parameters, objects it creates, and its
direct components. Reaching through chains of accessors creates hidden coupling to the
entire chain's internal structure.

### ❌ Wrong

```python
def charge_customer(customer: Customer, amount: float) -> None:
    customer.get_wallet().get_credit_card().charge(amount)
```

### ✅ Correct

```python
def charge_customer(customer: Customer, amount: float) -> None:
    customer.charge(amount)

class Customer:
    def charge(self, amount: float) -> None:
        self._wallet.charge(amount)

class Wallet:
    def charge(self, amount: float) -> None:
        card = self._select_valid_card()
        card.charge(amount)
```

**Key points:** The caller knows about `Customer`, not `Wallet` or `CreditCard`. If the payment structure changes (e.g., adding PayPal), only `Customer` and `Wallet` change — no ripple through every caller.

---

## 7. Orthogonality — Changes in One Area Don't Affect Others

Two components are orthogonal if changing one does not require changing the other. In an
orthogonal system, you can swap the database without touching business logic, change the
UI without rewriting services, or modify logging without editing every module.

### ❌ Wrong

```python
class ReportGenerator:
    def generate(self, data: list[dict]) -> None:
        html = "<html><body><table>"
        for row in data:
            tax = row["amount"] * 0.2  # tax logic embedded in presentation
            html += f"<tr><td>{row['name']}</td><td>${tax:.2f}</td></tr>"
        html += "</table></body></html>"
        with smtplib.SMTP("mail.example.com") as server:
            server.sendmail("reports@co.com", "boss@co.com", html)
```

### ✅ Correct

```python
class TaxCalculator:
    def __init__(self, rate: float = 0.2):
        self.rate = rate

    def compute(self, amount: float) -> float:
        return amount * self.rate

class ReportFormatter:
    def to_html(self, rows: list[dict]) -> str:
        lines = [f"<tr><td>{r['name']}</td><td>${r['tax']:.2f}</td></tr>" for r in rows]
        return f"<html><body><table>{''.join(lines)}</table></body></html>"

class ReportDelivery:
    def __init__(self, smtp_host: str):
        self.smtp_host = smtp_host

    def send(self, recipient: str, content: str) -> None:
        with smtplib.SMTP(self.smtp_host) as server:
            server.sendmail("reports@co.com", recipient, content)
```

**Key points:** Tax rate, output format, and delivery mechanism are independent axes of change. Switching from HTML to PDF touches only `ReportFormatter`. No shotgun surgery.

---

## 8. Dependency Injection — Pass Dependencies, Don't Create Them

A class should receive its collaborators from the outside rather than constructing them
internally. Hard-coded dependencies prevent isolated testing and force modification of the
class itself to swap a collaborator.

### ❌ Wrong

```python
class MovieLister:
    def __init__(self):
        self._finder = ColonDelimitedMovieFinder("movies.txt")  # hard-coded

    def movies_directed_by(self, director: str) -> list[Movie]:
        return [m for m in self._finder.find_all() if m.director == director]
```

### ✅ Correct

```python
class MovieFinder(ABC):
    @abstractmethod
    def find_all(self) -> list[Movie]: ...

class MovieLister:
    def __init__(self, finder: MovieFinder):
        self._finder = finder

    def movies_directed_by(self, director: str) -> list[Movie]:
        return [m for m in self._finder.find_all() if m.director == director]

# Wiring at the composition root
lister = MovieLister(ColonDelimitedMovieFinder("movies.txt"))
# In tests
lister = MovieLister(InMemoryMovieFinder([Movie("Jaws", "Spielberg")]))
```

**Key points:** `MovieLister` depends on the `MovieFinder` abstraction, not a concrete file parser. Swapping data sources requires zero changes to `MovieLister`. Dependencies are wired at the composition root — the one place that knows all concrete types.

---

## 9. Composition Over Inheritance — Combine Objects, Don't Extend

Favour assembling behaviour from small, composable parts rather than building deep
inheritance trees. Inheritance creates tight coupling, and combinatorial class explosions
appear when multiple axes of variation exist.

### ❌ Wrong — Class Explosion via Inheritance

```python
class Logger: ...
class FileLogger(Logger): ...
class ConsoleLogger(Logger): ...
class FilteredFileLogger(FileLogger): ...
class FilteredConsoleLogger(ConsoleLogger): ...
class JsonFilteredFileLogger(FilteredFileLogger): ...
class JsonFilteredConsoleLogger(FilteredConsoleLogger): ...
# 2 writers x 2 filters x 2 formats = 8 classes, and growing...
```

### ✅ Correct — Composition

```python
class Writer(ABC):
    @abstractmethod
    def write(self, text: str) -> None: ...

class FileWriter(Writer):
    def __init__(self, path: str):
        self._path = path
    def write(self, text: str) -> None:
        with open(self._path, "a") as f:
            f.write(text + "\n")

class ConsoleWriter(Writer):
    def write(self, text: str) -> None:
        print(text)

class LogFilter(ABC):
    @abstractmethod
    def should_log(self, message: str, level: str) -> bool: ...

class Logger:
    def __init__(self, writer: Writer, filters: list[LogFilter] | None = None):
        self._writer = writer
        self._filters = filters or []

    def log(self, message: str, level: str = "INFO") -> None:
        if all(f.should_log(message, level) for f in self._filters):
            self._writer.write(f"[{level}] {message}")

# Compose freely — no new classes needed
file_logger = Logger(FileWriter("/var/log/app.log"), [MinLevelFilter("WARNING")])
console_logger = Logger(ConsoleWriter())
```

**Key points:** Writers and filters are independent axes of variation composed at runtime. Adding a new writer or filter is one class — not a combinatorial explosion. `Logger` never changes when new writers or filters appear.

---

## 10. SOLID — Five Foundational Object-Oriented Principles

SOLID is a set of five principles that produce classes easy to extend, test, and maintain.

**S — Single Responsibility (SRP):** A class should have only one reason to change.
*Smell:* class name contains "And" or "Manager"; methods span different domains.

**O — Open/Closed (OCP):** Open for extension, closed for modification. New behaviour via new code, not editing existing code.
*Smell:* adding a feature requires editing `if/elif` chains in existing classes.

**L — Liskov Substitution (LSP):** Subtypes must be substitutable for their base types.
*Smell:* `isinstance()` checks for subclass-specific behaviour; overridden methods that throw `NotImplementedError`.

**I — Interface Segregation (ISP):** Clients should not depend on interfaces they do not use.
*Smell:* implementations with `pass` or `raise NotImplementedError` for many methods.

**D — Dependency Inversion (DIP):** High-level modules depend on abstractions, not low-level modules.
*Smell:* `import psycopg2` inside domain/service modules.

### ❌ Wrong — Violates SRP and OCP

```python
class UserService:
    def validate(self, data: dict) -> bool: ...
    def save(self, data: dict) -> None: ...
    def send_welcome_email(self, email: str) -> None: ...
    def generate_report(self, user_id: int) -> str: ...
```

### ✅ Correct — Each Class Has One Reason to Change

```python
class UserValidator:
    def validate(self, data: dict) -> bool:
        return bool(data.get("email")) and len(data.get("password", "")) >= 8

class UserRepository:
    def __init__(self, db):
        self._db = db
    def save(self, data: dict) -> None:
        self._db.execute("INSERT INTO users ...", data)

class WelcomeNotifier:
    def __init__(self, mailer):
        self._mailer = mailer
    def notify(self, email: str) -> None:
        self._mailer.send(email, "Welcome!", "Thanks for joining.")
```

**Key points:** Each class has a single axis of change. The validator evolves independently of persistence. New report formats are new classes, not modifications to existing ones.

---

## 11. Convention Over Configuration — Sensible Defaults, Override When Needed

A framework or library should work out of the box with reasonable defaults, requiring
explicit configuration only when behaviour must deviate. This reduces boilerplate and
makes the common case effortless while keeping the uncommon case possible.

### ❌ Wrong

```python
# Every route requires all 9 parameters
router.add_route("/users", list_users, "GET", "application/json",
                 True, 100, 60, True, True, True)
```

### ✅ Correct

```python
class Router:
    DEFAULTS = {
        "method": "GET", "content_type": "application/json",
        "auth_required": True, "rate_limit": 100, "cache_ttl": 0,
    }

    def add_route(self, path: str, handler, **overrides) -> None:
        config = {**self.DEFAULTS, **overrides}
        self._routes[path] = {"handler": handler, **config}

# Common case: zero config
router.add_route("/users", list_users)
# Override only what differs
router.add_route("/health", health_check, auth_required=False, rate_limit=1000)
```

**Key points:** Defaults handle the common case. Overrides handle the exceptions. Adding a new option with a sensible default does not break existing callers. The `DEFAULTS` dict is living documentation of the system's assumptions.

---

## 12. Command-Query Separation — Return a Value OR Change State

A method should either return information (a *query*) or change state (a *command*) —
never both. When a method mutates and returns, the caller cannot ask a question without
triggering a side effect.

### ❌ Wrong

```python
class ShoppingCart:
    def add_and_get_total(self, item: dict) -> float:
        """Mutation + query in one call."""
        self._items.append(item)
        return sum(i["price"] for i in self._items)

    def remove_and_check_empty(self, item_id: str) -> bool:
        """Cannot check emptiness without mutating."""
        self._items = [i for i in self._items if i["id"] != item_id]
        return len(self._items) == 0
```

### ✅ Correct

```python
class ShoppingCart:
    # Commands — change state, return nothing
    def add(self, item: dict) -> None:
        self._items.append(item)

    def remove(self, item_id: str) -> None:
        self._items = [i for i in self._items if i["id"] != item_id]

    # Queries — return state, change nothing
    @property
    def total(self) -> float:
        return sum(i["price"] for i in self._items)

    @property
    def is_empty(self) -> bool:
        return len(self._items) == 0
```

**Key points:** Queries are safe for assertions, logging, and debugging — no side effects. Commands are explicit mutations. The caller composes freely: `cart.add(item)` then `print(cart.total)`.

---

## 13. Code Reusability — Earned Through Proven Need

Reusability is *earned* by code that has proven useful across multiple callers, not an
aspirational goal that justifies speculative abstraction. Building for reuse before
demand wastes effort and couples code to imagined futures.

### ❌ Wrong

```python
class GenericDataTransformer:
    """Written before any consumer exists."""
    def __init__(self, mapping: dict[str, str], validators: list, transforms: list):
        self._mapping = mapping
        self._validators = validators
        self._transforms = transforms

    def transform(self, data: dict) -> dict: ...

# The only actual caller just needs to rename two keys
output = GenericDataTransformer(
    mapping={"first_name": "firstName", "last_name": "lastName"},
    validators=[], transforms=[],
).transform(user_data)
```

### ✅ Correct

```python
def to_api_format(user: dict) -> dict:
    """Direct solution for the actual need."""
    return {"firstName": user["first_name"], "lastName": user["last_name"]}
```

**Key points:** The "reusable" transformer solves no problem the direct function doesn't solve better. If three callers eventually need different mappings, *then* extract a shared utility shaped by real requirements.

---

## 14. Parse, Don't Validate — Transform Data into Types That Prove Validity

Validation checks data and discards the evidence. Parsing checks data and produces a
structured type that *cannot represent invalid state*. The "shotgun parsing" anti-pattern
scatters validation checks across many call sites, each trusting earlier checks were done.

### ❌ Wrong — Shotgun Parsing

```python
def handle_registration(data: dict) -> None:
    if "email" not in data or "@" not in data["email"]:
        raise ValueError("Invalid email")
    save_user(data)  # downstream receives raw dict
    send_welcome(data)

def save_user(data: dict) -> None:
    email = data.get("email", "")
    if not email:  # must re-check — can't trust caller
        raise ValueError("Missing email")
    db.execute("INSERT INTO users (email) VALUES (%s)", (email,))
```

### ✅ Correct — Parse Once, Use the Proven Type

```python
@dataclass(frozen=True)
class ValidatedUser:
    email: str
    age: int

    @classmethod
    def parse(cls, data: dict) -> "ValidatedUser":
        email = data.get("email", "")
        if "@" not in email:
            raise ValueError(f"Invalid email: {email!r}")
        age = data.get("age")
        if not isinstance(age, int) or age < 0:
            raise ValueError(f"Invalid age: {age!r}")
        return cls(email=email, age=age)

def handle_registration(data: dict) -> None:
    user = ValidatedUser.parse(data)  # parse at the boundary
    save_user(user)
    send_welcome(user)

def save_user(user: ValidatedUser) -> None:
    # No validation needed — the type guarantees validity
    db.execute("INSERT INTO users (email, age) VALUES (%s, %s)", (user.email, user.age))
```

**Key points:** `ValidatedUser` is proof that parsing succeeded. Downstream functions accept `ValidatedUser`, not `dict`, so they can never receive invalid data. Validation logic lives in one place. If a field is added, the type forces all callers to handle it.

---

## 15. Immutability — Once Created, State Cannot Change

An immutable object's state is fixed at construction. This eliminates race conditions,
unexpected aliasing, and debugging sessions that trace a corrupted value back through ten
functions that all had write access.

### ❌ Wrong

```python
class PriceRule:
    def __init__(self, product_id: str, discount_pct: float):
        self.product_id = product_id
        self.discount_pct = discount_pct

def apply_seasonal_boost(rules: list[PriceRule]) -> list[PriceRule]:
    for rule in rules:
        rule.discount_pct *= 1.5  # mutates shared objects!
    return rules

base_rules = [PriceRule("SKU-1", 0.1), PriceRule("SKU-2", 0.2)]
boosted = apply_seasonal_boost(base_rules)
print(base_rules[0].discount_pct)  # 0.15 — surprise!
```

### ✅ Correct

```python
@dataclass(frozen=True)
class PriceRule:
    product_id: str
    discount_pct: float

    def with_boost(self, multiplier: float) -> "PriceRule":
        return PriceRule(product_id=self.product_id,
                         discount_pct=self.discount_pct * multiplier)

def apply_seasonal_boost(rules: list[PriceRule]) -> list[PriceRule]:
    return [rule.with_boost(1.5) for rule in rules]

base_rules = [PriceRule("SKU-1", 0.1), PriceRule("SKU-2", 0.2)]
boosted = apply_seasonal_boost(base_rules)
print(base_rules[0].discount_pct)  # 0.1 — unchanged
```

**Key points:** `frozen=True` makes instances immutable — attribute assignment raises `FrozenInstanceError`. The `with_boost` method returns a new object (copy-on-modify pattern), safe for shared references, caching, and concurrency.

---

## 16. Idempotency — Multiple Executions Produce the Same Result as One

An idempotent operation can be safely retried, replayed, or duplicated without changing
the outcome beyond the first execution. Critical for network retries, message queue
duplicates, and overlapping cron jobs.

### ❌ Wrong

```python
def process_payment(order_id: str, amount: float) -> None:
    """Non-idempotent: retrying creates duplicate charges."""
    charge_id = payment_gateway.charge(amount)
    db.execute("INSERT INTO payments (order_id, charge_id, amount) VALUES (%s, %s, %s)",
               (order_id, charge_id, amount))

# Network timeout -> retry -> customer charged twice
try:
    process_payment("ORD-42", 99.99)
except TimeoutError:
    process_payment("ORD-42", 99.99)  # duplicate charge!
```

### ✅ Correct

```python
def process_payment(order_id: str, amount: float,
                    idempotency_key: str | None = None) -> str:
    """Idempotent: safe to retry any number of times."""
    key = idempotency_key or str(uuid.uuid4())

    existing = db.query("SELECT charge_id FROM payments WHERE idempotency_key = %s", (key,))
    if existing:
        return existing["charge_id"]  # already processed

    charge_id = payment_gateway.charge(amount, idempotency_key=key)
    db.execute(
        "INSERT INTO payments (order_id, charge_id, amount, idempotency_key) "
        "VALUES (%s, %s, %s, %s)", (order_id, charge_id, amount, key))
    return charge_id
```

**Key points:** The idempotency key identifies the *intent*. Before executing, the function checks for prior completion. The gateway also receives the key to prevent double-charging even if the DB write fails. This pattern applies to any state-changing operation that may be retried: API handlers, queue consumers, batch jobs.
