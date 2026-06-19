# collect_git.py
"""Deterministic local-git collector → dashboard.json.

Usage:
    python collect_git.py --repo . [--out dashboard.json] [--now UNIX_TS]
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time

import gitlog
import reposcan
import metrics
import thresholds as TH


def _dedupe_branches(branches: list[dict]) -> list[dict]:
    """Collapse a local branch and its origin/ remote-tracking copy into one,
    keeping the most-recent last_ts. Normalizes by stripping a leading 'origin/'.

    v1 limitation: only the 'origin/' remote prefix is stripped; branches on
    other named remotes (e.g. 'upstream/x') are not collapsed against locals.
    """
    best: dict[str, dict] = {}
    for b in branches:
        key = b["name"][len("origin/"):] if b["name"].startswith("origin/") else b["name"]
        if key not in best or b["last_ts"] > best[key]["last_ts"]:
            best[key] = b
    return list(best.values())


def build(repo: str, now_ts: int) -> dict:
    cfg = TH.load_config(repo)
    commits_all = gitlog.get_commits(repo)
    commits_90 = gitlog.get_commits(repo, since_days=90)
    fcc = gitlog.get_file_change_counts(repo, since_days=90)
    tags = gitlog.get_tags(repo)
    default = gitlog.default_branch(repo)
    branches = [b for b in gitlog.get_branches(repo)
                if b["name"] != default and not b["name"].endswith("/" + default)]
    # Collapse local + origin/ remote-tracking copies so one logical branch
    # is not counted twice in stale_branches (which can tip the Health light).
    branches = _dedupe_branches(branches)
    head = gitlog.repo_head(repo)
    idle_days = cfg["thresholds"]["stale_branch_days"]

    # Delivery
    pulse = metrics.pulse(commits_all, now_ts)
    stale = metrics.staleness_days(commits_all, now_ts)
    cadence = metrics.weekly_cadence(commits_all, now_ts)
    release = metrics.release_recency(tags, now_ts)
    throughput = metrics.throughput_per_week(commits_all, now_ts)
    heat = metrics.when_we_work(commits_90)
    modules = cfg.get("modules") or reposcan.detect_modules(repo)
    module_activity = [{"module": m, "commits_30d": gitlog.count_commits(repo, 30, m)}
                       for m in modules]

    # Health
    fire = metrics.firefighting_rate(commits_all, now_ts)
    hotspots = metrics.churn_hotspots(fcc)
    sbranch = metrics.stale_branches(branches, now_ts, idle_days)
    debt = reposcan.debt_markers(repo)
    hyg = reposcan.hygiene(repo)
    msg_hyg = metrics.commit_message_hygiene(commits_90)

    # Team
    bf = metrics.bus_factor(commits_all, now_ts)
    active = metrics.active_authors(commits_all, now_ts)
    dist = metrics.contribution_distribution(commits_all, now_ts)
    dormant = metrics.dormant_authors(commits_all, now_ts)
    solo = metrics.is_solo(commits_all)
    off = metrics.off_hours_pct(commits_all, now_ts) if cfg.get("off_hours") == "on" else None

    # Lights
    l_delivery = TH.worst([
        TH.light_staleness(stale, cfg),
        TH.light_release(release["days_since"], release["has_tags"], cfg),
    ])
    l_health = TH.worst([
        TH.light_firefighting(fire, cfg),
        TH.light_stale_branches(len(sbranch), cfg),
    ])
    l_team = "na" if solo else TH.light_bus_factor(bf["count"], cfg)
    overall = TH.worst([l_delivery, l_health, l_team])

    return {
        "schema": 1,
        "generated_ts": now_ts,
        "repo": {"name": os.path.basename(os.path.abspath(repo)),
                 "branch": head["branch"], "commit": head["commit"],
                 "default_branch": default},
        "flags": {"solo": solo, "shallow": gitlog.is_shallow(repo)},
        "kpis": {
            "pulse": {"count_30d": pulse["count_30d"], "pct_change": pulse["pct_change"]},
            "last_commit_days": stale,
            "bus_factor": bf["count"],
            "active_devs": active,
            "firefighting_pct": fire,
            "stale_branches": len(sbranch),
            "last_release_days": release["days_since"],
            "open_prs": None,
        },
        "lenses": {
            "delivery": {"light": l_delivery, "cadence": cadence, "release": release,
                         "throughput": throughput, "modules": module_activity, "heatmap": heat},
            "health": {"light": l_health, "firefighting_pct": fire, "hotspots": hotspots,
                       "stale_branches": sbranch, "debt": debt, "hygiene": hyg,
                       "msg_hygiene": msg_hyg},
            "team": {"light": l_team, "bus_factor": bf, "active_devs": active,
                     "distribution": dist, "dormant": dormant, "off_hours_pct": off},
        },
        "overall": {"light": overall, "summary": None},
        "repo_state": {"modules": modules, "size": reposcan.project_size(repo)},
        "narrative": None, "host": None, "code_quality": None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Collect deterministic dashboard metrics")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out", default=None)
    ap.add_argument("--now", type=int, default=None, help="Override clock (unix ts)")
    args = ap.parse_args()

    if not gitlog.is_git_repo(args.repo):
        print(f"error: not a git repo: {args.repo}", file=sys.stderr)
        return 1
    now_ts = args.now if args.now is not None else int(time.time())
    data = build(args.repo, now_ts)
    text = json.dumps(data, indent=2)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
