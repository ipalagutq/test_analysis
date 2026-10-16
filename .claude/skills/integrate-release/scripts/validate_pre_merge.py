#!/usr/bin/env python3
"""Validate integrate-release entry conditions before changelog/archive edits."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from detect_merge_route import current_branch, detect


def git_lines(args: list[str], cwd: Path) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--branch")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow dirty state after integrate-release has intentionally edited changelog/archive.",
    )
    args = parser.parse_args()

    cwd = args.cwd.resolve()
    errors: list[str] = []

    branch = args.branch or current_branch(cwd)
    route, spec_path, route_errors = detect(branch, cwd)
    errors.extend(route_errors)

    dirty = git_lines(["status", "--porcelain"], cwd)
    if dirty and not args.allow_dirty:
        errors.append("Worktree is not clean:")
        errors.extend(dirty[:20])

    branches = git_lines(["branch", "--list", "main", "master"], cwd)
    if not branches:
        errors.append("Neither main nor master branch is available locally.")

    if route == "small_fix" and spec_path is not None and spec_path.exists():
        errors.append("small_fix route must not have an active spec file.")

    if errors:
        print("FAIL")
        print(f"branch={branch}")
        print(f"route={route}")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    print(f"branch={branch}")
    print(f"route={route}")
    print(f"spec={spec_path.relative_to(cwd).as_posix() if spec_path else 'not required'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"FAIL\n- git command failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
