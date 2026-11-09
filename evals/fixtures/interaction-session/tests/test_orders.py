from api.orders import average_price
from api.routes import orders_summary


def test_orders_summary_empty_cart():
    assert orders_summary([]) == {"count": 0, "average": 0.0}


def test_average_price_empty_cart():
    assert average_price([]) == 0.0


def test_average_price():
    assert average_price([{"price": 2.0}, {"price": 4.0}]) == 3.0
