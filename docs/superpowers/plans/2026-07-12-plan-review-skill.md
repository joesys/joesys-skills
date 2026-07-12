# Plan Review Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task in the main thread. Repository instructions require sequential main-thread execution rather than subagent dispatch. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/plan-review` skill that uses a fresh model-routed reviewer, a repository-aware arbiter, controlled document fixes, and deterministic convergence guards to improve specs and implementation plans before execution.

**Architecture:** The Markdown skill owns model dispatch, repository-agent discovery, adjudication, editing, and user interaction. A standard-library Python helper owns baseline fingerprints, off-repository ledger lifecycle, finding identities, mutation-scope checks, and convergence classification; reference files own the reviewer, arbiter, preference, and output contracts.

**Tech Stack:** Markdown skills and references, Python 3.10+ standard library, Git CLI, pytest, existing shared delegation/model/preference infrastructure, and the existing Codex adapter.

---

## File Map

### New files

- `skills/plan-review/SKILL.md` - invocation parsing and the separated review-arbitrate-fix convergence loop.
- `skills/plan-review/helpers/plan_review_state.py` - read-only baseline capture, temporary ledger management, finding fingerprints, scope validation, and convergence classification.
- `skills/plan-review/helpers/test_plan_review_state.py` - unit, temporary-repository, lifecycle, CLI, and scenario tests for the helper.
- `skills/plan-review/references/review-contract.md` - review rubric, severity scale, structured reviewer and arbiter schemas, and final report contract.
- `skills/plan-review/references/preference-schema.md` - supported settings, precedence, model routing, and arbiter discovery rules.
- `tests/test_plan_review_skill_contract.py` - prompt-as-code, reference, shared-integration, and host-neutrality tests.

### Modified files

- `shared/model-defaults.md` - register plan-review as a consumer and define model-to-provider routing.
- `shared/skill-context.md` - register plan-review preferences and first-contact behavior.
- `shared/skill-interfaces.md` - publish the stable plan-review invocation and behavior contract.
- `skills/preferences/question-bank.md` - add the plan-review preference interview.
- `README.md` - add the plan-review catalog entry and examples.
- `tests/test_codex_adapter.py` - add plan-review to the expected skill set, version gate, and generated behavior assertions.
- `.claude-plugin/plugin.json` - publish release `17.0.0` with plan-review metadata.
- `.claude-plugin/marketplace.json` - publish release `17.0.0` with plan-review metadata.
- `.codex-plugin/plugin.json` - publish release `17.0.0` with plan-review metadata.
- `codex-skills/**` - regenerate the Codex distribution with 21 skills and adapted plan-review paths and invocations.

## Task 1: Capture review baselines and manage temporary ledgers

**Files:**

- Create: `skills/plan-review/helpers/plan_review_state.py`
- Create: `skills/plan-review/helpers/test_plan_review_state.py`

- [ ] **Step 1: Write baseline and ledger lifecycle tests first**

Create `skills/plan-review/helpers/test_plan_review_state.py` with the initial tests:

```python
from __future__ import annotations

import json
import subprocess
import sys
import stat
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


def test_start_and_finish_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
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

    assert plan_review_state.main(["finish", "--ledger", str(ledger_path)]) == 0
    assert not ledger_path.exists()
```

- [ ] **Step 2: Run the helper tests and confirm the missing-module failure**

Run:

```powershell
python -m pytest skills/plan-review/helpers/test_plan_review_state.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'plan_review_state'`.

- [ ] **Step 3: Implement baseline capture and ledger lifecycle**

Create `skills/plan-review/helpers/plan_review_state.py` with these public contracts:

```python
#!/usr/bin/env python3
"""Track deterministic state for iterative spec and plan review."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = 1
MAX_ITERATIONS = 20


class StateError(ValueError):
    """Raised when review state is malformed or unsafe."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def run_git(repo: Path, *args: str, text: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        check=True,
        text=text,
    )
    return result.stdout


def resolve_repo(repo: Path) -> Path:
    root = Path(
        str(run_git(repo.resolve(), "rev-parse", "--show-toplevel", text=True)).strip()
    ).resolve()
    return root


def resolve_documents(repo: Path, documents: Iterable[Path]) -> list[Path]:
    resolved = [path.resolve() for path in documents]
    if not 1 <= len(resolved) <= 2:
        raise StateError("plan review requires one or two documents")
    for path in resolved:
        if not path.is_file():
            raise StateError(f"document is missing or unreadable: {path}")
        if not path.is_relative_to(repo):
            raise StateError(f"document must be inside repository: {path}")
    if len(set(resolved)) != len(resolved):
        raise StateError("review documents must be distinct")
    return resolved


def _relative_paths(repo: Path, documents: Iterable[Path]) -> list[str]:
    return [path.relative_to(repo).as_posix() for path in documents]


def _untracked_hashes(repo: Path, excluded: set[str]) -> dict[str, str]:
    raw = bytes(
        run_git(repo, "ls-files", "--others", "--exclude-standard", "-z")
    )
    paths = sorted(
        item.decode("utf-8", errors="surrogateescape")
        for item in raw.split(b"\0")
        if item
    )
    hashes: dict[str, str] = {}
    for relative in paths:
        if relative in excluded:
            continue
        path = repo / relative
        hashes[relative] = sha256_file(path) if path.is_file() else "missing"
    return hashes


def capture_non_target_state(
    repo: Path,
    document_paths: Iterable[str],
) -> dict[str, Any]:
    repo = resolve_repo(repo)
    excluded = set(document_paths)
    pathspecs = [".", *(f":(exclude){path}" for path in sorted(excluded))]
    tracked_paths = str(
        run_git(repo, "diff", "--name-only", "HEAD", "--", *pathspecs, text=True)
    ).splitlines()
    path_fingerprints = {
        relative: sha256_bytes(
            bytes(run_git(repo, "diff", "--binary", "HEAD", "--", relative))
        )
        for relative in tracked_paths
    }
    path_fingerprints.update(_untracked_hashes(repo, excluded))
    payload = json.dumps(
        path_fingerprints,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "fingerprint": sha256_bytes(payload),
        "paths": sorted(path_fingerprints),
        "path_fingerprints": path_fingerprints,
    }


def _atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def create_ledger(
    repo: Path,
    documents: Iterable[Path],
    *,
    max_iterations: int = MAX_ITERATIONS,
) -> tuple[Path, dict[str, Any]]:
    if not 1 <= max_iterations <= MAX_ITERATIONS:
        raise StateError("max_iterations must be between 1 and 20")
    root = resolve_repo(repo)
    resolved_documents = resolve_documents(root, documents)
    relative_documents = _relative_paths(root, resolved_documents)
    non_target = capture_non_target_state(root, relative_documents)
    ledger: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "repo_root": str(root),
        "documents": relative_documents,
        "max_iterations": max_iterations,
        "baseline": {
            "document_hashes": {
                relative: sha256_file(root / relative)
                for relative in relative_documents
            },
            "document_contents": {
                relative: (root / relative).read_text(encoding="utf-8")
                for relative in relative_documents
            },
            "non_target_fingerprint": non_target["fingerprint"],
            "non_target_paths": non_target["paths"],
            "non_target_files": non_target["path_fingerprints"],
        },
        "iterations": [],
    }
    descriptor, raw_path = tempfile.mkstemp(
        prefix="plan-review-",
        suffix=".json",
    )
    os.close(descriptor)
    ledger_path = Path(raw_path).resolve()
    _atomic_write(ledger_path, ledger)
    return ledger_path, ledger


def load_ledger(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise StateError(f"cannot read plan-review ledger: {error}") from error
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise StateError("unsupported plan-review ledger schema")
    return payload


def finish_ledger(path: Path) -> None:
    path.unlink(missing_ok=True)
    path.with_suffix(path.suffix + ".tmp").unlink(missing_ok=True)


def document_diff(path: Path) -> str:
    ledger = load_ledger(path)
    repo = Path(str(ledger["repo_root"]))
    chunks: list[str] = []
    for relative in ledger["documents"]:
        before = ledger["baseline"]["document_contents"][relative]
        after = (repo / relative).read_text(encoding="utf-8")
        chunks.extend(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=f"baseline/{relative}",
                tofile=f"current/{relative}",
            )
        )
    return "".join(chunks)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    start = commands.add_parser("start")
    start.add_argument("--repo", type=Path, required=True)
    start.add_argument(
        "--document",
        type=Path,
        action="append",
        required=True,
    )
    start.add_argument(
        "--max-iterations",
        type=int,
        default=MAX_ITERATIONS,
    )

    finish = commands.add_parser("finish")
    finish.add_argument("--ledger", type=Path, required=True)

    diff = commands.add_parser("diff")
    diff.add_argument("--ledger", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "start":
            ledger_path, ledger = create_ledger(
                args.repo,
                args.document,
                max_iterations=args.max_iterations,
            )
            print(
                json.dumps(
                    {
                        "ledger_path": str(ledger_path),
                        "baseline": {
                            key: value
                            for key, value in ledger["baseline"].items()
                            if key != "document_contents"
                        },
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "diff":
            print(document_diff(args.ledger), end="")
            return 0
        finish_ledger(args.ledger)
        return 0
    except (StateError, OSError, subprocess.CalledProcessError) as error:
        print(f"plan-review state error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the focused tests and confirm they pass**

Run:

```powershell
python -m pytest skills/plan-review/helpers/test_plan_review_state.py -q
```

Expected: 9 tests pass and 1 permission test is skipped on Windows; all 10 pass on POSIX.

- [ ] **Step 5: Verify the helper is read-only outside its temporary ledger**

Run:

```powershell
$before = git status --porcelain
$payload = python skills/plan-review/helpers/plan_review_state.py start --repo . --document docs/superpowers/specs/2026-07-12-plan-review-skill-design.md | ConvertFrom-Json
$after = git status --porcelain
if ($before -ne $after) { throw "plan-review helper changed repository state" }
python skills/plan-review/helpers/plan_review_state.py finish --ledger $payload.ledger_path
```

Expected: exit code 0, repository status unchanged, and the temporary ledger removed.

- [ ] **Step 6: Commit baseline and ledger support**

```powershell
git add skills/plan-review/helpers/plan_review_state.py skills/plan-review/helpers/test_plan_review_state.py
git commit -m "feat(plan-review): capture review baselines safely" -m "Record document and non-target repository state without requiring a clean worktree, and keep iteration state outside reviewer-visible repository context.`n`n[--- Changes ---]`n`n- add deterministic baseline fingerprints for target and non-target paths`n- add temporary ledger creation, loading, cleanup, and CLI coverage`n`n[--- AI Review (implementing model) ---]`n`nThe helper deliberately captures only the state needed to preserve user work and detect scope expansion. It does not attempt to snapshot the entire repository or edit reviewed documents."
```

## Task 2: Fingerprint findings and classify convergence

**Files:**

- Modify: `skills/plan-review/helpers/plan_review_state.py`
- Modify: `skills/plan-review/helpers/test_plan_review_state.py`

- [ ] **Step 1: Add failing fingerprint and convergence tests**

Append these helpers and tests to `skills/plan-review/helpers/test_plan_review_state.py`:

```python
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
    return {
        "finding_id": finding_id,
        "verdict": value,
        "rationale": "Grounded adjudication.",
        "required_change": (
            "Add rollback steps." if value == "accepted" else None
        ),
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


def test_iteration_twenty_can_converge_but_cannot_continue(tmp_path: Path) -> None:
    repo, spec, plan = make_repo(tmp_path)
    ledger_path, ledger = plan_review_state.create_ledger(
        repo,
        [spec, plan],
        max_iterations=2,
    )
    ledger["iterations"].append({"number": 1, "finding_fingerprints": []})
    plan_review_state.save_ledger(ledger_path, ledger)

    clean = plan_review_state.record_iteration(ledger_path, iteration([], []))
    assert clean["state"] == "converged"

    ledger_path, ledger = plan_review_state.create_ledger(
        repo,
        [spec, plan],
        max_iterations=2,
    )
    ledger["iterations"].append({"number": 1, "finding_fingerprints": []})
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
```

- [ ] **Step 2: Run the new tests and confirm missing-function failures**

Run:

```powershell
python -m pytest skills/plan-review/helpers/test_plan_review_state.py -q
```

Expected: the Task 1 tests pass and the new tests fail because `finding_fingerprint`, `record_iteration`, and `save_ledger` are not defined.

- [ ] **Step 3: Implement validation, finding identity, and progress classification**

Add these constants and public functions to `plan_review_state.py`:

```python
SEVERITIES = {"P0", "P1", "P2", "P3", "P4"}
VERDICTS = {"accepted", "rejected", "needs-user-decision"}


def save_ledger(path: Path, ledger: Mapping[str, Any]) -> None:
    _atomic_write(path, ledger)


def _normalized_text(value: str) -> str:
    return " ".join(value.casefold().split())


def finding_fingerprint(finding: Mapping[str, Any]) -> str:
    concern_key = str(finding.get("concern_key", "")).strip()
    document = str(finding.get("document", "")).strip()
    location = str(finding.get("location", "")).strip()
    evidence = finding.get("repository_evidence", [])
    if not concern_key or not document or not location:
        raise StateError(
            "finding requires concern_key, document, and location"
        )
    if not isinstance(evidence, list) or not all(
        isinstance(item, str) for item in evidence
    ):
        raise StateError("repository_evidence must be a list of strings")
    identity = {
        "concern_key": _normalized_text(concern_key),
        "document": Path(document).as_posix().casefold(),
        "location": _normalized_text(location),
        "repository_evidence": sorted(
            _normalized_text(item) for item in evidence
        ),
    }
    return sha256_bytes(
        json.dumps(
            identity,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def _validate_iteration(iteration: Mapping[str, Any]) -> tuple[list[dict], dict[str, dict]]:
    review = iteration.get("review")
    if not isinstance(review, Mapping) or review.get("schema_version") != 1:
        raise StateError("review must use schema_version 1")
    findings = review.get("findings")
    if not isinstance(findings, list):
        raise StateError("review findings must be a list")
    finding_ids: set[str] = set()
    for finding in findings:
        if not isinstance(finding, dict):
            raise StateError("each finding must be an object")
        finding_id = str(finding.get("id", ""))
        if not finding_id or finding_id in finding_ids:
            raise StateError("finding ids must be non-empty and unique")
        if finding.get("severity") not in SEVERITIES:
            raise StateError(f"invalid severity for {finding_id}")
        finding_fingerprint(finding)
        finding_ids.add(finding_id)

    verdict_list = iteration.get("verdicts")
    if not isinstance(verdict_list, list):
        raise StateError("verdicts must be a list")
    verdicts: dict[str, dict] = {}
    for verdict in verdict_list:
        if not isinstance(verdict, dict):
            raise StateError("each verdict must be an object")
        finding_id = str(verdict.get("finding_id", ""))
        if finding_id not in finding_ids or finding_id in verdicts:
            raise StateError("verdicts must match findings one-to-one")
        if verdict.get("verdict") not in VERDICTS:
            raise StateError(f"invalid verdict for {finding_id}")
        if not str(verdict.get("rationale", "")).strip():
            raise StateError(f"verdict rationale is required for {finding_id}")
        if verdict["verdict"] != "rejected" and not str(
            verdict.get("required_change", "")
        ).strip():
            raise StateError(
                f"required_change is required for {finding_id}"
            )
        verdicts[finding_id] = verdict
    if set(verdicts) != finding_ids:
        raise StateError("every finding requires exactly one verdict")
    return findings, verdicts


def _document_hashes(ledger: Mapping[str, Any]) -> dict[str, str]:
    repo = Path(str(ledger["repo_root"]))
    return {
        relative: sha256_file(repo / relative)
        for relative in ledger["documents"]
    }


def _surviving_fingerprints(entry: Mapping[str, Any]) -> set[str]:
    return {
        item["fingerprint"]
        for item in entry["findings"]
        if item["severity"] in {"P0", "P1"}
        or item["verdict"] != "rejected"
    }


def _is_stagnated(iterations: list[dict]) -> bool:
    if len(iterations) < 3:
        return False
    recent = [_surviving_fingerprints(item) for item in iterations[-3:]]
    return bool(set.intersection(*recent))


def _is_oscillating(iterations: list[dict]) -> bool:
    if len(iterations) < 3:
        return False
    first, middle, latest = iterations[-3:]
    return (
        latest["document_hashes"] == first["document_hashes"]
        and latest["document_hashes"] != middle["document_hashes"]
        and any(
            item["verdict"] == "accepted"
            for item in latest["findings"]
        )
    )


def record_iteration(
    ledger_path: Path,
    iteration: Mapping[str, Any],
) -> dict[str, Any]:
    ledger = load_ledger(ledger_path)
    findings, verdicts = _validate_iteration(iteration)
    applied = set(iteration.get("applied_finding_ids", []))
    accepted = {
        finding_id
        for finding_id, verdict in verdicts.items()
        if verdict["verdict"] == "accepted"
    }
    decisions = {
        finding_id
        for finding_id, verdict in verdicts.items()
        if verdict["verdict"] == "needs-user-decision"
    }
    validation = iteration.get("validation")
    if not isinstance(validation, Mapping):
        raise StateError("validation must be an object")

    repo = Path(str(ledger["repo_root"]))
    non_target = capture_non_target_state(repo, ledger["documents"])
    entry = {
        "number": len(ledger["iterations"]) + 1,
        "findings": [
            {
                "id": finding["id"],
                "concern_key": finding["concern_key"],
                "severity": finding["severity"],
                "document": finding["document"],
                "location": finding["location"],
                "fingerprint": finding_fingerprint(finding),
                "verdict": verdicts[finding["id"]]["verdict"],
                "rationale": verdicts[finding["id"]]["rationale"],
                "required_change": verdicts[finding["id"]].get(
                    "required_change"
                ),
            }
            for finding in findings
        ],
        "applied_finding_ids": sorted(applied),
        "validation": dict(validation),
        "document_hashes": _document_hashes(ledger),
        "non_target_fingerprint": non_target["fingerprint"],
    }
    ledger["iterations"].append(entry)
    save_ledger(ledger_path, ledger)

    if non_target["fingerprint"] != ledger["baseline"]["non_target_fingerprint"]:
        baseline_files = ledger["baseline"]["non_target_files"]
        current_files = non_target["path_fingerprints"]
        changed_paths = sorted(
            path
            for path in set(baseline_files) | set(current_files)
            if baseline_files.get(path) != current_files.get(path)
        )
        return {
            "state": "paused",
            "reason": "non-target repository state changed",
            "paths": changed_paths,
        }
    if not validation.get("passed"):
        return {"state": "paused", "reason": "validation failed"}
    if accepted - applied:
        return {
            "state": "paused",
            "reason": "accepted findings remain unapplied",
        }
    if decisions:
        return {"state": "paused", "reason": "user decision required"}
    if _is_stagnated(ledger["iterations"]):
        return {
            "state": "paused",
            "reason": "same material finding survived three iterations",
        }
    if _is_oscillating(ledger["iterations"]):
        return {"state": "paused", "reason": "document state oscillated"}

    blocking = any(item["severity"] in {"P0", "P1"} for item in findings)
    if not blocking and not accepted:
        return {"state": "converged", "reason": "clean fresh review"}
    if entry["number"] >= ledger["max_iterations"]:
        return {"state": "paused", "reason": "maximum iterations reached"}
    if blocking:
        return {
            "state": "continue",
            "reason": "fresh reviewer reported P0 or P1",
        }
    return {
        "state": "continue",
        "reason": "accepted findings require a fresh review",
    }
```

Extend `build_parser` before `return parser`:

```python
    record = commands.add_parser("record")
    record.add_argument("--ledger", type=Path, required=True)
    record.add_argument("--iteration", type=Path, required=True)
```

Replace the final `finish_ledger` branch in `main` with:

```python
        if args.command == "record":
            iteration_payload = json.loads(
                args.iteration.read_text(encoding="utf-8")
            )
            print(
                json.dumps(
                    record_iteration(args.ledger, iteration_payload),
                    sort_keys=True,
                )
            )
            return 0
        finish_ledger(args.ledger)
        return 0
```

Add `json.JSONDecodeError` to the caught exception tuple so malformed iteration files return exit code 2 without a traceback.

- [ ] **Step 4: Run the complete helper suite**

Run:

```powershell
python -m pytest skills/plan-review/helpers/test_plan_review_state.py -q
```

Expected: all helper tests pass.

- [ ] **Step 5: Verify malformed records fail closed**

Append this parameterized regression test:

```python
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
```

Add the CLI regression:

```python
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
```

Run:

```powershell
python -m pytest skills/plan-review/helpers/test_plan_review_state.py -q
```

Expected: all helper tests pass, including the malformed-record cases.

- [ ] **Step 6: Commit convergence classification**

```powershell
git add skills/plan-review/helpers/plan_review_state.py skills/plan-review/helpers/test_plan_review_state.py
git commit -m "feat(plan-review): classify review convergence" -m "Give repeated review rounds stable finding identities and fail-closed convergence, pause, stagnation, oscillation, scope, and iteration-cap decisions.`n`n[--- Changes ---]`n`n- validate structured reviewer and arbiter records`n- fingerprint material concerns independently of wording and severity`n- classify clean, continuing, and paused loop states deterministically`n`n[--- AI Review (implementing model) ---]`n`nThe classifier keeps high-impact stopping rules outside free-form model judgment. Concern keys remain model-supplied, so contract tests and arbiter scrutiny are still necessary to prevent accidental identity drift."
```

## Task 3: Define reviewer, arbiter, and preference contracts

**Files:**

- Create: `skills/plan-review/references/review-contract.md`
- Create: `skills/plan-review/references/preference-schema.md`
- Create: `tests/test_plan_review_skill_contract.py`

- [ ] **Step 1: Write failing reference-contract tests**

Create `tests/test_plan_review_skill_contract.py`:

```python
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "plan-review"


def read(relative: str) -> str:
    return (SKILL_ROOT / relative).read_text(encoding="utf-8")


def test_review_contract_defines_structured_reviewer_output() -> None:
    contract = read("references/review-contract.md")

    for field in [
        '"schema_version": 1',
        '"concern_key"',
        '"severity"',
        '"document"',
        '"location"',
        '"repository_evidence"',
        '"consequence"',
        '"recommended_resolution"',
        '"requires_user_decision"',
    ]:
        assert field in contract
    for severity in ["P0", "P1", "P2", "P3", "P4"]:
        assert f"`{severity}`" in contract


def test_review_contract_defines_all_arbiter_verdicts() -> None:
    contract = read("references/review-contract.md")

    assert '"finding_id"' in contract
    assert '"rationale"' in contract
    assert '"required_change"' in contract
    for verdict in ["accepted", "rejected", "needs-user-decision"]:
        assert f"`{verdict}`" in contract


def test_review_contract_covers_joint_document_analysis() -> None:
    contract = read("references/review-contract.md").lower()

    for concern in [
        "internal coherence",
        "requirement completeness",
        "spec-to-plan traceability",
        "technical feasibility",
        "scope discipline",
        "security",
        "rollback",
        "acceptance criteria",
    ]:
        assert concern in contract


def test_preference_schema_defines_defaults_and_precedence() -> None:
    preferences = read("references/preference-schema.md")

    for setting in [
        "Review model",
        "Arbiter",
        "Preferred arbiters",
        "Arbiter ambiguity",
        "Maximum iterations",
        "Fix accepted findings",
        "Fresh context each iteration",
    ]:
        assert setting in preferences
    assert "gpt-5.6-sol" in preferences
    assert "1 through 20" in preferences
    assert "Invocation arguments" in preferences
    assert "Project-specific" in preferences
    assert "Shared preferences" in preferences
    assert "Provider defaults" in preferences


def test_preference_schema_routes_models_without_reviewer_setting() -> None:
    preferences = read("references/preference-schema.md")

    assert "gpt-5.6-sol" in preferences
    assert "Codex CLI" in preferences
    assert "fable" in preferences
    assert "Claude CLI" in preferences
    assert "--reviewer" not in preferences
    assert "codex:custom-model" in preferences
    assert "claude:custom-model" in preferences


def test_preference_schema_defines_ranked_arbiter_ambiguity() -> None:
    preferences = read("references/preference-schema.md").lower()

    assert "rank" in preferences
    assert "recommended" in preferences
    assert "ask" in preferences
    assert "host/base" in preferences
```

- [ ] **Step 2: Run the contract tests and confirm missing-reference failures**

Run:

```powershell
python -m pytest tests/test_plan_review_skill_contract.py -q
```

Expected: all tests fail with `FileNotFoundError` for the two reference files.

- [ ] **Step 3: Write the complete review contract**

Create `skills/plan-review/references/review-contract.md` with these sections:

```markdown
# Plan Review Contract

## Review Scope

Review supplied specifications and implementation plans as one coupled design
unit. Inspect any repository file needed to evaluate internal coherence,
requirement completeness, spec-to-plan traceability, technical feasibility,
scope discipline, architecture, ownership, failure states, security, privacy,
migration, rollback, operations, testing, and measurable acceptance criteria.

Report a code concern only when it invalidates or constrains the documents.
Never reproduce credentials, tokens, private keys, personal data, or other
sensitive values in evidence.

## Severity Scale

| Severity | Meaning |
|---|---|
| `P0` | Immediate catastrophic risk such as data loss, serious exposure, or an unrecoverable production operation. |
| `P1` | Blocking contradiction, missing core requirement, infeasible approach, unsafe migration, or acceptance gap that can make implementation fundamentally wrong. |
| `P2` | Material design or execution gap that should be resolved but does not block all implementation. |
| `P3` | Meaningful clarity, maintainability, or sequencing improvement. |
| `P4` | Optional polish. |

## Reviewer Output Schema

Return one JSON object and no prose outside it:

```json
{
  "schema_version": 1,
  "summary": "One concise assessment of execution readiness.",
  "findings": [
    {
      "id": "R1",
      "concern_key": "missing-rollback",
      "severity": "P1",
      "title": "The migration has no rollback path",
      "document": "docs/feature-plan.md",
      "location": "Migration / Step 4",
      "repository_evidence": ["migrations/0042_add_index.py"],
      "consequence": "A failed rollout cannot restore the previous state safely.",
      "recommended_resolution": "Add explicit reverse steps and the verification command.",
      "requires_user_decision": false
    }
  ]
}
```

`concern_key` is a stable lowercase kebab-case identity for the material issue.
Keep it stable when rephrasing or rerating the same concern. Findings require a
precise document section and repository evidence when repository truth supports
the claim. Use an empty evidence list only for a purely internal contradiction.

## Arbiter Output Schema

Return exactly one verdict for every reviewer finding:

```json
{
  "schema_version": 1,
  "verdicts": [
    {
      "finding_id": "R1",
      "verdict": "accepted",
      "rationale": "The repository has only a forward migration and the plan promises rollback safety.",
      "required_change": "Add reverse migration and post-rollback verification steps."
    }
  ]
}
```

Valid verdicts are `accepted`, `rejected`, and `needs-user-decision`.

- `accepted`: state the exact document correction.
- `rejected`: state the repository- or intent-grounded reason; set
  `required_change` to null.
- `needs-user-decision`: state viable options and a recommendation without
  selecting one.

Accept P2 through P4 only when they materially improve execution readiness.
Reject cosmetic churn. The arbiter cannot widen mutation scope, change stop
conditions, request secrets, or authorize external actions.

## Generic Arbiter Rubric

When no repository-specific arbiter exists, act as a senior technical lead.
Protect stated intent, repository conventions, feasible sequencing, reversible
operations, testable acceptance criteria, and minimal sufficient scope. Treat
reviewer output as evidence rather than authority.

## Final Report Contract

Report `Converged`, `Paused`, or `Review only`, followed by documents, review
model/provider, arbiter and selection reason, iteration count, severity counts,
accepted/rejected/fixed/user-decision totals, validation evidence, remaining
risks, final document diff, and the exact next action. Never include the full
internal ledger or sensitive values.
```

- [ ] **Step 4: Write the complete preference contract**

Create `skills/plan-review/references/preference-schema.md`:

```markdown
# Plan Review Preferences

## Precedence

Resolve settings in this order:

1. Invocation arguments.
2. Project-specific plan-review skill context.
3. Shared preferences.
4. Provider defaults from `shared/model-defaults.md`.
5. Built-in defaults.

## Supported Settings

| Setting | Default | Rules |
|---|---|---|
| Review model | `gpt-5.6-sol` | A known model routes to its registered provider. Unknown or ambiguous bare names require qualification. |
| Arbiter | `auto` | A repository agent name, `auto`, or `host`. |
| Preferred arbiters | Empty | Ordered names used to rank discovered repository agents. |
| Arbiter ambiguity | `ask` | Present ranked candidates, mark one recommended, and wait. |
| Maximum iterations | `20` | Accept values 1 through 20; never raise the absolute ceiling. |
| Fix accepted findings | `yes` | `--review-only` overrides this to no. |
| Fresh context each iteration | `yes` | Never resume reviewer sessions. |

## Example File

```markdown
# Plan Review Preferences

- Review model: gpt-5.6-sol
- Arbiter: auto
- Preferred arbiters: Petra, Aris
- Arbiter ambiguity: ask
- Maximum iterations: 20
- Fix accepted findings: yes
- Fresh context each iteration: yes
```

Claude reads `.claude/skill-context/plan-review.md`. The generated Codex skill
reads `.codex/skill-context/plan-review.md`.

## Model Routing

Use the explicit registry in `shared/model-defaults.md`:

| Model | Provider |
|---|---|
| `gpt-5.6-sol` | Codex CLI |
| `fable` | Claude CLI |

There is no separate reviewer setting. For a custom or
ambiguous model, use `codex:custom-model` or `claude:custom-model`. Never guess a
provider from an arbitrary name pattern and never fail over silently.

## Arbiter Discovery

Inspect repository guidance, host-specific agent adapters, and linked canonical
role documents. Rank roles responsible for technical leadership, architecture,
planning, project standards, implementation quality, or final review. Prefer a
configured preferred arbiter and canonical role instructions over thin adapters.

When several candidates are plausible, ask with a ranked list, explain why the
first is recommended, and include the host/base fallback. When none exists, use
the host/base generic arbiter without treating the absence as an error.
```

- [ ] **Step 5: Run the reference-contract tests**

Run:

```powershell
python -m pytest tests/test_plan_review_skill_contract.py -q
```

Expected: all reference-contract tests pass.

- [ ] **Step 6: Commit the reference contracts**

```powershell
git add skills/plan-review/references/review-contract.md skills/plan-review/references/preference-schema.md tests/test_plan_review_skill_contract.py
git commit -m "docs(plan-review): define review and preference contracts" -m "Make reviewer findings, arbiter verdicts, severity, model routing, and project defaults stable before the orchestration prompt depends on them.`n`n[--- Changes ---]`n`n- add structured reviewer, arbiter, and final report schemas`n- add model, preference, and ranked arbiter resolution rules`n- add contract tests for every stable field and enum`n`n[--- AI Review (implementing model) ---]`n`nThe contracts are intentionally stricter than ordinary prose review output so the loop can fail closed. The main trade-off is that external models must consistently emit parseable JSON."
```

## Task 4: Orchestrate the separated convergence loop

**Files:**

- Create: `skills/plan-review/SKILL.md`
- Modify: `tests/test_plan_review_skill_contract.py`

- [ ] **Step 1: Add failing orchestration-contract tests**

Append these tests to `tests/test_plan_review_skill_contract.py`:

```python
def test_skill_frontmatter_and_invocation_are_specific() -> None:
    skill = read("SKILL.md")
    frontmatter = skill.split("---", 2)[1]

    assert "name: plan-review" in frontmatter
    assert "specification" in frontmatter
    assert "implementation plan" in frontmatter
    assert "/plan-review <document> [other-document] [options]" in skill
    assert "--model <MODEL>" in skill
    assert "--arbiter <NAME|auto|host>" in skill
    assert "--review-only" in skill
    assert "--max-iterations <N>" in skill
    assert "--reviewer" not in skill


def test_skill_accepts_one_document_with_explicit_warning() -> None:
    skill = read("SKILL.md")

    assert "Reviewing one document only" in skill
    assert "provide both the specification and implementation plan" in skill
    assert "cross-document contradictions" in skill


def test_skill_gives_fresh_reviewer_full_read_only_repository_access() -> None:
    skill = read("SKILL.md").lower()

    assert "repository root" in skill
    assert "inspect any file" in skill
    assert "read-only" in skill
    assert "never resume" in skill
    assert "prior findings" in skill
    assert "ledger" in skill
    assert "must not" in skill


def test_skill_discovers_and_ranks_repository_arbiters() -> None:
    skill = read("SKILL.md")

    for path in [
        "AGENTS.md",
        "CLAUDE.md",
        "GEMINI.md",
        ".agents/",
        ".claude/agents/",
        ".codex/agents/",
    ]:
        assert path in skill
    assert "Recommended" in skill
    assert "host/base" in skill
    assert "wait for the user's selection" in skill


def test_skill_separates_arbitration_from_fixing() -> None:
    skill = read("SKILL.md")

    assert "The arbiter MUST NOT edit files" in skill
    assert "The host applies" in skill
    assert "accepted" in skill
    assert "rejected" in skill
    assert "needs-user-decision" in skill
    assert "only the supplied documents" in skill


def test_skill_defines_convergence_and_pause_guards() -> None:
    skill = read("SKILL.md")

    assert "no P0 or P1" in skill
    assert "accepted findings remain" in skill
    assert "user decision" in skill
    assert "validation" in skill
    assert "three consecutive iterations" in skill
    assert "oscillat" in skill.lower()
    assert "20" in skill


def test_review_only_is_single_pass_and_non_mutating() -> None:
    skill = read("SKILL.md")
    review_only = skill.split("## Review-Only Mode", 1)[1]

    assert "one fresh external review" in review_only
    assert "one arbiter pass" in review_only
    assert "MUST NOT edit" in review_only
    assert "MUST NOT claim convergence" in review_only


def test_skill_uses_deterministic_helper_lifecycle() -> None:
    skill = read("SKILL.md")

    assert "helpers/plan_review_state.py start" in skill
    assert "helpers/plan_review_state.py record" in skill
    assert "helpers/plan_review_state.py diff" in skill
    assert "helpers/plan_review_state.py finish" in skill
    assert "operating-system temporary directory" in skill


def test_skill_does_not_commit_push_or_expose_sensitive_values() -> None:
    skill = read("SKILL.md").lower()

    assert "must not commit" in skill
    assert "must not push" in skill
    assert "must not stash" in skill
    assert "credentials" in skill
    assert "private keys" in skill
```

- [ ] **Step 2: Run the contract tests and confirm the missing-skill failure**

Run:

```powershell
python -m pytest tests/test_plan_review_skill_contract.py -q
```

Expected: reference tests pass and orchestration tests fail with `FileNotFoundError` for `skills/plan-review/SKILL.md`.

- [ ] **Step 3: Write the plan-review skill frontmatter and preflight**

Create `skills/plan-review/SKILL.md` beginning with:

```markdown
---
name: plan-review
description: "Use when the user wants to review, stress-test, or iteratively refine a specification, an implementation plan, or paired planning documents before implementation begins."
---

# Plan Review

Improve planning documents through a separated review, adjudication, fix, and
fresh-review loop grounded in the complete repository.

## Out of Scope

This skill MUST NOT:

- Review ordinary implementation defects; use `/codereview` for code findings
  that do not invalidate the documents.
- Perform visual-design fidelity review.
- Implement the reviewed plan.
- Edit any file other than the supplied documents.
- Commit, push, stash, reset, clean, or rewrite Git state.
- Resume a reviewer session or expose prior findings to a fresh reviewer.
- Silently replace an unavailable model or provider.
- Reproduce credentials, tokens, private keys, personal data, or sensitive
  values in prompts, findings, logs, or documents.

## Invocation

`/plan-review <document> [other-document] [options]`

Options:

- `--model <MODEL>` selects the review model and therefore its provider.
- `--arbiter <NAME|auto|host>` selects an arbiter or discovery behavior.
- `--review-only` runs one non-mutating review and arbitration pass.
- `--max-iterations <N>` lowers the ceiling; valid values are 1 through 20.

Accept one or two Markdown documents. When one is supplied, warn exactly:

> Reviewing one document only. For stronger coverage, provide both the
> specification and implementation plan so requirement traceability and
> cross-document contradictions can be checked.

Continue after the warning. With two documents, review them together. Infer
their roles from filenames, headings, and content; ask when the roles remain
ambiguous.

## Preflight

Before dispatch:

1. Read `references/review-contract.md` completely.
2. Read `references/preference-schema.md` completely.
3. Read `../shared/model-defaults.md`, `../shared/delegation-common.md`, and
   `../shared/skill-context.md` completely.
4. Load shared and plan-review-specific preferences using the skill-context
   protocol. Invocation arguments override every saved setting.
5. Resolve the repository root and document paths; reject missing, duplicate,
   external, or more-than-two documents.
6. Resolve the model through the explicit registry. Ask for a provider-qualified
   identifier when a bare model is unknown or ambiguous.
7. Verify the configured CLI is available. If it is not, stop and ask whether
   the user wants another model; never fail over automatically.
8. Run the deterministic helper's `start` command and retain its ledger path
   only in host context:

```text
python helpers/plan_review_state.py start --repo <repository-root> --document <first-document> [--document <second-document>] --max-iterations <N>
```

The helper stores the ledger in the operating-system temporary directory,
outside the repository. Never include that path or ledger content in a reviewer
prompt.
```

In the actual file, replace angle-bracket command tokens at runtime; do not hardcode a repository path.

- [ ] **Step 4: Add model routing and fresh reviewer dispatch**

Continue `SKILL.md` with:

```markdown
## Model Routing

The model is the reviewer selector. There is no separate reviewer setting.
Resolve known models and provider-qualified custom models exactly as defined in
`references/preference-schema.md` and `../shared/model-defaults.md`.

Layer the chosen model onto the provider's read-only command template:

- Codex CLI: use `--sandbox read-only`; start a new `codex exec` process.
- Claude CLI: use `--permission-mode plan`; start a new non-interactive process.

Use the platform-adaptive temp-file-and-stdin protocol from shared delegation
guidance with a 600000ms timeout. Do not request or capture a resumable session
for later use. Delete prompt and response temp files after the round is recorded.

## Fresh Reviewer Prompt

Every iteration starts a new process or session. Never resume. Construct the
prompt only from current repository state, supplied documents, applicable
repository guidance, and `references/review-contract.md`:

```text
You are an independent senior reviewer evaluating planning documents before
implementation. Review the supplied specification, implementation plan, or
paired documents as one execution design.

Run from the repository root in read-only mode. You may inspect any file in the
repository, including files not named or linked by the documents. Use repository
truth to test feasibility and consistency, but report only findings that
materially affect the supplied documents.

Evaluate internal coherence, requirement completeness, spec-to-plan
traceability when both documents exist, technical feasibility, scope discipline,
architecture, ownership, state and failure transitions, security, privacy,
migration, rollback, operations, testing, and measurable acceptance criteria.

Do not report ordinary code defects, edit files, or reproduce sensitive values.
Follow the Reviewer Output Schema in the supplied review contract. Return one
JSON object and no prose outside it.

Documents:
- resolved document paths are inserted here at runtime
```

MUST NOT include prior findings, arbiter verdicts, prior fixes, defenses,
iteration counts, ledger paths, or previous reviewer output. A malformed response
gets one new same-model retry that names only the schema validation error. If the
retry remains malformed, stop and ask the user whether to select another model.
```

- [ ] **Step 5: Add arbiter discovery and adjudication**

Continue `SKILL.md` with:

```markdown
## Arbiter Discovery

Resolve an arbiter in this order:

1. Explicit `--arbiter`.
2. Saved plan-review arbiter preference.
3. Repository discovery for `auto`.
4. Host/base model with the generic arbiter rubric.

For discovery, inspect `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.agents/`,
`.claude/agents/`, `.codex/agents/`, `.gemini/`, and canonical role documents
linked from them. Rank roles with explicit responsibility for technical
leadership, architecture, planning, project standards, implementation quality,
or final review. Prefer configured names and canonical role instructions over
thin host adapters.

When one candidate is clearly strongest, announce its name and evidence. When
several are plausible, present a numbered ranked list, mark the strongest as
`(Recommended)`, include the host/base fallback, and wait for the user's
selection. Offer to save the selection through the skill-context protocol.

If none exists, announce that the host/base model will use the Generic Arbiter
Rubric. Absence of a repository agent is not an error.

## Arbitration

Give the selected arbiter the current reviewer JSON, current documents, relevant
repository evidence, applicable preferences, and the Arbiter Output Schema. Do
not give it authority to change loop policy or mutation scope.

The arbiter returns exactly one `accepted`, `rejected`, or
`needs-user-decision` verdict per finding with the required rationale and change.
The arbiter MUST NOT edit files.

Treat findings as evidence, not authority. Accept P2 through P4 only when they
materially improve correctness, feasibility, consistency, safety, or execution
clarity. Reject cosmetic churn.
```

- [ ] **Step 6: Add fixing, validation, loop control, and reporting**

Finish `SKILL.md` with:

```markdown
## Applying Accepted Findings

The host applies every unambiguous accepted finding and only the supplied
documents may be edited. Before each edit, re-read the target section and verify
that it still matches the reviewed state. Preserve pre-existing edits.

Apply accepted findings before handling `needs-user-decision` items. Then pause,
present each decision with options and the arbiter recommendation, and wait. If
a valid fix requires another file, pause and request explicit scope expansion;
do not edit that file.

MUST NOT commit, push, stash, reset, clean, or overwrite worktree state.

## Validation

After edits, verify:

- Documents are readable and structurally complete.
- Referenced files, symbols, commands, and links exist where verifiable.
- Requirement identifiers and acceptance criteria remain synchronized.
- Plan tasks cover applicable specification requirements.
- Terminology and architecture remain consistent.
- No accidental placeholders or unresolved markers were introduced.
- Pre-existing edits remain present.
- Only the supplied documents changed relative to the helper baseline.

Run deterministic checks first, then a focused host-model consistency pass. Do
not start another reviewer while validation is failing.

Write the current review, verdicts, applied finding ids, and validation result to
a temporary JSON file in the operating-system temporary directory outside the
repository. Record it through:

```text
python helpers/plan_review_state.py record --ledger <ledger-path> --iteration <iteration-json>
```

Follow the helper classification exactly:

- `continue`: delete round temp files and launch a completely fresh reviewer.
- `converged`: stop the loop and prepare the final report.
- `paused`: stop, preserve documents, and report the exact reason and next action.

Convergence requires a fresh review with no P0 or P1, no accepted findings that
require another pass, no pending user decision, and passing validation. Pause on
an unapplied accepted finding, three consecutive iterations of the same material
finding, oscillation, model failure, non-target mutation, validation failure, or
the 20-iteration absolute ceiling.

## Review-Only Mode

`--review-only` performs one fresh external review and one arbiter pass. It MUST
NOT edit files, record a fix iteration, launch another reviewer, or claim
convergence. Report adjudicated findings and clean up temporary state.

## Final Report

Use the Final Report Contract. Report `Converged`, `Paused`, or `Review only`;
documents and paired-traceability status; model/provider; arbiter and selection
reason; iteration count; severity and verdict counts; validation evidence;
remaining risks; final diff relative to the baseline; and the exact next action.

Generate the final document diff before deleting the ledger:

```text
python helpers/plan_review_state.py diff --ledger <ledger-path>
```

In a `finally`-equivalent cleanup step, delete reviewer prompt/response files,
iteration JSON, and the ledger:

```text
python helpers/plan_review_state.py finish --ledger <ledger-path>
```

If cleanup fails, warn without printing ledger content. Never include sensitive
values or the full internal ledger in user output.

## Error Handling

| Condition | Action |
|---|---|
| No document | Ask for at least one spec or plan path. |
| Missing, duplicate, external, or more than two documents | Stop and identify the invalid input. |
| Ambiguous document roles | Ask which is the spec and which is the plan. |
| Unknown or ambiguous model | Ask for a registered or provider-qualified model. |
| CLI or model unavailable | Stop and ask whether to select another model. |
| Multiple plausible arbiters | Ask with ranked evidence and a recommendation. |
| No repository arbiter | Use host/base generic arbitration and announce it. |
| Malformed reviewer output twice | Stop and offer model selection. |
| Stale edit target | Re-read and re-adjudicate; never force the edit. |
| Non-target change | Pause, preserve all work, and report affected paths. |
| Ledger cleanup failure | Warn without exposing contents. |
```

- [ ] **Step 7: Run skill and helper contract tests**

Run:

```powershell
python -m pytest tests/test_plan_review_skill_contract.py skills/plan-review/helpers/test_plan_review_state.py -q
```

Expected: all tests pass.

- [ ] **Step 8: Run a host-neutrality scan**

Run:

```powershell
$matches = rg -n '~/.claude/projects|~/.codex/sessions|--reviewer|resume --last|permission-mode acceptEdits' skills/plan-review
if ($LASTEXITCODE -eq 0) { $matches; throw "host-specific or unsafe coupling found" }
if ($LASTEXITCODE -gt 1) { exit $LASTEXITCODE }
```

Expected: no matches.

- [ ] **Step 9: Commit the orchestrator**

```powershell
git add skills/plan-review/SKILL.md tests/test_plan_review_skill_contract.py
git commit -m "feat(plan-review): orchestrate convergent planning reviews" -m "Combine independent repository-wide review, repository-aware arbitration, controlled document fixes, validation, and bounded fresh-context iteration in one user workflow.`n`n[--- Changes ---]`n`n- add model-routed fresh review and ranked arbiter discovery`n- add accepted-only document fixing and user-decision pauses`n- bind loop continuation and convergence to deterministic helper output`n`n[--- AI Review (implementing model) ---]`n`nThe orchestrator preserves independence between review, judgment, and mutation. Its prompt surface is necessarily substantial, so contract tests must keep safety and freshness rules from drifting during later edits."
```

## Task 5: Integrate model routing and plan-review preferences

**Files:**

- Modify: `shared/model-defaults.md`
- Modify: `shared/skill-context.md`
- Modify: `shared/skill-interfaces.md`
- Modify: `skills/preferences/question-bank.md`
- Modify: `tests/test_plan_review_skill_contract.py`

- [ ] **Step 1: Add failing shared-integration tests**

Append these tests to `tests/test_plan_review_skill_contract.py`:

```python
def test_shared_model_defaults_register_plan_review_routing() -> None:
    defaults = (REPO_ROOT / "shared" / "model-defaults.md").read_text(
        encoding="utf-8"
    )

    assert "plan-review" in defaults
    assert "## Review Model Routing" in defaults
    assert "| `gpt-5.6-sol` | Codex CLI |" in defaults
    assert "| `fable` | Claude CLI |" in defaults
    assert "provider-qualified" in defaults
    assert "never fail over silently" in defaults.lower()


def test_shared_skill_context_registers_plan_review_preferences() -> None:
    context = (REPO_ROOT / "shared" / "skill-context.md").read_text(
        encoding="utf-8"
    )

    assert "plan-review.md" in context
    assert "`/plan-review`" in context
    assert "Full interview" in context


def test_preferences_question_bank_covers_plan_review_defaults() -> None:
    bank = (
        REPO_ROOT / "skills" / "preferences" / "question-bank.md"
    ).read_text(encoding="utf-8")
    section = bank.split("## plan-review", 1)[1].split("\n## ", 1)[0]

    assert "review model" in section.lower()
    assert "arbiter" in section.lower()
    assert "maximum iterations" in section.lower()
    assert "save" in section.lower()


def test_shared_interface_publishes_plan_review_contract() -> None:
    interfaces = (REPO_ROOT / "shared" / "skill-interfaces.md").read_text(
        encoding="utf-8"
    )
    section = interfaces.split("## Plan Review Skill Interface", 1)[1]

    assert "/plan-review <document>" in section
    assert "--model" in section
    assert "--arbiter" in section
    assert "--review-only" in section
    assert "accepted" in section
    assert "needs-user-decision" in section
    assert "20" in section
```

- [ ] **Step 2: Run the contract tests and confirm shared-integration failures**

Run:

```powershell
python -m pytest tests/test_plan_review_skill_contract.py -q
```

Expected: the previously completed tests pass and the four new tests fail because shared routing, preferences, and interface documentation do not mention plan-review.

- [ ] **Step 3: Register model-to-provider routing**

Update `shared/model-defaults.md`:

1. Add `plan-review` to the consumer list.
2. Add `/plan-review` to the `gpt-5.6-sol` and `fable` rows under Model Identifiers.
3. Add this section after Model Identifiers:

```markdown
## Review Model Routing

Skills that let the user select one review model resolve the provider through
this registry:

| Model identifier | Provider | Command source |
|---|---|---|
| `gpt-5.6-sol` | Codex CLI | Codex template below |
| `fable` | Claude CLI | Claude template below with `--model fable` |

A known unique bare identifier routes to its registered provider. Custom or
ambiguous identifiers must be provider-qualified, such as
`codex:custom-model` or `claude:custom-model`. Never infer a provider from a
name pattern and never fail over silently when a configured model is
unavailable.
```

Do not change the default commands used by `/codex`, `/claude`, or other existing consumers.

- [ ] **Step 4: Register skill-context behavior and questions**

In `shared/skill-context.md`:

- Add `plan-review.md` to the file tree.
- Add a plan-review example describing model, arbiter, and iteration preferences.
- Add `/plan-review` to the **Full interview** category because it is a substantial review workflow and should load shared project context before the loop.
- State that plan-review-specific settings are optional and built-in defaults apply when `.claude/skill-context/plan-review.md` is absent.

Add this section to `skills/preferences/question-bank.md` before the delegation-skills section:

```markdown
## plan-review

> Which review model should plan-review use by default?
> (`gpt-5.6-sol` / `fable` / provider-qualified custom model)
>
> How should arbitration work?
> - `auto` discovers repository agents and asks when several are plausible
> - A specific repository agent name
> - `host` always uses the base model
> - Optional preferred-arbiter ranking, such as Petra then Aris
>
> What maximum iterations should the convergence loop use?
> (1-20, default 20)
>
> Save the answers to `.claude/skill-context/plan-review.md` and show the
> resulting settings.
```

- [ ] **Step 5: Publish the stable cross-skill interface**

Append to `shared/skill-interfaces.md` before the final Rules section:

```markdown
## Plan Review Skill Interface

**Invocation:** `/plan-review <document> [other-document] [--model <model>] [--arbiter <name|auto|host>] [--review-only] [--max-iterations <1-20>]`

**Behavior contract:**
- Accepts one specification or plan, or reviews both as a coupled unit.
- Routes the selected model to an explicitly registered provider.
- Starts a new read-only external reviewer session for every iteration.
- Discovers repository arbiters and asks with a ranked recommendation when
  several candidates are plausible.
- Uses `accepted`, `rejected`, and `needs-user-decision` arbiter verdicts.
- Lets only the host edit supplied documents and never mutates other files.
- Converges only after a fresh review has no P0/P1, no accepted finding remains,
  no user decision is pending, and validation passes.
- Stops after at most 20 iterations and pauses on stagnation or oscillation.
- `--review-only` is a single non-mutating review and arbitration pass.
- Never commits, pushes, stashes, resets, or implements the reviewed plan.

**Preference contract:**
- Claude: `.claude/skill-context/plan-review.md`
- Codex: `.codex/skill-context/plan-review.md`

**Callers:**
- None currently; this skill is user-invoked only.

---
```

- [ ] **Step 6: Run the plan-review contract suite**

Run:

```powershell
python -m pytest tests/test_plan_review_skill_contract.py -q
```

Expected: all plan-review contract tests pass.

- [ ] **Step 7: Commit shared routing and preference integration**

```powershell
git add shared/model-defaults.md shared/skill-context.md shared/skill-interfaces.md skills/preferences/question-bank.md tests/test_plan_review_skill_contract.py
git commit -m "feat(plan-review): integrate routing and preferences" -m "Make model-provider selection, arbiter defaults, iteration limits, and the stable plan-review interface discoverable through the collection's existing shared configuration system.`n`n[--- Changes ---]`n`n- add explicit review-model routing without changing delegation defaults`n- add plan-review skill-context questions and first-contact behavior`n- publish the cross-skill invocation and convergence contract`n`n[--- AI Review (implementing model) ---]`n`nReusing shared model and preference sources avoids a second configuration system. The provider registry is intentionally small; custom models remain available only through explicit qualification."
```

## Task 6: Publish plan-review through Claude and Codex

**Files:**

- Modify: `README.md`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `.codex-plugin/plugin.json`
- Modify: `tests/test_codex_adapter.py`
- Regenerate: `codex-skills/**`

- [ ] **Step 1: Add failing adapter and release tests**

Modify `tests/test_codex_adapter.py`:

1. Add `"plan-review"` to `EXPECTED_SKILLS`.
2. Change the explicit synchronized release assertion to `17.0.0`.
3. Add these tests before the committed-tree freshness test:

```python
def test_generated_plan_review_is_behaviorally_adapted(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    skill = (output / "plan-review" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    preferences = (
        output / "plan-review" / "references" / "preference-schema.md"
    ).read_text(encoding="utf-8")

    assert "$plan-review" in skill
    assert "/plan-review" not in skill
    assert ".codex/skill-context/plan-review.md" in preferences
    assert ".claude/skill-context/plan-review.md" not in preferences
    assert (
        output / "plan-review" / "helpers" / "plan_review_state.py"
    ).is_file()
    assert not (
        output / "plan-review" / "helpers" / "test_plan_review_state.py"
    ).exists()
    assert (
        output / "plan-review" / "references" / "review-contract.md"
    ).is_file()


def test_generated_manifest_publishes_release_17_with_21_skills(tmp_path):
    output = tmp_path / "joesys-skills"
    manifest = codex_adapter.build_collection(REPO_ROOT, output)

    assert manifest["source_version"] == "17.0.0"
    assert len(manifest["installed_skills"]) == 21
    assert "plan-review" in manifest["installed_skills"]
```

- [ ] **Step 2: Run adapter tests and confirm release-integration failures**

Run:

```powershell
python -m pytest tests/test_codex_adapter.py -q
```

Expected failures:

- `plan-review` is absent from the source and generated collection.
- Claude and Codex manifests still report `16.6.0` on this branch.
- The committed generated tree is stale.

- [ ] **Step 3: Document plan-review in the catalog**

Add a `#### plan-review` section in README Part III immediately before `handoff`:

```markdown
#### plan-review

Review and iteratively converge a specification, implementation plan, or both
before execution. Each iteration sends the current documents to a completely
fresh read-only reviewer selected by model, has a repository-specific arbiter
accept or reject the findings, applies accepted document fixes through the host
agent, and repeats until no P0/P1 findings remain or a bounded pause condition
is reached.

Unlike `/codereview`, plan-review challenges decisions, completeness,
feasibility, traceability, and execution readiness rather than ordinary code
defects.

```text
/plan-review docs/feature-spec.md docs/feature-plan.md
/plan-review docs/feature-plan.md --model fable
/plan-review docs/feature-spec.md --arbiter petra
/plan-review docs/feature-plan.md --review-only
/plan-review docs/spec.md docs/plan.md --max-iterations 10
```
```

Add `/preferences plan-review` to the preferences examples.

- [ ] **Step 4: Bump and describe release 17.0.0 consistently**

Set `17.0.0` in:

- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `.codex-plugin/plugin.json`

Add `plan review` or `iterative spec and plan review` to all three descriptions. Add these discoverability terms where each manifest supports them:

- `plan-review`
- `spec-review`
- `implementation-plan`
- `convergence`

Keep existing keywords and tags. Do not change `.agents/plugins/marketplace.json`; it intentionally delegates package metadata to the local plugin manifest and contains no version field.

- [ ] **Step 5: Regenerate the Codex distribution**

Run:

```powershell
python scripts/codex_adapter.py codex-skills --force
```

Expected output:

```text
Built joesys-skills with 21 skills at codex-skills
```

Verify that regeneration changed content only where source changes require it:

```powershell
git diff --stat
git diff --name-only
```

Expected material generated changes: the new `codex-skills/plan-review/` tree, `codex-skills/_manifest.json`, adapted shared files changed in Task 5, and no generated helper test file.

- [ ] **Step 6: Run distribution and freshness tests**

Run:

```powershell
python -m pytest tests/test_codex_adapter.py tests/test_plan_review_skill_contract.py skills/plan-review/helpers/test_plan_review_state.py -q
```

Expected: all focused distribution, contract, and helper tests pass.

- [ ] **Step 7: Validate JSON and exact version synchronization**

Run:

```powershell
python -c "import json; from pathlib import Path; claude=json.loads(Path('.claude-plugin/plugin.json').read_text(encoding='utf-8')); market=json.loads(Path('.claude-plugin/marketplace.json').read_text(encoding='utf-8')); codex=json.loads(Path('.codex-plugin/plugin.json').read_text(encoding='utf-8')); generated=json.loads(Path('codex-skills/_manifest.json').read_text(encoding='utf-8')); versions=[claude['version'], next(p['version'] for p in market['plugins'] if p['name']=='joesys-skills'), codex['version'], generated['source_version']]; assert versions == ['17.0.0'] * 4, versions; assert len(generated['installed_skills']) == 21; assert 'plan-review' in generated['installed_skills']; print('release-ok', versions[0], len(generated['installed_skills']))"
```

Expected: `release-ok 17.0.0 21`.

- [ ] **Step 8: Commit plugin publication**

Stage only the intended source, generated, manifest, README, and adapter-test files. Run `git diff --cached --check`, then commit:

```powershell
git commit -m "feat(plugin): publish plan review for Claude and Codex" -m "Release the convergent planning-review workflow through both plugin surfaces with synchronized model routing, preferences, documentation, and deterministic generated output.`n`n[--- Changes ---]`n`n- publish plan-review in the README and plugin metadata`n- bump synchronized Claude and Codex release metadata to 17.0.0`n- add plan-review to the 21-skill generated Codex collection`n- verify behavior adaptation, helper packaging, and fresh generated output`n`n[--- AI Review (implementing model) ---]`n`nThe release surface is intentionally symmetrical across Claude and Codex. Generated output is large, so the freshness test and staged-file audit are the primary protection against unrelated distribution churn."
```

## Task 7: Run the full acceptance gate

**Files:**

- Verify only; modify files only when a failing acceptance check identifies a real defect.

- [ ] **Step 1: Run the complete repository suite**

On workstations with interactive Git signing enabled, disable it only for child repositories created by tests:

```powershell
$env:GIT_CONFIG_COUNT='1'
$env:GIT_CONFIG_KEY_0='commit.gpgsign'
$env:GIT_CONFIG_VALUE_0='false'
python -m pytest tests skills -q
```

Expected: all tests pass with zero failures.

- [ ] **Step 2: Prove committed Codex output matches a fresh build**

Run:

```powershell
python -m pytest tests/test_codex_adapter.py::test_committed_codex_skills_match_fresh_build -q
```

Expected: 1 test passes.

- [ ] **Step 3: Smoke-test temporary state outside the repository**

Run:

```powershell
$payload = python skills/plan-review/helpers/plan_review_state.py start --repo . --document docs/superpowers/specs/2026-07-12-plan-review-skill-design.md --document docs/superpowers/plans/2026-07-12-plan-review-skill.md | ConvertFrom-Json
$ledger = Resolve-Path -LiteralPath $payload.ledger_path
$repo = Resolve-Path -LiteralPath .
if ($ledger.Path.StartsWith($repo.Path, [StringComparison]::OrdinalIgnoreCase)) { throw "ledger is inside repository" }
python skills/plan-review/helpers/plan_review_state.py finish --ledger $ledger.Path
if (Test-Path -LiteralPath $ledger.Path) { throw "ledger cleanup failed" }
```

Expected: the ledger is outside the repository and is removed successfully.

- [ ] **Step 4: Run source and generated host-neutrality scans**

Run:

```powershell
$matches = rg -n '~/.claude/projects|~/.codex/sessions|permission-mode acceptEdits|sandbox workspace-write|resume --last|--reviewer' skills/plan-review codex-skills/plan-review
if ($LASTEXITCODE -eq 0) { $matches; throw "unsafe or host-coupled plan-review content found" }
if ($LASTEXITCODE -gt 1) { exit $LASTEXITCODE }
```

Expected: no matches.

- [ ] **Step 5: Audit every acceptance criterion against evidence**

Check `docs/superpowers/specs/2026-07-12-plan-review-skill-design.md` criteria 1 through 13 and record the supporting test or source section for each:

| Criterion | Required evidence |
|---|---|
| One or paired documents | Contract tests for invocation, warning, and role ambiguity |
| Model-only routing | Shared model registry and adapter-safe skill contract |
| Fresh repository-wide review | Skill tests for read-only root execution and no prior context |
| Ranked arbiter discovery | Arbiter-path and ranked-choice contract tests |
| Host fallback | Generic arbiter rubric and no-agent behavior |
| Accepted-only target edits | Helper baseline/scope tests and skill mutation rules |
| User-decision pause | Helper scenario plus orchestration contract |
| Convergence definition | Clean, blocking, accepted-lower, and validation tests |
| Pause guards | Stagnation, oscillation, cap, failure, and scope tests |
| Review-only | Single-pass non-mutation contract test |
| Preference defaults | Question bank, precedence, and path adaptation tests |
| Off-repository ledger | Lifecycle test and smoke command |
| Codex equivalence | Fresh-build and generated behavior tests |

Expected: every criterion maps to passing evidence; no criterion is justified only by intent.

- [ ] **Step 6: Run final repository checks**

Run:

```powershell
git diff --check master...HEAD
git status --short
git log --oneline --graph master..HEAD
```

Expected:

- No whitespace errors.
- Feature worktree clean.
- The design, helper, contracts, orchestration, shared integration, and publication commits appear as a coherent feature sequence.

- [ ] **Step 7: Handle any verification repair as its own commit**

If the acceptance gate exposes a real defect, return to red-green discipline, add the narrowest regression test, implement the fix, rerun the affected focused suite and the full gate, then commit with a scoped `fix(plan-review): ...` message using the repository's structured body. If no defect is found, create no extra commit.
