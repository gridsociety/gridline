import asyncio
import copy
import json
import os
import sys
from pathlib import Path
import pytest
import fitz
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from gridline.workspace import new,check
from gridline.workflows import new_workflow,children,render_combined
from gridline.cli import mcp_config
from gridline_bticino.context import workspace,root
from gridline_bticino.integration import project_context,RESOURCES
from gridline_bticino.model import validate_request,validate_exports,digest,confined
from gridline_bticino.checks import three_phase_current,ampacity_ok,mt_screen
from gridline_bticino.native import fit
from gridline_bticino.engineering import validate
from gridline_bticino.server import safe_path


def test_workspace_contract_and_no_personal_assets(tmp_path):
    p=new(tmp_path/'quadri con spazi','bticino')
    assert check(p)['errors']  # empty does not claim a ready design
    assert (p/'source/bticino/docs/templates/drawings/fascicolo.html').is_file()
    assert not list((p/'source/bticino/assets').glob('*.png'))
    assert mcp_config(p)['mcpServers']['gridline-bticino']['env']['BTICINO_ALLOWED_ROOTS']==str(p)
    with pytest.raises(FileExistsError):new(p,'bticino')


def test_workspace_context_isolated(tmp_path):
    a=new(tmp_path/'a','bticino');b=new(tmp_path/'b','bticino')
    with project_context(a):
        first=root()
        with project_context(b):assert root()!=first
        assert root()==first
    with pytest.raises(RuntimeError):root()


def test_combined_routes_and_unfinished_state(tmp_path):
    p=new_workflow(tmp_path/'combined','combined')
    assert set(children(p))=={'general','equipment'}
    assert set(mcp_config(p)['mcpServers'])=={'gridline-bticino','gridline-qelectrotech'}
    assert check(p)['errors']
    with pytest.raises(ValueError,match='Complete both'):render_combined(p)


def test_combined_rejects_recursive_child(tmp_path):
    p=new_workflow(tmp_path/'combined','combined')
    cfg=json.loads((p/'gridline.json').read_text(encoding="utf-8"));cfg['children']['general']='.'
    (p/'gridline.json').write_text(json.dumps(cfg))
    with pytest.raises(ValueError):children(p)


def test_mcp_path_and_symlink_boundary(tmp_path,monkeypatch):
    p=tmp_path/'allowed';p.mkdir();monkeypatch.setenv('BTICINO_ALLOWED_ROOTS',str(p))
    assert safe_path(str(p/'new'))==p/'new'
    with pytest.raises(ValueError):safe_path(str(tmp_path/'outside'))
    try:(p/'link').symlink_to(tmp_path,target_is_directory=True)
    except OSError:pytest.skip('Symlink creation not permitted')
    with pytest.raises(ValueError):safe_path(str(p/'link/outside'))


def test_native_fit_preserves_aspect():
    source=fitz.Rect(10,20,210,120);space=fitz.Rect(30,30,330,330)
    target=fit(source,space)
    assert space.contains(target)
    assert target.width/source.width==target.height/source.height==1.5


def test_vector_transport_never_regenerates_symbols():
    # Geometric test fixture only; not an electrical or simulated vendor symbol.
    with fitz.open() as source,fitz.open() as dest:
        page=source.new_page(width=200,height=100)
        page.draw_rect(fitz.Rect(30,20,50,60),width=.2)
        page.insert_text((70,45),'TEST')
        p=dest.new_page();xref=p.show_pdf_page(fitz.Rect(0,0,400,200),source,0)
        assert dest.xref_stream(xref)==page.read_contents()
        assert 'TEST' in p.get_text()


@pytest.mark.parametrize('args',[(0,400,1),(30,0,1),(30,400,0),(30,400,1.1),(float('nan'),400,1),(True,400,1)])
def test_numeric_invalid(args):
    with pytest.raises(ValueError):three_phase_current(*args)


def test_independent_numerical_oracles():
    assert three_phase_current(30,400,.9)==pytest.approx(48.1125224)
    assert ampacity_ok(48.17,63,66.96)
    assert not ampacity_ok(48.17,63,60)
    data={'apparent_kVA':8000,'voltage_V':20000,'length_m':40,'section_mm2':120,'k_adiabatic':143,'fault_duration_s':1,'fault_kA':16,'ampacity_A':360,'resistance_ohm_km':.196,'reactance_ohm_km':.12,'cos_phi':1}
    assert mt_screen(data)['drop_pct']==pytest.approx(.01568)
    assert mt_screen(data)['conductor_withstand_kA']==17.16
    assert mt_screen(dict(data,fault_duration_s=4))['conductor_thermal_status']=='FAIL'


def test_render_input_rejects_active_geometry():
    model={'scope':'PRELIMINARE','engineering_approval':None,'pages':[{'id':'x','width':400,'height':260,'labels':[{'x':'0" onload="alert(1)','y':1,'size':3}],'regions':[],'nodes':[],'edges':[],'table':{'y':200,'columns':[400],'headers':['x'],'rows':[]}}]}
    with pytest.raises(ValueError,match='geometry'):validate(model,{}, {})


def test_example_contract_rejects_wrong_units_and_binding(tmp_path):
    path=Path(__file__).parents[2]/'examples/bticino/request.json'
    req=json.loads(path.read_text(encoding="utf-8"));assert validate_request(req)==[]
    bundle={'schema_version':1,'profile':'tisystem-technical-a4-v1','design_sha256':digest(req['design'])}
    changed=copy.deepcopy(req);changed['design']['circuits'][0]['power']['value']=60
    with pytest.raises(ValueError,match='different design'):validate_exports(changed,bundle,tmp_path)
    req['design']['circuits'][0]['power']['unit']='MWh'
    with pytest.raises(ValueError):validate_request(req)


def test_real_mcp_stdio_workspace_and_boundary(tmp_path):
    async def run():
        env=dict(os.environ,BTICINO_ALLOWED_ROOTS=str(tmp_path),PYTHONUTF8="1")
        params=StdioServerParameters(command=sys.executable,args=['-m','gridline_bticino.server'],env=env)
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as s:
                await s.initialize()
                names={t.name for t in (await s.list_tools()).tools}
                assert {'prepare_case','inspect_exports','build_document','verify_document'}<=names
                health=await s.call_tool('health_check',{})
                assert not health.isError and not health.structuredContent['tisystem_login_verified']
                result=await s.call_tool('create_workspace',{'destination':str(tmp_path/'new')})
                assert not result.isError and result.structuredContent['state']=='NEEDS_NATIVE_INPUTS'
                rejected=await s.call_tool('create_workspace',{'destination':str(tmp_path.parent/'outside')})
                assert rejected.isError
    asyncio.run(run())
