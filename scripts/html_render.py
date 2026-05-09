#!/usr/bin/env python3
"""html_render.py — Convert Markdown reports to self-contained HTML.

Phase 1 scope:
    - Pandoc orchestration (markdown → HTML5 with our template)
    - Mermaid enrichment block transformation
    - Sidebar TOC auto-generation (via Pandoc --toc)
    - Front-matter parsing
    - Bootstrap of docs/.assets/report-lib/ on first run
    - Wired by /explain --save

Out of scope (Phase 2+):
    - Chart.js enrichment blocks
    - Devlog profile (image-pair, lightbox)
    - Reveal.js / --presentation output mode
    - --portable inlining

Usage:
    python scripts/html_render.py <input.md> [options]
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


# ── Constants ──────────────────────────────────────────────────────────


SCRIPTS_DIR = Path(__file__).resolve().parent
PLUGIN_VENDOR_DIR = SCRIPTS_DIR / "vendor"
TEMPLATE_PATH = SCRIPTS_DIR / "templates" / "report.html"


# ── Errors ─────────────────────────────────────────────────────────────


class HtmlRenderError(Exception):
    """Base error class for html_render."""


class NotInRepoError(HtmlRenderError):
    """Raised when the input file is not inside a git repository."""


class VendorMissingError(HtmlRenderError):
    """Raised when the plugin's vendor directory is missing."""


class PandocMissingError(HtmlRenderError):
    """Raised when the pandoc executable cannot be found."""


# ── Repo discovery ─────────────────────────────────────────────────────


def find_repo_root(start: Path) -> Path:
    """Find the git repository root containing `start`.

    Args:
        start: An existing path inside the desired repo.

    Returns:
        Absolute path to the repo root.

    Raises:
        NotInRepoError: if `start` is not inside a git repo.
    """
    cwd = start if start.is_dir() else start.parent
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        raise NotInRepoError(
            f"{start} is not inside a git repository "
            "(or `git` is not on PATH)"
        ) from e
    return Path(result.stdout.strip())


# ── Asset bootstrap ────────────────────────────────────────────────────


def bootstrap_assets(repo_root: Path, vendor_dir: Path = PLUGIN_VENDOR_DIR) -> Path:
    """Ensure docs/.assets/report-lib/ exists in the repo.

    On first invocation in a project, copies the plugin's vendored libraries
    (from `vendor_dir`) into `<repo_root>/docs/.assets/report-lib/`. On
    subsequent runs, the directory already exists and this is a no-op.

    Args:
        repo_root: Project repository root.
        vendor_dir: Source vendor directory (defaults to plugin's bundled assets).

    Returns:
        Absolute path to the report-lib directory inside the repo.

    Raises:
        VendorMissingError: if `vendor_dir` does not exist.
    """
    if not vendor_dir.is_dir():
        raise VendorMissingError(
            f"Plugin vendor directory not found: {vendor_dir}. "
            "Reinstall the joesys-skills plugin."
        )

    dest = repo_root / "docs" / ".assets" / "report-lib"
    if dest.exists():
        return dest

    print(
        f"Creating {dest.relative_to(repo_root)} (one-time setup; "
        "commit this directory to git so other contributors get "
        "working reports).",
        file=sys.stderr,
    )
    shutil.copytree(vendor_dir, dest)
    return dest


# ── Enrichment block transforms ────────────────────────────────────────


_MERMAID_PATTERN = re.compile(
    r"^```mermaid\s*\n(.*?)^```\s*$",
    re.MULTILINE | re.DOTALL,
)


def transform_mermaid_blocks(markdown: str) -> str:
    """Replace ```mermaid fenced blocks with raw-HTML <pre class="mermaid"> blocks.

    Pandoc passes raw HTML through to its output. By wrapping mermaid source
    in a <pre class="mermaid">, the inlined Mermaid library will render it as
    SVG at page load.

    Args:
        markdown: Source markdown text.

    Returns:
        Markdown with mermaid fences replaced by HTML wrappers.
    """

    def _wrap(match: re.Match) -> str:
        diagram = match.group(1).rstrip("\n")
        # Mermaid syntax relies on `<`, `>`, `-->`, `<<` etc. as part of its
        # diagram language, and the content lives inside a <pre> tag where
        # Mermaid does its own parsing. Escape only `&` so that any literal
        # ampersands in labels don't break HTML parsing — leave `<` and `>`
        # alone so diagrams render correctly.
        escaped = diagram.replace("&", "&amp;")
        return f'\n<pre class="mermaid">\n{escaped}\n</pre>\n'

    return _MERMAID_PATTERN.sub(_wrap, markdown)


# ── Main entry point ───────────────────────────────────────────────────


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point. Returns process exit code."""
    # Phase 1 fills this in across Tasks 6-12.
    raise NotImplementedError("html_render.main is implemented in Tasks 6-12")


if __name__ == "__main__":
    sys.exit(main())
