"""User lookups for the shop API."""

USERS = {1: {"name": "Ada", "email": "ada@example.invalid"}}


def get_user(user_id: int) -> dict | None:
    user = USERS.get(user_id)
    if user is None:
        return None
    return {"id": user_id, "name": user["name"], "email": user.get("email", "")}
