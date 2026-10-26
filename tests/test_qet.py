from xml.etree import ElementTree as ET

import pytest

from gridline.paths import RESOURCES
from qelectrotech_mcp import server
from qelectrotech_mcp.installation import discover


def test_explicit_installation_paths(tmp_path):
    binary = tmp_path / "portable qet"; binary.write_text("")
    symbols = tmp_path / "elements"; symbols.mkdir()
    paths = discover(environ={"QET_BINARY": str(binary), "QET_ELEMENTS_ROOT": str(symbols)},
                     platform="win32", which=lambda _: None)
    assert paths["binary"] == binary
    assert paths["elements"] == symbols


@pytest.mark.parametrize("platform", ["darwin", "win32", "linux"])
def test_missing_explicit_binary_is_not_hidden(platform, tmp_path):
    missing = tmp_path / "does-not-exist"
    paths = discover(environ={"QET_BINARY": str(missing)}, platform=platform, which=lambda _: None)
    assert paths["binary"] == missing
    assert not paths["binary"].exists()


def test_edit_cycle_without_desktop(tmp_path, monkeypatch):
    monkeypatch.setenv("QET_ALLOWED_ROOTS", str(tmp_path))
    monkeypatch.setattr(server, "ELEMENTS_ROOT", None)
    p = tmp_path / "project.qet"
    server.create_project(str(p), "Demo")
    symbol = str(RESOURCES / "symbols/cb.elmt")
    a = server.add_element(str(p), symbol, 100, 100, "Q1")
    b = server.add_element(str(p), symbol, 100, 250, "Q2")
    server.connect_elements(str(p), a["element_uuid"], 2, b["element_uuid"], 1)
    assert server.validate_project(str(p))["valid"]
    assert server.export_bom(str(p))["count"] == 2
    assert ET.parse(p).findtext("diagram/elements/element/dynamic_texts/dynamic_elmt_text/text") == "Q1"
    server.update_element(str(p), a["element_uuid"], {"label": "Q.UPDATED"})
    preview = tmp_path / "preview.svg"
    server.render_preview(str(p), str(preview))
    assert "Q.UPDATED" in preview.read_text()
    assert list(tmp_path.glob("*.bak-*"))
    with pytest.raises(ValueError, match="already connected"):
        server.connect_elements(str(p), a["element_uuid"], 2, b["element_uuid"], 1)
    with pytest.raises(ValueError, match="itself"):
        server.connect_elements(str(p), a["element_uuid"], 1, a["element_uuid"], 1)
    server.delete_element(str(p), a["element_uuid"])
    assert not ET.parse(p).findall("diagram/conductors/conductor")
    assert server.validate_project(str(p))["valid"]


def test_mcp_confines_writes(tmp_path, monkeypatch):
    root = tmp_path / "authorized"; root.mkdir()
    monkeypatch.setenv("QET_ALLOWED_ROOTS", str(root))
    with pytest.raises(ValueError, match="outside allowed"):
        server.create_project(str(tmp_path / "outside.qet"), "No")


def test_same_filename_different_symbols_do_not_alias(tmp_path, monkeypatch):
    monkeypatch.setenv("QET_ALLOWED_ROOTS", str(tmp_path))
    monkeypatch.setattr(server, "ELEMENTS_ROOT", None)
    a_dir = tmp_path / "a"; a_dir.mkdir()
    b_dir = tmp_path / "b"; b_dir.mkdir()
    text = (RESOURCES / "symbols/cb.elmt").read_text()
    (a_dir / "part.elmt").write_text(text)
    (b_dir / "part.elmt").write_text(text.replace('width="', 'data-variant="b" width="', 1))
    p = tmp_path / "p.qet"; server.create_project(str(p), "Demo")
    server.add_element(str(p), str(a_dir / "part.elmt"), 100, 100, "A")
    server.add_element(str(p), str(b_dir / "part.elmt"), 100, 200, "B")
    types = [e.get("type") for e in ET.parse(p).findall("diagram/elements/element")]
    assert len(set(types)) == 2
