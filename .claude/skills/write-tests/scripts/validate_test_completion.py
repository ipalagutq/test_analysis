#!/usr/bin/env python3
"""Validate basic write-tests completion signals for a branch."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


STAGE_HEADING = re.compile(r"^###\s+(.+?)(?:\s+(⬜|🔄|✅))?\s*$", re.MULTILINE)
IMPLEMENTATION_SECTION = re.compile(
    r"^##\s+Этапы реализации\s*$([\s\S]*?)(?=^##\s+|\Z)",
    re.MULTILINE,
)
LIVE_IO_PATTERNS = (
    "requests.get(",
    "requests.post(",
    "httpx.get(",
    "httpx.post(",
    "urlopen(",
    "openai.",
)


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


def validate_spec(spec_path: Path) -> list[str]:
    errors: list[str] = []
    if not spec_path.exists():
        return [f"Spec not found: {spec_path}"]

    text = spec_path.read_text(encoding="utf-8")
    section = IMPLEMENTATION_SECTION.search(text)
    if not section:
        errors.append("Missing `## Этапы реализации` section.")
        return errors

    stages = list(STAGE_HEADING.finditer(section.group(1)))
    if not stages:
        errors.append("No implementation stages found in spec.")
        return errors

    incomplete = [stage.group(0) for stage in stages if "✅" not in stage.group(0)]
    if incomplete:
        errors.append("Spec has incomplete stages: " + "; ".join(incomplete))

    return errors


def changed_files(base: str, cwd: Path) -> list[str]:
    names = run_git(["diff", "--name-only", f"{base}...HEAD"], cwd)
    if not names:
        names = run_git(["diff", "--name-only", base], cwd)
    if not names:
        names = run_git(["diff", "--name-only"], cwd)
    return names


def validate_tests(paths: list[str], cwd: Path) -> list[str]:
    errors: list[str] = []
    test_paths = [path for path in paths if path.replace("\\", "/").startswith("tests/")]
    source_paths = [
        path
        for path in paths
        if path.endswith(".py") and not path.replace("\\", "/").startswith("tests/")
    ]

    if source_paths and not test_paths:
        errors.append("Python source changed but no tests changed.")

    for path in test_paths:
        normalized = path.replace("\\", "/")
        if not normalized.startswith("tests/unit/") and not normalized.startswith("tests/api/"):
            continue
        full_path = cwd / path
        if not full_path.exists() or full_path.suffix != ".py":
            continue
        text = full_path.read_text(encoding="utf-8")
        found = [pattern for pattern in LIVE_IO_PATTERNS if pattern in text]
        if found:
            errors.append(f"Potential live I/O in {path}: {', '.join(found)}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec_path", type=Path)
    parser.add_argument("--base", default="main")
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    args = parser.parse_args()

    cwd = args.cwd.resolve()
    spec_path = args.spec_path if args.spec_path.is_absolute() else cwd / args.spec_path
    changed = changed_files(args.base, cwd)

    errors = validate_spec(spec_path)
    errors.extend(validate_tests(changed, cwd))

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
