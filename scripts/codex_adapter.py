#!/usr/bin/env python3
"""Build a Codex-ready copy of the joesys Claude Code skills."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


COLLECTION_NAME = "joesys-skills"
ADAPTER_VERSION = "1.0.0"
DEFAULT_INSTALL_ROOT = "~/.codex/skills/joesys-skills"


def discover_skill_names(source_root: Path) -> list[str]:
    skills_root = source_root / "skills"
    return sorted(
        path.name for path in skills_root.iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )


def build_collection(
    source_root: Path,
    output_root: Path,
    *,
    install_root: str = DEFAULT_INSTALL_ROOT,
    force: bool = False,
) -> dict:
    """Write an adapted skill collection to output_root and return its manifest."""

    source_root = source_root.resolve()
    output_root = output_root.resolve()
    skill_names = discover_skill_names(source_root)

    _remove_existing_output(output_root, force=force)
    output_root.mkdir(parents=True, exist_ok=True)

    for skill_name in skill_names:
        _copy_skill(
            source_root / "skills" / skill_name,
            output_root / skill_name,
            skill_names=skill_names,
            install_root=install_root,
        )

    _copy_tree(source_root / "shared", output_root / "shared")
    _copy_tree(source_root / "scripts", output_root / "scripts")

    manifest = {
        "name": COLLECTION_NAME,
        "source_version": _source_version(source_root),
        "source_commit": _source_commit(source_root),
        "installed_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "installed_skills": skill_names,
        "slash_commands": [f"/joesys-{name}" for name in skill_names],
        "adapter_version": ADAPTER_VERSION,
    }
    (output_root / "_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def adapt_skill_markdown(text: str, skill_names: Iterable[str], install_root: str) -> str:
    metadata, body = _split_frontmatter(text)
    name = _metadata_value(metadata, "name")
    description = _metadata_value(metadata, "description")
    if not name or not description:
        raise ValueError("SKILL.md frontmatter must include name and description")

    adapted_description = _adapt_text(
        description,
        skill_names,
        install_root,
        current_skill=name,
    )
    adapted_body = _adapt_text(
        body,
        skill_names,
        install_root,
        current_skill=name,
    )

    return _ascii_normalize("\n".join([
        "---",
        f"name: {name}",
        f"description: {json.dumps(adapted_description)}",
        "---",
        "",
        adapted_body.lstrip(),
    ]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a Codex-ready joesys-skills collection.",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Output directory for the adapted skill collection.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Source repository root. Defaults to this repository.",
    )
    parser.add_argument(
        "--install-root",
        default=DEFAULT_INSTALL_ROOT,
        help="Path used inside generated skill instructions.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing non-joesys output directory.",
    )
    args = parser.parse_args(argv)

    manifest = build_collection(
        args.source,
        args.output,
        install_root=args.install_root,
        force=args.force,
    )
    print(
        f"Built {manifest['name']} with {len(manifest['installed_skills'])} "
        f"skills at {args.output}"
    )
    return 0


def _copy_skill(
    source: Path,
    destination: Path,
    *,
    skill_names: Iterable[str],
    install_root: str,
) -> None:
    shutil.copytree(source, destination, ignore=_copy_ignore)
    skill_md = destination / "SKILL.md"
    skill_md.write_text(
        adapt_skill_markdown(
            skill_md.read_text(encoding="utf-8"),
            skill_names,
            install_root,
        ),
        encoding="utf-8",
    )


def _copy_tree(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, destination, ignore=_copy_ignore)


def _copy_ignore(_: str, names: list[str]) -> set[str]:
    ignored = {
        "__pycache__",
        ".pytest_cache",
        "codex_adapter.py",
        "install_codex_skills.py",
    }
    ignored.update(name for name in names if name.endswith((".pyc", ".pyo")))
    ignored.update(
        name
        for name in names
        if name.startswith("test_") and name.endswith(".py")
    )
    return ignored


def _remove_existing_output(output_root: Path, *, force: bool) -> None:
    if not output_root.exists():
        return
    if output_root.is_file():
        raise FileExistsError(f"Output path is a file: {output_root}")

    manifest_path = output_root / "_manifest.json"
    safe_to_replace = False
    if manifest_path.is_file():
        try:
            safe_to_replace = (
                json.loads(manifest_path.read_text(encoding="utf-8")).get("name")
                == COLLECTION_NAME
            )
        except json.JSONDecodeError:
            safe_to_replace = False

    if force or safe_to_replace:
        shutil.rmtree(output_root)
        return

    raise FileExistsError(
        f"Refusing to replace {output_root}; pass --force if this is intentional."
    )


def _split_frontmatter(text: str) -> tuple[str, str]:
    match = re.match(r"^---\r?\n(?P<meta>.*?)\r?\n---\r?\n?(?P<body>.*)$", text, re.S)
    if not match:
        raise ValueError("SKILL.md must start with YAML frontmatter")
    return match.group("meta"), match.group("body")


def _metadata_value(metadata: str, key: str) -> str | None:
    for line in metadata.splitlines():
        if not line.startswith(f"{key}:"):
            continue
        value = line.split(":", 1)[1].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            return value[1:-1]
        return value
    return None


def _adapt_text(
    text: str,
    skill_names: Iterable[str],
    install_root: str,
    *,
    current_skill: str,
) -> str:
    adapted = text
    for skill_name in sorted(skill_names, key=len, reverse=True):
        adapted = re.sub(
            rf"(?<![\w/-])/{re.escape(skill_name)}(?=($|[\s`'\"\])>.,;:|]))",
            f"/joesys-{skill_name}",
            adapted,
        )

    adapted = adapted.replace("AskUserQuestion", "ask the user directly")
    adapted = adapted.replace("Bash tool", "shell command tool")
    adapted = adapted.replace("Bash", "shell")
    adapted = adapted.replace("Agent tool", "Codex agent workflow")
    adapted = adapted.replace("Task tool", "Codex agent workflow")
    adapted = adapted.replace(".claude/skill-context", ".codex/skill-context")
    adapted = adapted.replace(".claude/audit.yaml", ".codex/audit.yaml")
    adapted = adapted.replace(".claude/audit.yml", ".codex/audit.yml")

    adapted = _adapt_resource_paths(adapted, install_root, current_skill)
    return adapted


def _adapt_resource_paths(text: str, install_root: str, current_skill: str) -> str:
    adapted = text

    adapted = re.sub(
        r"(?<![\w~/.:-])skills/([a-z0-9-]+)/",
        rf"{install_root}/\1/",
        adapted,
    )
    adapted = re.sub(
        r"(?<![\w~/.:-])shared/",
        f"{install_root}/shared/",
        adapted,
    )
    adapted = re.sub(
        r"(?<![\w~/.:-])scripts/",
        f"{install_root}/scripts/",
        adapted,
    )
    for folder in ("principles", "references", "templates", "benchmarks", "helpers"):
        adapted = re.sub(
            rf"(?<![\w~/.:-]){folder}/",
            f"{install_root}/{current_skill}/{folder}/",
            adapted,
        )
    return adapted


def _ascii_normalize(text: str) -> str:
    replacements = {
        "\u00a0": " ",
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2015": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
        "\u2190": "<-",
        "\u2192": "->",
        "\u21d2": "=>",
        "\u2264": "<=",
        "\u2265": ">=",
        "\u00d7": "x",
    }
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _source_version(source_root: Path) -> str | None:
    plugin_json = source_root / ".claude-plugin" / "plugin.json"
    if not plugin_json.is_file():
        return None
    try:
        return json.loads(plugin_json.read_text(encoding="utf-8")).get("version")
    except json.JSONDecodeError:
        return None


def _source_commit(source_root: Path) -> str | None:
    try:
        result = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={source_root.as_posix()}",
                "-C",
                str(source_root),
                "rev-parse",
                "HEAD",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


if __name__ == "__main__":
    raise SystemExit(main())
