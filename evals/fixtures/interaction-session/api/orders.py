"""Order totals for the shop API."""


def apply_discount(total: float, percent: float) -> float:
    return round(total * (1 - percent / 100), 2)


def average_price(items: list[dict]) -> float:
    if not items:
        return 0.0
    return sum(item["price"] for item in items) / len(items)
