"""MCP for native-export preparation/inspection/composition, not a TiSystem API."""
from pathlib import Path
import os
from typing import Any
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from . import integration
from .environment import doctor

READ=ToolAnnotations(readOnlyHint=True,destructiveHint=False,openWorldHint=False)
WRITE=ToolAnnotations(readOnlyHint=False,destructiveHint=False,openWorldHint=False)
mcp=FastMCP('GridlineBTicino',instructions='Prepare and inspect locally supplied TiSystem exports; compose native PDF content in Documentor frames. No TiSystem login, sizing API or browser control is provided. Electrical approval remains OPEN.')


def safe_path(value):
    path=Path(value).expanduser().resolve()
    roots=[Path(p).expanduser().resolve() for p in os.environ.get('BTICINO_ALLOWED_ROOTS','').split(os.pathsep) if p] or [Path.cwd().resolve()]
    if not any(path.is_relative_to(root) for root in roots):
        raise ValueError('Path outside BTICINO_ALLOWED_ROOTS')
    return path


@mcp.tool(annotations=READ)
def health_check() -> dict[str, Any]:
    return doctor(probe=False)


@mcp.tool(annotations=WRITE)
def create_workspace(destination:str) -> dict[str, Any]:
    return {'project':str(integration.new(safe_path(destination))),'state':'NEEDS_NATIVE_INPUTS'}


@mcp.tool(annotations=WRITE)
def prepare_case(project:str) -> dict[str, Any]:
    return integration.prepare(safe_path(project))


@mcp.tool(annotations=READ)
def inspect_exports(project:str) -> dict[str, Any]:
    return integration.inspect(safe_path(project))


@mcp.tool(annotations=WRITE)
def build_document(project:str,formats:list[str]|None=None) -> dict[str, Any]:
    return {'pdfs':integration.render(safe_path(project),formats),'status':'DRAFT','visual_review':'PENDING','electrical_approval':'OPEN'}


@mcp.tool(annotations=READ)
def verify_document(project:str,package:str) -> dict[str, Any]:
    return integration.verify(safe_path(project),package)


def main():
    mcp.run(transport='stdio')


if __name__=='__main__':
    main()
