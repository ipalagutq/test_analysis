#!/usr/bin/env python3
"""Find Python modules above the integrate-release size threshold."""

from __future__ import annotations

import argparse
from pathlib import Path


MARKER = "MODULE_SIZE_REVIEWED"


def is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts & {"tests", ".venv", "venv", "__pycache__"})


def has_marker(path: Path) -> bool:
    try:
        head = "".join(path.read_text(encoding="utf-8").splitlines(keepends=True)[:20])
    except UnicodeDecodeError:
        head = "".join(path.read_text(encoding="utf-8-sig").splitlines(keepends=True)[:20])
    return MARKER in head


def line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default="src")
    parser.add_argument("--limit", type=int, default=500)
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print("PASS")
        print(f"root not found: {root}")
        return 0

    findings: list[tuple[Path, int, bool]] = []
    for path in sorted(root.rglob("*.py")):
        if is_excluded(path):
            continue
        count = line_count(path)
        if count > args.limit:
            findings.append((path, count, has_marker(path)))

    if not findings:
        print("PASS")
        print(f"No Python modules exceed {args.limit} lines.")
        return 0

    print("| File | Lines | Reviewed |")
    print("|---|---:|---|")
    for path, count, reviewed in findings:
        print(f"| `{path.as_posix()}` | {count} | {'yes' if reviewed else 'no'} |")

    unreviewed = [path for path, _, reviewed in findings if not reviewed]
    if unreviewed and not args.warn_only:
        print("FAIL")
        print("- Unreviewed large modules found.")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
