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


def finding(
    finding_id: str,
    *,
    severity: str = "P1",
    concern_key: str = "missing-rollback",
    title: str = "Rollback is missing",
) -> dict:
    return {
        "id": finding_id,
        "concern_key": concern_key,
        "severity": severity,
        "title": title,
        "document": "plan.md",
        "location": "Migration / Step 4",
        "repository_evidence": ["migrations/0042_add_index.py"],
        "consequence": "The migration cannot be reversed safely.",
        "recommended_resolution": "Add an explicit rollback procedure.",
        "requires_user_decision": False,
    }


def iteration(
    findings: list[dict],
    verdicts: list[dict],
    *,
    applied: list[str] | None = None,
    validation_passed: bool = True,
) -> dict:
    return {
        "review": {"schema_version": 1, "findings": findings},
        "verdicts": verdicts,
        "applied_finding_ids": applied or [],
        "validation": {
            "passed": validation_passed,
            "checks": ["documents-readable", "traceability"],
        },
    }


def verdict(finding_id: str, value: str) -> dict:
    if value == "accepted":
        required_change = "Add rollback steps."
    elif value == "needs-user-decision":
        required_change = "Choose a rollback ownership model."
    else:
        required_change = None
    return {
        "finding_id": finding_id,
        "verdict": value,
        "rationale": "Grounded adjudication.",
        "required_change": required_change,
    }


def test_fingerprint_ignores_title_and_severity_wording() -> None:
    first = finding("R1")
    second = finding(
        "R9",
        severity="P2",
        title="No safe reverse migration exists",
    )

    assert plan_review_state.finding_fingerprint(first) == (
        plan_review_state.finding_fingerprint(second)
    )


def test_fingerprint_preserves_distinct_concerns() -> None:
    first = finding("R1")
    second = finding("R2", concern_key="missing-observability")

    assert plan_review_state.finding_fingerprint(first) != (
        plan_review_state.finding_fingerprint(second)
    )


def test_clean_rejected_lower_severity_round_converges(tmp_path: Path) -> None:
    repo, spec, plan = make_repo(tmp_path)
    ledger_path, _ = plan_review_state.create_ledger(repo, [spec, plan])
    low = finding("R1", severity="P3")

    result = plan_review_state.record_iteration(
        ledger_path,
        iteration([low], [verdict("R1", "rejected")]),
    )

    assert result == {"state": "converged", "reason": "clean fresh review"}


def test_accepted_lower_severity_fix_requires_fresh_iteration(
    tmp_path: Path,
) -> None:
    repo, spec, plan = make_repo(tmp_path)
    ledger_path, _ = plan_review_state.create_ledger(repo, [spec, plan])
    low = finding("R1", severity="P3")

    result = plan_review_state.record_iteration(
        ledger_path,
        iteration([low], [verdict("R1", "accepted")], applied=["R1"]),
    )

    assert result["state"] == "continue"
    assert result["reason"] == "accepted findings require a fresh review"
    recorded = plan_review_state.load_ledger(ledger_path)["iterations"][0]
    assert recorded["findings"][0]["document"] == "plan.md"
    assert recorded["findings"][0]["location"] == "Migration / Step 4"
    assert recorded["findings"][0]["rationale"] == "Grounded adjudication."
    assert recorded["findings"][0]["required_change"] == "Add rollback steps."


def test_blocking_finding_requires_fresh_iteration(tmp_path: Path) -> None:
    repo, spec, plan = make_repo(tmp_path)
    ledger_path, _ = plan_review_state.create_ledger(repo, [spec, plan])

    result = plan_review_state.record_iteration(
        ledger_path,
        iteration(
            [finding("R1")],
            [verdict("R1", "accepted")],
            applied=["R1"],
        ),
    )

    assert result == {
        "state": "continue",
        "reason": "fresh reviewer reported P0 or P1",
    }


def test_user_decision_pauses_after_other_fixes(tmp_path: Path) -> None:
    repo, spec, plan = make_repo(tmp_path)
    ledger_path, _ = plan_review_state.create_ledger(repo, [spec, plan])
    decision = finding("R1", severity="P2")
    decision["requires_user_decision"] = True

    result = plan_review_state.record_iteration(
        ledger_path,
        iteration(
            [decision],
            [verdict("R1", "needs-user-decision")],
        ),
    )

    assert result == {
        "state": "paused",
        "reason": "user decision required",
    }


def test_unapplied_accepted_finding_pauses(tmp_path: Path) -> None:
    repo, spec, plan = make_repo(tmp_path)
    ledger_path, _ = plan_review_state.create_ledger(repo, [spec, plan])

    result = plan_review_state.record_iteration(
        ledger_path,
        iteration(
            [finding("R1")],
            [verdict("R1", "accepted")],
        ),
    )

    assert result == {
        "state": "paused",
        "reason": "accepted findings remain unapplied",
    }


def test_validation_failure_pauses(tmp_path: Path) -> None:
    repo, spec, plan = make_repo(tmp_path)
    ledger_path, _ = plan_review_state.create_ledger(repo, [spec, plan])

    result = plan_review_state.record_iteration(
        ledger_path,
        iteration([], [], validation_passed=False),
    )

    assert result == {"state": "paused", "reason": "validation failed"}


def test_non_target_change_pauses(tmp_path: Path) -> None:
    repo, spec, plan = make_repo(tmp_path)
    ledger_path, _ = plan_review_state.create_ledger(repo, [spec, plan])
    (repo / "app.py").write_text("VALUE = 2\n", encoding="utf-8")

    result = plan_review_state.record_iteration(
        ledger_path,
        iteration([], []),
    )

    assert result["state"] == "paused"
    assert result["reason"] == "non-target repository state changed"
    assert result["paths"] == ["app.py"]


def test_same_material_finding_three_times_pauses_for_stagnation(
    tmp_path: Path,
) -> None:
    repo, spec, plan = make_repo(tmp_path)
    ledger_path, _ = plan_review_state.create_ledger(repo, [spec, plan])

    for review_id in ["R1", "R8"]:
        result = plan_review_state.record_iteration(
            ledger_path,
            iteration(
                [finding(review_id)],
                [verdict(review_id, "accepted")],
                applied=[review_id],
            ),
        )
        assert result["state"] == "continue"

    result = plan_review_state.record_iteration(
        ledger_path,
        iteration(
            [finding("R20", title="Rollback still absent")],
            [verdict("R20", "accepted")],
            applied=["R20"],
        ),
    )

    assert result == {
        "state": "paused",
        "reason": "same material finding survived three iterations",
    }


def test_document_state_a_b_a_pauses_for_oscillation(tmp_path: Path) -> None:
    repo, spec, plan = make_repo(tmp_path)
    ledger_path, _ = plan_review_state.create_ledger(repo, [spec, plan])
    state_a = plan.read_text(encoding="utf-8")

    plan_review_state.record_iteration(
        ledger_path,
        iteration(
            [finding("R1", severity="P3")],
            [verdict("R1", "accepted")],
            applied=["R1"],
        ),
    )
    plan.write_text("# Plan\n\nAlternative B\n", encoding="utf-8")
    plan_review_state.record_iteration(
        ledger_path,
        iteration(
            [finding("R2", severity="P3", concern_key="sequence-choice")],
            [verdict("R2", "accepted")],
            applied=["R2"],
        ),
    )
    plan.write_text(state_a, encoding="utf-8")

    result = plan_review_state.record_iteration(
        ledger_path,
        iteration(
            [finding("R3", severity="P3", concern_key="sequence-choice")],
            [verdict("R3", "accepted")],
            applied=["R3"],
        ),
    )

    assert result == {
        "state": "paused",
        "reason": "document state oscillated",
    }


def test_iteration_ceiling_allows_convergence_but_not_continuation(
    tmp_path: Path,
) -> None:
    repo, spec, plan = make_repo(tmp_path)
    ledger_path, ledger = plan_review_state.create_ledger(
        repo,
        [spec, plan],
        max_iterations=2,
    )
    ledger["iterations"].append({"number": 1, "findings": []})
    plan_review_state.save_ledger(ledger_path, ledger)

    clean = plan_review_state.record_iteration(ledger_path, iteration([], []))
    assert clean["state"] == "converged"

    ledger_path, ledger = plan_review_state.create_ledger(
        repo,
        [spec, plan],
        max_iterations=2,
    )
    ledger["iterations"].append({"number": 1, "findings": []})
    plan_review_state.save_ledger(ledger_path, ledger)
    blocking = plan_review_state.record_iteration(
        ledger_path,
        iteration(
            [finding("R1")],
            [verdict("R1", "rejected")],
        ),
    )
    assert blocking == {
        "state": "paused",
        "reason": "maximum iterations reached",
    }


@pytest.mark.parametrize(
    "case",
    [
        "invalid-severity",
        "duplicate-id",
        "missing-verdict",
        "unknown-verdict",
        "bad-evidence",
        "future-schema",
        "blank-rationale",
        "blank-required-change",
    ],
)
def test_malformed_iteration_does_not_append(
    tmp_path: Path,
    case: str,
) -> None:
    repo, spec, plan = make_repo(tmp_path)
    ledger_path, _ = plan_review_state.create_ledger(repo, [spec, plan])
    item = finding("R1")
    payload = iteration(
        [item],
        [verdict("R1", "accepted")],
        applied=["R1"],
    )

    if case == "invalid-severity":
        item["severity"] = "P9"
    elif case == "duplicate-id":
        payload["review"]["findings"].append(dict(item))
    elif case == "missing-verdict":
        payload["verdicts"] = []
    elif case == "unknown-verdict":
        payload["verdicts"][0]["verdict"] = "maybe"
    elif case == "bad-evidence":
        item["repository_evidence"] = "app.py"
    elif case == "future-schema":
        payload["review"]["schema_version"] = 2
    elif case == "blank-rationale":
        payload["verdicts"][0]["rationale"] = ""
    elif case == "blank-required-change":
        payload["verdicts"][0]["required_change"] = ""

    with pytest.raises(plan_review_state.StateError):
        plan_review_state.record_iteration(ledger_path, payload)

    assert plan_review_state.load_ledger(ledger_path)["iterations"] == []


def test_record_cli_rejects_malformed_payload(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, spec, plan = make_repo(tmp_path / "repo")
    ledger_path, _ = plan_review_state.create_ledger(repo, [spec, plan])
    iteration_path = tmp_path / "iteration.json"
    iteration_path.write_text(
        json.dumps({"schema_version": 99}),
        encoding="utf-8",
    )

    exit_code = plan_review_state.main(
        [
            "record",
            "--ledger",
            str(ledger_path),
            "--iteration",
            str(iteration_path),
        ]
    )

    assert exit_code == 2
    assert capsys.readouterr().err.startswith("plan-review state error:")
    assert plan_review_state.load_ledger(ledger_path)["iterations"] == []
