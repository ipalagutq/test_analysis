#!/usr/bin/env python3
"""Validate apply-small-fix entry conditions before creating fix/* branch."""

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
    parser.add_argument("--future-slug", help="Slug planned for fix/{slug}.")
    args = parser.parse_args()

    cwd = args.cwd.resolve()
    errors: list[str] = []

    branch = git_output(["branch", "--show-current"], cwd)
    if branch not in {"main", "master"}:
        errors.append(f"apply-small-fix must start from main/master; current branch is `{branch}`.")

    status = git_output(["status", "--porcelain"], cwd)
    if status:
        errors.append("Worktree is not clean.")

    if args.future_slug:
        spec_path = cwd / ".ai" / "specs" / f"fix-{args.future_slug}.md"
        if spec_path.exists():
            errors.append(f"apply-small-fix must not have a spec: {spec_path.relative_to(cwd).as_posix()}")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    print(f"branch={branch}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"FAIL\n- git command failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
