#!/usr/bin/env python3
"""Install joesys-skills into the local Codex skills directory."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import codex_adapter


def default_destination() -> Path:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return codex_home / "skills" / codex_adapter.COLLECTION_NAME


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install a Codex-ready copy of joesys-skills.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Source repository root. Defaults to this repository.",
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=default_destination(),
        help=(
            "Destination collection directory. Defaults to "
            "$CODEX_HOME/skills/joesys-skills or ~/.codex/skills/joesys-skills."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing non-joesys destination directory.",
    )
    args = parser.parse_args(argv)

    args.dest.parent.mkdir(parents=True, exist_ok=True)
    manifest = codex_adapter.build_collection(
        args.source,
        args.dest,
        force=args.force,
    )

    print(
        f"Installed {manifest['name']} with {len(manifest['installed_skills'])} "
        f"skills to {args.dest}"
    )
    print("Restart Codex to pick up new skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
