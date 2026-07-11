# Handoff Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task in the main thread. Repository instructions require sequential main-thread execution rather than subagent dispatch. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a host-neutral `/handoff` skill that writes resumable Markdown checkpoints, validates live repository drift deterministically, and ships as a synchronized Claude and Codex plugin feature.

**Architecture:** The skill remains a Markdown orchestrator responsible for context synthesis, audience shaping, target bootstrap, safety, and user interaction. A standard-library Python helper owns Git snapshot capture, file fingerprints, project identity, schema extraction, and conservative `exact`/`advanced`/`drifted`/`unverifiable` classification so automatic continuation never depends on free-form model judgment alone.

**Tech Stack:** Markdown skills and references, Python 3.10+ standard library, Git CLI, pytest, the existing Codex adapter, JSON embedded as an inline YAML frontmatter value.

---

## File Map

### New files

- `skills/handoff/SKILL.md` - invocation parsing, creation and resume orchestration, audience and target handling, privacy rules, error handling, and user-facing output.
- `skills/handoff/helpers/handoff_state.py` - read-only repository snapshot and drift-classification CLI.
- `skills/handoff/helpers/test_handoff_state.py` - unit and temporary-repository tests for the helper.
- `skills/handoff/references/artifact-schema.md` - schema version 1, canonical sections, frontmatter contract, and detail modes.
- `skills/handoff/references/audience-target-profiles.md` - controlled audience and runtime-target differences.
- `tests/test_handoff_skill_contract.py` - prompt-as-code contract tests for the skill and references.
- `.github/workflows/test.yml` - Windows and Ubuntu verification for the complete intended suite.

### Modified files

- `shared/skill-interfaces.md` - stable invocation, artifact, and resume contract.
- `README.md` - catalog entry, commands, and behavior summary.
- `tests/test_codex_adapter.py` - expected-skill set, generated handoff assertions, and complete version synchronization.
- `.claude-plugin/plugin.json` - version `16.6.0`, description, and keywords.
- `.claude-plugin/marketplace.json` - version `16.6.0`, description, and tags.
- `.codex-plugin/plugin.json` - version `16.6.0`, description, and interface summary.
- `codex-skills/**` - regenerated Codex distribution, including `handoff` without helper tests.

## Task 1: Capture deterministic repository snapshots

**Files:**

- Create: `skills/handoff/helpers/handoff_state.py`
- Create: `skills/handoff/helpers/test_handoff_state.py`

- [ ] **Step 1: Write snapshot tests first**

Create `skills/handoff/helpers/test_handoff_state.py` with repository helpers and the initial capture assertions:

```python
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import handoff_state


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


def make_repo(tmp_path: Path, *, remote: str | None = None) -> Path:
    git(tmp_path, "init")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test User")
    (tmp_path / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    git(tmp_path, "add", "app.py")
    git(tmp_path, "commit", "-m", "initial")
    if remote:
        git(tmp_path, "remote", "add", "origin", remote)
    return tmp_path


def test_capture_clean_git_snapshot(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, remote="git@github.com:joesys/example.git")

    snapshot = handoff_state.capture_snapshot(repo, ["app.py"])

    assert snapshot["snapshot_version"] == 1
    assert snapshot["kind"] == "git"
    assert snapshot["project_identity"] == "github.com/joesys/example"
    assert snapshot["root_name"] == tmp_path.name
    assert snapshot["branch"] in {"main", "master"}
    assert len(snapshot["head"]) == 40
    assert snapshot["status"] == []
    assert snapshot["dirty_patch_sha256"] == handoff_state.EMPTY_SHA256
    assert snapshot["relevant_files"]["app.py"]["exists"] is True


def test_capture_dirty_and_untracked_files(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    (repo / "notes.txt").write_text("next step\n", encoding="utf-8")

    snapshot = handoff_state.capture_snapshot(repo, ["app.py", "notes.txt"])

    assert {item["path"] for item in snapshot["status"]} == {
        "app.py",
        "notes.txt",
    }
    assert snapshot["dirty_patch_sha256"] != handoff_state.EMPTY_SHA256
    assert snapshot["relevant_files"]["app.py"]["sha256"]
    assert snapshot["relevant_files"]["notes.txt"]["tracked"] is False


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("git@github.com:Owner/Repo.git", "github.com/Owner/Repo"),
        ("https://github.com/Owner/Repo.git", "github.com/Owner/Repo"),
        ("ssh://git@github.com/Owner/Repo.git", "github.com/Owner/Repo"),
    ],
)
def test_normalize_remote_url(raw: str, expected: str) -> None:
    assert handoff_state.normalize_remote_url(raw) == expected


def test_sensitive_path_detection() -> None:
    assert handoff_state.is_sensitive_path(".env") is True
    assert handoff_state.is_sensitive_path(".env.production") is True
    assert handoff_state.is_sensitive_path("config/production.pem") is True
    assert handoff_state.is_sensitive_path("src/config.py") is False


def test_snapshot_cli_outputs_json(tmp_path: Path, capsys) -> None:
    repo = make_repo(tmp_path)

    exit_code = handoff_state.main(
        ["snapshot", "--repo", str(repo), "--relevant", "app.py"]
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["kind"] == "git"
```

- [ ] **Step 2: Run the focused tests and confirm the import failure**

Run:

```powershell
python -m pytest skills/handoff/helpers/test_handoff_state.py -q
```

Expected: collection fails with `ModuleNotFoundError: No module named 'handoff_state'`.

- [ ] **Step 3: Implement snapshot capture and the `snapshot` CLI**

Create `skills/handoff/helpers/handoff_state.py` with these public functions and data contract:

```python
#!/usr/bin/env python3
"""Capture and compare read-only repository state for handoff artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


SNAPSHOT_VERSION = 1
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    "credentials.json",
    "secrets.json",
    "id_rsa",
    "id_ed25519",
}
SENSITIVE_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}


class GitError(RuntimeError):
    """Raised when required Git state cannot be read."""


def run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitError(message or f"git {' '.join(args)} failed")
    return result


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_remote_url(raw: str) -> str:
    value = raw.strip().replace("\\", "/")
    scp_match = re.fullmatch(r"(?:[^@]+@)?([^:]+):(.+)", value)
    if scp_match and "://" not in value:
        host, path = scp_match.groups()
    else:
        parsed = urlparse(value if "://" in value else f"ssh://{value}")
        host = parsed.hostname or ""
        path = parsed.path.lstrip("/")
    path = path.removesuffix(".git").rstrip("/")
    return f"{host.lower()}/{path}" if host and path else value.removesuffix(".git")


def is_sensitive_path(value: str) -> bool:
    path = Path(value)
    lowered = {part.lower() for part in path.parts}
    return (
        path.name.lower() in SENSITIVE_NAMES
        or path.name.lower().startswith(".env.")
        or path.suffix.lower() in SENSITIVE_SUFFIXES
        or bool(lowered & {"secrets", "credentials", ".ssh"})
    )


def parse_porcelain_z(raw: bytes) -> list[dict[str, str]]:
    tokens = raw.decode("utf-8", errors="surrogateescape").split("\0")
    entries: list[dict[str, str]] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if not token:
            continue
        status = token[:2]
        path = token[3:]
        entry = {"status": status, "path": path.replace("\\", "/")}
        if "R" in status or "C" in status:
            if index < len(tokens) and tokens[index]:
                entry["original_path"] = tokens[index].replace("\\", "/")
                index += 1
        entries.append(entry)
    return sorted(entries, key=lambda item: item["path"])


def git_root(repo: Path) -> Path | None:
    result = run_git(repo, "rev-parse", "--show-toplevel", check=False)
    if result.returncode != 0:
        return None
    return Path(result.stdout.decode().strip()).resolve()


def project_identity(root: Path) -> tuple[str, str | None]:
    remote = run_git(root, "config", "--get", "remote.origin.url", check=False)
    raw_remote = remote.stdout.decode().strip() if remote.returncode == 0 else ""
    normalized = normalize_remote_url(raw_remote) if raw_remote else None
    return normalized or f"local:{root.name}", normalized


def file_record(root: Path, relative: str, tracked_paths: set[str]) -> dict[str, object]:
    normalized = relative.replace("\\", "/")
    path = root / normalized
    if not path.is_file():
        return {"exists": False, "tracked": normalized in tracked_paths, "sha256": None}
    return {
        "exists": True,
        "tracked": normalized in tracked_paths,
        "sha256": sha256_file(path),
        "sensitive": is_sensitive_path(normalized),
    }


def capture_snapshot(repo: Path, relevant_paths: list[str] | None = None) -> dict[str, object]:
    requested_root = repo.resolve()
    root = git_root(requested_root)
    relevant = sorted({path.replace("\\", "/") for path in relevant_paths or []})
    if root is None:
        return {
            "snapshot_version": SNAPSHOT_VERSION,
            "kind": "non_git",
            "project_identity": f"local:{requested_root.name}",
            "root_name": requested_root.name,
            "relevant_files": {
                path: file_record(requested_root, path, set()) for path in relevant
            },
        }

    identity, remote = project_identity(root)
    branch_result = run_git(root, "branch", "--show-current", check=False)
    head_result = run_git(root, "rev-parse", "HEAD", check=False)
    status = parse_porcelain_z(
        run_git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").stdout
    )
    tracked_raw = run_git(root, "ls-files", "-z").stdout.decode(
        "utf-8", errors="surrogateescape"
    )
    tracked = {item for item in tracked_raw.split("\0") if item}
    patch = run_git(root, "diff", "--binary", "HEAD", "--", ".", check=False).stdout
    return {
        "snapshot_version": SNAPSHOT_VERSION,
        "kind": "git",
        "project_identity": identity,
        "remote": remote,
        "root_name": root.name,
        "branch": branch_result.stdout.decode().strip() or None,
        "head": head_result.stdout.decode().strip() or None,
        "status": status,
        "dirty_patch_sha256": sha256_bytes(patch),
        "relevant_files": {
            path: file_record(root, path, tracked) for path in relevant
        },
        "sensitive_paths": sorted(
            item["path"] for item in status if is_sensitive_path(item["path"])
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    snapshot = subparsers.add_parser("snapshot", help="Capture repository state")
    snapshot.add_argument("--repo", type=Path, default=Path("."))
    snapshot.add_argument("--relevant", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "snapshot":
        print(json.dumps(capture_snapshot(args.repo, args.relevant), sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run snapshot tests and verify they pass**

Run:

```powershell
python -m pytest skills/handoff/helpers/test_handoff_state.py -q
```

Expected: all snapshot, remote-normalization, sensitive-path, and CLI tests pass.

- [ ] **Step 5: Verify the helper is read-only**

Run:

```powershell
$before = git status --porcelain=v1
python skills/handoff/helpers/handoff_state.py snapshot --repo . --relevant README.md | Out-Null
$after = git status --porcelain=v1
if ($before -ne $after) { throw 'handoff_state.py modified the worktree' }
```

Expected: exit 0 and no worktree-state difference.

- [ ] **Step 6: Commit snapshot capture**

Stage only the helper and its tests, then commit with the repository's structured commit body:

```powershell
git add skills/handoff/helpers/handoff_state.py skills/handoff/helpers/test_handoff_state.py
git commit
```

Subject: `feat(handoff): capture deterministic repository state`

## Task 2: Classify resume drift conservatively

**Files:**

- Modify: `skills/handoff/helpers/handoff_state.py`
- Modify: `skills/handoff/helpers/test_handoff_state.py`

- [ ] **Step 1: Add failing drift-classification tests**

Append tests covering the four states and frontmatter extraction:

```python
def write_handoff(path: Path, snapshot: dict[str, object]) -> None:
    compact = json.dumps(snapshot, separators=(",", ":"), sort_keys=True)
    path.write_text(
        "---\n"
        "schema_version: 1\n"
        f"repository_snapshot: {compact}\n"
        "---\n\n"
        "# Checkpoint\n",
        encoding="utf-8",
    )


def test_extract_snapshot_from_handoff(tmp_path: Path) -> None:
    snapshot = {"snapshot_version": 1, "kind": "non_git"}
    artifact = tmp_path / "handoff.md"
    write_handoff(artifact, snapshot)

    assert handoff_state.extract_snapshot(artifact) == snapshot


def test_extract_snapshot_rejects_unterminated_frontmatter(tmp_path: Path) -> None:
    artifact = tmp_path / "broken.md"
    artifact.write_text(
        "---\nschema_version: 1\nrepository_snapshot: {}\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not terminated"):
        handoff_state.extract_snapshot(artifact)


def test_extract_snapshot_rejects_newer_snapshot_version(tmp_path: Path) -> None:
    artifact = tmp_path / "future.md"
    write_handoff(artifact, {"snapshot_version": 2, "kind": "git"})

    with pytest.raises(ValueError, match="unsupported repository snapshot version"):
        handoff_state.extract_snapshot(artifact)


def test_compare_exact_state(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    recorded = handoff_state.capture_snapshot(repo, ["app.py"])

    comparison = handoff_state.compare_snapshot(repo, recorded)

    assert comparison["classification"] == "exact"
    assert comparison["reasons"] == []


def test_compare_advanced_state_for_unrelated_commit(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    recorded = handoff_state.capture_snapshot(repo, ["app.py"])
    (repo / "unrelated.txt").write_text("new\n", encoding="utf-8")
    git(repo, "add", "unrelated.txt")
    git(repo, "commit", "-m", "advance unrelated file")

    comparison = handoff_state.compare_snapshot(repo, recorded)

    assert comparison["classification"] == "advanced"


def test_compare_drifted_when_relevant_file_changes(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    recorded = handoff_state.capture_snapshot(repo, ["app.py"])
    (repo / "app.py").write_text("VALUE = 99\n", encoding="utf-8")

    comparison = handoff_state.compare_snapshot(repo, recorded)

    assert comparison["classification"] == "drifted"
    assert any("app.py" in reason for reason in comparison["reasons"])


def test_compare_drifted_when_relevant_file_is_renamed(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    recorded = handoff_state.capture_snapshot(repo, ["app.py"])
    git(repo, "mv", "app.py", "renamed.py")

    comparison = handoff_state.compare_snapshot(repo, recorded)

    assert comparison["classification"] == "drifted"
    assert any("disappeared: app.py" in reason for reason in comparison["reasons"])
    rename = next(item for item in comparison["current"]["status"] if "R" in item["status"])
    assert rename["path"] == "renamed.py"
    assert rename["original_path"] == "app.py"


def test_compare_drifted_after_branch_divergence(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    recorded = handoff_state.capture_snapshot(repo, ["app.py"])
    git(repo, "checkout", "-b", "other-work")

    comparison = handoff_state.compare_snapshot(repo, recorded)

    assert comparison["classification"] == "drifted"
    assert any("branch" in reason.lower() for reason in comparison["reasons"])


def test_compare_accepts_different_clone_with_same_remote(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    source = make_repo(source, remote="git@github.com:joesys/example.git")
    recorded = handoff_state.capture_snapshot(source, ["app.py"])

    clone = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", str(source), str(clone)],
        capture_output=True,
        text=True,
        check=True,
    )
    git(clone, "remote", "set-url", "origin", "https://github.com/joesys/example.git")

    comparison = handoff_state.compare_snapshot(clone, recorded)

    assert comparison["classification"] == "exact"


def test_compare_rejects_different_project_identity(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, remote="git@github.com:joesys/example.git")
    recorded = handoff_state.capture_snapshot(repo, ["app.py"])
    git(repo, "remote", "set-url", "origin", "git@github.com:joesys/other.git")

    comparison = handoff_state.compare_snapshot(repo, recorded)

    assert comparison["classification"] == "drifted"
    assert "project identity differs" in comparison["reasons"]


def test_compare_non_git_is_unverifiable(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text("one\n", encoding="utf-8")
    recorded = handoff_state.capture_snapshot(tmp_path, ["notes.md"])

    comparison = handoff_state.compare_snapshot(tmp_path, recorded)

    assert comparison["classification"] == "unverifiable"


def test_compare_cli_reads_handoff(tmp_path: Path, capsys) -> None:
    repo = make_repo(tmp_path)
    artifact = tmp_path / "checkpoint.md"
    write_handoff(artifact, handoff_state.capture_snapshot(repo, ["app.py"]))

    exit_code = handoff_state.main(
        ["compare", "--repo", str(repo), "--handoff", str(artifact)]
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["classification"] == "exact"
```

- [ ] **Step 2: Run the new tests and confirm missing-function failures**

Run:

```powershell
python -m pytest skills/handoff/helpers/test_handoff_state.py -q
```

Expected: failures name `extract_snapshot`, `compare_snapshot`, or the missing `compare` subcommand.

- [ ] **Step 3: Implement frontmatter extraction and drift classification**

Add these functions to `handoff_state.py`:

```python
def extract_snapshot(handoff: Path) -> dict[str, object]:
    text = handoff.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("handoff must start with YAML frontmatter")
    terminator = text.find("\n---\n", 4)
    if terminator == -1:
        raise ValueError("handoff frontmatter is not terminated")
    frontmatter = text[4:terminator]
    for line in frontmatter.splitlines():
        if line.startswith("repository_snapshot:"):
            value = line.split(":", 1)[1].strip()
            snapshot = json.loads(value)
            if snapshot.get("snapshot_version") != SNAPSHOT_VERSION:
                raise ValueError(
                    f"unsupported repository snapshot version: "
                    f"{snapshot.get('snapshot_version')}"
                )
            return snapshot
    raise ValueError("handoff has no repository_snapshot field")


def is_ancestor(repo: Path, older: str, newer: str) -> bool:
    result = run_git(repo, "merge-base", "--is-ancestor", older, newer, check=False)
    return result.returncode == 0


def relevant_file_changes(
    recorded: dict[str, object], current: dict[str, object]
) -> list[str]:
    reasons: list[str] = []
    recorded_files = recorded.get("relevant_files", {})
    current_files = current.get("relevant_files", {})
    for path, old_record in recorded_files.items():
        new_record = current_files.get(path)
        if new_record is None:
            reasons.append(f"relevant path is no longer recorded: {path}")
        elif old_record.get("exists") and not new_record.get("exists"):
            reasons.append(f"relevant file disappeared: {path}")
        elif old_record.get("sha256") != new_record.get("sha256"):
            reasons.append(f"relevant file changed: {path}")
    return reasons


def compare_snapshot(repo: Path, recorded: dict[str, object]) -> dict[str, object]:
    relevant = list(recorded.get("relevant_files", {}).keys())
    current = capture_snapshot(repo, relevant)
    reasons: list[str] = []

    if recorded.get("kind") != "git" or current.get("kind") != "git":
        reasons.extend(relevant_file_changes(recorded, current))
        return {
            "classification": "unverifiable",
            "reasons": reasons or ["Git metadata is unavailable"],
            "recorded": recorded,
            "current": current,
        }

    if recorded.get("project_identity") != current.get("project_identity"):
        reasons.append("project identity differs")
    if recorded.get("branch") != current.get("branch"):
        reasons.append(
            f"branch differs: {recorded.get('branch')} -> {current.get('branch')}"
        )
    reasons.extend(relevant_file_changes(recorded, current))
    if recorded.get("dirty_patch_sha256") != current.get("dirty_patch_sha256"):
        reasons.append("working-tree patch fingerprint differs")

    recorded_head = recorded.get("head")
    current_head = current.get("head")
    if reasons:
        classification = "drifted"
    elif recorded_head == current_head:
        classification = "exact"
    elif recorded_head and current_head and is_ancestor(repo, recorded_head, current_head):
        classification = "advanced"
    else:
        classification = "drifted"
        reasons.append("recorded HEAD is not an ancestor of current HEAD")

    return {
        "classification": classification,
        "reasons": reasons,
        "recorded": recorded,
        "current": current,
    }
```

Extend `build_parser()` and `main()`:

```python
compare = subparsers.add_parser("compare", help="Compare a handoff with live state")
compare.add_argument("--repo", type=Path, default=Path("."))
compare.add_argument("--handoff", type=Path, required=True)
```

```python
if args.command == "compare":
    recorded = extract_snapshot(args.handoff)
    print(json.dumps(compare_snapshot(args.repo, recorded), sort_keys=True))
    return 0
```

Replace `main()` with an exact error boundary so expected input failures return JSON on stderr rather than a traceback:

```python
def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        if args.command == "snapshot":
            payload = capture_snapshot(args.repo, args.relevant)
        elif args.command == "compare":
            payload = compare_snapshot(args.repo, extract_snapshot(args.handoff))
        else:
            return 2
        print(json.dumps(payload, sort_keys=True))
        return 0
    except (GitError, OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
```

- [ ] **Step 4: Run helper tests and verify all classifications pass**

Run:

```powershell
python -m pytest skills/handoff/helpers/test_handoff_state.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Add the dirty-patch compatibility regression test**

Add a test proving an unrelated commit is not `advanced` when the dirty patch changed after capture:

```python
def test_compare_drifted_when_dirty_patch_changes_during_advance(tmp_path: Path) -> None:
    repo = make_repo(tmp_path)
    (repo / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
    recorded = handoff_state.capture_snapshot(repo, ["app.py"])
    (repo / "unrelated.txt").write_text("new\n", encoding="utf-8")
    git(repo, "add", "unrelated.txt")
    git(repo, "commit", "-m", "advance")
    (repo / "app.py").write_text("VALUE = 3\n", encoding="utf-8")

    comparison = handoff_state.compare_snapshot(repo, recorded)

    assert comparison["classification"] == "drifted"
```

Run the focused suite again and expect all tests to pass.

- [ ] **Step 6: Commit drift comparison**

```powershell
git add skills/handoff/helpers/handoff_state.py skills/handoff/helpers/test_handoff_state.py
git commit
```

Subject: `feat(handoff): classify repository drift on resume`

## Task 3: Define and test the handoff artifact contract

**Files:**

- Create: `tests/test_handoff_skill_contract.py`
- Create: `skills/handoff/references/artifact-schema.md`
- Create: `skills/handoff/references/audience-target-profiles.md`

- [ ] **Step 1: Write failing prompt-contract tests**

Create `tests/test_handoff_skill_contract.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "handoff"


def read(relative: str) -> str:
    return (SKILL_ROOT / relative).read_text(encoding="utf-8")


def test_handoff_references_exist() -> None:
    assert (SKILL_ROOT / "references" / "artifact-schema.md").is_file()
    assert (SKILL_ROOT / "references" / "audience-target-profiles.md").is_file()
    assert (SKILL_ROOT / "helpers" / "handoff_state.py").is_file()


def test_schema_defines_required_sections() -> None:
    schema = read("references/artifact-schema.md")
    for heading in [
        "Resume Directive",
        "Objective and Success Criteria",
        "Current State",
        "Decisions and Rationale",
        "Constraints and Guardrails",
        "Working Set",
        "Repository State",
        "Verification Evidence",
        "Blockers and Uncertainties",
        "Next Actions",
        "Audience Notes",
        "Target Bootstrap",
    ]:
        assert heading in schema
    assert "schema_version: 1" in schema
    assert "repository_snapshot:" in schema


def test_schema_defines_all_detail_modes() -> None:
    schema = read("references/artifact-schema.md")
    assert "operational" in schema
    assert "--full" in schema
    assert "--compact" in schema
    assert "--include-diff" in schema


def test_profiles_separate_audience_from_target() -> None:
    profiles = read("references/audience-target-profiles.md")
    for audience in ["self", "agent", "human"]:
        assert f"`{audience}`" in profiles
    for target in ["auto", "claude", "codex", "gemini", "generic"]:
        assert f"`{target}`" in profiles
    assert "authority" in profiles.lower()
    assert "report-back" in profiles.lower()
    assert "review" in profiles.lower()
```

- [ ] **Step 2: Run the contract tests and confirm missing-reference failures**

Run:

```powershell
python -m pytest tests/test_handoff_skill_contract.py -q
```

Expected: failures report the two missing reference files.

- [ ] **Step 3: Write `artifact-schema.md`**

Define:

- YAML metadata fields: `schema_version`, `created_at`, `audience`, `detail`, `project`, `source_host`, `target_host`, `branch`, `head`, `working_tree`, and compact inline JSON `repository_snapshot`.
- The twelve required Markdown sections in their fixed order.
- Operational, full, and compact requirements.
- Unknown-value language: `Unknown` and `Not established`.
- Diff Appendix placement and secret omission.
- Filename and collision rules.
- One complete operational example containing representative but non-sensitive values.

The example frontmatter must include this parseable snapshot form:

```yaml
repository_snapshot: {"branch":"master","dirty_patch_sha256":"...","head":"...","kind":"git","project_identity":"github.com/joesys/example","relevant_files":{},"snapshot_version":1,"status":[]}
```

- [ ] **Step 4: Write `audience-target-profiles.md`**

Define two independent tables:

```markdown
| Audience | Assumptions | Required emphasis |
|---|---|---|
| `self` | Same operator and project | Operational continuity and exact next action |
| `agent` | No hidden prior context | Authority, mutation scope, inputs, deliverable, completion criteria, report-back format |
| `human` | Human reader | Rationale, ownership, review points, and judgment calls |
```

```markdown
| Target | Bootstrap-only differences |
|---|---|
| `auto` | Detect current host; fall back to generic |
| `claude` | Claude Code terminology and applicable CLAUDE.md guidance |
| `codex` | Codex skill terminology, applicable AGENTS.md, active sandbox and approval policy |
| `gemini` | Gemini terminology and applicable GEMINI.md guidance |
| `generic` | No client-specific commands, paths, tools, or capabilities |
```

State explicitly that target profiles may modify only **Target Bootstrap**, invocation examples, and `source_host`/`target_host` metadata; they may not fork the canonical body schema.

- [ ] **Step 5: Run the contract tests**

```powershell
python -m pytest tests/test_handoff_skill_contract.py -q
```

Expected: all reference-contract tests pass.

- [ ] **Step 6: Commit the artifact contract**

```powershell
git add tests/test_handoff_skill_contract.py skills/handoff/references
git commit
```

Subject: `feat(handoff): define checkpoint artifact contract`

## Task 4: Implement the handoff orchestration skill

**Files:**

- Create: `skills/handoff/SKILL.md`
- Modify: `tests/test_handoff_skill_contract.py`

- [ ] **Step 1: Extend contract tests for invocation and behavior**

Append:

```python
def skill_text() -> str:
    return read("SKILL.md")


def test_skill_frontmatter_and_invocations() -> None:
    skill = skill_text()
    assert skill.startswith("---\nname: handoff\n")
    assert "description:" in skill.split("---", 2)[1]
    for invocation in [
        "/handoff",
        "--full",
        "--compact",
        "--interactive",
        "--for self|agent|human",
        "--target auto|claude|codex|gemini|generic",
        "--include-diff",
        "--output <path>",
        "/handoff resume",
    ]:
        assert invocation in skill


def test_skill_requires_deterministic_snapshot_and_compare() -> None:
    skill = skill_text()
    assert "handoff_state.py snapshot" in skill
    assert "handoff_state.py compare" in skill
    for state in ["exact", "advanced", "drifted", "unverifiable"]:
        assert f"`{state}`" in skill
    assert "continue automatically" in skill.lower()
    assert "must not continue" in skill.lower()
    assert "newest valid handoff" in skill.lower()
    assert "project identity" in skill.lower()


def test_skill_has_privacy_and_evidence_guards() -> None:
    skill = skill_text().lower()
    for phrase in [
        "raw conversation transcripts",
        "environment variables",
        "credentials",
        "shell history",
        "never invent",
        "executed evidence",
        "secret-bearing",
    ]:
        assert phrase in skill


def test_skill_preserves_files_and_avoids_sibling_dispatch() -> None:
    skill = skill_text().lower()
    assert "temporary file" in skill
    assert "rename" in skill
    assert "never overwrite" in skill
    assert "must not invoke" in skill
    for sibling in ["/commit", "/devlog", "/retrospective"]:
        assert sibling in skill


def test_skill_does_not_mine_host_transcript_paths() -> None:
    skill = skill_text()
    assert "~/.claude/projects" not in skill
    assert "~/.codex/sessions" not in skill
    assert "~/.gemini/tmp" not in skill
```

- [ ] **Step 2: Run tests and verify `SKILL.md` is missing**

```powershell
python -m pytest tests/test_handoff_skill_contract.py -q
```

Expected: tests that read `SKILL.md` fail with `FileNotFoundError`.

- [ ] **Step 3: Write `skills/handoff/SKILL.md`**

Use this exact top-level structure:

```markdown
---
name: handoff
description: "Use when the user invokes /handoff to create a durable checkpoint for resuming work in a fresh session, transferring work to another agent or human, or safely continuing from a saved handoff."
---

# Handoff Skill

## Out of Scope
## Reference Files
## Invocation
## Phase 0: Parse and Detect
## Phase 1: Gather Current Truth
## Phase 2: Capture Repository Snapshot
## Phase 3: Synthesize and Validate Artifact
## Phase 4: Save and Report
## Resume Flow
## Drift Handling
## Safety and Privacy
## Error Handling
```

The phase contract must say:

1. Parse `--full`, `--compact`, `--interactive`, `--for`, `--target`, `--include-diff`, `--output`, and `resume`; reject incompatible detail flags.
2. Use current conversation context directly and inspect live repository state. Do not read raw host transcript databases.
3. Resolve the helper to an absolute plugin path before execution, using `python3` when present and `python` on Windows.
4. Run `handoff_state.py snapshot --repo <root>` after extracting the working-set paths, adding one `--relevant <path>` per repository-relative path.
5. Embed the compact JSON output as `repository_snapshot:` in frontmatter.
6. Apply the canonical schema from `artifact-schema.md`, then the audience and target rules from `audience-target-profiles.md`.
7. Never invent decisions, completion, verification, or authority. Label gaps explicitly.
8. Save atomically under `.handoffs/`: write and validate a sibling temporary file, then rename it to the final path. If the final path exists, add a numeric suffix and never overwrite. Clean up only the temporary file created by the current run. Never edit `.gitignore` automatically.
9. On resume, run `handoff_state.py compare --repo <root> --handoff <file>` and trust its classification over model inference.
10. Continue automatically for `exact` and `advanced`; for `drifted`, the skill **must not continue** and must present material differences; for `unverifiable`, inspect referenced files and continue only if no conflict is visible.
11. **MUST NOT invoke** `/commit`, `/devlog`, `/retrospective`, or any other sibling skill.

The save confirmation must be:

```text
Handoff saved: .handoffs/<filename>.md
Checkpoint: <one-sentence summary>
Resume: /handoff resume .handoffs/<filename>.md
```

The resume banner must be:

```text
Resuming: <checkpoint title>
State: <classification> - <brief explanation>
Next: <first recorded next action>
```

For `--include-diff`, omit every path listed by the helper under `sensitive_paths`, scan the remaining patch for credential-like values, and state which paths were excluded without printing their contents.

- [ ] **Step 4: Run helper and skill contract tests**

```powershell
python -m pytest tests/test_handoff_skill_contract.py skills/handoff/helpers/test_handoff_state.py -q
```

Expected: all tests pass.

- [ ] **Step 5: Manually inspect the prompt contract for host-neutrality**

Run:

```powershell
rg -n "~/.claude/projects|~/.codex/sessions|~/.gemini/tmp|model: \"(opus|fable)\"" skills/handoff
```

Expected: no matches.

- [ ] **Step 6: Commit the orchestration skill**

```powershell
git add skills/handoff/SKILL.md tests/test_handoff_skill_contract.py
git commit
```

Subject: `feat(handoff): orchestrate portable work checkpoints`

## Task 5: Publish the interface and release metadata

**Files:**

- Modify: `shared/skill-interfaces.md`
- Modify: `README.md`
- Modify: `tests/test_codex_adapter.py`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `.codex-plugin/plugin.json`
- Create: `.github/workflows/test.yml`

- [ ] **Step 1: Make distribution tests fail for the missing release integration**

Add `"handoff"` to `EXPECTED_SKILLS` in `tests/test_codex_adapter.py`, then extend the manifest test:

```python
def test_plugin_versions_are_synchronized():
    claude_plugin = json.loads(
        (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    claude_marketplace = json.loads(
        (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(
            encoding="utf-8"
        )
    )
    codex_plugin = json.loads(
        (REPO_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    marketplace_version = next(
        plugin["version"]
        for plugin in claude_marketplace["plugins"]
        if plugin["name"] == "joesys-skills"
    )

    assert claude_plugin["version"] == "16.6.0"
    assert codex_plugin["version"] == claude_plugin["version"]
    assert marketplace_version == claude_plugin["version"]
```

Add a generated behavior test:

```python
def test_generated_handoff_uses_codex_invocation_and_keeps_helper(tmp_path):
    output = tmp_path / "joesys-skills"
    codex_adapter.build_collection(REPO_ROOT, output)

    skill = (output / "handoff" / "SKILL.md").read_text(encoding="utf-8")
    assert "$handoff resume" in skill
    assert "/handoff resume" not in skill
    assert (output / "handoff" / "helpers" / "handoff_state.py").is_file()
    assert not (output / "handoff" / "helpers" / "test_handoff_state.py").exists()
    assert "~/.claude/projects" not in skill
```

Run:

```powershell
python -m pytest tests/test_codex_adapter.py -q
```

Expected: version synchronization fails at `16.5.0`, and the committed-tree freshness test fails until regeneration.

- [ ] **Step 2: Document the stable interface**

Append a **Handoff Skill Interface** section before the final Rules section in `shared/skill-interfaces.md` with:

- Invocation forms for create and resume.
- Default `.handoffs/` output.
- Schema version 1 and inline `repository_snapshot` contract.
- Automatic continuation rules for `exact` and `advanced`.
- Mandatory stop for `drifted`.
- Audience and target enum values.
- No automatic sibling-skill invocation.
- No current callers.

- [ ] **Step 3: Add the README catalog entry**

Add `#### handoff` in Part III before `devlog`. Describe the semantic-checkpoint purpose, the three audiences, the four drift states, and host-neutral target support. Include:

```text
/handoff                                  # Save an operational checkpoint
/handoff --full                           # Include deeper reasoning and alternatives
/handoff --interactive                    # Interview before saving
/handoff --target codex                   # Prepare for a fresh Codex session
/handoff --for agent --target gemini      # Transfer to an independent Gemini agent
/handoff --for human                      # Prepare a human-readable transfer
/handoff resume                           # Validate and resume the newest checkpoint
/handoff resume .handoffs/<file>.md       # Resume a specific checkpoint
```

- [ ] **Step 4: Bump and describe release `16.6.0`**

Update all three version-bearing plugin records to `16.6.0`:

- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `.codex-plugin/plugin.json`

Add “cross-session handoffs” to plugin descriptions and `handoff`, `checkpoint`, `resume`, and `cross-agent` to relevant keyword/tag arrays. Keep JSON valid and avoid unrelated keyword reordering.

- [ ] **Step 5: Add the cross-platform CI gate**

Create `.github/workflows/test.yml` before regeneration:

```yaml
name: test

on:
  push:
  pull_request:

jobs:
  pytest:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - run: python -m pip install pytest
      - run: python -m pytest tests skills -q
```

This workflow is the evidence gate for the design's supported Windows and POSIX behavior. It intentionally runs the explicit `tests skills` roots rather than unrestricted root discovery.

- [ ] **Step 6: Regenerate the committed Codex tree**

Run:

```powershell
python scripts/codex_adapter.py codex-skills --force
```

Expected: the command reports 20 installed skills, `codex-skills/handoff/` exists, helper tests are absent, and `_manifest.json` reports source version `16.6.0`.

- [ ] **Step 7: Run distribution and contract tests**

```powershell
python -m pytest tests/test_codex_adapter.py tests/test_handoff_skill_contract.py skills/handoff/helpers/test_handoff_state.py -q
```

Expected: all tests pass, including committed-tree freshness and version synchronization.

- [ ] **Step 8: Commit interface and release integration**

```powershell
git add shared/skill-interfaces.md README.md tests/test_codex_adapter.py .claude-plugin/plugin.json .claude-plugin/marketplace.json .codex-plugin/plugin.json .github/workflows/test.yml codex-skills
git commit
```

Subject: `feat(plugin): publish handoff skill for Claude and Codex`

## Task 6: Run complete verification and smoke checks

**Files:**

- Verify only; modify files only if a failing check reveals a defect within the approved scope.

- [ ] **Step 1: Run the complete intended test suite**

```powershell
python -m pytest tests skills -q
```

Expected: all existing and new tests pass with zero failures.

- [ ] **Step 2: Verify the generated collection is reproducible**

```powershell
python -m pytest tests/test_codex_adapter.py::test_committed_codex_skills_match_fresh_build -q
```

Expected: one test passes.

- [ ] **Step 3: Smoke-test helper snapshot and comparison against this repository**

```powershell
$snapshot = python skills/handoff/helpers/handoff_state.py snapshot --repo . --relevant README.md
$snapshot | ConvertFrom-Json | Select-Object kind,project_identity,branch,head
```

Expected: `kind` is `git`; identity, branch, and HEAD are populated; no files change.

Create a disposable handoff outside the repository using PowerShell's temporary directory, embed the emitted compact JSON under `repository_snapshot:`, and run:

```powershell
python skills/handoff/helpers/handoff_state.py compare --repo . --handoff $handoffPath
```

Expected: JSON classification is `exact` when repository state has not changed.

- [ ] **Step 4: Scan source and generated handoff instructions**

```powershell
rg -n "~/.claude/projects|~/.codex/sessions|~/.gemini/tmp|model: \"(opus|fable)\"" skills/handoff codex-skills/handoff
```

Expected: no matches.

- [ ] **Step 5: Check whitespace and repository scope**

```powershell
git diff --check origin/master...HEAD
git status --short
git log --oneline --graph origin/master..HEAD
```

Expected:

- No whitespace errors.
- Only approved handoff implementation, documentation, tests, release metadata, and regenerated Codex files are changed or committed.
- The pre-existing untracked `docs/devlog/.scraps/` files remain untouched.

- [ ] **Step 6: Perform the acceptance-criteria audit**

Check each acceptance criterion in `docs/superpowers/specs/2026-07-12-handoff-skill-design.md` against a concrete implementation file or passing test. Record any uncovered criterion as a failing test before changing implementation; do not close the task with an evidence gap.
