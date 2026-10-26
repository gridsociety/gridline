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


def mcp_config(project, backend=None):
    project = Path(project).expanduser().resolve()
    if backend is None and (project/'gridline.json').is_file():
        backend=json.loads((project/'gridline.json').read_text(encoding="utf-8")).get('backend')
    if backend == 'bticino':
        return {'mcpServers':{'gridline-bticino':{
            'command':str(Path(sys.executable).absolute()),'args':['-m','gridline_bticino.server'],
            'env':{'BTICINO_ALLOWED_ROOTS':str(project),'PYTHONUTF8':'1',**{k:os.environ[k] for k in ['GRIDLINE_DOCUMENTOR'] if k in os.environ}}}}}
    if backend == 'combined':
        from .workflows import children
        servers={}
        for child in children(project).values():servers.update(mcp_config(child)['mcpServers'])
        return {'mcpServers':servers}
    return {"mcpServers": {"gridline-qelectrotech": {
        "command": str(Path(sys.executable).absolute()),
        "args": ["-m", "qelectrotech_mcp.server"],
        "env": {"QET_ALLOWED_ROOTS": str(project), "PYTHONUTF8": "1", **{
            name: os.environ[name] for name in ["QET_BINARY", "QET_ELEMENTS_ROOT", "QET_TITLEBLOCKS_ROOT"] if name in os.environ}},
    }}}


def main():
    parser = argparse.ArgumentParser(description="Gridline — Grid Society single-line diagrams")
    sub = parser.add_subparsers(dest="command", required=True)
    d = sub.add_parser("doctor"); d.add_argument("--json", action="store_true"); d.add_argument('--backend',choices=list(BACKENDS),default='qelectrotech')
    sub.add_parser("integrations")
    sub.add_parser('workflows')
    imp=sub.add_parser('bticino-import',help='Import a verified local native-export case into a new workspace')
    imp.add_argument('source_root');imp.add_argument('destination');imp.add_argument('--request',required=True)
    prep=sub.add_parser('bticino-prepare');prep.add_argument('project')
    smoke=sub.add_parser('bticino-smoke');smoke.add_argument('project')
    ver=sub.add_parser('bticino-verify');ver.add_argument('project');ver.add_argument('package')
    for name in ["new", "check", "render", "demo", "smoke", "mcp-config"]:
        p = sub.add_parser(name); p.add_argument("project")
        if name == "new":
            group=p.add_mutually_exclusive_group()
            group.add_argument("--backend", choices=list(BACKENDS))
            group.add_argument('--workflow',choices=['general','equipment','combined'])
        if name == "demo": p.add_argument("--no-render", action="store_true")
        if name == "render":p.add_argument('--format',choices=['A3','A4'],action='append')
        if name == "mcp-config":
            p.add_argument("--format", choices=["json", "toml"], default="json")
            p.add_argument('--backend',choices=list(BACKENDS))
    args = parser.parse_args()
    try:
        if args.command == "doctor":
            report = doctor(backend=args.backend); print_doctor(report, args.json)
            return 0 if report["status"] == "preflight_passed" else 1
        if args.command == "integrations":
            print(json.dumps(BACKENDS, indent=2)); return 0
        if args.command == 'workflows':
            from .workflows import WORKFLOWS
            print(json.dumps(WORKFLOWS,indent=2,ensure_ascii=False));return 0
        if args.command == "new":
            if args.workflow:
                from .workflows import new_workflow
                print(new_workflow(args.project,args.workflow))
            else:print(new(args.project, args.backend or 'qelectrotech'))
        elif args.command == "check":
            result = check(args.project); print(json.dumps(result, indent=2)); return int(bool(result["errors"]))
        elif args.command == "render":
            backend=json.loads((Path(args.project)/'gridline.json').read_text(encoding="utf-8")).get('backend')
            if backend=='bticino':
                from gridline_bticino.integration import render
                print(json.dumps(render(args.project,args.format),indent=2))
            elif backend=='qelectrotech':
                if args.format:raise ValueError('--format is currently specific to BTicino')
                from .compose import render
                print(render(args.project))
            elif backend=='combined':
                if args.format:raise ValueError('Use child workspace to select a sheet format')
                from .workflows import render_combined
                print(json.dumps(render_combined(args.project),indent=2))
            else:raise ValueError('Unknown backend')
        elif args.command=='bticino-import':
            from gridline_bticino.integration import import_case
            print(import_case(args.source_root,args.request,args.destination))
        elif args.command=='bticino-prepare':
            from gridline_bticino.integration import prepare
            print(json.dumps(prepare(args.project),indent=2,ensure_ascii=False))
        elif args.command=='bticino-verify':
            from gridline_bticino.integration import verify
            print(json.dumps(verify(args.project,args.package),indent=2))
        elif args.command=='bticino-smoke':
            from gridline_bticino.smoke import run
            report=asyncio.run(run(args.project))
            print(json.dumps({k:v for k,v in report.items() if k!='trace'},indent=2))
        elif args.command in {"demo", "smoke"}:
            from .demo import build
            print(asyncio.run(build(args.project, render_pdf=not getattr(args, "no_render", False), require_desktop=args.command == "smoke")))
        elif args.command == "mcp-config":
            config = mcp_config(args.project,args.backend)
            if args.format == "json": print(json.dumps(config, indent=2))
            else:
                for name,server in config['mcpServers'].items():
                    print('[mcp_servers.'+name+']')
                    print('command = ' + json.dumps(server["command"]))
                    print('args = ' + json.dumps(server["args"]))
                    print('[mcp_servers.'+name+'.env]')
                    for key, value in server["env"].items(): print(key + ' = ' + json.dumps(value))
        return 0
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print(f"Gridline: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
