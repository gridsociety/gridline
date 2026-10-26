import asyncio
import json
from xml.etree import ElementTree as ET

from gridline.demo import build


def test_double_feeder_through_actual_stdio(tmp_path):
    p = asyncio.run(build(tmp_path / "demo with spaces", render_pdf=False))
    root = ET.parse(p / "source/double-feeder.qet")
    elements = root.findall("diagram/elements/element")
    conductors = root.findall("diagram/conductors/conductor")
    assert len(elements) == 6
    assert len(conductors) == 5
    # Independent oracle: every component reachable, two distinct outgoing breakers.
    owner = {t.get("id"): e.get("uuid") for e in elements for t in e.findall("terminals/terminal")}
    adjacent = {e.get("uuid"): set() for e in elements}
    for c in conductors:
        a, b = owner[c.get("terminal1")], owner[c.get("terminal2")]
        adjacent[a].add(b); adjacent[b].add(a)
    seen = set(); queue = [elements[0].get("uuid")]
    while queue:
        node = queue.pop()
        if node not in seen:
            seen.add(node); queue.extend(adjacent[node]-seen)
    assert len(seen) == 6
    labels = {e.findtext("elementInformations/elementInformation[@name='label']"): e.get("uuid") for e in elements}
    assert labels["DG.CLIENTE"] != labels["DG.BESS"]
    assert len(adjacent[labels["DG.CLIENTE"]]) == len(adjacent[labels["DG.BESS"]]) == 1
    report = json.loads((p / "qa/environment-readiness.json").read_text())
    assert report["mcp_stdio_verified"] and not report["documentor_render_verified"]
    assert not report["native_qet_visual_verified"]
