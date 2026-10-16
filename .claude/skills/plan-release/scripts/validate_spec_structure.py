#!/usr/bin/env python3
"""Validate the basic Markdown structure expected from plan-release."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "Workflow выполнения",
    "Видение",
    "Архитектурные решения",
    "Этапы реализации",
]

WORKFLOW_SKILLS = [
    "implement-spec-stage",
    "write-tests",
    "integrate-release",
    "deploy-release",
]


def has_section(text: str, section: str) -> bool:
    return re.search(rf"^##\s+{re.escape(section)}\s*$", text, re.MULTILINE) is not None


def validate(text: str) -> list[str]:
    errors: list[str] = []

    if not re.search(r"^# .+Specification \(v[^)]+\)", text, re.MULTILINE):
        errors.append("Missing H1 title with `Specification (v...)`.")

    for label in ["Дата создания", "Ветка", "Статус", "Standard"]:
        if f"**{label}:**" not in text:
            errors.append(f"Missing metadata field: {label}.")

    for section in REQUIRED_SECTIONS:
        if not has_section(text, section):
            errors.append(f"Missing required section: {section}.")

    if has_section(text, "Workflow выполнения"):
        for skill in WORKFLOW_SKILLS:
            if f"`{skill}`" not in text:
                errors.append(f"Workflow table missing skill: {skill}.")

    if not re.search(r"^###\s+(?:\S+\s+)?Этап\s+\d+:", text, re.MULTILINE):
        errors.append("Missing implementation stage heading: `### [⬜] Этап N:`.")

    for marker in ["**Файлы:**", "**Что делаем:**", "**Определение готовности:**"]:
        if marker not in text:
            errors.append(f"Missing stage marker: {marker}.")

    if "Score:" not in text:
        errors.append("Missing standard score in metadata.")

    if re.search(r"\b(и т\.д\.|etc\.|прочее)\b", text, re.IGNORECASE):
        errors.append("Vague placeholder detected: avoid `и т.д.`, `etc.`, or `прочее`.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a spec Markdown file.")
    parser.add_argument("spec_path", type=Path)
    args = parser.parse_args()

    if not args.spec_path.exists():
        print(f"ERROR: file not found: {args.spec_path}", file=sys.stderr)
        return 2

    text = args.spec_path.read_text(encoding="utf-8")
    errors = validate(text)

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
