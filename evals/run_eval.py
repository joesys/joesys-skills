#!/usr/bin/env python3
"""Run a review skill, old version vs new version, on the planted-defect fixture.

Usage (from the repository root):

    python3 evals/run_eval.py --skill quick-review --runs 2
    python3 evals/run_eval.py --skill codereview --old-ref HEAD --runs 1 --budget 15

The "old" plugin comes from a git ref (default HEAD). The "new" plugin is the
working tree. Each copy is renamed (skilleval-old / skilleval-new) so it can
load next to an installed joesys-skills plugin. Every run works in a fresh
temporary git repo, so nothing touches this repository.

This makes real model calls through `claude -p` and costs money.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import scoring

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "evals" / "fixtures"
PLUGIN_PARTS = [".claude-plugin", "skills", "shared", "scripts"]
FIXTURE_ONLY = {"answer-key.json"}

SKILL_TARGETS = {
    "codereview": ("review-target", "src/"),
    "quick-review": ("review-target", "src/"),
}

ALLOWED_TOOLS = [
    "Read", "Grep", "Glob", "Agent", "Task", "Skill", "TodoWrite",
    "Bash(git *)", "Bash(ls *)", "Bash(wc *)", "Bash(find *)", "Bash(cat *)",
    "Bash(python3 *)",
]


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


def prepare_workdir(fixture: str, work: Path) -> Path:
    """Copy a fixture into a fresh git repo with one commit."""
    shutil.copytree(
        FIXTURES / fixture, work, ignore=lambda _d, names: [n for n in names if n in FIXTURE_ONLY]
    )
    git = ["git", "-c", "commit.gpgsign=false", "-c", "user.name=eval", "-c", "user.email=eval@example.invalid"]
    subprocess.run(["git", "init", "-q"], cwd=work, check=True)
    subprocess.run(["git", "add", "-A"], cwd=work, check=True)
    subprocess.run([*git, "commit", "-q", "-m", "fixture"], cwd=work, check=True)
    return work


def build_prompt(plugin_name: str, skill: str, target: str) -> str:
    return (
        f"/{plugin_name}:{skill} {target}\n\n"
        "This is a non-interactive evaluation run. Nobody can answer questions. "
        "Where the skill would ask, choose the option that runs no extra tools "
        "and changes no files, then continue. Print the complete final report."
    )


def run_once(plugin: Path, plugin_name: str, skill: str, work: Path,
             budget: float, model: str | None) -> dict:
    fixture_target = SKILL_TARGETS[skill][1]
    cmd = [
        "claude", "-p", build_prompt(plugin_name, skill, fixture_target),
        "--plugin-dir", str(plugin),
        "--output-format", "json",
        "--max-budget-usd", str(budget),
        "--allowedTools", *ALLOWED_TOOLS,
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--skill", choices=sorted(SKILL_TARGETS), required=True)
    parser.add_argument("--old-ref", default="HEAD")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--budget", type=float, default=10.0, help="USD cap per run")
    parser.add_argument("--model", default=None)
    parser.add_argument("--only", choices=["old", "new"], default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    stamp = time.strftime("%Y%m%d-%H%M%S")
    out = args.out or REPO_ROOT / "evals" / "results" / f"{stamp}-{args.skill}"
    out.mkdir(parents=True, exist_ok=True)
    key = json.loads((FIXTURES / SKILL_TARGETS[args.skill][0] / "answer-key.json").read_text())

    labels = [args.only] if args.only else ["old", "new"]
    summary = []
    with tempfile.TemporaryDirectory(prefix="skilleval-") as tmp:
        tmp_root = Path(tmp)
        plugins = {
            label: make_plugin_copy(REPO_ROOT, args.old_ref if label == "old" else None, label, tmp_root)
            for label in labels
        }
        for run in range(1, args.runs + 1):
            for label in labels:
                work = prepare_workdir(SKILL_TARGETS[args.skill][0], tmp_root / f"work-{label}-{run}")
                payload = run_once(plugins[label], f"skilleval-{label}", args.skill,
                                   work, args.budget, args.model)
                report = payload.get("result") or ""
                (out / f"{label}-{run}.md").write_text(report, encoding="utf-8")
                (out / f"{label}-{run}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
                result = scoring.score(report, key, skill=args.skill)
                result.update({
                    "version": label, "run": run,
                    "cost_usd": payload.get("total_cost_usd"),
                    "seconds": payload.get("wall_seconds"),
                    "error": bool(payload.get("is_error")),
                })
                summary.append(result)
                print(json.dumps(result))

    (out / "summary.json").write_text(json.dumps({
        "skill": args.skill, "old_ref": args.old_ref, "results": summary,
    }, indent=2), encoding="utf-8")
    print(f"Saved to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
