#!/usr/bin/env python3
"""Run a skill, old version vs new version, on a fixture with known answers.

Usage (from the repository root):

    python3 evals/run_eval.py --skill quick-review --runs 2
    python3 evals/run_eval.py --skill codereview --old-ref HEAD --runs 2
    python3 evals/run_eval.py --skill codebase-audit --runs 1 --budget 25
    python3 evals/run_eval.py --skill interaction-review --runs 1 --budget 15

The "old" plugin comes from a git ref (default HEAD). The "new" plugin is the
working tree. Each copy is renamed (skilleval-old / skilleval-new) so it can
load next to an installed joesys-skills plugin. Every run works in a fresh
temporary git repo, so nothing touches this repository.

Per skill:

- codereview, quick-review: review the planted-defect code in
  fixtures/review-target and score the printed report against its answer key.
- codebase-audit: audit the same code with `--static-only`, so no tests or
  dependency audits run. The work dir gets a short multi-author git history
  (for churn) and seeded project context in .claude/skill-context/ (so the
  skill has nothing to ask). The report files are copied into the results
  folder, and summary.json gets a grade comparison between old and new.
  Compare two separate summaries with `python3 evals/audit_scoring.py`.
- interaction-review: review the synthetic session in
  fixtures/interaction-session. Before each run the session is installed as a
  Claude Code log for the work dir (~/.claude/projects/<slug>/<id>.jsonl);
  after the run that folder is removed. The report is scored against the
  answer key (lens score bands and designed issues).

This makes real model calls through `claude -p` and costs money.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import audit_scoring
import interaction_scoring
import scoring

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "evals" / "fixtures"
PLUGIN_PARTS = [".claude-plugin", "skills", "shared", "scripts"]
# Files that hold the answers. They never go into the work dir.
FIXTURE_ONLY = {"answer-key.json", "session.jsonl"}

ALLOWED_TOOLS = [
    "Read", "Grep", "Glob", "Agent", "Task", "Skill", "TodoWrite",
    "Bash(git *)", "Bash(ls *)", "Bash(wc *)", "Bash(find *)", "Bash(cat *)",
    "Bash(python3 *)",
]

NO_QUESTIONS = "This is a non-interactive evaluation run. Nobody can answer questions. "
REVIEW_ANSWERS = (
    "Where the skill would ask, choose the option that runs no extra tools "
    "and changes no files, then continue. Print the complete final report."
)
AUDIT_ANSWERS = (
    "Project context is already saved in .claude/skill-context/ (preferences.md and "
    "codebase-audit.md). Use it and do not ask about it. If the skill asks to approve "
    "live commands, choose Static only. At the metrics gate, choose Write both "
    "(metrics.json, metrics.md, and analysis.md). For any other question, choose the "
    "option that changes no source code, then continue. Write the report files, then "
    "print the final summary."
)
INTERACTION_ANSWERS = (
    "When the skill asks you to confirm the session list, proceed with the analysis. "
    "Skip the devlog offer. For any other question, choose the option that changes no "
    "source code, then continue. Write the report files, then print the final summary."
)

# Commits that rebuild the review-target code for the audit, so the churn and
# authorship agents have history to measure: (days ago, author, file, share of
# the file's final lines). src/orders.py grows in three steps, so it is the
# most-changed file. All dates fall inside the audit's 30-day churn window.
AUDIT_HISTORY = (
    (24, "alice", "src/orders.py", 1 / 3),
    (20, "bob", "src/auth.ts", 1.0),
    (16, "carol", "src/cache.go", 1.0),
    (10, "alice", "src/orders.py", 2 / 3),
    (3, "alice", "src/orders.py", 1.0),
)


@dataclass(frozen=True)
class SkillConfig:
    fixture: str                        # folder in evals/fixtures copied into the work dir
    target: str                         # text after the skill name in the prompt
    answers: str = REVIEW_ANSWERS       # how to answer the skill's questions headless
    budget: float = 10.0                # default USD cap per run
    extra_tools: tuple[str, ...] = ()   # tools on top of ALLOWED_TOOLS
    writes_reports: bool = False        # allow Write and Edit inside the work dir only
    report_dir: str | None = None       # folder in the work dir copied into the results
    overlay: str | None = None          # fixture folder copied on top (seeded context)
    history: tuple = ()                 # commits to build instead of one fixture commit
    session: str | None = None          # transcript installed as a Claude Code log
    answer_key: bool = True             # score against <fixture>/answer-key.json


SKILLS = {
    # codereview runs cost $6-11 in November 2026; a $10 cap would cut some short.
    "codereview": SkillConfig("review-target", "src/", budget=20.0),
    "quick-review": SkillConfig("review-target", "src/"),
    "codebase-audit": SkillConfig(
        "review-target", "--static-only",
        answers=AUDIT_ANSWERS, budget=25.0,
        extra_tools=("Bash(python *)", "Bash(mkdir *)", "Bash(head *)", "Bash(tail *)",
                     "Bash(grep *)", "Bash(sort *)"),
        writes_reports=True, report_dir="docs/reports/codebase-audit",
        overlay="audit-context", history=AUDIT_HISTORY, answer_key=False,
    ),
    "interaction-review": SkillConfig(
        "interaction-session", "session {session_id}",
        answers=INTERACTION_ANSWERS, budget=15.0,
        extra_tools=("Bash(python *)", "Bash(mkdir *)", "Bash(head *)", "Bash(tail *)",
                     "Bash(grep *)", "Bash(jq *)"),
        writes_reports=True, report_dir="docs/interaction-review",
        session="interaction-session/session.jsonl",
    ),
}


def make_plugin_copy(repo: Path, ref: str | None, label: str, root: Path) -> Path:
    """Copy the plugin (from `ref`, or the working tree if None) and rename it."""
    dest = root / f"plugin-{label}"
    dest.mkdir(parents=True)
    if ref is None:
        for part in PLUGIN_PARTS:
            source = repo / part
            shutil.copytree(source, dest / part, ignore=shutil.ignore_patterns("__pycache__"))
    else:
        archive = subprocess.run(
            ["git", "archive", ref, *PLUGIN_PARTS],
            cwd=repo, capture_output=True, check=True,
        ).stdout
        subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)

    manifest_path = dest / ".claude-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["name"] = f"skilleval-{label}"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return dest


def prepare_workdir(fixture: str, work: Path, *, overlay: str | None = None,
                    history: tuple = ()) -> Path:
    """Copy a fixture into a fresh git repo: one commit, or the given history."""
    shutil.copytree(
        FIXTURES / fixture, work, ignore=lambda _d, names: [n for n in names if n in FIXTURE_ONLY]
    )
    if overlay:
        shutil.copytree(FIXTURES / overlay, work, dirs_exist_ok=True)
    git = ["git", "-c", "commit.gpgsign=false", "-c", "user.name=eval", "-c", "user.email=eval@example.invalid"]
    subprocess.run(["git", "init", "-q"], cwd=work, check=True)
    if history:
        _commit_history(work, history)
    else:
        subprocess.run(["git", "add", "-A"], cwd=work, check=True)
        subprocess.run([*git, "commit", "-q", "-m", "fixture"], cwd=work, check=True)
    return work


def _commit_history(work: Path, history: tuple) -> None:
    """Commit the work dir as a short history with fixed authors and dates.

    Each step writes the first share of a file's final lines and commits it.
    The first commit also holds every file the history does not name. The last
    step for each file writes all of it, so the final tree equals the fixture.
    Dates are relative to now, so they stay inside a "last 30 days" window.
    """
    final = {path: (work / path).read_text(encoding="utf-8") for _, _, path, _ in history}
    for path in final:
        (work / path).unlink()
    now = datetime.now(timezone.utc)
    for index, (days_ago, author, path, share) in enumerate(history):
        lines = final[path].splitlines(keepends=True)
        (work / path).write_text("".join(lines[:round(len(lines) * share)]), encoding="utf-8")
        subprocess.run(["git", "add", "-A" if index == 0 else path], cwd=work, check=True)
        when = (now - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%S+0000")
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "-c", f"user.name={author}",
             "-c", f"user.email={author}@example.invalid",
             "commit", "-q", "-m", "Start the project" if index == 0 else f"Update {path}"],
            cwd=work, check=True,
            env={**os.environ, "GIT_AUTHOR_DATE": when, "GIT_COMMITTER_DATE": when},
        )


def prepare_skill_workdir(skill: str, work: Path) -> Path:
    config = SKILLS[skill]
    return prepare_workdir(config.fixture, work, overlay=config.overlay, history=config.history)


def build_prompt(plugin_name: str, skill: str, target: str) -> str:
    return f"/{plugin_name}:{skill} {target}\n\n{NO_QUESTIONS}{SKILLS[skill].answers}"


def allowed_tools(skill: str, work: Path) -> list[str]:
    """The tools a run may use. Report-writing skills may write only in the work dir."""
    config = SKILLS[skill]
    tools = ALLOWED_TOOLS + list(config.extra_tools)
    if config.writes_reports:
        # In a permission rule, "//" starts an absolute path, so `work` is absolute.
        tools += [f"Write(/{work}/**)", f"Edit(/{work}/**)"]
    return tools


def claude_project_slug(path: Path) -> str:
    """Claude Code's log folder name for a cwd: every non-alphanumeric character becomes '-'."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(path))


def claude_projects_root() -> Path:
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude"
    return Path(config_dir) / "projects"


@contextmanager
def installed_session(fixture_file: Path, work: Path, projects_root: Path, session_id: str):
    """Install a transcript as a Claude Code log for `work`, and remove it afterwards.

    The fixture was written for a made-up project folder. Every mention of that
    folder (the `cwd` fields and the tool file paths) is rewritten to `work`, and
    every `sessionId` to `session_id`, so the log looks like a real session of
    the work dir.
    """
    folder = projects_root / claude_project_slug(work)
    created = not folder.exists()
    path = folder / f"{session_id}.jsonl"
    raw_lines = fixture_file.read_text(encoding="utf-8").splitlines()
    fixture_cwd = next(json.loads(raw)["cwd"] for raw in raw_lines if '"cwd"' in raw)
    try:
        folder.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as out:
            for raw in raw_lines:
                line = json.loads(raw.replace(fixture_cwd, str(work)))
                line["sessionId"] = session_id
                out.write(json.dumps(line) + "\n")
        yield path
    finally:
        if created:
            shutil.rmtree(folder, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)


def run_once(plugin: Path, plugin_name: str, skill: str, work: Path,
             budget: float, model: str | None, target: str | None = None) -> dict:
    cmd = [
        "claude", "-p", build_prompt(plugin_name, skill, target or SKILLS[skill].target),
        "--plugin-dir", str(plugin),
        "--output-format", "json",
        "--max-budget-usd", str(budget),
        "--allowedTools", *allowed_tools(skill, work),
    ]
    if model:
        cmd += ["--model", model]
    started = time.time()
    proc = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=3600)
    elapsed = round(time.time() - started, 1)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"result": proc.stdout, "is_error": True, "stderr": proc.stderr[-2000:]}
    payload["wall_seconds"] = elapsed
    return payload


def run_skill(plugin: Path, plugin_name: str, skill: str, work: Path,
              budget: float, model: str | None) -> dict:
    """Run once; for interaction-review, with the session log installed around the run."""
    config = SKILLS[skill]
    if config.session is None:
        return run_once(plugin, plugin_name, skill, work, budget, model)
    session_id = str(uuid.uuid4())
    with installed_session(FIXTURES / config.session, work, claude_projects_root(), session_id):
        payload = run_once(plugin, plugin_name, skill, work, budget, model,
                           target=config.target.format(session_id=session_id))
    payload["eval_session_id"] = session_id
    return payload


def collect_reports(skill: str, work: Path, dest: Path) -> Path | None:
    """Copy the report files the skill wrote, before the temp work dir is deleted."""
    report_dir = SKILLS[skill].report_dir
    if report_dir is None or not (work / report_dir).is_dir():
        return None
    shutil.copytree(work / report_dir, dest, dirs_exist_ok=True)
    return dest


def score_run(skill: str, report: str, files: Path | None, key: dict | None) -> dict:
    """Score one run: from the copied report files where the skill writes them."""
    if skill == "codebase-audit":
        return {"skill": skill, **audit_scoring.score_audit(files)}
    if skill == "interaction-review":
        written = sorted(files.rglob("*-interaction-review.md")) if files else []
        text = written[-1].read_text(encoding="utf-8") if written else report
        return {**interaction_scoring.score_interaction(text, key), "report_file": bool(written)}
    return scoring.score(report, key, skill=skill)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--skill", choices=sorted(SKILLS), required=True)
    parser.add_argument("--old-ref", default="HEAD")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--budget", type=float, default=None,
                        help="USD cap per run (default: 10, codebase-audit 25, interaction-review 15)")
    parser.add_argument("--model", default=None)
    parser.add_argument("--only", choices=["old", "new"], default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    config = SKILLS[args.skill]
    budget = args.budget if args.budget is not None else config.budget
    stamp = time.strftime("%Y%m%d-%H%M%S")
    out = args.out or REPO_ROOT / "evals" / "results" / f"{stamp}-{args.skill}"
    out.mkdir(parents=True, exist_ok=True)
    key = None
    if config.answer_key:
        key = json.loads((FIXTURES / config.fixture / "answer-key.json").read_text())

    labels = [args.only] if args.only else ["old", "new"]
    summary = []
    with tempfile.TemporaryDirectory(prefix="skilleval-") as tmp:
        tmp_root = Path(tmp).resolve()
        plugins = {
            label: make_plugin_copy(REPO_ROOT, args.old_ref if label == "old" else None, label, tmp_root)
            for label in labels
        }
        for run in range(1, args.runs + 1):
            for label in labels:
                work = prepare_skill_workdir(args.skill, tmp_root / f"work-{label}-{run}")
                payload = run_skill(plugins[label], f"skilleval-{label}", args.skill,
                                    work, budget, args.model)
                report = payload.get("result") or ""
                (out / f"{label}-{run}.md").write_text(report, encoding="utf-8")
                (out / f"{label}-{run}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
                files = collect_reports(args.skill, work, out / f"{label}-{run}-files")
                result = score_run(args.skill, report, files, key)
                result.update({
                    "version": label, "run": run,
                    "cost_usd": payload.get("total_cost_usd"),
                    "seconds": payload.get("wall_seconds"),
                    "error": bool(payload.get("is_error")),
                })
                summary.append(result)
                print(json.dumps(result))

    document = {"skill": args.skill, "old_ref": args.old_ref, "budget": budget, "results": summary}
    if args.skill == "codebase-audit":
        old, new = audit_scoring.split_by_version(summary)
        if old and new:
            document["grade_comparison"] = audit_scoring.compare_grades(old, new)
            moved = document["grade_comparison"]["changed"]
            print("Grades are stable." if not moved else
                  "Grades moved: " + ", ".join(f"{r['criterion']} {r['old']} -> {r['new']}" for r in moved))
    (out / "summary.json").write_text(json.dumps(document, indent=2), encoding="utf-8")
    print(f"Saved to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
