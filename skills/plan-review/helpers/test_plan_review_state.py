from __future__ import annotations

import json
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import plan_review_state


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


def make_repo(tmp_path: Path) -> tuple[Path, Path, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test User")
    git(tmp_path, "config", "commit.gpgsign", "false")
    spec = tmp_path / "spec.md"
    plan = tmp_path / "plan.md"
    source = tmp_path / "app.py"
    spec.write_text("# Spec\n\nRequirement A\n", encoding="utf-8")
    plan.write_text("# Plan\n\nImplement A\n", encoding="utf-8")
    source.write_text("VALUE = 1\n", encoding="utf-8")
    git(tmp_path, "add", "spec.md", "plan.md", "app.py")
    git(tmp_path, "commit", "-m", "initial")
    return tmp_path, spec, plan


def test_create_ledger_outside_repository(tmp_path: Path) -> None:
    repo, spec, plan = make_repo(tmp_path)

    ledger_path, ledger = plan_review_state.create_ledger(
        repo,
        [spec, plan],
        max_iterations=20,
    )

    assert ledger["schema_version"] == 1
    assert ledger["repo_root"] == str(repo.resolve())
    assert ledger["documents"] == ["spec.md", "plan.md"]
    assert ledger["max_iterations"] == 20
    assert ledger["iterations"] == []
    assert not ledger_path.is_relative_to(repo.resolve())
    assert ledger_path.parent == Path(tempfile.gettempdir()).resolve()
    assert json.loads(ledger_path.read_text(encoding="utf-8")) == ledger
    plan_review_state.finish_ledger(ledger_path)


def test_create_ledger_rejects_invalid_iteration_ceiling(tmp_path: Path) -> None:
    repo, spec, _ = make_repo(tmp_path)

    with pytest.raises(plan_review_state.StateError, match="between 1 and 20"):
        plan_review_state.create_ledger(repo, [spec], max_iterations=21)


@pytest.mark.skipif(sys.platform == "win32", reason="Windows uses ACLs")
def test_ledger_is_private_to_current_user(tmp_path: Path) -> None:
    repo, spec, plan = make_repo(tmp_path)

    ledger_path, _ = plan_review_state.create_ledger(repo, [spec, plan])

    assert stat.S_IMODE(ledger_path.stat().st_mode) == 0o600


def test_create_ledger_requires_documents_inside_repo(tmp_path: Path) -> None:
    repo, _, _ = make_repo(tmp_path / "repo")
    outside = tmp_path / "outside.md"
    outside.write_text("# Outside\n", encoding="utf-8")

    with pytest.raises(plan_review_state.StateError, match="inside repository"):
        plan_review_state.create_ledger(repo, [outside], max_iterations=20)


def test_baseline_preserves_existing_document_edits(tmp_path: Path) -> None:
    repo, spec, plan = make_repo(tmp_path)
    spec.write_text("# Spec\n\nDraft edit\n", encoding="utf-8")

    _, ledger = plan_review_state.create_ledger(repo, [spec, plan])

    assert ledger["baseline"]["document_hashes"]["spec.md"] == (
        plan_review_state.sha256_file(spec)
    )
    assert "spec.md" not in ledger["baseline"]["non_target_paths"]


def test_non_target_fingerprint_ignores_review_documents(tmp_path: Path) -> None:
    repo, spec, plan = make_repo(tmp_path)
    _, ledger = plan_review_state.create_ledger(repo, [spec, plan])
    before = ledger["baseline"]["non_target_fingerprint"]

    spec.write_text("# Spec\n\nAccepted fix\n", encoding="utf-8")

    assert plan_review_state.capture_non_target_state(
        repo,
        ledger["documents"],
    )["fingerprint"] == before


def test_non_target_fingerprint_detects_tracked_and_untracked_changes(
    tmp_path: Path,
) -> None:
    repo, spec, plan = make_repo(tmp_path)
    _, ledger = plan_review_state.create_ledger(repo, [spec, plan])
    before = ledger["baseline"]["non_target_fingerprint"]

    (repo / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    (repo / "notes.txt").write_text("concurrent work\n", encoding="utf-8")
    current = plan_review_state.capture_non_target_state(
        repo,
        ledger["documents"],
    )

    assert current["fingerprint"] != before
    assert current["paths"] == ["app.py", "notes.txt"]


def test_finish_ledger_removes_file(tmp_path: Path) -> None:
    repo, spec, plan = make_repo(tmp_path)
    ledger_path, _ = plan_review_state.create_ledger(repo, [spec, plan])

    plan_review_state.finish_ledger(ledger_path)

    assert not ledger_path.exists()


def test_document_diff_uses_captured_draft_baseline(tmp_path: Path) -> None:
    repo, spec, plan = make_repo(tmp_path)
    spec.write_text("# Spec\n\nDraft requirement\n", encoding="utf-8")
    ledger_path, _ = plan_review_state.create_ledger(repo, [spec, plan])
    spec.write_text("# Spec\n\nAccepted requirement\n", encoding="utf-8")

    diff = plan_review_state.document_diff(ledger_path)

    assert "-Draft requirement" in diff
    assert "+Accepted requirement" in diff
    assert "Requirement A" not in diff


def test_start_and_finish_cli(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, spec, plan = make_repo(tmp_path)

    exit_code = plan_review_state.main(
        [
            "start",
            "--repo",
            str(repo),
            "--document",
            str(spec),
            "--document",
            str(plan),
        ]
    )

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    ledger_path = Path(payload["ledger_path"])
    assert ledger_path.is_file()
    assert "document_contents" not in payload["baseline"]

    assert plan_review_state.main(["finish", "--ledger", str(ledger_path)]) == 0
    assert not ledger_path.exists()
