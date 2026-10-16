#!/usr/bin/env python3
"""Render deploy SSH/SCP commands from deploy.env without executing them."""

from __future__ import annotations

import argparse
from pathlib import Path

from validate_deploy_config import parse_env, validate


def quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


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

    host = f"{values['VPS_USER']}@{values['VPS_HOST']}"
    app_dir = f"{values['VPS_APP_DIR'].rstrip('/')}/{values['PROJECT_NAME']}"
    key = values["VPS_SSH_KEY"]
    ssh = f"ssh -i {quote(key)} -o StrictHostKeyChecking=accept-new {quote(host)}"

    print("# Deploy command plan")
    print(f"APP_DIR={quote(app_dir)}")
    print(f"SSH_CMD={ssh}")
    print(f"scp -i {quote(key)} .env {quote(host + ':' + app_dir + '/repo/.env')}")
    print(f"{ssh} {quote('cd ' + app_dir + '/repo && git status --porcelain')}")
    print(f"{ssh} {quote('cd ' + app_dir + '/repo && git pull origin main')}")
    print(f"{ssh} {quote('cd ' + app_dir + '/repo && docker compose build && docker compose up -d')}")
    print(f"{ssh} {quote('cd ' + app_dir + '/repo && docker compose ps && docker compose logs --tail=30')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
