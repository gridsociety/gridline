"""Small CLI for agents and humans; no hidden global configuration writes."""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import sys
from pathlib import Path

from .environment import doctor, print_doctor
from .workspace import new, check, BACKENDS


def mcp_config(project):
    project = Path(project).expanduser().resolve()
    return {"mcpServers": {"gridline-qelectrotech": {
        "command": str(Path(sys.executable).absolute()),
        "args": ["-m", "qelectrotech_mcp.server"],
        "env": {"QET_ALLOWED_ROOTS": str(project), **{
            name: os.environ[name] for name in ["QET_BINARY", "QET_ELEMENTS_ROOT", "QET_TITLEBLOCKS_ROOT"] if name in os.environ}},
    }}}


def main():
    parser = argparse.ArgumentParser(description="Gridline — Grid Society single-line diagrams")
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("doctor"); d.add_argument("--json", action="store_true")
    sub.add_parser("integrations")
    for name in ["new", "check", "render", "demo", "smoke", "mcp-config"]:
        p = sub.add_parser(name); p.add_argument("project")
        if name == "new": p.add_argument("--backend", default="qelectrotech", choices=list(BACKENDS))
        if name == "demo": p.add_argument("--no-render", action="store_true")
        if name == "mcp-config": p.add_argument("--format", choices=["json", "toml"], default="json")
    args = parser.parse_args()
    try:
        if args.command == "doctor":
            report = doctor(); print_doctor(report, args.json)
            return 0 if report["status"] == "preflight_passed" else 1
        if args.command == "integrations":
            print(json.dumps(BACKENDS, indent=2)); return 0
        if args.command == "new":
            print(new(args.project, args.backend))
        elif args.command == "check":
            result = check(args.project); print(json.dumps(result, indent=2)); return int(bool(result["errors"]))
        elif args.command == "render":
            from .compose import render
            print(render(args.project))
        elif args.command in {"demo", "smoke"}:
            from .demo import build
            print(asyncio.run(build(args.project, render_pdf=not getattr(args, "no_render", False), require_desktop=args.command == "smoke")))
        elif args.command == "mcp-config":
            config = mcp_config(args.project)
            if args.format == "json": print(json.dumps(config, indent=2))
            else:
                server = config["mcpServers"]["gridline-qelectrotech"]
                print('[mcp_servers.gridline-qelectrotech]')
                print('command = ' + json.dumps(server["command"]))
                print('args = ' + json.dumps(server["args"]))
                print('[mcp_servers.gridline-qelectrotech.env]')
                for key, value in server["env"].items(): print(key + ' = ' + json.dumps(value))
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Gridline: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
