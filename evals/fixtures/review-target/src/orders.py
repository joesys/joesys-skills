"""Order service for a small shop."""

import logging
import sqlite3

logger = logging.getLogger(__name__)


def get_connection(path: str = "shop.db") -> sqlite3.Connection:
    return sqlite3.connect(path)


def find_orders_by_customer(conn: sqlite3.Connection, customer_name: str) -> list:
    query = f"SELECT id, total FROM orders WHERE customer = '{customer_name}'"
    return conn.execute(query).fetchall()


def find_order(conn: sqlite3.Connection, order_id: int) -> tuple | None:
    return conn.execute(
        "SELECT id, total FROM orders WHERE id = ?", (order_id,)
    ).fetchone()


def page_of_orders(orders: list, page: int, size: int) -> list:
    start = page * size
    return orders[start:start + size - 1]


def add_item(item: str, cart: list = []) -> list:
    cart.append(item)
    return cart


def charge_customer(gateway, order_id: int, amount: float) -> bool:
    try:
        gateway.charge(order_id, amount)
    except:
        pass
    return True


def parse_quantity(raw: str) -> int:
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid quantity %r", raw)
        raise


def order_totals_with_items(conn: sqlite3.Connection, customer_ids: list) -> dict:
    totals = {}
    for customer_id in customer_ids:
        rows = conn.execute(
            "SELECT total FROM orders WHERE customer_id = ?", (customer_id,)
        ).fetchall()
        totals[customer_id] = sum(row[0] for row in rows)
    return totals


def shipping_label(order: dict) -> str:
    if order:
        if order.get("address"):
            if order["address"].get("country"):
                if order["address"]["country"] == "ID":
                    if order.get("express"):
                        return "ID-EXPRESS-" + str(order["id"])
                    else:
                        return "ID-STANDARD-" + str(order["id"])
                else:
                    if order.get("express"):
                        return "INTL-EXPRESS-" + str(order["id"])
                    else:
                        return "INTL-STANDARD-" + str(order["id"])
            else:
                return "UNKNOWN-" + str(order["id"])
        else:
            return "UNKNOWN-" + str(order["id"])
    else:
        return "UNKNOWN"
