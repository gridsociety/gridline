#!/usr/bin/env python3
"""Run even before uv sync; do not change the user's environment."""
import sys
from pathlib import Path

if sys.version_info < (3, 12):
    raise SystemExit("Gridline richiede Python 3.12+. Installare Python/uv, poi eseguire uv sync --frozen.")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gridline.environment import doctor, print_doctor

report = doctor()
print_doctor(report, "--json" in sys.argv)
raise SystemExit(0 if report["status"] == "preflight_passed" else 1)
