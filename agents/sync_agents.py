#!/usr/bin/env python3
"""Replaces the managed FIDES block in an agent guide with a release's rules.

Usage: sync_agents.py RULES_FILE TARGET_FILE VERSION

The target must already hold the markers, placed where the rules belong:

    <!-- FIDES:BEGIN -->
    <!-- FIDES:END -->

Everything outside the markers is the repository's own and is never touched.
The script never guesses where the block goes: without markers it exits 2.
It prints "unchanged" or "updated to VERSION" and exits 0 either way.
"""

import re
import sys
from pathlib import Path

BLOCK = re.compile(r"<!-- FIDES:BEGIN[^>]*-->.*?<!-- FIDES:END -->", re.DOTALL)


def managed_block(rules: str, version: str) -> str:
    header = (f"<!-- FIDES:BEGIN version={version}. Managed by the FIDES sync: "
              "edit the rules upstream, not here. -->")
    return f"{header}\n{rules.strip()}\n<!-- FIDES:END -->"


def sync(rules: str, guide: str, version: str) -> str:
    """Returns the guide with its managed block replaced."""
    found = BLOCK.findall(guide)
    if len(found) != 1:
        raise ValueError(f"expected one FIDES:BEGIN/FIDES:END block, found {len(found)}")
    return BLOCK.sub(lambda _: managed_block(rules, version), guide)


def main(arguments: list[str]) -> int:
    if len(arguments) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    rules_path, target_path, version = Path(arguments[0]), Path(arguments[1]), arguments[2]
    guide = target_path.read_text(encoding="utf-8")
    try:
        updated = sync(rules_path.read_text(encoding="utf-8"), guide, version)
    except ValueError as error:
        print(f"{target_path}: {error}; add the markers where the rules belong",
              file=sys.stderr)
        return 2
    if updated == guide:
        print("unchanged")
    else:
        target_path.write_text(updated, encoding="utf-8")
        print(f"updated to {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
