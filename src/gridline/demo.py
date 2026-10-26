"""Synthetic double-feeder exercise built through a real MCP STDIO session."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from .paths import RESOURCES
from .workspace import new, write_json, check, artifact_manifest


async def build(destination, *, render_pdf=True, require_desktop=False):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    project = new(destination)
    qet = project / "source/double-feeder.qet"
    svg = project / "source/double-feeder.svg"
    env = dict(os.environ)
    env["QET_ALLOWED_ROOTS"] = str(project)
    params = StdioServerParameters(command=sys.executable, args=["-m", "qelectrotech_mcp.server"], env=env)
    trace = []
    with (project / "qa/mcp-stderr.log").open("w", encoding="utf-8") as log:
        async with stdio_client(params, errlog=log) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                async def call(name, **arguments):
                    result = await session.call_tool(name, arguments)
                    if result.isError:
                        raise RuntimeError(f"MCP {name}: {result.content}")
                    data = result.structuredContent
                    if data is None:
                        data = json.loads(next(c.text for c in result.content if c.type == "text"))
                    trace.append({"tool": name, "result": data})
                    return data
                health = await call("health_check")
                if require_desktop and (not health["installed"] or not health["symbol_count"]):
                    raise RuntimeError("Smoke requires the QET desktop installation and library: run gridline doctor")
                await call("create_project", path=str(qet), title="Gridline — doppio montante didattico", author="Grid Society")
                for filename in ["qs.elmt", "j4.elmt", "cb.elmt"]:
                    await call("inspect_symbol", symbol_path=str(RESOURCES / "symbols" / filename))
                elements = {}
                for key, symbol, x, y, label in [
                    ("incoming", "qs", 500, 100, "QS.ARRIVO"),
                    ("bus", "j4", 500, 240, ""),
                    ("left_bus", "j4", 300, 240, ""),
                    ("right_bus", "j4", 700, 240, ""),
                    ("customer", "cb", 300, 380, "DG.CLIENTE"),
                    ("bess", "cb", 700, 380, "DG.BESS"),
                ]:
                    elements[key] = await call("add_element", path=str(qet),
                        symbol_path=str(RESOURCES / "symbols" / f"{symbol}.elmt"), x=x, y=y, label=label, backup=False)
                # QET junction ports: top=1, bottom=2, right=3, left=4.
                # Circuit-breaker terminal order is resolved from definition geometry.
                from xml.etree import ElementTree as ET
                def ends(symbol):
                    terminals = ET.parse(RESOURCES / "symbols" / f"{symbol}.elmt").findall("description/terminal")
                    ordered = sorted(range(len(terminals)), key=lambda i: float(terminals[i].get("y", "0")))
                    return ordered[0]+1, ordered[-1]+1
                _, incoming_bottom = ends("qs")
                breaker_top, _ = ends("cb")
                for a, at, b, bt in [
                    ("incoming", incoming_bottom, "bus", 1),
                    ("bus", 4, "left_bus", 3), ("bus", 3, "right_bus", 4),
                    ("left_bus", 2, "customer", breaker_top), ("right_bus", 2, "bess", breaker_top),
                ]:
                    await call("connect_elements", path=str(qet), from_element_uuid=elements[a]["element_uuid"],
                               from_terminal=at, to_element_uuid=elements[b]["element_uuid"], to_terminal=bt, backup=False)
                validation = await call("validate_project", path=str(qet))
                if not validation["valid"]:
                    raise RuntimeError(str(validation))
                await call("inspect_project", path=str(qet))
                await call("export_bom", path=str(qet), output_csv=str(project / "out/components.csv"))
                await call("render_preview", path=str(qet), output_svg=str(svg))
    write_json(project / "qa/mcp-trace.json", trace)
    metadata_path = project / "variables/drawing-set.json"
    metadata = json.loads(metadata_path.read_text())
    metadata.update(title="Doppio montante — esempio didattico", client="CLIENTE FITTIZIO", site="SITO DIMOSTRATIVO")
    metadata["pages"] = [{"source": "source/double-feeder.svg", "title": "Doppio montante — esempio didattico",
        "kind": "general", "variant": "A", "width_mm": 420,
        "clip": [240, 45, 800, 455], "note": "Topologia dimostrativa: utenze, cavi, taglie e protezioni da progettare."}]
    write_json(metadata_path, metadata)
    (project / "notes/context.md").write_text("# Contesto\n\nEsempio sintetico: arrivo comune e due partenze, cliente e BESS. Nessun dato di una commessa reale.\n", encoding="utf-8")
    (project / "notes/status.md").write_text("# Stato\n\nDRAFT didattico. Nessun dimensionamento o approvazione elettrica. Resa nativa QET da verificare.\n", encoding="utf-8")
    validation = check(project)
    if validation["errors"]:
        raise RuntimeError(str(validation))
    if render_pdf:
        from .compose import render
        render(project)
    report = {"status": "pending_visual_review" if render_pdf else "qet_generated_pdf_not_tested",
              "mcp_stdio_verified": True, "agent_mcp_session_verified": False,
              "qet_xml_verified": True, "documentor_render_verified": render_pdf,
              "native_qet_visual_verified": False, "electrical_compliance_verified": False}
    write_json(project / "qa/environment-readiness.json", report)
    write_json(project / "qa/artifact-manifest.json", artifact_manifest(project))
    return project
