from __future__ import annotations

import csv
import html
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import sys
import unicodedata
import uuid
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


from .installation import discover
from gridline.paths import RESOURCES

_INSTALLATION = discover()
BINARY = _INSTALLATION["binary"]
ELEMENTS_ROOT = _INSTALLATION["elements"]
TITLEBLOCKS_ROOT = _INSTALLATION["titleblocks"]
BUNDLED_SYMBOLS = RESOURCES / "symbols"
DEFAULT_ALLOWED_ROOTS = (Path.cwd().resolve(),)

READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=False)

mcp = FastMCP(
    "QElectroTechMCP",
    instructions=(
        "Edit QElectroTech .qet electrical projects through explicit tools. "
        "Inspect a project and search/inspect symbols before inserting them. "
        "Use UUIDs returned by tools for edits and connections. Generate an SVG preview after layout changes. "
        "Writes create timestamped backups by default. The SVG preview is approximate and is not a substitute "
        "for final validation inside QElectroTech or by a qualified electrical designer."
    ),
)


def _allowed_roots() -> tuple[Path, ...]:
    raw = os.environ.get("QET_ALLOWED_ROOTS", "")
    roots = [Path(p).expanduser().resolve() for p in raw.split(os.pathsep) if p]
    return tuple(roots) if roots else DEFAULT_ALLOWED_ROOTS


def _safe_path(
    value: str,
    *,
    must_exist: bool = False,
    suffix: str | None = None,
    allow_qet_resources: bool = False,
) -> Path:
    path = Path(value).expanduser().resolve()
    allowed = any(path == root or root in path.parents for root in _allowed_roots())
    resource_allowed = allow_qet_resources and any(
        path == root or root in path.parents for root in (ELEMENTS_ROOT, TITLEBLOCKS_ROOT, BUNDLED_SYMBOLS) if root is not None
    )
    if not (allowed or resource_allowed):
        raise ValueError(f"Path outside allowed roots: {path}")
    if must_exist and not path.exists():
        raise FileNotFoundError(path)
    if suffix and path.suffix.lower() != suffix.lower():
        raise ValueError(f"Expected a {suffix} file: {path}")
    return path


def _parse_project(path: str) -> tuple[Path, ET.ElementTree, ET.Element]:
    project_path = _safe_path(path, must_exist=True, suffix=".qet")
    try:
        tree = ET.parse(project_path)
    except ET.ParseError as exc:
        raise ValueError(f"Invalid QElectroTech XML: {exc}") from exc
    root = tree.getroot()
    if root.tag != "project":
        raise ValueError(f"Expected <project>, found <{root.tag}>")
    return project_path, tree, root


def _indent(root: ET.Element) -> None:
    ET.indent(root, space="    ")


def _write_tree(path: Path, tree: ET.ElementTree, *, backup: bool = True) -> str | None:
    backup_path: Path | None = None
    if backup and path.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        backup_path = path.with_suffix(path.suffix + f".bak-{stamp}")
        shutil.copy2(path, backup_path)
    _indent(tree.getroot())
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        tree.write(temp_path, encoding="utf-8", xml_declaration=True)
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)
    return str(backup_path) if backup_path else None


def _brace_uuid() -> str:
    return "{" + str(uuid.uuid4()) + "}"


def _normalise(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _as_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(value) if value is not None else default
    except ValueError:
        return default


def _folio(root: ET.Element, selector: int | str = 1) -> ET.Element:
    diagrams = root.findall("diagram")
    if isinstance(selector, int):
        if selector < 1 or selector > len(diagrams):
            raise ValueError(f"Folio {selector} not found; project has {len(diagrams)} folios")
        return diagrams[selector - 1]
    for diagram in diagrams:
        if diagram.get("title") == selector or diagram.get("uuid") == selector:
            return diagram
    raise ValueError(f"Folio not found: {selector}")


def _element(diagram: ET.Element, element_uuid: str) -> ET.Element:
    elements = diagram.find("elements")
    if elements is not None:
        for item in elements.findall("element"):
            if item.get("uuid") == element_uuid:
                return item
    raise ValueError(f"Element not found: {element_uuid}")


def _information(item: ET.Element) -> dict[str, str]:
    result: dict[str, str] = {}
    node = item.find("elementInformations")
    if node is not None:
        for child in node.findall("elementInformation"):
            result[child.get("name", "")] = child.text or ""
    return result


def _set_information(item: ET.Element, values: dict[str, str]) -> None:
    node = item.find("elementInformations")
    if node is None:
        node = ET.SubElement(item, "elementInformations")
    existing = {child.get("name", ""): child for child in node.findall("elementInformation")}
    for key, value in values.items():
        if not key or not re.fullmatch(r"[A-Za-z0-9_.:-]+", key):
            raise ValueError(f"Invalid information key: {key!r}")
        child = existing.get(key)
        if child is None:
            child = ET.SubElement(node, "elementInformation", {"show": "1", "name": key})
        child.text = str(value)
    dynamics = item.find("dynamic_texts")
    if dynamics is not None:
        for dynamic in dynamics.findall("dynamic_elmt_text"):
            info_name = dynamic.findtext("info_name")
            if info_name in values:
                text = dynamic.find("text")
                if text is None:
                    text = ET.SubElement(dynamic, "text")
                text.text = str(values[info_name])


def _sequence(parent: ET.Element) -> None:
    seq = ET.SubElement(parent, "sequentialNumbers")
    for name in ("unit", "unitFolio", "ten", "tenFolio", "hundred", "hundredFolio"):
        ET.SubElement(seq, name)


def _default_conductor_attrs() -> dict[str, str]:
    return {
        "x": "0", "y": "0", "condsize": "1", "cable": "", "onetextperfolio": "1",
        "vertical-alignment": "AlignLeft", "horizrotatetext": "0", "bicolor": "false",
        "bus": "", "dash-size": "2", "numsize": "7", "horizontal-alignment": "AlignTop",
        "function": "", "conductor_color": "", "conductor_section": "", "text_color": "#000000",
        "color2": "#000000", "tension_protocol": "", "displaytext": "1", "formula": "",
        "vertirotatetext": "270", "freezeLabel": "false", "num": "", "type": "multi",
    }


def _new_project_tree(title: str, folio_title: str, author: str) -> ET.ElementTree:
    root = ET.Element("project", {"title": title, "version": "0.100.0"})
    properties = ET.SubElement(root, "properties")
    for key, value in (("saveddate", datetime.now().strftime("%d/%m/%Y")), ("savedtime", datetime.now().strftime("%H:%M"))):
        node = ET.SubElement(properties, "property", {"show": "1", "name": key})
        node.text = value
    defaults = ET.SubElement(root, "newdiagrams")
    ET.SubElement(defaults, "border", {"rowsize": "80", "rows": "9", "displaycols": "true", "cols": "18", "colsize": "60", "displayrows": "true"})
    ET.SubElement(defaults, "inset", {"titleblocktemplate": "default", "titleblocktemplateCollection": "common", "displayAt": "bottom", "folio": "%id", "indexrev": "", "plant": "", "date": "null", "filename": "", "author": author, "locmach": "", "title": "", "version": "", "auto_page_num": ""})
    ET.SubElement(defaults, "conductors", _default_conductor_attrs())
    ET.SubElement(defaults, "report", {"label": "%f-%l%c"})
    ET.SubElement(defaults, "xrefs")
    ET.SubElement(defaults, "conductors_autonums", {"freeze_new_conductors": "false", "current_autonum": ""})
    ET.SubElement(defaults, "folio_autonums")
    ET.SubElement(defaults, "element_autonums", {"freeze_new_elements": "false", "current_autonum": ""})
    diagram = ET.SubElement(root, "diagram", {
        "freezeNewElement": "false", "freezeNewConductor": "false", "titleblocktemplate": "default",
        "titleblocktemplateCollection": "common", "cols": "18", "rows": "9", "colsize": "60",
        "rowsize": "80", "displaycols": "true", "displayrows": "true", "displayAt": "bottom",
        "folio": "%id", "version": "0.100.0", "indexrev": "", "date": datetime.now().strftime("%Y%m%d"),
        "author": author, "height": "740", "title": folio_title, "filename": "", "order": "1",
        "locmach": "", "plant": "", "auto_page_num": "", "uuid": _brace_uuid(),
    })
    ET.SubElement(diagram, "properties")
    ET.SubElement(diagram, "defaultconductor", _default_conductor_attrs())
    ET.SubElement(diagram, "elements")
    ET.SubElement(diagram, "conductors")
    ET.SubElement(root, "collection")
    return ET.ElementTree(root)


@lru_cache(maxsize=1)
def _symbol_index() -> tuple[dict[str, Any], ...]:
    records: list[dict[str, Any]] = []
    if ELEMENTS_ROOT is None or not ELEMENTS_ROOT.exists():
        return tuple()
    for path in ELEMENTS_ROOT.rglob("*.elmt"):
        try:
            definition = ET.parse(path).getroot()
        except (ET.ParseError, OSError):
            continue
        names = {n.get("lang", ""): n.text or "" for n in definition.findall("./names/name")}
        description = definition.find("description")
        terminals = len(description.findall("terminal")) if description is not None else 0
        relative = path.relative_to(ELEMENTS_ROOT).as_posix()
        search = _normalise(" ".join((relative, *names.values())))
        records.append({
            "path": str(path), "relative_path": relative, "names": names,
            "width": _as_float(definition.get("width")), "height": _as_float(definition.get("height")),
            "terminals": terminals, "search": search,
        })
    return tuple(records)


def _definition_from_instance(root: ET.Element, item: ET.Element) -> ET.Element | None:
    kind = item.get("type", "")
    if kind.startswith("embed://"):
        parts = kind.removeprefix("embed://").split("/")
        current = root.find("collection")
        if current is None:
            return None
        for part in parts[:-1]:
            current = next((c for c in current.findall("category") if c.get("name") == part), None)
            if current is None:
                return None
        embedded = next((c for c in current.findall("element") if c.get("name") == parts[-1]), None)
        return embedded.find("definition") if embedded is not None else None
    for prefix in ("common://", "custom://"):
        if kind.startswith(prefix) and ELEMENTS_ROOT is not None:
            candidate = (ELEMENTS_ROOT / kind.removeprefix(prefix)).resolve()
            if not candidate.is_relative_to(ELEMENTS_ROOT.resolve()):
                return None
            if candidate.exists():
                try:
                    return ET.parse(candidate).getroot()
                except ET.ParseError:
                    return None
    return None


def _embed_definition(root: ET.Element, symbol_path: Path) -> str:
    definition = ET.parse(symbol_path).getroot()
    if definition.tag != "definition":
        raise ValueError(f"Not a QElectroTech element definition: {symbol_path}")
    try:
        relative = symbol_path.relative_to(ELEMENTS_ROOT).as_posix()
    except (ValueError, TypeError):
        digest = hashlib.sha256(symbol_path.read_bytes()).hexdigest()[:16]
        relative = f"{digest}/{symbol_path.name}"
    parts = ["import", *relative.split("/")]
    collection = root.find("collection")
    if collection is None:
        collection = ET.SubElement(root, "collection")
    current = collection
    for part in parts[:-1]:
        child = next((c for c in current.findall("category") if c.get("name") == part), None)
        if child is None:
            child = ET.SubElement(current, "category", {"name": part})
        current = child
    filename = parts[-1]
    embedded = next((c for c in current.findall("element") if c.get("name") == filename), None)
    if embedded is None:
        embedded = ET.SubElement(current, "element", {"name": filename})
        embedded.append(ET.fromstring(ET.tostring(definition, encoding="utf-8")))
    return "embed://" + "/".join(parts)


def _terminal_instance(source: ET.Element, terminal_id: int) -> ET.Element:
    orientation_map = {"n": "0", "e": "1", "s": "2", "w": "3"}
    direction = source.get("orientation", "n").lower()
    x, y = _as_float(source.get("x")), _as_float(source.get("y"))
    if direction == "n": y += 4
    elif direction == "s": y -= 4
    elif direction == "e": x -= 4
    elif direction == "w": x += 4
    return ET.Element("terminal", {
        "x": f"{x:g}", "y": f"{y:g}", "name": source.get("name", "_"),
        "orientation": orientation_map.get(direction, "0"), "id": str(terminal_id),
        "number": source.get("number", "_"), "nameHidden": "0",
    })


def _dynamic_texts(definition: ET.Element, info: dict[str, str]) -> ET.Element:
    output = ET.Element("dynamic_texts")
    description = definition.find("description")
    if description is None:
        return output
    for source in description.findall("dynamic_text"):
        attrs = dict(source.attrib)
        attrs["uuid"] = _brace_uuid()
        target = ET.SubElement(output, "dynamic_elmt_text", attrs)
        text_value = source.findtext("text") or ""
        info_name = source.findtext("info_name")
        if info_name:
            text_value = info.get(info_name, text_value)
        text = ET.SubElement(target, "text")
        text.text = text_value
        if info_name:
            node = ET.SubElement(target, "info_name")
            node.text = info_name
    for source in description.findall("input"):
        tag = source.get("tagg", "label")
        value = info.get(tag, source.get("text", ""))
        target = ET.SubElement(output, "dynamic_elmt_text", {
            "rotation": "0", "x": source.get("x", "0"), "y": source.get("y", "0"),
            "Halignment": "AlignLeft", "Valignment": "AlignTop", "frame": "false",
            "keep_visual_rotation": "true", "text_width": "-1", "uuid": _brace_uuid(),
            "text_from": "ElementInfo", "font": f"Sans Serif,{source.get('size', '9')},-1,5,50,0,0,0,0,0,Condensed",
        })
        text = ET.SubElement(target, "text"); text.text = value
        name = ET.SubElement(target, "info_name"); name.text = tag
    if info.get("label") and not any(t.findtext("info_name") == "label" for t in output):
        # Some collection symbols contain geometry only. Keep the label in the
        # native QET, not merely as an annotation on a derived SVG.
        right = _as_float(definition.get("width")) - _as_float(definition.get("hotspot_x"))
        target = ET.SubElement(output, "dynamic_elmt_text", {
            "rotation": "0", "x": f"{right+8:g}", "y": "0",
            "Halignment": "AlignLeft", "Valignment": "AlignTop", "frame": "false",
            "keep_visual_rotation": "true", "text_width": "-1", "uuid": _brace_uuid(),
            "text_from": "ElementInfo", "font": "Sans Serif,9,-1,5,50,0,0,0,0,0,Condensed",
        })
        ET.SubElement(target, "text").text = info["label"]
        ET.SubElement(target, "info_name").text = "label"
    return output


def _find_terminal(diagram: ET.Element, element_uuid: str, terminal_index: int) -> ET.Element:
    item = _element(diagram, element_uuid)
    terminals = item.findall("./terminals/terminal")
    if terminal_index < 1 or terminal_index > len(terminals):
        raise ValueError(f"Terminal {terminal_index} not found on {element_uuid}; available: 1..{len(terminals)}")
    return terminals[terminal_index - 1]


def _terminal_world(item: ET.Element, terminal: ET.Element) -> tuple[float, float]:
    x, y = _as_float(terminal.get("x")), _as_float(terminal.get("y"))
    angle = int(item.get("orientation", "0")) * 90
    rad = math.radians(angle)
    rx = x * math.cos(rad) - y * math.sin(rad)
    ry = x * math.sin(rad) + y * math.cos(rad)
    return _as_float(item.get("x")) + rx, _as_float(item.get("y")) + ry


@mcp.tool(annotations=READ_ONLY)
def health_check() -> dict[str, Any]:
    """Report the local QElectroTech installation, symbol library and MCP capabilities."""
    version = None
    if BINARY and sys.platform == "darwin":
        plist = BINARY.parent.parent / "Info.plist"
        if plist.is_file():
            import plistlib
            with plist.open("rb") as handle:
                version = plistlib.load(handle).get("CFBundleShortVersionString")
    return {
        "mcp_version": "0.2.0", "installed": bool(BINARY and BINARY.is_file()),
        "qelectrotech_version": version, "binary": str(BINARY) if BINARY else None,
        "binary_exists": bool(BINARY and BINARY.is_file()),
        "elements_root": str(ELEMENTS_ROOT) if ELEMENTS_ROOT else None,
        "symbol_count": len(_symbol_index()), "bundled_symbols": str(BUNDLED_SYMBOLS),
        "native_headless_export": False,
        "preview": "Approximate SVG; native QET visual validation is a separate check.",
        "allowed_roots": [str(p) for p in _allowed_roots()],
    }


@mcp.tool(annotations=READ_ONLY)
def search_symbols(query: str, limit: int = 20, language: str = "it") -> dict[str, Any]:
    """Search the installed QElectroTech symbol library by Italian/English name or path."""
    terms = _normalise(query).split()
    if not terms:
        raise ValueError("Query cannot be empty")
    matches = []
    for record in _symbol_index():
        if all(term in record["search"] for term in terms):
            matches.append({k: v for k, v in record.items() if k != "search"} | {"name": record["names"].get(language) or record["names"].get("en") or Path(record["path"]).stem})
            if len(matches) >= max(1, min(limit, 100)):
                break
    return {"query": query, "count": len(matches), "symbols": matches}


@mcp.tool(annotations=READ_ONLY)
def inspect_symbol(symbol_path: str) -> dict[str, Any]:
    """Inspect names, dimensions, terminals and default information of one .elmt symbol."""
    path = _safe_path(symbol_path, must_exist=True, suffix=".elmt", allow_qet_resources=True)
    root = ET.parse(path).getroot()
    if root.tag != "definition":
        raise ValueError("Not a QElectroTech element definition")
    description = root.find("description")
    terminals = []
    if description is not None:
        terminals = [dict(t.attrib) | {"index": index} for index, t in enumerate(description.findall("terminal"), 1)]
    return {
        "path": str(path), "version": root.get("version"), "type": root.get("type"),
        "link_type": root.get("link_type"), "width": root.get("width"), "height": root.get("height"),
        "names": {n.get("lang", ""): n.text or "" for n in root.findall("./names/name")},
        "terminals": terminals,
        "information_defaults": {n.get("name", ""): n.text or "" for n in root.findall("./elementInformations/elementInformation")},
    }


@mcp.tool(annotations=WRITE)
def create_project(path: str, title: str, folio_title: str = "Schema unifilare", author: str = "", overwrite: bool = False) -> dict[str, Any]:
    """Create a portable QElectroTech .qet project with one empty folio."""
    project_path = _safe_path(path, suffix=".qet")
    if project_path.exists() and not overwrite:
        raise FileExistsError(f"Project already exists: {project_path}")
    backup = _write_tree(project_path, _new_project_tree(title, folio_title, author), backup=overwrite)
    return {"path": str(project_path), "title": title, "folios": 1, "backup": backup}


@mcp.tool(annotations=READ_ONLY)
def inspect_project(path: str) -> dict[str, Any]:
    """Summarize folios, elements, conductors and project metadata."""
    project_path, _, root = _parse_project(path)
    folios = []
    for index, diagram in enumerate(root.findall("diagram"), 1):
        elements = diagram.find("elements")
        conductors = diagram.find("conductors")
        folios.append({
            "index": index, "uuid": diagram.get("uuid"), "title": diagram.get("title", ""),
            "author": diagram.get("author", ""), "order": diagram.get("order", str(index)),
            "elements": len(elements.findall("element")) if elements is not None else 0,
            "conductors": len(conductors.findall("conductor")) if conductors is not None else 0,
        })
    return {"path": str(project_path), "title": root.get("title", ""), "version": root.get("version", ""), "folios": folios}


@mcp.tool(annotations=READ_ONLY)
def list_elements(path: str, folio: int | str = 1) -> dict[str, Any]:
    """List placed elements, UUIDs, positions, terminals and component information on a folio."""
    _, _, root = _parse_project(path)
    diagram = _folio(root, folio)
    output = []
    elements = diagram.find("elements")
    for item in elements.findall("element") if elements is not None else []:
        output.append({
            "uuid": item.get("uuid"), "symbol": item.get("type"), "x": _as_float(item.get("x")),
            "y": _as_float(item.get("y")), "orientation": int(item.get("orientation", "0")),
            "prefix": item.get("prefix", ""), "terminals": len(item.findall("./terminals/terminal")),
            "information": _information(item),
        })
    return {"folio": diagram.get("title", ""), "count": len(output), "elements": output}


@mcp.tool(annotations=WRITE)
def add_folio(path: str, title: str, author: str = "", backup: bool = True) -> dict[str, Any]:
    """Append an empty folio to an existing QElectroTech project."""
    project_path, tree, root = _parse_project(path)
    order = len(root.findall("diagram")) + 1
    new_diagram = _new_project_tree(root.get("title", ""), title, author).getroot().find("diagram")
    assert new_diagram is not None
    new_diagram.set("order", str(order))
    collection = root.find("collection")
    insertion = list(root).index(collection) if collection is not None else len(root)
    root.insert(insertion, new_diagram)
    backup_path = _write_tree(project_path, tree, backup=backup)
    return {"path": str(project_path), "folio": order, "title": title, "uuid": new_diagram.get("uuid"), "backup": backup_path}


@mcp.tool(annotations=WRITE)
def set_folio_metadata(path: str, folio: int | str = 1, title: str | None = None, author: str | None = None, revision: str | None = None, backup: bool = True) -> dict[str, Any]:
    """Change title-block metadata for one folio."""
    project_path, tree, root = _parse_project(path)
    diagram = _folio(root, folio)
    if title is not None: diagram.set("title", title)
    if author is not None: diagram.set("author", author)
    if revision is not None: diagram.set("indexrev", revision)
    backup_path = _write_tree(project_path, tree, backup=backup)
    return {"path": str(project_path), "folio": diagram.get("title", ""), "backup": backup_path}


@mcp.tool(annotations=WRITE)
def add_element(path: str, symbol_path: str, x: float, y: float, label: str, folio: int | str = 1, orientation: int = 0, information: dict[str, str] | None = None, backup: bool = True) -> dict[str, Any]:
    """Embed and place one installed .elmt symbol on a folio. Orientation is 0..3 quarter-turns."""
    if orientation not in (0, 1, 2, 3):
        raise ValueError("orientation must be 0, 1, 2 or 3")
    project_path, tree, root = _parse_project(path)
    symbol = _safe_path(symbol_path, must_exist=True, suffix=".elmt", allow_qet_resources=True)
    definition = ET.parse(symbol).getroot()
    diagram = _folio(root, folio)
    elements = diagram.find("elements")
    if elements is None: elements = ET.SubElement(diagram, "elements")
    type_uri = _embed_definition(root, symbol)
    all_ids = [int(t.get("id", "-1")) for t in root.findall(".//diagram/elements/element/terminals/terminal") if t.get("id", "").isdigit()]
    next_id = max(all_ids, default=-1) + 1
    prefix_match = re.match(r"[A-Za-z]+", label)
    info = {"label": label, **(information or {})}
    item = ET.Element("element", {
        "freezeLabel": "false", "z": "10", "x": f"{x:g}", "y": f"{y:g}",
        "prefix": prefix_match.group(0) if prefix_match else "", "type": type_uri,
        "orientation": str(orientation), "uuid": _brace_uuid(),
    })
    _sequence(item)
    terminals_node = ET.SubElement(item, "terminals")
    description = definition.find("description")
    sources = description.findall("terminal") if description is not None else []
    for offset, source in enumerate(sources):
        terminals_node.append(_terminal_instance(source, next_id + offset))
    ET.SubElement(item, "inputs")
    infos = ET.SubElement(item, "elementInformations")
    defaults = {n.get("name", ""): n.text or "" for n in definition.findall("./elementInformations/elementInformation")}
    defaults.update(info)
    for key, value in defaults.items():
        node = ET.SubElement(infos, "elementInformation", {"show": "1", "name": key}); node.text = value
    item.append(_dynamic_texts(definition, defaults))
    ET.SubElement(item, "texts_groups")
    elements.append(item)
    backup_path = _write_tree(project_path, tree, backup=backup)
    return {"path": str(project_path), "folio": diagram.get("title", ""), "element_uuid": item.get("uuid"), "label": label, "terminals": len(sources), "terminal_ids": list(range(next_id, next_id + len(sources))), "backup": backup_path}


@mcp.tool(annotations=WRITE)
def move_element(path: str, element_uuid: str, x: float, y: float, folio: int | str = 1, orientation: int | None = None, backup: bool = True) -> dict[str, Any]:
    """Move and optionally rotate a placed element by UUID."""
    if orientation is not None and orientation not in (0, 1, 2, 3):
        raise ValueError("orientation must be 0, 1, 2 or 3")
    project_path, tree, root = _parse_project(path)
    item = _element(_folio(root, folio), element_uuid)
    item.set("x", f"{x:g}"); item.set("y", f"{y:g}")
    if orientation is not None: item.set("orientation", str(orientation))
    backup_path = _write_tree(project_path, tree, backup=backup)
    return {"element_uuid": element_uuid, "x": x, "y": y, "orientation": int(item.get("orientation", "0")), "backup": backup_path}


@mcp.tool(annotations=WRITE)
def update_element(path: str, element_uuid: str, information: dict[str, str], folio: int | str = 1, backup: bool = True) -> dict[str, Any]:
    """Update label, manufacturer, designation, comment or other element-information fields."""
    project_path, tree, root = _parse_project(path)
    item = _element(_folio(root, folio), element_uuid)
    _set_information(item, information)
    if "label" in information:
        match = re.match(r"[A-Za-z]+", information["label"])
        item.set("prefix", match.group(0) if match else "")
    backup_path = _write_tree(project_path, tree, backup=backup)
    return {"element_uuid": element_uuid, "information": _information(item), "backup": backup_path}


@mcp.tool(annotations=WRITE)
def connect_elements(path: str, from_element_uuid: str, from_terminal: int, to_element_uuid: str, to_terminal: int, folio: int | str = 1, conductor_label: str = "", conductor_properties: dict[str, str] | None = None, backup: bool = True) -> dict[str, Any]:
    """Connect two placed-element terminals. Terminal numbers are 1-based as returned by inspect_symbol/list_elements."""
    project_path, tree, root = _parse_project(path)
    diagram = _folio(root, folio)
    first = _find_terminal(diagram, from_element_uuid, from_terminal)
    second = _find_terminal(diagram, to_element_uuid, to_terminal)
    first_id, second_id = first.get("id", ""), second.get("id", "")
    if first_id == second_id:
        raise ValueError("Cannot connect a terminal to itself")
    conductors = diagram.find("conductors")
    if conductors is None: conductors = ET.SubElement(diagram, "conductors")
    for existing in conductors.findall("conductor"):
        if {existing.get("terminal1"), existing.get("terminal2")} == {first_id, second_id}:
            raise ValueError("These terminals are already connected")
    attrs = _default_conductor_attrs()
    attrs.update({"terminal1": first_id, "terminal2": second_id, "num": conductor_label})
    if conductor_properties:
        allowed = set(attrs) - {"terminal1", "terminal2"}
        unknown = set(conductor_properties) - allowed
        if unknown: raise ValueError(f"Unsupported conductor properties: {sorted(unknown)}")
        attrs.update({k: str(v) for k, v in conductor_properties.items()})
    conductor = ET.SubElement(conductors, "conductor", attrs)
    _sequence(conductor)
    backup_path = _write_tree(project_path, tree, backup=backup)
    return {"from_terminal_id": first_id, "to_terminal_id": second_id, "label": conductor_label, "backup": backup_path}


@mcp.tool(annotations=DESTRUCTIVE)
def delete_element(path: str, element_uuid: str, folio: int | str = 1, backup: bool = True) -> dict[str, Any]:
    """Delete one placed element and every conductor attached to its terminals."""
    project_path, tree, root = _parse_project(path)
    diagram = _folio(root, folio)
    item = _element(diagram, element_uuid)
    terminal_ids = {t.get("id") for t in item.findall("./terminals/terminal")}
    conductors = diagram.find("conductors")
    removed_conductors = 0
    if conductors is not None:
        for conductor in list(conductors.findall("conductor")):
            if conductor.get("terminal1") in terminal_ids or conductor.get("terminal2") in terminal_ids:
                conductors.remove(conductor); removed_conductors += 1
    elements = diagram.find("elements"); assert elements is not None
    elements.remove(item)
    backup_path = _write_tree(project_path, tree, backup=backup)
    return {"deleted": element_uuid, "removed_conductors": removed_conductors, "backup": backup_path}


@mcp.tool(annotations=READ_ONLY)
def validate_project(path: str) -> dict[str, Any]:
    """Validate XML structure, UUID uniqueness, terminal references and basic QET project invariants."""
    project_path, _, root = _parse_project(path)
    errors: list[str] = []
    warnings: list[str] = []
    uuids: set[str] = set()
    for index, diagram in enumerate(root.findall("diagram"), 1):
        terminal_ids: set[str] = set()
        for item in diagram.findall("./elements/element"):
            uid = item.get("uuid", "")
            if not uid: errors.append(f"Folio {index}: element without UUID")
            elif uid in uuids: errors.append(f"Duplicate element UUID: {uid}")
            uuids.add(uid)
            if _definition_from_instance(root, item) is None: warnings.append(f"Definition not resolved: {item.get('type')}")
            for terminal in item.findall("./terminals/terminal"):
                tid = terminal.get("id", "")
                if not tid: errors.append(f"Element {uid}: terminal without id")
                elif tid in terminal_ids: errors.append(f"Folio {index}: duplicate terminal id {tid}")
                terminal_ids.add(tid)
        for conductor in diagram.findall("./conductors/conductor"):
            for attr in ("terminal1", "terminal2"):
                if conductor.get(attr, "") not in terminal_ids:
                    errors.append(f"Folio {index}: conductor references missing {attr}={conductor.get(attr)}")
    if not root.findall("diagram"): warnings.append("Project has no folios")
    return {"path": str(project_path), "valid": not errors, "errors": errors, "warnings": warnings}


@mcp.tool(annotations=READ_ONLY)
def export_bom(path: str, output_csv: str | None = None) -> dict[str, Any]:
    """Build a basic BOM from placed element-information fields; optionally write it to CSV."""
    _, _, root = _parse_project(path)
    rows: list[dict[str, str]] = []
    for folio_index, diagram in enumerate(root.findall("diagram"), 1):
        for item in diagram.findall("./elements/element"):
            info = _information(item)
            rows.append({
                "folio": str(folio_index), "folio_title": diagram.get("title", ""),
                "uuid": item.get("uuid", ""), "label": info.get("label", ""),
                "manufacturer": info.get("manufacturer", ""), "designation": info.get("designation", ""),
                "description": info.get("description", ""), "comment": info.get("comment", ""),
                "symbol": item.get("type", ""),
            })
    csv_path = None
    if output_csv:
        target = _safe_path(output_csv)
        if target.suffix.lower() != ".csv": raise ValueError("output_csv must end in .csv")
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["folio", "folio_title", "uuid", "label", "manufacturer", "designation", "description", "comment", "symbol"])
            writer.writeheader(); writer.writerows(rows)
        csv_path = str(target)
    return {"count": len(rows), "rows": rows, "csv_path": csv_path}


def _svg_primitive(node: ET.Element) -> str:
    a = node.attrib
    stroke = "#111"; fill = "none"
    if node.tag == "line":
        return f'<line x1="{a.get("x1","0")}" y1="{a.get("y1","0")}" x2="{a.get("x2","0")}" y2="{a.get("y2","0")}" stroke="{stroke}" />'
    if node.tag == "rect":
        return f'<rect x="{a.get("x","0")}" y="{a.get("y","0")}" width="{a.get("width","0")}" height="{a.get("height","0")}" fill="{fill}" stroke="{stroke}" />'
    if node.tag == "ellipse":
        x, y, w, h = map(lambda k: _as_float(a.get(k)), ("x", "y", "width", "height"))
        return f'<ellipse cx="{x+w/2:g}" cy="{y+h/2:g}" rx="{w/2:g}" ry="{h/2:g}" fill="{fill}" stroke="{stroke}" />'
    if node.tag == "circle":
        return f'<circle cx="{a.get("x","0")}" cy="{a.get("y","0")}" r="{a.get("diameter",a.get("radius","4"))}" fill="{fill}" stroke="{stroke}" />'
    if node.tag == "polygon":
        points=[]
        for i in range(1, 50):
            if f"x{i}" not in a: break
            points.append(f'{a[f"x{i}"]},{a.get(f"y{i}","0")}')
        return f'<polyline points="{" ".join(points)}" fill="{fill}" stroke="{stroke}" />'
    if node.tag == "text":
        value = html.escape(a.get("text", "")); size = a.get("size", "7")
        return f'<text x="{a.get("x","0")}" y="{a.get("y","0")}" font-size="{size}" fill="#111">{value}</text>'
    return ""


@mcp.tool(annotations=WRITE)
def render_preview(path: str, output_svg: str, folio: int | str = 1) -> dict[str, Any]:
    """Render an approximate SVG preview for visual iteration. QElectroTech remains the final rendering authority."""
    _, _, root = _parse_project(path)
    diagram = _folio(root, folio)
    target = _safe_path(output_svg)
    if target.suffix.lower() != ".svg": raise ValueError("output_svg must end in .svg")
    width = int(_as_float(diagram.get("cols"), 18) * _as_float(diagram.get("colsize"), 60))
    height = int(_as_float(diagram.get("height"), 740))
    items = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="white"/>', f'<rect x="5" y="5" width="{width-10}" height="{height-10}" fill="none" stroke="#888"/>']
    by_terminal: dict[str, tuple[float, float]] = {}
    for item in diagram.findall("./elements/element"):
        definition = _definition_from_instance(root, item)
        x, y = _as_float(item.get("x")), _as_float(item.get("y"))
        angle = int(item.get("orientation", "0")) * 90
        items.append(f'<g transform="translate({x:g} {y:g}) rotate({angle})">')
        description = definition.find("description") if definition is not None else None
        if description is not None:
            from gridline.svg_primitives import symbol, explicit_dashes
            fragment = ET.Element("g")
            symbol(fragment, definition, 0, 0, 0)
            explicit_dashes(fragment)
            items.append(ET.tostring(fragment, encoding="unicode"))
        for dynamic in item.findall("./dynamic_texts/dynamic_elmt_text"):
            value = html.escape(dynamic.findtext("text") or "")
            items.append(f'<text x="{dynamic.get("x","0")}" y="{dynamic.get("y","0")}" font-size="8" fill="#075985">{value}</text>')
        for terminal in item.findall("./terminals/terminal"):
            tx, ty = _as_float(terminal.get("x")), _as_float(terminal.get("y"))
            items.append(f'<circle cx="{tx:g}" cy="{ty:g}" r="2" fill="#b91c1c"/>')
            by_terminal[terminal.get("id", "")] = _terminal_world(item, terminal)
        items.append('</g>')
    for conductor in diagram.findall("./conductors/conductor"):
        first, second = by_terminal.get(conductor.get("terminal1", "")), by_terminal.get(conductor.get("terminal2", ""))
        if first and second:
            items.append(f'<path d="M {first[0]:g} {first[1]:g} L {second[0]:g} {second[1]:g}" fill="none" stroke="#166534" stroke-width="1.5"/>')
            if conductor.get("num"):
                mx, my = (first[0]+second[0])/2, (first[1]+second[1])/2
                items.append(f'<text x="{mx:g}" y="{my-3:g}" font-size="7" fill="#166534">{html.escape(conductor.get("num", ""))}</text>')
    items.append(f'<text x="10" y="{height-12}" font-size="8" fill="#666">MCP preview — verify final output in QElectroTech</text>')
    items.append('</svg>')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(items), encoding="utf-8")
    return {"path": str(target), "folio": diagram.get("title", ""), "width": width, "height": height, "approximate": True}


@mcp.tool(annotations=WRITE)
def open_project(path: str) -> dict[str, Any]:
    """Open a .qet project in the installed QElectroTech desktop application."""
    project_path = _safe_path(path, must_exist=True, suffix=".qet")
    if BINARY is None or not BINARY.is_file():
        raise FileNotFoundError("QElectroTech not found; run gridline doctor or set QET_BINARY")
    subprocess.Popen([str(BINARY), str(project_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"opened": str(project_path), "application": str(BINARY)}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
