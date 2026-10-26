"""Workspace contract shared by integrations, without a universal circuit schema."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET

from .paths import RESOURCES, project_file

BACKENDS = {"qelectrotech": "available", "bticino": "available-native-exports"}


def new(destination, backend="qelectrotech"):
    if backend == "bticino":
        from gridline_bticino.integration import new as new_bticino
        return new_bticino(destination)
    if BACKENDS.get(backend) != "available":
        raise ValueError(f"Integration {backend!r} is not implemented; see integrations/{backend}/README.md")
    project = Path(destination).resolve()
    project.mkdir(parents=True, exist_ok=False)
    for name in ["source", "inputs", "variables", "notes", "out", "published", "qa", "static/unifilar", "templates/drawings"]:
        (project / name).mkdir(parents=True)
    today = date.today().isoformat()
    metadata = {
        "title": "Nuovo unifilare", "client": "CLIENTE DA DEFINIRE", "site": "SITO DA DEFINIRE",
        "code": "GS-DEMO-SLD-001", "slug": "single-line", "revision": "R00", "date": today,
        "status": "DRAFT", "revisions": [{"revision": "R00", "date": today, "description": "Prima bozza"}],
        "pages": [],
    }
    write_json(project / "variables/drawing-set.json", metadata)
    write_json(project / "gridline.json", {"schema_version": 1, "backend": backend, "gridline_version": "0.1.0"})
    for name in ["context", "decisions", "status", "attachments"]:
        (project / "notes" / f"{name}.md").write_text(f"# {name}\n\nDa compilare. Nessun dato di esempio è un requisito di progetto.\n", encoding="utf-8")
    (project / "documentor.toml").write_text('[documentor]\ntemplates = "templates"\nvariables = "variables"\nstatic = "static"\nmetadata = "template_metadata.json"\noutput = "out"\n', encoding="utf-8")
    shutil.copy2(RESOURCES / "templates/single-line-set.html", project / "templates/drawings/project-single-line.html")
    write_json(project / "template_metadata.json", {"drawings/project-single-line.html": {
        "default_variables_set": "single-line-sheets", "page_size": "A3", "linked_documents": [],
    }})
    (project / "README.md").write_text("# Unifilare\n\nAprire con l'agente e leggere le skill Gridline. Compilare notes/ e variables/drawing-set.json.\n", encoding="utf-8")
    return project


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def check(project):
    project = Path(project).resolve()
    try:
        config=json.loads((project/'gridline.json').read_text(encoding="utf-8"))
        if config.get('backend')=='combined':
            from .workflows import children
            results={k:check(v) for k,v in children(project).items()}
            return {'errors':[key+': '+e for key,res in results.items() for e in res['errors']],
                    'electrical_compliance_verified':False,'coordination_review':'OPEN','children':results}
        if config.get('backend')=='bticino':
            from gridline_bticino.integration import check as check_bticino
            return check_bticino(project)
        if config.get('backend')!='qelectrotech':
            return {'errors':['Unknown backend'],'electrical_compliance_verified':False}
    except (OSError,ValueError):
        pass  # Existing QET validation reports malformed/missing files below.
    errors = []
    required = ["gridline.json", "documentor.toml", "template_metadata.json", "variables/drawing-set.json"]
    required += [f"notes/{n}.md" for n in ["context", "decisions", "status", "attachments"]]
    for relative in required:
        if not (project / relative).is_file():
            errors.append(f"Missing {relative}")
    if errors:
        return {"errors": errors, "electrical_compliance_verified": False}
    try:
        meta = json.loads((project / "variables/drawing-set.json").read_text(encoding="utf-8"))
        for key in ["title", "client", "site", "code", "slug", "revision", "date", "revisions", "pages"]:
            if not meta.get(key):
                errors.append(f"Missing or empty {key}")
        for key in ["code", "slug", "revision"]:
            if not re.fullmatch(r"[A-Za-z0-9_-]+", str(meta.get(key, ""))):
                errors.append(f"Unsafe filename field {key}")
        saw_detail = False
        for page in meta.get("pages", []):
            saw_detail = saw_detail or page.get("kind") == "detail"
            if saw_detail and page.get("kind") == "general":
                errors.append("General sheets must precede details")
            if page.get("kind") not in {"general", "detail"} or not page.get("title"):
                errors.append("Each page needs title and kind general/detail")
            if not 420 <= float(page.get("width_mm", 420)) <= 2000:
                errors.append("Sheet width must be 420..2000 mm for this cartouche")
            asset = project_file(project, page["source"])
            if not asset.is_file() or asset.suffix.lower() not in {".svg", ".pdf"}:
                errors.append(f"Missing or unsupported view: {page['source']}")
            elif asset.suffix.lower() == ".svg":
                root = ET.parse(asset).getroot()
                for node in root.iter():
                    if node.tag.split("}")[-1] in {"script", "foreignObject"}:
                        errors.append(f"Active SVG content in {page['source']}")
                    for key, value in node.attrib.items():
                        if key.split("}")[-1] == "href" and not value.startswith(("#", "data:image/")):
                            errors.append(f"External SVG resource in {page['source']}")
        for qet in (project / "source").glob("*.qet"):
            root = ET.parse(qet).getroot()
            if root.tag != "project":
                errors.append(f"Invalid QET root: {qet.name}")
            uuids = set()
            for diagram in root.findall("diagram"):
                ids = [t.get("id") for t in diagram.findall("elements/element/terminals/terminal")]
                if len(ids) != len(set(ids)) or None in ids:
                    errors.append(f"Invalid terminal IDs: {qet.name}")
                for element in diagram.findall("elements/element"):
                    uid = element.get("uuid")
                    if not uid or uid in uuids:
                        errors.append(f"Invalid element UUID: {qet.name}")
                    uuids.add(uid)
                for conductor in diagram.findall("conductors/conductor"):
                    a, b = conductor.get("terminal1"), conductor.get("terminal2")
                    if a not in ids or b not in ids or a == b:
                        errors.append(f"Unresolved or self-connected conductor: {qet.name}")
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as exc:
        errors.append(str(exc))
    return {"errors": errors, "electrical_compliance_verified": False}


def artifact_manifest(project, *, native_visual=False):
    project = Path(project).resolve()
    paths = list((project / "source").glob("*")) + list((project / "out").glob("*"))
    return {"schema_version": 1, "backend": "qelectrotech", "status": "DRAFT",
            "native_qet_visual_verified": native_visual, "electrical_compliance_verified": False,
            "artifacts": [{"path": str(p.relative_to(project)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                          for p in sorted(paths) if p.is_file() and ".bak-" not in p.name]}
