"""Read-only preflight. Works before third-party dependencies are installed."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from qelectrotech_mcp.installation import discover

DOCUMENTOR_REVISION = "22e215a70209ca48aa3a94c9e9a63341b143aa49"


def documentor_command():
    override = os.environ.get("GRIDLINE_DOCUMENTOR")
    return str(Path(override).expanduser()) if override else shutil.which("documentor")


def doctor(*, probe=True, backend='qelectrotech'):
    if backend == 'bticino':
        from gridline_bticino.environment import doctor as bt_doctor
        return bt_doctor(probe=probe)
    qet = discover()
    command = documentor_command()
    checks = []
    def add(name, ok, detail, remedy):
        checks.append({"name": name, "ok": bool(ok), "detail": detail, "remedy": "" if ok else remedy})
    add("python", sys.version_info >= (3, 12), sys.version.split()[0], "Installare Python 3.12+; ambiente verificato: Python 3.13.")
    for name in ["mcp", "fitz"]:
        add(name, importlib.util.find_spec(name) is not None, name,
            "Dalla radice del checkout: uv sync --frozen")
    add("qelectrotech", qet["binary"] and qet["binary"].is_file(), str(qet["binary"] or "assente"),
        "Installare QElectroTech da https://qelectrotech.org/download.html oppure impostare QET_BINARY al file eseguibile.")
    add("qet-library", qet["elements"] and qet["elements"].is_dir(), str(qet["elements"] or "assente"),
        "Installare la collezione QET oppure impostare QET_ELEMENTS_ROOT alla cartella elements.")
    add("documentor", command and Path(command).is_file(), command or "assente",
        "Seguire docs/installation.md: accesso a gridsociety/documentor, revisione fissata; oppure GRIDLINE_DOCUMENTOR al comando esistente.")
    if command and probe:
        try:
            result = subprocess.run([command, "doctor"], capture_output=True, encoding="utf-8",
                                    env={**os.environ, "PYTHONUTF8": "1"}, timeout=60)
            add("documentor-browser", result.returncode == 0, (result.stdout + result.stderr).strip(),
                "Usare documentor install-browser e ripetere documentor doctor; vedere docs/installation.md.")
        except (OSError, subprocess.TimeoutExpired) as exc:
            add("documentor-browser", False, str(exc), "Controllare eseguibile Documentor, Chromium e permessi per il browser locale.")
    return {
        "status": "preflight_passed" if all(c["ok"] for c in checks) else "missing_requirements",
        "checks": checks,
        "documentor_reference_revision": DOCUMENTOR_REVISION,
        "mcp_session_verified": False,
        "render_verified": False,
        "next_step": "gridline smoke CARTELLA_NUOVA; poi ispezione PDF e apertura del QET nativo. Il preflight non certifica l'ambiente.",
    }


def print_doctor(report, as_json=False):
    if as_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        for check in report["checks"]:
            print(f"{'OK' if check['ok'] else 'MISSING'} {check['name']}: {check['detail']}")
            if check["remedy"]:
                print(f"  -> {check['remedy']}")
        print(report["next_step"])
