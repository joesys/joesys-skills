from __future__ import annotations
import pytest
import tooltips


def test_every_id_has_complete_copy():
    for mid in tooltips.METRIC_IDS:
        t = tooltips.get(mid)
        assert set(t) >= {"title", "what", "why"}, mid
        assert t["title"].strip(), mid
        assert t["what"].strip(), mid
        assert t["why"].strip(), mid


def test_tooltips_dict_matches_ids():
    assert set(tooltips.TOOLTIPS) == set(tooltips.METRIC_IDS)


def test_ids_cover_expected_surface():
    # Sanity: the canonical surface the renderer attaches tips to.
    expected = {
        "overall",
        "kpi.pulse", "kpi.last_commit", "kpi.bus_factor", "kpi.active_devs",
        "kpi.firefighting", "kpi.stale_branches", "kpi.last_release",
        "kpi.open_prs", "kpi.wip_branches",
        "lens.delivery", "delivery.cadence", "delivery.throughput",
        "delivery.release", "delivery.modules", "delivery.heatmap", "delivery.host",
        "lens.health", "health.hotspots", "health.stale_branches",
        "health.hygiene", "health.debt", "health.code_quality",
        "lens.team", "team.bus_factor", "team.distribution",
        "team.dormant", "team.off_hours",
    }
    assert set(tooltips.METRIC_IDS) == expected


def test_get_unknown_raises():
    with pytest.raises(KeyError):
        tooltips.get("nope.nope")
