"""Gridline delivery adapter. Originals are supplied locally, never downloaded."""
from contextlib import contextmanager
from pathlib import Path
import json
import shutil
from datetime import date
from .context import workspace
from .model import read, write, confined, sha
from . import pipeline, engineering

RESOURCES=Path(__file__).parent/'resources'


def new(destination):
    p=Path(destination).expanduser().resolve()
    p.mkdir(parents=True,exist_ok=False)
    for name in ['inputs','source','notes','variables','qa','out','published']:
        (p/name).mkdir()
    root=p/'source/bticino';root.mkdir()
    shutil.copytree(RESOURCES/'templates',root/'docs/templates')
    shutil.copytree(RESOURCES/'profiles',root/'profiles')
    shutil.copytree(RESOURCES/'schemas',root/'schemas')
    shutil.copytree(RESOURCES/'assets',root/'assets')
    for name in ['variables','static','attachments']:(root/'docs'/name).mkdir()
    shutil.copy2(RESOURCES/'template_metadata.json',root/'docs/template_metadata.json')
    (root/'docs/documentor.toml').write_text('[documentor]\ntemplates="templates"\nvariables="variables"\nstatic="static"\nmetadata="template_metadata.json"\noutput="out"\n',encoding='utf-8')
    write(p/'gridline.json',{'schema_version':1,'backend':'bticino','gridline_version':'0.1.0','bticino':{'root':'source/bticino','case':'cases/current','formats':['A3','A4']}})
    write(root/'profiles/native-symbols.json',{})
    write(root/'sources/registry.json',{})
    write(root/'cases/current/engineering.json',{'scope':'PRELIMINARE','engineering_approval':None,'pages':[]})
    write(root/'research/tisystem-capabilities.json',{'state':'UNVERIFIED','instructions':'Inspect TiSystem capabilities before selecting OEM symbols.'})
    for name in ['context','decisions','status','attachments']:
        (p/'notes'/f'{name}.md').write_text(f'# {name}\n\nDa compilare. Export TiSystem richiesti; nessun calcolo implicito.\n',encoding='utf-8')
    write(p/'variables/backend.json',{'backend':'bticino','request':'source/bticino/cases/current/request.json','exports':'source/bticino/cases/current/exports.json','documentor':'source/bticino/docs/documentor.toml'})
    (p/'README.md').write_text('# Gridline BTicino\n\nLeggere integrations/bticino/README.md nel checkout. Compilare request.json, cover.json ed exports.json nel caso configurato; conservare gli export nativi originali. Gli schemi JSON sono in source/bticino/schemas.\n',encoding='utf-8')
    return p


@contextmanager
def project_context(project):
    p=Path(project).expanduser().resolve();cfg=read(p/'gridline.json')
    if cfg.get('schema_version')!=1 or cfg.get('backend')!='bticino':
        raise ValueError('Expected a Gridline BTicino workspace')
    root=confined(p,cfg['bticino']['root']);case=confined(root,cfg['bticino']['case'])
    with workspace(root,confined(p,'out')):
        yield p,case,cfg


def prepare(project):
    with project_context(project) as (p,case,_):
        path=pipeline.prepare(case/'request.json')
        result=read(path);write(p/'qa/native-input-plan.json',result)
        return result


def inspect(project):
    with project_context(project) as (_,case,_):
        _,_,_,_,pages,csv,report=pipeline.inspect_bundle(case/'request.json',case/'exports.json')
        model,symbols,registry=engineering.load(case)
        return {'status':'PASS','pages':pages,'csv':csv['status'],'native_report':report,
                'geometry':engineering.validate(model,symbols,registry),'electrical_approval':'OPEN'}


def check(project):
    try:
        result=inspect(project)
        return {'errors':[],'electrical_compliance_verified':False,'bticino':result}
    except (OSError,ValueError,KeyError,TypeError) as exc:
        return {'errors':[str(exc)],'electrical_compliance_verified':False}


def render(project,formats=None):
    with project_context(project) as (p,case,cfg):
        outputs=[]
        for fmt in dict.fromkeys(formats or cfg['bticino']['formats']):
            if fmt not in {'A3','A4'}:raise ValueError('Format must be A3 or A4')
            outputs.append(pipeline.build(case/'request.json',case/'exports.json',fmt))
        write(p/'qa/artifacts.json',{'backend':'bticino','status':'DRAFT','electrical_approval':'OPEN','visual_review':'PENDING','artifacts':[{'path':str(f.relative_to(p)),'sha256':sha(f)} for f in outputs]})
        return [str(f) for f in outputs]


def verify(project,package):
    with project_context(project) as (p,_,_):
        return pipeline.verify_package(confined(p,package))


def import_case(source_root,request_relative,destination):
    """Import an explicit legacy case's dependency closure to a new LOCAL workspace.

    Source templates/code are not executed. Native hashes are verified before
    copying. Original absolute/user paths remain outside the public repository.
    """
    s=Path(source_root).expanduser().resolve()
    req=confined(s,request_relative);c=req.parent
    with workspace(s):
        request,bundle,paths,*_=pipeline.inspect_bundle(req,c/'exports.json')
        model,symbols,registry=engineering.load(c)
        cover=read(c/'cover.json')
        files={req,c/'exports.json',c/'engineering.json',c/'cover.json',*paths.values(),s/'sources/registry.json',s/'profiles/native-symbols.json',s/'research/tisystem-capabilities.json'}
        files.update(confined(s,item['path']) for item in registry.values())
        if cover.get('stamp'):files.add(confined(s,cover['stamp']))
        if (s/'research/design-basis.json').is_file():files.add(s/'research/design-basis.json')
        for file in files:
            if not file.is_file():raise ValueError('Missing dependency: '+str(file.relative_to(s)))
    p=new(destination);target=p/'source/bticino'
    for file in sorted(files):
        dest=confined(target,str(file.relative_to(s)));dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(file,dest)
    cfg=read(p/'gridline.json');cfg['bticino']['case']=str(c.relative_to(s));write(p/'gridline.json',cfg)
    write(p/'variables/backend.json',{'backend':'bticino','request':str((target/c.relative_to(s)/'request.json').relative_to(p)),'exports':str((target/c.relative_to(s)/'exports.json').relative_to(p)),'documentor':'source/bticino/docs/documentor.toml'})
    write(p/'qa/import-provenance.json',{'mode':'local dependency closure','source_request_sha256':sha(req),'files':{str(f.relative_to(s)):sha(f) for f in sorted(files)},'source_unchanged':True})
    errors=check(p)['errors']
    if errors:raise ValueError('Imported case failed checks: '+'; '.join(errors))
    return p
