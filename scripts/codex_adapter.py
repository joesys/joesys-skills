#!/usr/bin/env python3
"""Build the Codex plugin copy of the joesys Claude Code skills.

The output directory is what `.codex-plugin/plugin.json` points at via its
`skills` field. Inside the Codex plugin snapshot the skills live wherever
Codex caches the plugin, so every cross-tree reference is rewritten relative
to the skill's own directory (`../shared/`, `../scripts/`) instead of an
absolute install path. Skill-local references (`references/`, `principles/`,
...) are already relative to the skill directory and ship unchanged.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Iterable


COLLECTION_NAME = "joesys-skills"
ADAPTER_VERSION = "2.0.0"


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
        )

    _copy_tree(source_root / "shared", output_root / "shared")
    # Shared bodies ship to Codex verbatim otherwise, carrying Claude
    # Code-only tool names (AskUserQuestion, WebSearch, Bash), `.claude/`
    # paths, and repo-relative plugin references. Shared files sit next to
    # the skill folders, so their own `shared/` references become siblings.
    for md in sorted((output_root / "shared").glob("**/*.md")):
        _write_text(
            md,
            _adapt_text(
                md.read_text(encoding="utf-8"),
                skill_names,
                in_shared=True,
            ),
        )
    _copy_tree(source_root / "scripts", output_root / "scripts")

    # The manifest must stay deterministic: the built tree is committed as
    # codex-skills/ and a freshness test diffs it against a fresh build, so
    # no timestamps and no commit hashes.
    manifest = {
        "name": COLLECTION_NAME,
        "source_version": _source_version(source_root),
        "installed_skills": skill_names,
        "skill_mentions": [f"${name}" for name in skill_names],
        "adapter_version": ADAPTER_VERSION,
    }
    _write_text(
        output_root / "_manifest.json",
        json.dumps(manifest, indent=2) + "\n",
    )
    return manifest


def adapt_skill_markdown(text: str, skill_names: Iterable[str]) -> str:
    metadata, body = _split_frontmatter(text)
    name = _metadata_value(metadata, "name")
    description = _metadata_value(metadata, "description")
    if not name or not description:
        raise ValueError("SKILL.md frontmatter must include name and description")

    adapted_description = _adapt_text(description, skill_names)
    adapted_body = _adapt_text(body, skill_names)

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
        description="Build the Codex plugin copy of joesys-skills.",
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
        "--force",
        action="store_true",
        help="Replace an existing non-joesys output directory.",
    )
    args = parser.parse_args(argv)

    manifest = build_collection(
        args.source,
        args.output,
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
) -> None:
    shutil.copytree(source, destination, ignore=_copy_ignore)
    skill_md = destination / "SKILL.md"
    _write_text(
        skill_md,
        adapt_skill_markdown(
            skill_md.read_text(encoding="utf-8"),
            skill_names,
        ),
    )
    # Reference/principle/template markdown ships to Codex too — adapt tool
    # names, .claude paths, slash commands, and resource paths in them as
    # well, so a dispatched Codex agent never reads a Claude Code-only
    # instruction or a repo-relative plugin path.
    for md in sorted(destination.glob("**/*.md")):
        if md.name == "SKILL.md":
            continue
        _write_text(
            md,
            _adapt_text(
                md.read_text(encoding="utf-8"),
                skill_names,
            ),
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
        "reinstall-plugin.ps1",
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


def _write_text(path: Path, text: str) -> None:
    # LF always, so the committed codex-skills/ tree is byte-stable across
    # regenerations regardless of platform newline defaults.
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


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
    *,
    in_shared: bool = False,
) -> str:
    adapted = text
    # Codex has no slash commands for skills — explicit invocation is a
    # `$name` mention in the composer.
    for skill_name in sorted(skill_names, key=len, reverse=True):
        adapted = re.sub(
            rf"(?<![\w/-])/{re.escape(skill_name)}(?=($|[\s`'\"\])>.,;:|]))",
            f"${skill_name}",
            adapted,
        )

    adapted = adapted.replace("AskUserQuestion", "ask the user directly")
    adapted = adapted.replace("WebSearch", "web search")
    adapted = adapted.replace("Bash tool", "shell command tool")
    adapted = adapted.replace("Bash", "shell")
    adapted = adapted.replace("Agent tool", "Codex agent workflow")
    adapted = adapted.replace("Task tool", "Codex agent workflow")
    adapted = adapted.replace(".claude/skill-context", ".codex/skill-context")
    adapted = adapted.replace(".claude/audit.yaml", ".codex/audit.yaml")
    adapted = adapted.replace(".claude/audit.yml", ".codex/audit.yml")

    adapted = _adapt_resource_paths(adapted, in_shared=in_shared)
    return adapted


def _adapt_resource_paths(text: str, *, in_shared: bool) -> str:
    """Rewrite repo-root-relative references relative to the reading file.

    In the built collection every skill folder, shared/, and scripts/ are
    siblings, so from inside a skill folder the cross-tree prefix is `../`.
    Files in shared/ reference their own folder as `./`. Skill-local folders
    (references/, principles/, ...) stay untouched — they are already
    relative to the skill directory.
    """
    adapted = text

    # Dynamic skill-name validation is not matched by the concrete-name regex
    # below. Generated skills are siblings in the collection, not children of
    # a canonical `skills/` directory.
    adapted = adapted.replace(
        "skills/<skill-name>/SKILL.md",
        "../<skill-name>/SKILL.md",
    )

    adapted = re.sub(
        r"(?<![\w~/.:-])skills/([a-z0-9-]+)/",
        r"../\1/",
        adapted,
    )
    adapted = re.sub(
        r"(?<![\w~/.:-])shared/",
        "./" if in_shared else "../shared/",
        adapted,
    )
    adapted = re.sub(
        r"(?<![\w~/.:-])scripts/",
        "../scripts/",
        adapted,
    )

    # Canonical skills sit under plugin-root/skills/<name>; generated skills
    # sit directly under collection-root/<name>. Keep the explanatory prose in
    # sync with the rewritten ../ paths, especially for standalone installs
    # that do not contain the canonical repository tree.
    adapted = adapted.replace(
        "plugin root (two levels above this SKILL.md",
        "collection root (one level above this SKILL.md",
    )
    adapted = adapted.replace(
        "plugin root — two levels above this SKILL.md —",
        "collection root (one level above this SKILL.md) —",
    )
    adapted = adapted.replace(
        "plugin root (two levels above the skill directory)",
        "collection root (one level above the skill directory)",
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
        "\u2260": "!=",
        "\u00d7": "x",
        "\u00a7": "Section",
        "\u00b1": "+/-",
        "\u00b7": "*",
        "\u2500": "-",
        "\u2502": "|",
        "\u250c": "+",
        "\u2510": "+",
        "\u2514": "+",
        "\u2518": "+",
        "\u251c": "+",
        "\u2524": "+",
        "\u252c": "+",
        "\u2534": "+",
        "\u253c": "+",
        "\u26a0": "WARNING",
        "\u2713": "yes",
        "\u23f8": "paused",
        "\ufe0f": "",
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


if __name__ == "__main__":
    raise SystemExit(main())
