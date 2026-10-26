"""The final PDF is always rendered by Documentor; no alternate renderer."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .environment import documentor_command, DOCUMENTOR_REVISION
from .workspace import write_json


def generate(project, book, meta, pages, out):
    import fitz

    project = Path(project).resolve()
    sheets = []
    for i, page in enumerate(book):
        asset = f"unifilar/sheet-{i+1:02d}.svg"
        svg = page.get_svg_image(text_as_path=False).replace('font-family="Nimbus Sans"', 'font-family="Arial, Helvetica, sans-serif"')
        (project / "static" / asset).write_text(svg, encoding="utf-8")
        sheets.append({"number": i+1, "title": pages[i]["title"], "width_mm": page.rect.width*25.4/72,
                       "height_mm": page.rect.height*25.4/72, "svg_path": asset})
    variables = {"sender": {"company_name": "GRID SOCIETY S.R.L."}, "customer": {"company_name": meta["client"]},
                 "document": {key: meta[key] for key in ["date", "title", "code", "revision"]}, "sheets": sheets}
    variables_path = project / "variables/single-line-sheets.json"
    write_json(variables_path, variables)
    command = documentor_command()
    if not command:
        raise RuntimeError("Documentor missing: run gridline doctor and read docs/installation.md")
    out = Path(out).resolve()
    with tempfile.TemporaryDirectory(prefix=".gridline-render-", dir=out.parent) as temp:
        pending = Path(temp) / out.name
        cmd = [command, "render", "drawings/project-single-line.html", "--vars", str(variables_path),
               "--workspace", str(project), "--draft", "--out", str(pending)]
        result = subprocess.run(cmd, encoding="utf-8", capture_output=True,
                                env={**os.environ, "PYTHONUTF8": "1"}, timeout=180)
        (project / "out/documentor-render.log").write_text(result.stdout + "\n" + result.stderr, encoding="utf-8")
        if result.returncode:
            raise RuntimeError("Documentor failed. See out/documentor-render.log. No PDF fallback.")
        with fitz.open(pending) as pdf:
            if len(pdf) != len(sheets):
                raise RuntimeError(f"Documentor returned {len(pdf)} pages; expected {len(sheets)}")
            if "Documentor" not in pdf.metadata.get("producer", ""):
                raise RuntimeError("Unexpected PDF producer")
            for page, sheet in zip(pdf, sheets):
                if abs(page.rect.width*25.4/72-sheet["width_mm"]) > .6 or abs(page.rect.height*25.4/72-sheet["height_mm"]) > .6:
                    raise RuntimeError("Documentor page dimensions differ from the drawing set")
        os.replace(pending, out)
    write_json(project / "out/documentor-provenance.json", {
        "generator": "Documentor", "command": cmd, "reference_revision": DOCUMENTOR_REVISION,
        "output_sha256": hashlib.sha256(out.read_bytes()).hexdigest(), "pages": len(sheets),
        "time_utc": datetime.now(timezone.utc).isoformat(), "status": "local-draft",
        "variables_sha256": hashlib.sha256(variables_path.read_bytes()).hexdigest(),
    })
    return fitz.open(out)
