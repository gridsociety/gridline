"""Discover QET on macOS, Windows and Linux without machine-specific paths."""
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


def discover(*, environ=None, platform=None, which=None):
    env = os.environ if environ is None else environ
    platform = sys.platform if platform is None else platform
    which = shutil.which if which is None else which
    binary_candidates = []
    resource_candidates = []
    if platform == "darwin":
        for app in [Path("/Applications/QElectroTech.app"), Path.home() / "Applications/QElectroTech.app"]:
            binary_candidates.append(app / "Contents/MacOS/qelectrotech")
            resource_candidates.append(app / "Contents/Resources")
    elif platform == "win32":
        for key in ["ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"]:
            if env.get(key):
                for name in ["QElectroTech", "qelectrotech"]:
                    root = Path(env[key]) / name
                    binary_candidates.extend([root / "qelectrotech.exe", root / "bin/qelectrotech.exe"])
                    resource_candidates.extend([root, root / "share/qelectrotech"])
    else:
        resource_candidates.extend([Path("/usr/share/qelectrotech"), Path("/usr/local/share/qelectrotech")])
    on_path = which("qelectrotech")
    if on_path:
        binary_candidates.insert(0, Path(on_path))
        resource_candidates.append(Path(on_path).resolve().parent.parent / "share/qelectrotech")
    binary = (Path(env["QET_BINARY"]).expanduser() if env.get("QET_BINARY") else
              next((p for p in binary_candidates if p.is_file()), None))
    def resources(name, key):
        if env.get(key):
            return Path(env[key]).expanduser()
        return next((p / name for p in resource_candidates if (p / name).is_dir()), None)
    return {
        "binary": binary,
        "elements": resources("elements", "QET_ELEMENTS_ROOT"),
        "titleblocks": resources("titleblocks", "QET_TITLEBLOCKS_ROOT"),
    }
