#!/usr/bin/env python3
"""Validate small-fix completion before handing off to integrate-release."""

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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--base", default="main")
    parser.add_argument("--verification", help="Command/result or 'not applicable: reason'.")
    args = parser.parse_args()

    cwd = args.cwd.resolve()
    errors: list[str] = []
    branch = git_output(["branch", "--show-current"], cwd)
    if not branch.startswith("fix/"):
        errors.append(f"Expected fix/* branch, got `{branch}`.")

    status = git_output(["status", "--porcelain"], cwd)
    if status:
        errors.append("Worktree is not clean; commit or revert scoped changes first.")

    commits = git_output(["rev-list", "--count", f"{args.base}..HEAD"], cwd)
    if commits == "0":
        errors.append("No commit found on apply-small-fix branch.")

    if not args.verification:
        errors.append("Verification result is required.")

    active_specs = list((cwd / ".ai" / "specs").glob("fix-*.md")) if (cwd / ".ai" / "specs").exists() else []
    if active_specs:
        errors.append("apply-small-fix must not leave active fix specs: " + ", ".join(p.as_posix() for p in active_specs))

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    print(f"branch={branch}")
    print(f"commits_ahead={commits}")
    print(f"verification={args.verification}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"FAIL\n- git command failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
