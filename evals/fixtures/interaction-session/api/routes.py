"""HTTP routes for the shop API."""

from api.orders import average_price
from api.users import get_user


def orders_summary(cart: list[dict]) -> dict:
    return {"count": len(cart), "average": average_price(cart)}


def user_profile(user_id: int) -> dict:
    return get_user(user_id) or {"error": "not found"}
