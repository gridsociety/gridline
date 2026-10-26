"""Actual STDIO exercise against a populated local workspace."""
import asyncio
import json
import os
import sys
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from .model import write
from .integration import project_context


async def run(project):
    p=Path(project).resolve()
    with project_context(p):pass
    trace=[]
    env=dict(os.environ,BTICINO_ALLOWED_ROOTS=str(p),PYTHONUTF8="1")
    params=StdioServerParameters(command=sys.executable,args=['-m','gridline_bticino.server'],env=env)
    with (p/'qa/mcp-stderr.log').open('w',encoding='utf-8') as log:
        async with stdio_client(params,errlog=log) as (read,write_stream):
            async with ClientSession(read,write_stream) as session:
                await session.initialize()
                async def call(name,**args):
                    result=await session.call_tool(name,args)
                    if result.isError:raise RuntimeError(f'MCP {name}: {result.content}')
                    data=result.structuredContent
                    if data is None:data=json.loads(next(c.text for c in result.content if c.type=='text'))
                    trace.append({'tool':name,'result':data})
                    return data
                await call('health_check')
                await call('prepare_case',project=str(p))
                await call('inspect_exports',project=str(p))
                result=await call('build_document',project=str(p),formats=['A3','A4'])
                for pdf in result['pdfs']:
                    await call('verify_document',project=str(p),package=str(Path(pdf).parent.relative_to(p)))
    report={'mcp_stdio_verified':True,'documentor_render_verified':True,'native_app_reimport_verified':False,'visual_review':'PENDING','electrical_approval':'OPEN','trace':trace}
    write(p/'qa/mcp-real-demo.json',report)
    return report
