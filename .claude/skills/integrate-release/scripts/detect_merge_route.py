#!/usr/bin/env python3
"""Detect the integrate-release route for the current branch."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


IMPLEMENTATION_SECTION = re.compile(
    r"^##\s+Этапы реализации\s*$([\s\S]*?)(?=^##\s+|\Z)",
    re.MULTILINE,
)
STAGE_HEADING = re.compile(r"^###\s+(.+?)(?:\s+(⬜|🔄|✅))?\s*$", re.MULTILINE)


def git_output(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def current_branch(cwd: Path) -> str:
    return git_output(["branch", "--show-current"], cwd)


def branch_slug(branch: str) -> str:
    return branch.replace("/", "-")


def incomplete_stages(spec_path: Path) -> list[str]:
    text = spec_path.read_text(encoding="utf-8")
    section = IMPLEMENTATION_SECTION.search(text)
    if not section:
        return ["Missing `## Этапы реализации` section."]
    stages = list(STAGE_HEADING.finditer(section.group(1)))
    if not stages:
        return ["No implementation stages found."]
    return [stage.group(0) for stage in stages if "✅" not in stage.group(0)]


def detect(branch: str, cwd: Path) -> tuple[str, Path | None, list[str]]:
    errors: list[str] = []
    if branch in {"main", "master"}:
        return "STOP", None, ["integrate-release must run from a non-main branch."]

    spec_path = cwd / ".ai" / "specs" / f"{branch_slug(branch)}.md"
    if spec_path.exists():
        incomplete = incomplete_stages(spec_path)
        if incomplete:
            errors.append("Spec route found, but stages are incomplete:")
            errors.extend(incomplete)
            return "STOP", spec_path, errors
        return "spec", spec_path, []

    if branch.startswith("fix/"):
        return "small_fix", None, []

    return "STOP", spec_path, [
        "Spec file is missing and no-spec merge is allowed only for fix/* branches."
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cwd", type=Path, default=Path.cwd())
    parser.add_argument("--branch")
    args = parser.parse_args()

    cwd = args.cwd.resolve()
    branch = args.branch or current_branch(cwd)
    route, spec_path, errors = detect(branch, cwd)

    if errors:
        print("FAIL")
        print(f"branch={branch}")
        print(f"route={route}")
        if spec_path is not None:
            print(f"spec={spec_path.relative_to(cwd).as_posix()}")
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
