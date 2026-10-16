#!/usr/bin/env python3
"""Validate changed-file scope for an apply-small-fix branch."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


FORBIDDEN_PARTS = ("migrations", "migration")
FORBIDDEN_SUFFIXES = (".sql",)


def git_lines(args: list[str], cwd: Path) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def changed_files(base: str, cwd: Path) -> list[str]:
    files = git_lines(["diff", "--name-only", f"{base}...HEAD"], cwd)
    if not files:
        files = git_lines(["diff", "--name-only", base], cwd)
    if not files:
        files = git_lines(["diff", "--name-only"], cwd)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--base", default="main")
    parser.add_argument("--max-files", type=int, default=3)
    parser.add_argument("--allow-mechanical-overage", action="store_true")
    args = parser.parse_args()

    cwd = args.cwd.resolve()
    files = changed_files(args.base, cwd)
    errors: list[str] = []

    if len(files) > args.max_files and not args.allow_mechanical_overage:
        errors.append(f"Too many changed files for apply-small-fix: {len(files)} > {args.max_files}.")

    spec_files = [path for path in files if path.replace("\\", "/").startswith(".ai/specs/")]
    if spec_files:
        errors.append("apply-small-fix must not create or edit spec files: " + ", ".join(spec_files))

    forbidden = [
        path
        for path in files
        if any(part in path.lower() for part in FORBIDDEN_PARTS)
        or path.lower().endswith(FORBIDDEN_SUFFIXES)
    ]
    if forbidden:
        errors.append("Migration/schema-like files require plan-release: " + ", ".join(forbidden))

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    print(f"changed_files={len(files)}")
    for path in files:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"FAIL\n- git command failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
