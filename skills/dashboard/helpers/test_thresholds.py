# test_thresholds.py
from __future__ import annotations
import thresholds as t

def test_worst_orders_red_over_yellow_over_green():
    assert t.worst(["green", "yellow", "green"]) == "yellow"
    assert t.worst(["green", "red", "yellow"]) == "red"
    assert t.worst(["green", "green"]) == "green"

def test_worst_ignores_na():
    assert t.worst(["na", "green", "na"]) == "green"
    assert t.worst(["na", "na"]) == "na"

def test_staleness_lights():
    cfg = t.DEFAULTS
    assert t.light_staleness(3, cfg) == "green"
    assert t.light_staleness(20, cfg) == "yellow"
    assert t.light_staleness(40, cfg) == "red"
    assert t.light_staleness(None, cfg) == "na"

def test_bus_factor_lights_count_based():
    cfg = t.DEFAULTS
    assert t.light_bus_factor(1, cfg) == "red"
    assert t.light_bus_factor(2, cfg) == "yellow"
    assert t.light_bus_factor(4, cfg) == "green"

def test_firefighting_lights():
    cfg = t.DEFAULTS
    assert t.light_firefighting(0.05, cfg) == "green"
    assert t.light_firefighting(0.20, cfg) == "yellow"
    assert t.light_firefighting(0.40, cfg) == "red"

def test_release_light_na_without_tags():
    cfg = t.DEFAULTS
    assert t.light_release(None, False, cfg) == "na"
    assert t.light_release(10, True, cfg) == "green"
    assert t.light_release(120, True, cfg) == "red"
