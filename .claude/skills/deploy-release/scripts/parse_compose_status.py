#!/usr/bin/env python3
"""Parse docker compose status/log text for deploy health signals."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


BAD_PATTERNS = (
    "traceback",
    "critical",
    "panic",
    "fatal",
    "unhealthy",
    "exited",
)
ERROR_RE = re.compile(r"\berror\b", re.IGNORECASE)
UP_RE = re.compile(r"\b(up|running)\b", re.IGNORECASE)


def read_text(path: Path | None) -> str:
    if path is None:
        import sys

        return sys.stdin.read()
    return path.read_text(encoding="utf-8", errors="replace")


def suspicious_lines(text: str) -> list[str]:
    lines: list[str] = []
    for line in text.splitlines():
        lower = line.lower()
        if any(pattern in lower for pattern in BAD_PATTERNS):
            lines.append(line)
            continue
        if ERROR_RE.search(line) and "0 error" not in lower and "no error" not in lower:
            lines.append(line)
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", type=Path)
    parser.add_argument("--require-up", action="store_true")
    args = parser.parse_args()

    text = read_text(args.file)
    errors: list[str] = []
    findings = suspicious_lines(text)
    if findings:
        errors.append("Suspicious log/status lines found:")
        errors.extend(findings[:20])
    if args.require_up and not UP_RE.search(text):
        errors.append("No `Up` or `running` container status found.")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    print("Health output looks clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
