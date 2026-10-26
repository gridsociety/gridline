"""Portable resources and confined project assets."""
from pathlib import Path

RESOURCES = Path(__file__).resolve().parent / "resources"


def project_file(project, relative):
    root = Path(project).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Asset outside project: {relative}")
    return path
