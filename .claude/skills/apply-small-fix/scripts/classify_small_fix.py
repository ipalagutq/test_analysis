#!/usr/bin/env python3
"""Classify whether a task looks suitable for apply-small-fix."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ESCALATION_PATTERNS = {
    "migration": re.compile(r"\b(migration|migrate|schema|database|db)\b", re.I),
    "public_contract": re.compile(r"\b(api|public contract|protocol|endpoint|breaking)\b", re.I),
    "architecture": re.compile(r"\b(architecture|redesign|refactor architecture|new module)\b", re.I),
    "feature": re.compile(r"\b(new feature|add feature|support new|implement new)\b", re.I),
    "multi_stage": re.compile(r"\b(stage|phase|multi-step|несколько этапов)\b", re.I),
}


def read_description(args: argparse.Namespace) -> str:
    if args.description:
        return args.description
    if args.file:
        return args.file.read_text(encoding="utf-8")
    return sys.stdin.read()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("description", nargs="?")
    parser.add_argument("--file", type=Path)
    parser.add_argument("--changed-files", nargs="*", default=[])
    args = parser.parse_args()

    text = read_description(args)
    reasons: list[str] = []
    for name, pattern in ESCALATION_PATTERNS.items():
        if pattern.search(text):
            reasons.append(name)

    files = [path for path in args.changed_files if path]
    if len(files) > 3:
        reasons.append("more_than_3_files")
    if any(path.replace("\\", "/").startswith(".ai/specs/") for path in files):
        reasons.append("spec_artifact")
    if any("migration" in path.lower() for path in files):
        reasons.append("migration_file")

    if reasons:
        print("ROUTE=plan-release")
        print("REASONS=" + ",".join(sorted(set(reasons))))
        return 1

    print("ROUTE=apply-small-fix")
    print("REASONS=local,limited,checkable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
