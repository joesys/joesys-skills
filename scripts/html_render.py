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


# ── Front-matter parsing ──────────────────────────────────────────────


_FRONTMATTER_PATTERN = re.compile(
    r"\A---\s*\n(.*?)^---\s*$\n?",
    re.MULTILINE | re.DOTALL,
)


def parse_frontmatter(markdown: str) -> tuple[dict, str]:
    """Extract YAML front-matter from the head of a markdown document.

    Supports a tiny subset of YAML — flat key:value pairs, optional
    double-quoted values. Sufficient for our front-matter needs without
    pulling in PyYAML.

    Args:
        markdown: Source markdown text.

    Returns:
        Tuple of (metadata dict, body markdown with front-matter stripped).
    """
    match = _FRONTMATTER_PATTERN.match(markdown)
    if not match:
        return ({}, markdown)

    raw = match.group(1)
    metadata: dict = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        # Strip surrounding double quotes if present.
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            value = value[1:-1]
        metadata[key.strip()] = value

    body = markdown[match.end():]
    return (metadata, body)


def compute_assets_relpath(assets_dir: Path, output_path: Path) -> str:
    """Compute the relative path from output HTML back to the assets dir.

    HTML <link> and <script> tags must use forward slashes regardless of
    the host OS, so we normalize the result.

    Args:
        assets_dir: Absolute path to docs/.assets/report-lib/.
        output_path: Absolute path to the HTML file being generated.

    Returns:
        POSIX-style relative path string (e.g., "../.assets/report-lib").
    """
    rel = os.path.relpath(assets_dir, start=output_path.parent)
    return rel.replace(os.sep, "/")


# ── Pandoc orchestration ──────────────────────────────────────────────


def _ensure_pandoc() -> None:
    """Raise PandocMissingError if pandoc is not on PATH."""
    if shutil.which("pandoc") is None:
        raise PandocMissingError(
            "pandoc is required but was not found on PATH. "
            "Install: choco install pandoc / brew install pandoc / "
            "apt install pandoc"
        )


def render_html(
    input_md: Path,
    output_html: Path,
    assets_dir: Path,
    template_path: Path,
    toc: bool = True,
) -> None:
    """Render a markdown report to a self-contained HTML file.

    1. Read source markdown.
    2. Parse and strip front-matter (use as Pandoc metadata).
    3. Apply enrichment-block transforms (Phase 1: mermaid only).
    4. Compute relative asset path.
    5. Write transformed markdown to a temp file.
    6. Run Pandoc to render through our HTML5 template.
    7. Clean up the temp file.

    Args:
        input_md: Source markdown.
        output_html: Output HTML path.
        assets_dir: Absolute path to docs/.assets/report-lib/.
        template_path: Pandoc HTML5 template path.
        toc: If True (default), pass --toc / --toc-depth=3 to Pandoc so the
            sidebar table of contents is auto-built. Set False to suppress
            (the sidebar h1 "Contents" remains but the list is empty).

    Raises:
        PandocMissingError: if pandoc is not installed.
        HtmlRenderError: if pandoc subprocess fails.
    """
    _ensure_pandoc()

    raw = input_md.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(raw)

    # Default title: first H1 or filename
    if "title" not in metadata:
        m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        metadata["title"] = m.group(1).strip() if m else input_md.stem

    body = transform_mermaid_blocks(body)

    rel_assets = compute_assets_relpath(assets_dir, output_html)

    output_html.parent.mkdir(parents=True, exist_ok=True)

    # Write transformed markdown to a temp file alongside the input
    tmp_md = input_md.parent / (input_md.stem + ".tmp.md")
    try:
        tmp_md.write_text(body, encoding="utf-8")

        cmd = [
            "pandoc",
            str(tmp_md),
            "-o", str(output_html),
            "--from=markdown",
            "--to=html5",
            "--template", str(template_path),
            "--standalone",
            "--variable", f"assets-rel={rel_assets}",
        ]
        if toc:
            cmd.extend(["--toc", "--toc-depth=3"])
        for key, value in metadata.items():
            cmd.extend(["--variable", f"{key}={value}"])

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise HtmlRenderError(
                f"pandoc failed (exit {e.returncode}):\n{e.stderr}"
            ) from e
    finally:
        if tmp_md.exists():
            tmp_md.unlink()


# ── CLI ───────────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="html_render",
        description="Render a Markdown report to a self-contained HTML file.",
    )
    p.add_argument("input", help="Path to the input markdown file.")
    p.add_argument(
        "--output",
        help="Output HTML path. Default: same dir, .html extension.",
    )
    p.add_argument(
        "--profile",
        choices=["analytical"],   # Phase 1 supports only analytical
        default="analytical",
        help="Report profile (Phase 1 supports only 'analytical').",
    )
    p.add_argument(
        "--no-toc",
        action="store_true",
        help="Skip the sidebar TOC.",
    )
    p.add_argument(
        "--vendor-dir",
        help="Override the plugin's vendor directory (testing).",
    )
    p.add_argument(
        "--template",
        help="Override the Pandoc HTML5 template path (testing).",
    )
    p.add_argument(
        "--assets-dir",
        help="Override the docs/.assets/report-lib/ destination (testing).",
    )
    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    input_md = Path(args.input).resolve()
    if not input_md.is_file():
        print(f"Input markdown not found: {input_md}", file=sys.stderr)
        return 2

    output_html = Path(args.output).resolve() if args.output else input_md.with_suffix(".html")
    template_path = Path(args.template).resolve() if args.template else TEMPLATE_PATH
    vendor_dir = Path(args.vendor_dir).resolve() if args.vendor_dir else PLUGIN_VENDOR_DIR

    try:
        if args.assets_dir:
            assets_dir = Path(args.assets_dir).resolve()
            assets_dir.mkdir(parents=True, exist_ok=True)
        else:
            repo_root = find_repo_root(input_md)
            assets_dir = bootstrap_assets(repo_root, vendor_dir=vendor_dir)
    except NotInRepoError as e:
        print(str(e), file=sys.stderr)
        return 6
    except VendorMissingError as e:
        print(str(e), file=sys.stderr)
        return 4

    try:
        render_html(
            input_md=input_md,
            output_html=output_html,
            assets_dir=assets_dir,
            template_path=template_path,
            toc=not args.no_toc,
        )
    except PandocMissingError as e:
        print(str(e), file=sys.stderr)
        return 1
    except HtmlRenderError as e:
        print(str(e), file=sys.stderr)
        return 3

    print(f"Rendered: {output_html}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
