#!/usr/bin/env python3
"""Check local deploy preconditions before SSH operations."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from validate_deploy_config import parse_env, validate


def git_output(args: list[str]) -> str:
    result = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("deploy/deploy.env"))
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--env-optional", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []

    try:
        branch = git_output(["branch", "--show-current"])
    except subprocess.CalledProcessError as exc:
        print(f"FAIL\n- git command failed: {exc}")
        return 2

    if branch != "main":
        errors.append(f"Deploy must run from main; current branch is `{branch}`.")

    if not args.config.exists():
        errors.append(f"Config not found: {args.config}")
    else:
        values = parse_env(args.config)
        errors.extend(validate(values, args.config.parent))

    if not args.env_optional and not args.env_file.exists():
        errors.append(f"Env file not found: {args.env_file}")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    print(f"branch={branch}")
    print(f"env={'optional' if args.env_optional else args.env_file.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
