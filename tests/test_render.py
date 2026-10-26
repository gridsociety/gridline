from types import SimpleNamespace

import fitz
import pytest

from gridline import documentor_bridge
from gridline.workspace import new


def test_documentor_failure_does_not_replace_existing_pdf(tmp_path, monkeypatch):
    p = new(tmp_path / "project")
    output = p / "out/result.pdf"; output.write_bytes(b"previous verified result")
    book = fitz.open(); book.new_page(width=1200, height=800)
    monkeypatch.setattr(documentor_bridge, "documentor_command", lambda: "documentor-test")
    monkeypatch.setattr(documentor_bridge.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="failed"))
    meta = dict(client="Demo", date="2026-10-26", title="Demo", code="GS-DEMO", revision="R00")
    with pytest.raises(RuntimeError, match="No PDF fallback"):
        documentor_bridge.generate(p, book, meta, [{"title": "Demo"}], output)
    assert output.read_bytes() == b"previous verified result"
    assert not (p / "out/documentor-provenance.json").exists()
    assert "failed" in (p / "out/documentor-render.log").read_text()
