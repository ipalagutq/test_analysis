#!/usr/bin/env python3
"""Validate that CHANGELOG contains an integrate-release entry."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


VERSION_RE = re.compile(r"^##\s+\[([^\]]+)\]\s+[—-]\s+(.+)$", re.MULTILINE)


def latest_entry(text: str) -> str:
    matches = list(VERSION_RE.finditer(text))
    if not matches:
        return ""
    start = matches[0].start()
    end = matches[1].start() if len(matches) > 1 else len(text)
    return text[start:end]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("changelog", type=Path, nargs="?", default=Path(".ai/CHANGELOG.md"))
    parser.add_argument("--version")
    parser.add_argument("--route", choices=["spec", "small_fix"])
    args = parser.parse_args()

    if not args.changelog.exists():
        print("FAIL")
        print(f"- Changelog not found: {args.changelog}")
        return 1

    text = args.changelog.read_text(encoding="utf-8")
    entry = latest_entry(text)
    errors: list[str] = []

    if not entry:
        errors.append("No version entry found.")
    if args.version and f"[{args.version}]" not in entry:
        errors.append(f"Latest entry is not version {args.version}.")
    if not re.search(r"^###\s+(Added|Fixed|Changed)\s+[—-]\s+.+", entry, re.MULTILINE):
        errors.append("Latest entry has no Added/Fixed/Changed summary heading.")
    if "**Tests:**" not in entry:
        errors.append("Latest entry has no `**Tests:**` line.")
    if args.route == "spec" and "**Компоненты:**" not in entry:
        errors.append("Spec route changelog entry has no components section.")
    if args.route == "small_fix" and "spec" in entry.lower():
        errors.append("Small-fix changelog entry should not reference a missing spec.")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
