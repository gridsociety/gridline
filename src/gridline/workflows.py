"""Professional deliverable names; independent models, coordinated workspaces."""
from pathlib import Path
import json

WORKFLOWS={
    'general':{'title':'Schema generale di integrazione','backend':'qelectrotech','purpose':'Architettura di impianto, esistente e nuovo BESS, montanti e interfacce'},
    'equipment':{'title':'Schema di quadro con dati di dimensionamento','backend':'bticino','purpose':'Componenti, cavi, portate, poteri di interruzione e tarature da export nativi'},
    'combined':{'title':'Fascicolo coordinato generale e quadri','backend':'combined','purpose':'Due viste distinte della stessa commessa; riconciliazione tecnica esplicita'},
}


def new_workflow(destination,workflow):
    from .workspace import new,write_json
    if workflow not in WORKFLOWS:raise ValueError('Unknown workflow')
    backend=WORKFLOWS[workflow]['backend']
    if backend!='combined':return new(destination,backend)
    p=Path(destination).expanduser().resolve();p.mkdir(parents=True,exist_ok=False)
    write_json(p/'gridline.json',{'schema_version':1,'backend':'combined','gridline_version':'0.1.0','children':{'general':'general','equipment':'quadri'}})
    new(p/'general','qelectrotech');new(p/'quadri','bticino')
    (p/'README.md').write_text('# Fascicolo coordinato\n\nGeneral: QElectroTech. Quadri: export nativi BTicino. Collegare gli stessi ID di circuito e le revisioni; nessuna conversione automatica o doppio calcolo implicito.\n',encoding='utf-8')
    (p/'coordination.json').write_text(json.dumps({'status':'OPEN','circuit_map':[],'checks':['Origini e destinazioni','Identita apparecchi','Tensioni/potenze','Riferimenti incrociati e revisioni'],'electrical_approval':None},indent=2)+'\n',encoding='utf-8')
    return p


def children(project):
    from .paths import project_file
    p=Path(project).resolve();cfg=json.loads((p/'gridline.json').read_text(encoding="utf-8"))
    if cfg.get('backend')!='combined' or set(cfg.get('children',{}))!={'general','equipment'}:
        raise ValueError('Invalid combined workspace')
    items={k:project_file(p,v) for k,v in cfg['children'].items()}
    if len(set(items.values()))!=2 or any(v==p for v in items.values()):raise ValueError('Combined children must be distinct subprojects')
    for key,child in items.items():
        expected=WORKFLOWS[key]['backend']
        if json.loads((child/'gridline.json').read_text(encoding="utf-8")).get('backend')!=expected:
            raise ValueError('Unexpected combined child backend: '+key)
    return items


def render_combined(project):
    from .workspace import check,write_json
    from .compose import render as qet_render
    from gridline_bticino.integration import render as bt_render
    paths=children(project)
    checks={k:check(v) for k,v in paths.items()}
    if any(c['errors'] for c in checks.values()):raise ValueError('Complete both models before combined delivery: '+json.dumps(checks))
    out={'general':str(qet_render(paths['general'])),'equipment':bt_render(paths['equipment'])}
    write_json(Path(project)/'delivery.json',{'outputs':out,'status':'DRAFT','coordination_review':'OPEN','electrical_approval':None})
    return out
