"""Tests for the offline parts of the eval runner (evals/run_eval.py)."""

import json
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
