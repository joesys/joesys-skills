"""Tests for the offline parts of the eval runner (evals/run_eval.py)."""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals"))

import run_eval  # noqa: E402


def test_plugin_copy_from_working_tree_is_renamed(tmp_path):
    dest = run_eval.make_plugin_copy(REPO_ROOT, None, "new", tmp_path)
    manifest = json.loads((dest / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "skilleval-new"
    assert (dest / "skills" / "codereview" / "SKILL.md").is_file()
    assert (dest / "shared" / "review-common.md").is_file()
    assert (dest / "scripts" / "html_render.py").is_file()


def test_plugin_copy_from_git_ref_uses_committed_files(tmp_path):
    dest = run_eval.make_plugin_copy(REPO_ROOT, "HEAD", "old", tmp_path)
    manifest = json.loads((dest / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "skilleval-old"
    committed = subprocess.run(
        ["git", "show", "HEAD:skills/commit/SKILL.md"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    assert (dest / "skills" / "commit" / "SKILL.md").read_text() == committed


def test_workdir_is_a_fresh_git_repo_with_the_fixture(tmp_path):
    work = run_eval.prepare_workdir("review-target", tmp_path / "work")
    assert (work / "src" / "orders.py").is_file()
    assert not (work / "answer-key.json").exists()
    log = subprocess.run(
        ["git", "log", "--oneline"], cwd=work, capture_output=True, text=True, check=True
    ).stdout
    assert log.strip()


def test_prompt_names_the_renamed_skill_and_forbids_questions():
    prompt = run_eval.build_prompt("skilleval-old", "quick-review", "src/")
    assert prompt.startswith("/skilleval-old:quick-review src/")
    assert "non-interactive" in prompt


# --- Per-skill settings ---------------------------------------------------


def test_existing_review_skills_keep_their_tools_and_prompt(tmp_path):
    for skill in ("codereview", "quick-review"):
        assert run_eval.allowed_tools(skill, tmp_path) == run_eval.ALLOWED_TOOLS
        assert run_eval.SKILLS[skill].target == "src/"
    assert run_eval.SKILLS["quick-review"].budget == 10.0
    prompt = run_eval.build_prompt("skilleval-new", "codereview", "src/")
    assert "choose the option that runs no extra tools" in prompt


def test_new_skills_have_bigger_default_budgets():
    assert run_eval.SKILLS["codebase-audit"].budget >= 20
    assert run_eval.SKILLS["interaction-review"].budget >= 10


# --- codebase-audit -------------------------------------------------------


def test_codebase_audit_prompt_is_static_only_and_answers_the_gates():
    target = run_eval.SKILLS["codebase-audit"].target
    prompt = run_eval.build_prompt("skilleval-new", "codebase-audit", target)
    assert prompt.startswith("/skilleval-new:codebase-audit --static-only")
    assert "non-interactive" in prompt
    assert "Static only" in prompt
    assert "Write both" in prompt
    assert ".claude/skill-context" in prompt


def test_codebase_audit_may_write_only_inside_the_work_dir(tmp_path):
    work = tmp_path / "work"
    tools = run_eval.allowed_tools("codebase-audit", work)
    assert f"Write(/{work}/**)" in tools
    assert f"Edit(/{work}/**)" in tools
    assert "Write" not in tools and "Edit" not in tools
    assert "Bash(python3 *)" in tools and "Bash(python *)" in tools
    assert set(run_eval.ALLOWED_TOOLS) <= set(tools)


def _git(work, *args):
    return subprocess.run(["git", *args], cwd=work, capture_output=True, text=True,
                          check=True).stdout


def test_codebase_audit_workdir_has_context_and_history(tmp_path):
    work = run_eval.prepare_skill_workdir("codebase-audit", tmp_path / "work")
    fixture = REPO_ROOT / "evals" / "fixtures" / "review-target"

    # Same code as the review fixture, without the answer key.
    for name in ("orders.py", "auth.ts", "cache.go"):
        assert (work / "src" / name).read_text() == (fixture / "src" / name).read_text()
    assert not (work / "answer-key.json").exists()

    # Seeded project context, so the skill has no reason to ask.
    shared = (work / ".claude" / "skill-context" / "preferences.md").read_text()
    audit = (work / ".claude" / "skill-context" / "codebase-audit.md").read_text()
    for field in ("Project phase", "Team size", "Deployment cadence", "Business priority"):
        assert field in shared
    assert "Known Trade-offs" in audit

    # A short history with several authors, all inside the 30-day churn window.
    authors = _git(work, "log", "--format=%an").split()
    assert len(authors) >= 4
    assert len(set(authors)) >= 2
    orders_commits = _git(work, "log", "--format=%h", "--", "src/orders.py").split()
    assert len(orders_commits) >= 3
    recent = _git(work, "log", "--since=30 days ago", "--format=%h").split()
    assert len(recent) == len(authors)
    assert _git(work, "status", "--porcelain").strip() == ""


def test_audit_reports_are_copied_out_of_the_work_dir(tmp_path):
    work = tmp_path / "work"
    report = work / "docs" / "reports" / "codebase-audit" / "20261109"
    report.mkdir(parents=True)
    (report / "metrics.json").write_text("{}")
    dest = run_eval.collect_reports("codebase-audit", work, tmp_path / "out" / "new-1-files")
    assert (dest / "20261109" / "metrics.json").read_text() == "{}"


def test_collect_reports_returns_none_when_nothing_was_written(tmp_path):
    assert run_eval.collect_reports("codebase-audit", tmp_path, tmp_path / "out") is None
    assert run_eval.collect_reports("quick-review", tmp_path, tmp_path / "out") is None


def test_score_run_reads_audit_files(tmp_path):
    report_dir = tmp_path / "files" / "20261109"
    report_dir.mkdir(parents=True)
    (report_dir / "metrics.json").write_text(json.dumps({
        "overall_grade": "C",
        "criteria": {"security": {"grade": "D"}},
    }))
    result = run_eval.score_run("codebase-audit", "printed text", tmp_path / "files", None)
    assert result["overall_grade"] == "C"
    assert result["grades"]["security"] == "D"


# --- interaction-review ---------------------------------------------------


def test_claude_project_slug_replaces_every_non_alphanumeric_character():
    assert run_eval.claude_project_slug(Path("/tmp/skilleval-rq_8m/work-old-1")) == \
        "-tmp-skilleval-rq-8m-work-old-1"
    assert run_eval.claude_project_slug(Path("/home/a/.config")) == "-home-a--config"


def test_interaction_review_prompt_targets_one_session():
    prompt = run_eval.build_prompt("skilleval-old", "interaction-review", "session abc-123")
    assert prompt.startswith("/skilleval-old:interaction-review session abc-123")
    assert "non-interactive" in prompt
    assert "proceed" in prompt.lower()


def test_interaction_review_may_write_only_inside_the_work_dir(tmp_path):
    tools = run_eval.allowed_tools("interaction-review", tmp_path)
    assert f"Write(/{tmp_path}/**)" in tools
    assert "Write" not in tools


def test_interaction_workdir_has_the_project_but_no_session_or_key(tmp_path):
    work = run_eval.prepare_skill_workdir("interaction-review", tmp_path / "work")
    assert (work / "api" / "orders.py").is_file()
    assert not (work / "session.jsonl").exists()
    assert not (work / "answer-key.json").exists()
    assert not (work / "CLAUDE.md").exists()
    assert not (work / "AGENTS.md").exists()


def test_session_is_installed_with_rewritten_ids_and_removed_afterwards(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    projects = tmp_path / "claude-projects"
    fixture = REPO_ROOT / "evals" / "fixtures" / "interaction-session" / "session.jsonl"
    session_id = "11111111-2222-4333-8444-555555555555"

    try:
        with run_eval.installed_session(fixture, work, projects, session_id) as path:
            assert path == projects / run_eval.claude_project_slug(work) / f"{session_id}.jsonl"
            installed = [json.loads(line) for line in path.read_text().splitlines()]
            original = fixture.read_text().splitlines()
            assert len(installed) == len(original)
            assert all(line["sessionId"] == session_id for line in installed)
            assert all(line["cwd"] == str(work) for line in installed if "cwd" in line)
            # Tool paths in the transcript point into the work dir too.
            assert str(work) in path.read_text()
            assert "/home/dev/shop-api" not in path.read_text()
            raise RuntimeError("the run failed")
    except RuntimeError:
        pass
    assert not (projects / run_eval.claude_project_slug(work)).exists()


def test_run_transcripts_are_copied_out_before_the_log_folder_is_removed(tmp_path):
    # The review run writes its own transcript, and its helpers' transcripts,
    # into the same folder as the installed fixture log. Without a copy, nobody
    # can check afterwards what the helpers were told.
    work = tmp_path / "work"
    work.mkdir()
    projects = tmp_path / "claude-projects"
    fixture = REPO_ROOT / "evals" / "fixtures" / "interaction-session" / "session.jsonl"
    session_id = "11111111-2222-4333-8444-555555555555"
    keep = tmp_path / "kept"

    try:
        with run_eval.installed_session(fixture, work, projects, session_id, keep=keep) as path:
            (path.parent / "run-1" / "subagents").mkdir(parents=True)
            (path.parent / "run-1.jsonl").write_text("main\n")
            (path.parent / "run-1" / "subagents" / "agent-a.jsonl").write_text("helper\n")
            raise RuntimeError("the run failed")
    except RuntimeError:
        pass
    assert not (projects / run_eval.claude_project_slug(work)).exists()
    assert (keep / "run-1.jsonl").read_text() == "main\n"
    assert (keep / "run-1" / "subagents" / "agent-a.jsonl").read_text() == "helper\n"
    assert not (keep / f"{session_id}.jsonl").exists()


def test_other_sessions_in_an_existing_log_folder_are_not_copied(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    projects = tmp_path / "claude-projects"
    folder = projects / run_eval.claude_project_slug(work)
    folder.mkdir(parents=True)
    (folder / "someone-elses-session.jsonl").write_text("private\n")
    fixture = REPO_ROOT / "evals" / "fixtures" / "interaction-session" / "session.jsonl"
    keep = tmp_path / "kept"

    with run_eval.installed_session(fixture, work, projects, "s-1", keep=keep) as path:
        (path.parent / "run-1.jsonl").write_text("main\n")
    assert sorted(p.name for p in keep.iterdir()) == ["run-1.jsonl"]
    assert (folder / "someone-elses-session.jsonl").is_file()


def test_saved_results_are_ignored_by_git():
    # Transcripts hold everything the run read. They must never be staged.
    import subprocess
    probe = "evals/results/any-run/new-1-transcripts/run-1.jsonl"
    ignored = subprocess.run(["git", "check-ignore", "-q", probe], cwd=REPO_ROOT)
    assert ignored.returncode == 0


def test_score_run_reads_the_interaction_report_file(tmp_path):
    files = tmp_path / "files"
    files.mkdir()
    (files / "20261109-interaction-review.md").write_text(
        "---\nrubric_version: 2\n---\n\n| Lens | Score | Grade | Trend |\n|---|---|---|---|\n"
        "| Prompt Craft | 55 | F | new |\n"
    )
    key = json.loads(
        (REPO_ROOT / "evals" / "fixtures" / "interaction-session" / "answer-key.json").read_text()
    )
    result = run_eval.score_run("interaction-review", "printed only", files, key)
    assert result["report_file"] is True
    assert result["rubric_version"] == "2"
    assert result["lens_scores"]["prompt_craft"] == 55


# --- End to end with a fake `claude` command (no model calls) -------------

FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, os, re, sys
from pathlib import Path

prompt = sys.argv[sys.argv.index("-p") + 1]
work = Path.cwd()
if ":codebase-audit" in prompt:
    folder = work / "docs" / "reports" / "codebase-audit" / "20261109"
    folder.mkdir(parents=True)
    grade = "B" if "skilleval-old" in prompt else "C"
    (folder / "metrics.json").write_text(json.dumps(
        {"overall_grade": "C", "criteria": {"security": {"grade": grade}}}))
    (folder / "analysis.md").write_text("one two three")
else:
    session_id = re.search(r"session (\S+)", prompt).group(1)
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(work))
    log = Path(os.environ["CLAUDE_CONFIG_DIR"]) / "projects" / slug / f"{session_id}.jsonl"
    if log.is_file():
        (log.parent / "run-1" / "subagents").mkdir(parents=True)
        (log.parent / "run-1.jsonl").write_text('{"main": true}\n')
        (log.parent / "run-1" / "subagents" / "agent-a.jsonl").write_text('{"helper": true}\n')
    folder = work / "docs" / "interaction-review"
    folder.mkdir(parents=True)
    (folder / "20261109-interaction-review.md").write_text(
        "---\nrubric_version: 2\n---\n| Prompt Craft | 50 | F | new |\n"
        + ("log found" if log.is_file() else "log missing"))
print(json.dumps({"result": "printed report", "total_cost_usd": 0.0}))
'''


def _fake_claude(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "claude"
    fake.write_text(FAKE_CLAUDE)
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}:{os.environ['PATH']}")
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude-config"))


def test_main_audit_run_copies_reports_and_compares_grades(tmp_path, monkeypatch):
    _fake_claude(tmp_path, monkeypatch)
    out = tmp_path / "results"
    assert run_eval.main(["--skill", "codebase-audit", "--out", str(out)]) == 0
    summary = json.loads((out / "summary.json").read_text())
    assert summary["budget"] == run_eval.SKILLS["codebase-audit"].budget
    assert (out / "new-1-files" / "20261109" / "metrics.json").is_file()
    assert [r["analysis_words"] for r in summary["results"]] == [3, 3]
    moved = summary["grade_comparison"]["changed"]
    assert [(r["criterion"], r["old"], r["new"]) for r in moved] == [("security", ["B"], ["C"])]


def test_main_interaction_run_installs_and_removes_the_session_log(tmp_path, monkeypatch):
    _fake_claude(tmp_path, monkeypatch)
    out = tmp_path / "results"
    assert run_eval.main(["--skill", "interaction-review", "--only", "new", "--out", str(out)]) == 0
    report = next((out / "new-1-files").glob("*-interaction-review.md")).read_text()
    assert "log found" in report
    projects = tmp_path / "claude-config" / "projects"
    assert not projects.exists() or list(projects.iterdir()) == []
    result = json.loads((out / "summary.json").read_text())["results"][0]
    assert result["report_file"] is True
    assert result["lens_scores"] == {"prompt_craft": 50}
    # The run's own transcript is kept; the installed fixture log is not.
    kept = out / "new-1-transcripts"
    assert (kept / "run-1.jsonl").is_file()
    assert (kept / "run-1" / "subagents" / "agent-a.jsonl").is_file()
    assert sorted(path.name for path in kept.iterdir()) == ["run-1", "run-1.jsonl"]


def test_codereview_default_budget_covers_a_full_run():
    # Observed codereview runs cost up to $11.09; the default cap must not cut them short.
    assert run_eval.SKILLS["codereview"].budget >= 20
