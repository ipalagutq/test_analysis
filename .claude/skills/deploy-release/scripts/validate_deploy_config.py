#!/usr/bin/env python3
"""Validate deploy/deploy.env without exposing secrets."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_KEYS = (
    "VPS_HOST",
    "VPS_USER",
    "VPS_SSH_KEY",
    "VPS_APP_DIR",
    "PROJECT_NAME",
    "REPO_URL",
)
PROJECT_RE = re.compile(r"^[A-Za-z0-9._-]+$")
GIT_URL_RE = re.compile(r"^(https://|git@|ssh://).+")


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def validate(values: dict[str, str], base_dir: Path) -> list[str]:
    errors: list[str] = []
    for key in REQUIRED_KEYS:
        if not values.get(key):
            errors.append(f"Missing required key: {key}")

    project = values.get("PROJECT_NAME", "")
    if project and not PROJECT_RE.fullmatch(project):
        errors.append("PROJECT_NAME must contain only letters, numbers, dot, underscore or dash.")

    app_dir = values.get("VPS_APP_DIR", "")
    if app_dir and not app_dir.startswith("/"):
        errors.append("VPS_APP_DIR must be an absolute Unix path.")
    if app_dir and (".." in app_dir or "\\" in app_dir):
        errors.append("VPS_APP_DIR must not contain `..` or backslashes.")

    repo_url = values.get("REPO_URL", "")
    if repo_url and not GIT_URL_RE.match(repo_url):
        errors.append("REPO_URL should look like https://, git@, or ssh:// URL.")

    ssh_key = values.get("VPS_SSH_KEY", "")
    if ssh_key:
        key_path = Path(ssh_key).expanduser()
        if not key_path.is_absolute():
            key_path = base_dir / key_path
        if not key_path.exists():
            errors.append("VPS_SSH_KEY path does not exist locally.")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", nargs="?", type=Path, default=Path("deploy/deploy.env"))
    args = parser.parse_args()

    if not args.config.exists():
        print("FAIL")
        print(f"- Config not found: {args.config}")
        return 1

    values = parse_env(args.config)
    errors = validate(values, args.config.parent)
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS")
    print(f"host={values['VPS_USER']}@{values['VPS_HOST']}")
    print(f"project={values['VPS_APP_DIR'].rstrip('/')}/{values['PROJECT_NAME']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
