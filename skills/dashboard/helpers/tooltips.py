# tooltips.py
"""Static, definitional tooltip copy for every dashboard metric.

This is the *deterministic* half of the tooltip system: the "What this
measures" and "Why it matters" text is the same for every repo and lives in
code (so it works on --no-llm and in CI). The per-repo "In this repo" line is
the *prose* half, written by the narrative step into ``narrative.analysis`` and
composed in by the renderer.

Each entry is ``{"title", "what", "why"}``. Copy is plain-English and frames
every metric as a proxy that points at where to look — not a verdict.
"""
from __future__ import annotations

TOOLTIPS: dict[str, dict[str, str]] = {
    "overall": {
        "title": "Overall health",
        "what": "The worst of the three lens lights (Delivery, Health, Team), "
                "rolled up into one traffic light.",
        "why": "A one-glance read on where the project stands. The colour is "
               "driven by whichever lens is in the worst shape.",
    },
    # ---- KPI strip ----
    "kpi.pulse": {
        "title": "Pulse (30 days)",
        "what": "Commits in the last 30 days, with the percentage change versus "
                "the previous 30 days.",
        "why": "A rough gauge of how much work is landing right now. Rising "
               "pulse means momentum; a sharp drop can signal a stall.",
    },
    "kpi.last_commit": {
        "title": "Last commit",
        "what": "Whole days since the most recent commit on any branch.",
        "why": "Shows whether the repo is actively worked on. A long gap may "
               "mean the project is paused, finished, or abandoned.",
    },
    "kpi.bus_factor": {
        "title": "Bus factor",
        "what": "How many authors it takes to account for more than half of "
                "recent commits. 1 means a single person wrote most of the code.",
        "why": "A low bus factor is key-person risk: if that person leaves, "
               "knowledge and momentum leave with them.",
    },
    "kpi.active_devs": {
        "title": "Active developers",
        "what": "Distinct authors who committed in the last 30 days.",
        "why": "How many people are contributing right now. It also frames other "
               "metrics — concentration is expected when few devs are active.",
    },
    "kpi.firefighting": {
        "title": "Firefighting rate",
        "what": "Share of recent commits whose messages look like reverts, "
                "rollbacks, or hotfixes (a keyword heuristic).",
        "why": "A high rate suggests reacting to breakage rather than building. "
               "It points at instability — it doesn't by itself prove a problem.",
    },
    "kpi.stale_branches": {
        "title": "Stale branches",
        "what": "Non-default branches with no activity beyond the stale "
                "threshold (default 30 days).",
        "why": "Unfinished or forgotten work. A growing pile signals merge debt, "
               "abandoned features, and a cluttered history.",
    },
    "kpi.last_release": {
        "title": "Last release",
        "what": "Whole days since the newest git tag. A dash means the repo has "
                "no tags.",
        "why": "Roughly how recently something shipped. No tags can mean "
               "releases aren't tracked in git — not that nothing ships.",
    },
    "kpi.open_prs": {
        "title": "Open PRs",
        "what": "Open pull requests, read live from the host (GitHub) as of the "
                "run.",
        "why": "Work waiting to merge. A large or aging backlog points at review "
               "bottlenecks slowing delivery.",
    },
    "kpi.wip_branches": {
        "title": "WIP branches",
        "what": "Count of stale (idle) branches, shown here when no host/PR data "
                "is available.",
        "why": "A stand-in for work-in-progress that hasn't merged. A high count "
               "hints at unfinished or stuck work.",
    },
    # ---- Delivery lens ----
    "lens.delivery": {
        "title": "Delivery & Momentum",
        "what": "Are we shipping steadily? Combines commit cadence, throughput, "
                "and how recently anything was released.",
        "why": "Tracks whether the project keeps moving and delivering — "
               "independent of code quality or who is doing the work.",
    },
    "delivery.cadence": {
        "title": "Commit cadence",
        "what": "Weekly commit counts over the last 26 weeks (the sparkline), "
                "oldest to newest.",
        "why": "The rhythm of work: steady, accelerating, or fading. Spikes "
               "often line up with deadlines, releases, or holidays.",
    },
    "delivery.throughput": {
        "title": "Throughput",
        "what": "Average merge commits per week over the recent window.",
        "why": "A simple flow measure — how often finished work lands. Good for "
               "spotting whether delivery is speeding up or slowing down.",
    },
    "delivery.release": {
        "title": "Release recency",
        "what": "The newest git tag and how long ago it was created (or that "
                "there are no tags).",
        "why": "Whether shipping is recent and tracked. No tags isn't "
               "automatically bad — many teams release without tagging.",
    },
    "delivery.modules": {
        "title": "Module activity",
        "what": "Commits in the last 30 days broken down by top-level "
                "module/directory.",
        "why": "Where effort is concentrated. Helps confirm work is happening "
               "where the roadmap expects it.",
    },
    "delivery.heatmap": {
        "title": "When we work",
        "what": "Commit counts by weekday and hour over the last 90 days "
                "(darker = more commits).",
        "why": "Working patterns — crunch times, weekend or off-hours work that "
               "may hint at workload. It's a pattern, not a judgement.",
    },
    "delivery.host": {
        "title": "From the host",
        "what": "Live pull-request, CI, and issue figures pulled from GitHub as "
                "of the run.",
        "why": "The collaboration picture git alone can't see — review backlog, "
               "build health, and open issues at build time.",
    },
    # ---- Health lens ----
    "lens.health": {
        "title": "Health & Risk",
        "what": "Where might problems be hiding? Combines firefighting, stale "
                "branches, churn hotspots, debt markers, and basic hygiene.",
        "why": "Surfaces risk and friction that raw output numbers miss — "
               "pointing at where to look before things break.",
    },
    "health.hotspots": {
        "title": "Churn hotspots",
        "what": "The files changed most often in the last 90 days, with their "
                "change counts.",
        "why": "Frequently-churned files are often unstable or carrying too much "
               "responsibility — natural candidates for review or refactoring.",
    },
    "health.stale_branches": {
        "title": "Stale branches",
        "what": "Non-default branches idle past the threshold, listed most-idle "
                "first with their idle days.",
        "why": "Each is unfinished or forgotten work. The list shows exactly "
               "which branches to merge, rebase, or delete.",
    },
    "health.hygiene": {
        "title": "Repo hygiene",
        "what": "Quick yes/no checks: is there CI, a lockfile, is .env "
                "git-ignored, and are there tests?",
        "why": "Basic guardrails that prevent whole classes of problems. A "
               "failing check is a cheap, concrete thing to fix.",
    },
    "health.debt": {
        "title": "Debt markers",
        "what": "Counts of TODO, FIXME, and HACK comments left in the code.",
        "why": "A rough proxy for acknowledged shortcuts and unfinished work. "
               "The trend matters more than the absolute number.",
    },
    "health.code_quality": {
        "title": "Code quality (borrowed)",
        "what": "The most recent /codebase-audit grade, if one exists — this "
                "dashboard never grades code itself.",
        "why": "Points to a deeper, sourced assessment. It's point-in-time: it "
               "describes the commit it ran against, which may be behind HEAD.",
    },
    # ---- Team lens ----
    "lens.team": {
        "title": "Team & Contribution",
        "what": "How healthy is the contribution pattern? Looks at bus factor, "
                "how evenly commits are spread, and who's gone quiet.",
        "why": "Highlights key-person risk and knowledge concentration — people "
               "problems that threaten a project as much as technical ones.",
    },
    "team.bus_factor": {
        "title": "Bus factor & ownership",
        "what": "How concentrated commits are: the bus-factor count plus the "
                "largest contributor's share of recent work.",
        "why": "Concentrated ownership is fragile. Spreading review and "
               "authorship reduces the risk of losing one critical person.",
    },
    "team.distribution": {
        "title": "Contribution spread",
        "what": "Per-author commit counts (the bars) and a Gini index from 0 "
                "(even) toward 1 (concentrated).",
        "why": "Whether work is shared or resting on a few shoulders — context "
               "for the bus factor and for planning coverage.",
    },
    "team.dormant": {
        "title": "Dormant & newly active",
        "what": "Authors who've gone quiet for 90+ days versus those who first "
                "appeared in the last 30.",
        "why": "Team churn — who's drifted away (taking knowledge with them) and "
               "who's ramping up.",
    },
    "team.off_hours": {
        "title": "Off-hours commits",
        "what": "Share of recent commits on weekends or outside ~08:00–19:00 "
                "(a proxy, only shown when enabled).",
        "why": "A soft signal of crunch. It's noisy — time zones and schedules "
               "vary — so treat it as a prompt to ask, not a conclusion.",
    },
}

METRIC_IDS: list[str] = list(TOOLTIPS)


def get(metric_id: str) -> dict[str, str]:
    """Return the ``{title, what, why}`` copy for a metric id.

    Raises ``KeyError`` on an unknown id so the renderer and this dictionary
    cannot drift apart silently.
    """
    return TOOLTIPS[metric_id]
