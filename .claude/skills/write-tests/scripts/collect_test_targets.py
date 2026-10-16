#!/usr/bin/env python3
"""Collect likely test targets from a spec and git diff."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


BACKTICK_PATH = re.compile(r"`([^`]+\.(?:py|md|toml|yaml|yml|json))`")
HEADING = re.compile(r"^###\s+(.+?)\s*(?:✅|🔄|⬜)?\s*$")


def run_git(args: list[str], cwd: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def paths_from_spec(spec_path: Path) -> set[str]:
    if not spec_path.exists():
        return set()
    text = spec_path.read_text(encoding="utf-8")
    return {
        match.group(1).replace("\\", "/")
        for match in BACKTICK_PATH.finditer(text)
        if not match.group(1).startswith("tests/")
    }


def changed_paths(base: str, cwd: Path) -> set[str]:
    names = run_git(["diff", "--name-only", f"{base}...HEAD"], cwd)
    if not names:
        names = run_git(["diff", "--name-only", base], cwd)
    if not names:
        names = run_git(["diff", "--name-only"], cwd)
    return {name.replace("\\", "/") for name in names}


def classify(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("tests/"):
        return "existing-test"
    if normalized.endswith((".md", ".toml", ".yaml", ".yml", ".json")):
        return "unit/config"
    if "client" in normalized or "api" in normalized:
        return "api"
    if "pipeline" in normalized or "agent" in normalized or "workflow" in normalized:
        return "integration"
    return "unit"


def find_reference_tests(path: str, cwd: Path) -> str:
    stem = Path(path).stem
    candidates = sorted(cwd.glob(f"tests/**/*{stem}*.py"))
    if candidates:
        return candidates[0].as_posix()

    parent = Path(path).parent.name
    if parent:
        candidates = sorted(cwd.glob(f"tests/**/*{parent}*.py"))
        if candidates:
            return candidates[0].as_posix()

    return "NOT_FOUND"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec_path", type=Path)
    parser.add_argument("--base", default="main")
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    args = parser.parse_args()

    cwd = args.cwd.resolve()
    spec_path = args.spec_path if args.spec_path.is_absolute() else cwd / args.spec_path

    paths = paths_from_spec(spec_path) | changed_paths(args.base, cwd)
    paths = {path for path in paths if path and not path.startswith(".ai/specs/")}

    if not paths:
        print("No target files found.", file=sys.stderr)
        return 1

    print("| Changed file | Source | Existing test pattern | Proposed test layer |")
    print("|---|---|---|---|")
    spec_paths = paths_from_spec(spec_path)
    diff_paths = changed_paths(args.base, cwd)
    for path in sorted(paths):
        source = "+".join(
            label
            for label, collection in (("spec", spec_paths), ("diff", diff_paths))
            if path in collection
        )
        print(
            f"| `{path}` | {source or 'unknown'} | "
            f"`{find_reference_tests(path, cwd)}` | {classify(path)} |"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
