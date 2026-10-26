import json
from pathlib import Path

import pytest

from gridline.workspace import new, check, write_json
from gridline.paths import project_file
from gridline.cli import mcp_config


def valid_project(tmp_path):
    project = new(tmp_path / "commessa con spazi")
    (project / "source/view.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200"><path d="M 10 20 L 90 20"/></svg>')
    meta = json.loads((project / "variables/drawing-set.json").read_text(encoding="utf-8"))
    meta["pages"] = [{"source": "source/view.svg", "title": "Schema", "kind": "general", "width_mm": 420}]
    write_json(project / "variables/drawing-set.json", meta)
    return project, meta


def test_new_never_overwrites(tmp_path):
    p = new(tmp_path / "project")
    (p / "source/user.txt").write_text("keep")
    with pytest.raises(FileExistsError):
        new(p)
    assert (p / "source/user.txt").read_text(encoding="utf-8") == "keep"


def test_unknown_backend_does_not_create_fake_project(tmp_path):
    with pytest.raises(ValueError, match="not implemented"):
        new(tmp_path / "bt", "unknown")
    assert not (tmp_path / "bt").exists()


def test_empty_project_is_not_ready(tmp_path):
    p = new(tmp_path / "empty")
    assert any("pages" in e for e in check(p)["errors"])


def test_spaces_and_file_contract(tmp_path):
    p, _ = valid_project(tmp_path)
    assert check(p) == {"errors": [], "electrical_compliance_verified": False}
    cfg = mcp_config(p)["mcpServers"]["gridline-qelectrotech"]
    assert cfg["env"]["QET_ALLOWED_ROOTS"] == str(p)
    assert cfg["args"] == ["-m", "qelectrotech_mcp.server"]
    assert Path(cfg["command"]).is_file()


def test_unicode_project_metadata(tmp_path):
    p, meta = valid_project(tmp_path)
    meta["client"] = "Città — società elettrica"
    write_json(p / "variables/drawing-set.json", meta)
    assert not check(p)["errors"]
    assert json.loads((p / "variables/drawing-set.json").read_text(encoding="utf-8"))["client"] == meta["client"]


@pytest.mark.parametrize("field,value", [("source", "../outside.svg"), ("width_mm", 200), ("kind", "unknown")])
def test_reject_invalid_view(tmp_path, field, value):
    p, meta = valid_project(tmp_path)
    meta["pages"][0][field] = value
    write_json(p / "variables/drawing-set.json", meta)
    assert check(p)["errors"]


def test_reject_filename_traversal(tmp_path):
    p, meta = valid_project(tmp_path)
    meta["slug"] = "../../outside"
    write_json(p / "variables/drawing-set.json", meta)
    assert any("Unsafe filename" in e for e in check(p)["errors"])


def test_reject_external_svg(tmp_path):
    p, _ = valid_project(tmp_path)
    (p / "source/view.svg").write_text('<svg><image href="https://example.com/private"/></svg>')
    assert any("External SVG" in e for e in check(p)["errors"])


def test_symlink_cannot_escape_project(tmp_path):
    root = tmp_path / "root"; root.mkdir()
    target = tmp_path / "outside"; target.mkdir()
    try:
        (root / "link").symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("Symlinks unavailable on this platform")
    with pytest.raises(ValueError, match="outside project"):
        project_file(root, "link/file.svg")
