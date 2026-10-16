#!/usr/bin/env python3
"""Validate post-merge state for integrate-release."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def git_output(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def slug(branch: str) -> str:
    return branch.replace("/", "-")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_branch")
    parser.add_argument("--route", choices=["spec", "small_fix"], required=True)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    args = parser.parse_args()

    cwd = args.cwd.resolve()
    errors: list[str] = []
    current = git_output(["branch", "--show-current"], cwd)
    if current not in {"main", "master"}:
        errors.append(f"Current branch is `{current}`, expected main/master.")

    changelog = cwd / ".ai" / "CHANGELOG.md"
    if not changelog.exists():
        errors.append(".ai/CHANGELOG.md is missing.")

    branch_slug = slug(args.source_branch)
    active_spec = cwd / ".ai" / "specs" / f"{branch_slug}.md"
    archived_spec = cwd / ".ai" / "specs" / "archive" / f"{branch_slug}.md"

    if args.route == "spec":
        if active_spec.exists():
            errors.append(f"Active spec still exists: {active_spec.relative_to(cwd).as_posix()}")
        if not archived_spec.exists():
            errors.append(f"Archived spec is missing: {archived_spec.relative_to(cwd).as_posix()}")
    elif archived_spec.exists():
        errors.append("small_fix route should not create an archived spec.")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"FAIL\n- git command failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
