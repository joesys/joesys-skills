from __future__ import annotations
import json, subprocess
from pathlib import Path
import render_dashboard as rd

SAMPLE = {
    "schema": 1, "generated_ts": 9999999999,
    "repo": {"name": "demo", "branch": "main", "commit": "abc1234", "default_branch": "main"},
    "flags": {"solo": False, "shallow": False},
    "kpis": {"pulse": {"count_30d": 12, "pct_change": 0.18}, "last_commit_days": 2,
             "bus_factor": 1, "active_devs": 5, "firefighting_pct": 0.08,
             "stale_branches": 12, "last_release_days": 9, "open_prs": None},
    "lenses": {
        "delivery": {"light": "green", "cadence": [1, 3, 2, 5], "release": {"has_tags": True, "days_since": 9, "last_tag": "v1"},
                     "throughput": 2.0, "modules": [{"module": "src", "commits_30d": 8}], "heatmap": [[0]*24 for _ in range(7)]},
        "health": {"light": "yellow", "firefighting_pct": 0.08, "hotspots": [{"file": "a.py", "changes": 47}],
                   "stale_branches": [{"name": "old", "idle_days": 80}], "debt": {"total": 3, "todo": 2, "fixme": 1, "hack": 0},
                   "hygiene": {"ci": True, "lockfile": True, "env_gitignored": True, "tests": True},
                   "msg_hygiene": {"conventional_pct": 0.9, "wip_pct": 0.0}},
        "team": {"light": "red", "bus_factor": {"count": 1, "top_author": "sam", "top_share": 0.71},
                 "active_devs": 5, "distribution": {"authors": [{"author": "sam", "commits": 30}], "gini": 0.6},
                 "dormant": {"gone_quiet": ["bob"], "newly_active": []}, "off_hours_pct": None}},
    "overall": {"light": "red", "summary": "Shipping well, but one dev owns 71% of recent work."},
    "repo_state": {"modules": ["src"], "size": {"files": 10, "languages": {"py": 8}}},
    "narrative": None, "host": None, "code_quality": None,
}


def test_render_produces_self_contained_html():
    html = rd.render(SAMPLE)
    assert html.startswith("<!DOCTYPE html>")
    assert "demo" in html
    assert "71%" in html or "0.71" in html or "sam" in html
    # self-contained: no external resource references
    assert "http://" not in html and "https://" not in html
    assert "<svg" in html  # at least one inline chart


def test_verdict_dot_reflects_overall():
    html = rd.render(SAMPLE)
    assert 'class="dot red"' in html


def test_escapes_hostile_json_text():
    import copy
    data = copy.deepcopy(SAMPLE)
    data["repo"]["name"] = "<script>evil</script>"
    data["lenses"]["delivery"]["release"] = {"has_tags": True, "days_since": 3, "last_tag": "v1<img src=x>&"}
    data["lenses"]["health"]["hotspots"] = [{"file": "<b>a.py</b>", "changes": 5}]
    data["lenses"]["team"]["bus_factor"] = {"count": 1, "top_author": "<i>sam</i>", "top_share": 0.71}
    data["overall"]["summary"] = "<svg onload=alert(1)>"
    html = rd.render(data)
    for bad in ["<script>evil", "<img src=x>", "<b>a.py</b>", "<i>sam</i>", "<svg onload"]:
        assert bad not in html, f"unescaped: {bad}"
    # escaped forms should be present instead
    assert "&lt;script&gt;evil" in html


def test_cli_writes_file(tmp_path):
    metrics_path = tmp_path / "d.json"
    metrics_path.write_text(json.dumps(SAMPLE), encoding="utf-8")
    out = tmp_path / "out.html"
    subprocess.run(["python", str(Path(__file__).parent / "render_dashboard.py"),
                    "--metrics", str(metrics_path), "--out", str(out)],
                   capture_output=True, text=True, check=True)
    assert out.exists() and out.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")


def test_open_prs_tile_uses_host_when_present():
    import copy
    data = copy.deepcopy(SAMPLE)
    data["host"] = {"available": True, "host": "github", "open_prs": 7,
                    "pr_median_age_days": 3.5, "ci_pass_rate": 0.9, "open_issues": 4}
    html = rd.render(data)
    assert "Open PRs" in html
    assert ">7<" in html or ">7 " in html
    assert "from github" in html.lower()


def test_open_prs_tile_falls_back_to_wip_branches_without_host():
    html = rd.render(SAMPLE)  # host None
    assert "WIP branches" in html
