#!/usr/bin/env python3
"""Validate deploy report completeness."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_LABELS = ("Сервер:", "Проект:", "Контейнер:", "Git:", "Версия:")
HASH_RE = re.compile(r"\b[0-9a-f]{7,40}\b", re.IGNORECASE)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()

    if not args.report.exists():
        print("FAIL")
        print(f"- Report not found: {args.report}")
        return 1

    text = args.report.read_text(encoding="utf-8")
    errors = [f"Missing label: {label}" for label in REQUIRED_LABELS if label not in text]
    if not HASH_RE.search(text):
        errors.append("No git commit hash found.")
    if "Deploy завершён" not in text and "Deploy не завершён" not in text:
        errors.append("Report does not state deploy outcome.")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
