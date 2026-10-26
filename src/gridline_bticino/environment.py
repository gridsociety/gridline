"""Read-only local prerequisites; never claims a browser login is active."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import os
from gridline.environment import documentor_command,DOCUMENTOR_REVISION


def doctor(*,probe=True):
    checks=[]
    def add(name,ok,detail,remedy):
        checks.append({'name':name,'ok':bool(ok),'detail':detail,'remedy':'' if ok else remedy})
    add('python',sys.version_info>=(3,12),sys.version.split()[0],'Install Python 3.12+')
    for name in ['mcp','fitz']:
        add(name,importlib.util.find_spec(name) is not None,name,'uv sync --frozen')
    cmd=documentor_command()
    add('documentor',cmd and Path(cmd).is_file(),cmd or 'missing','Read docs/installation.md; set GRIDLINE_DOCUMENTOR if needed')
    if cmd and probe:
        try:
            r=subprocess.run([cmd,'doctor'],capture_output=True,text=True,encoding="utf-8",env={**os.environ,"PYTHONUTF8":"1"},timeout=60)
            add('documentor-browser',r.returncode==0,r.stdout+r.stderr,'Run documentor install-browser and doctor')
        except (OSError,subprocess.TimeoutExpired) as exc:
            add('documentor-browser',False,str(exc),'Check Documentor and Chromium')
    return {'status':'preflight_passed' if all(c['ok'] for c in checks) else 'missing_requirements',
            'checks':checks,'documentor_reference_revision':DOCUMENTOR_REVISION,
            'tisystem_login_verified':False,'mcp_session_verified':False,'render_verified':False,
            'acquisition':'https://tisystem.bticino.it/ — personal authenticated browser session; no stored credentials',
            'next_step':'Acquire calculated native TiSystem exports, prepare/inspect, render and visually review. Preflight does not verify browser authentication.'}
