"""Local export-to-document automation; browser engineering remains upstream."""
from __future__ import annotations
from .context import root, output_root
import base64
from collections import Counter
from datetime import datetime,timezone
import hashlib
from pathlib import Path
import subprocess
import os
import tempfile
import fitz
from .model import read,write,digest,sha,confined,validate_request,validate_exports,reconcile_csv,document_code,filename
from .native import detect,available,fit,text_sizes,check_native_reports
from . import engineering

SIZES={'a4_portrait':(210,297),'a4_landscape':(297,210),'a3_landscape':(420,297)}
MM=72/25.4

def prepare(request_path):
    request_path=confined(root(),str(Path(request_path).resolve()))
    request=read(request_path);missing=validate_request(request)
    result={'state':'NEEDS_NATIVE_EXPORT' if not missing else 'NEEDS_INPUTS','design_sha256':digest(request['design']),
            'document_code':document_code(request),'missing_required':missing,'native_input':request['design'],
            'next_actions':['Read back the structured request and declare assumptions.','Create or update a copy in TiSystem; read back source/circuits.','Calculate and verify in TiSystem.','Export technical PDF, CSV, detailed report and .ti8; capture hashes and circuit map.','Run build with request.json and exports.json.'],
            'scope':'Prepares data for the agent; does not call TiSystem or calculate an electrical design.'}
    case=Path(request_path).parent
    if (case/'engineering.json').exists():
        model,symbols,registry=engineering.load(case)
        result['engineering_model']='engineering.json'
        result['engineering_sha256']=digest(model)
        result['engineering_checks']=engineering.validate(model,symbols,registry)
        result['next_actions'] += ['Verify TiSystem capabilities before selecting external native glyphs.', 'Reconcile current BOM and OEM interfaces; keep unresolved values explicit.', 'Review every rendered sheet and keep electrical approval separate.']
    path=case/'prepared/native-input-plan.json';write(path,result)
    return path

def inspect_bundle(request_path,bundle_path):
    request_path=Path(request_path).resolve();bundle_path=Path(bundle_path).resolve()
    confined(root(),str(request_path));confined(root(),str(bundle_path))
    if request_path.parent!=bundle_path.parent:raise ValueError('Request and export bundle must share a case directory')
    request,bundle=read(request_path),read(bundle_path)
    paths=validate_exports(request,bundle,bundle_path.parent)
    profile_path=root()/'profiles'/(bundle['profile']+'.json');profile=read(profile_path)
    csv_check=reconcile_csv(request,bundle,paths['csv'])
    detections=[]
    with fitz.open(paths['pdf']) as source,fitz.open(paths['report']) as report:
        if sorted(p['source_page'] for p in bundle['pages'])!=list(range(len(source))):
            raise ValueError('Every native page must be assigned exactly once')
        for item in bundle['pages']:
            detections.append(dict(detect(source[item['source_page']],profile,item['kind']),source_page=item['source_page']))
        report_check=check_native_reports(request,source,report)
        unacknowledged=set(report_check['findings'])-set(bundle['acknowledged_findings'])
        if unacknowledged:raise ValueError('Native report findings require review: '+', '.join(sorted(unacknowledged)))
        if report_check['findings'] and not any('Iz' in x and 'report' in x for x in request['notes']['findings']):
            raise ValueError('Acknowledged Iz discrepancy must be disclosed in document notes')
    return request,bundle,paths,profile,detections,csv_check,report_check

def document_data(request,bundle,fmt,case=None):
    doc=request['document'];code=document_code(request)
    cart={'committente':doc['customer'],'progetto':code+' · '+doc['project_name'],
          'scala':'NTS','data':datetime.fromisoformat(doc['date']).strftime('%d/%m/%Y'),
          'redatto':doc['designer'],'approvato':'','emissione':'PRELIMINARE / DRAFT','rev':doc['revision'],
          'logo_url':'data:image/svg+xml;base64,'+base64.b64encode((root()/'assets/logo-grid-society.svg').read_bytes()).decode()}
    pages=[{'number':1,'kind':'cover','title':'Copertina tecnica e revisioni','format':'a4_portrait'}]
    extras={}
    native_pages=bundle['pages']
    if case:
        model,symbols,registry=engineering.load(case)
        cover=read(case/'cover.json')
        if cover.get('approval') or cover.get('check'):raise ValueError('Cover cannot imply approval')
        if cover['revisions'][-1]['revision']!=doc['revision']:raise ValueError('Cover revision mismatch')
        stamp=confined(root(),cover['stamp']) if cover.get('stamp') else None
        extras={'cover':cover,'stamp_url':('data:image/png;base64,'+base64.b64encode(stamp.read_bytes()).decode()) if stamp else '',
                'engineering':model,'symbols':symbols,'registry':registry}
        for view in model['pages']:
            pages.append({'number':len(pages)+1,'kind':'engineering','title':view['title'],
                          'format':fmt.lower()+'_landscape','view':view,'svg':engineering.svg(view,symbols)})
        native_pages=sorted(bundle['pages'],key=lambda p:p['kind']!='legend')
    for source in native_pages:
        pages.append({'number':len(pages)+1,'kind':'native','title':source['title'],'format':fmt.lower()+'_landscape','source_page':source['source_page']})
    if case:
        pages.append({'number':len(pages)+1,'kind':'basis','title':'Basi, riscontri e verifiche aperte','format':'a4_portrait'})
    else:
        pages.extend([{'number':len(pages)+1,'kind':'assumptions','title':'Basi e ipotesi','format':'a4_portrait'},
                      {'number':len(pages)+2,'kind':'checks','title':'Risultati e verifiche aperte','format':'a4_portrait'}])
    return dict({'document':doc,'code':code,'output_name':filename(request,fmt),'drawing_format':fmt,'cart':cart,
            'pages':pages,'total':len(pages),'index':[{'number':p['number'],'title':p['title']} for p in pages],
            'native_revision':bundle['native_revision'],'notes':request['notes'],
            'scope':doc.get('scope','Schema preliminare, ipotesi dichiarate.')},**extras)

def render_frames(data,work):
    from gridline.environment import documentor_command
    command=documentor_command()
    if not command:raise RuntimeError('Documentor missing: run gridline doctor --backend bticino')
    frames={}
    for fmt in dict.fromkeys(p['format'] for p in data['pages']):
        group=dict(data,format=fmt,pages=[p for p in data['pages'] if p['format']==fmt],
                   cart=dict(data['cart'],formato='A3' if fmt.startswith('a3') else 'A4',portrait=fmt.endswith('portrait')))
        variables=work/(fmt+'.json');write(variables,group)
        html,pdf=work/(fmt+'.html'),work/(fmt+'.pdf')
        args=[f'drawings/fascicolo-{fmt}.html','--vars',str(variables),'-w',str(root()/'docs')]
        for action,tail in [('validate',['--template',*args]),('html',[*args,'--out',str(html)]),('render',[*args,'--out',str(pdf)])]:
            result=subprocess.run([command,action,*tail],text=True,encoding="utf-8",capture_output=True,env={**os.environ,"PYTHONUTF8":"1"},timeout=180)
            (work/(fmt+'-'+action+'.log')).write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
            if result.returncode:raise RuntimeError('Documentor '+action+' failed: '+result.stderr[-2000:])
        with fitz.open(pdf) as rendered:
            if len(rendered)!=len(group['pages']):raise ValueError('Unexpected Documentor pagination')
            w,h=SIZES[fmt]
            if any(abs(p.rect.width/MM-w)>.35 or abs(p.rect.height/MM-h)>.35 for p in rendered):
                raise ValueError('Wrong Documentor sheet dimensions')
        for i,p in enumerate(group['pages']):frames[p['number']]=(pdf,i)
    return frames

def compose(data,frames,source_path,detections,output):
    results=[];by_page={x['source_page']:x for x in detections}
    with fitz.open(source_path) as src,fitz.open() as dst:
        for item in data['pages']:
            path,index=frames[item['number']]
            with fitz.open(path) as f:dst.insert_pdf(f,from_page=index,to_page=index)
            page=dst[-1]
            if item['kind']=='engineering':
                symbols=engineering.place_native(page,item['view'],data['drawing_format'],data['symbols'],data['registry'])
                results.append({'kind':'engineering','page':item['number'],'view':item['view']['id'],'symbols':symbols})
                continue
            if item['kind']!='native':continue
            original=src[item['source_page']];det=by_page[item['source_page']]
            clip=fitz.Rect(det['clip_pt']);space=available(data['drawing_format']);target=fit(clip,space)
            xref=page.show_pdf_page(target,src,item['source_page'],clip=clip,keep_proportion=True)
            if dst.xref_stream(xref)!=original.read_contents():raise ValueError('Native PDF operators modified')
            scale=target.width/clip.width;size=text_sizes(original,clip)
            results.append(dict(det,page=item['number'],target_pt=list(target),available_pt=list(space),
                                scale=scale,dominant_native_text_pt=size,dominant_final_text_pt=size*scale,
                                occupied_area_ratio=target.get_area()/space.get_area()))
        dst.set_metadata({'title':data['output_name']+' — '+data['document']['title'],'author':data['document']['designer'],
                          'subject':'PRELIMINARE / DRAFT — scenario di calcolo con ipotesi dichiarate',
                          'producer':'Documentor Grid Society; native BTicino / ABB PDF symbols'})
        dst.set_toc([[1,p['title'],p['number']] for p in data['pages']])
        dst.save(output,deflate=True,garbage=0)
    return results

def norm(text):return ' '.join(text.split())

def verify(data,source_path,profile,output,records,qa):
    with fitz.open(output) as dst,fitz.open(source_path) as src:
        if len(dst)!=data['total']:raise ValueError('Wrong final page count')
        for item in data['pages']:
            page=dst[item['number']-1];text=norm(page.get_text())
            if 'PRELIMINARE / DRAFT' not in text or data['code'] not in text:
                raise ValueError('Missing identification/status in title block')
            if item['kind'] in ('assumptions','basis'):
                expected=[a[k] for a in data['notes']['assumptions'] for k in ('value','basis')]
                if item['kind']=='basis':expected+=data['notes']['findings']+data['notes']['open_checks']
            elif item['kind']=='checks':expected=data['notes']['findings']+data['notes']['open_checks']
            elif item['kind']=='engineering':
                view=item['view'];expected=[n['text'] for n in view['nodes'] if n['kind']=='box']
                expected += [l['text'] for l in view['labels']]
                expected += [cell for row in [view['table']['headers'],*view['table']['rows']] for cell in row]
            elif item['kind']=='cover' and 'cover' in data:
                expected=[data['cover'][k] for k in ('studio','owner','location','site_address','phase','subject','designer','professional_register')]
                expected += [r['description'] for r in data['cover']['revisions']]
            else:expected=[]
            if any(norm(e) not in text for e in expected):raise ValueError('Documentor notes clipped or incomplete')
        engineering_records=[r for r in records if r.get('kind')=='engineering']
        if engineering_records:engineering.verify_symbols(dst,engineering_records,data['symbols'],data['registry'])
        for r in records:
            if r.get('kind')=='engineering':continue
            page=dst[r['page']-1];original=src[r['source_page']]
            target=fitz.Rect(r['target_pt']);clip=fitz.Rect(r['clip_pt']);space=fitz.Rect(r['available_pt'])
            if not space.contains(target):raise ValueError('Native viewport outside title-block aperture')
            if abs(target.width/clip.width-target.height/clip.height)>1e-6:
                raise ValueError('Anisotropic distortion of native symbols')
            # Compare the WHOLE available space, not just the placed region:
            # catches stray banners, notices or other visible overlays too.
            with fitz.open() as control:
                cp=control.new_page(width=page.rect.width,height=page.rect.height)
                cp.show_pdf_page(target,src,r['source_page'],clip=clip,keep_proportion=True)
                a=cp.get_pixmap(matrix=fitz.Matrix(2,2),clip=space,alpha=False)
                b=page.get_pixmap(matrix=fitz.Matrix(2,2),clip=space,alpha=False)
                if (a.width,a.height,a.samples)!=(b.width,b.height,b.samples):
                    raise ValueError(f'Extra content or altered native rendering on page {r["page"]}')
            if not any(dst.xref_stream(x[0])==original.read_contents() for x in page.get_xobjects() if x[1]=='fullpage'):
                raise ValueError('Original native stream absent after saving')
            expected=Counter(w[4] for w in original.get_text('words',clip=clip))
            actual=Counter(w[4] for w in page.get_text('words',clip=target))
            if expected!=actual:raise ValueError('Technical text changed during clipping/composition')
            rendered_text=page.get_text(clip=space)
            if any(s in rendered_text for s in profile['forbidden_visible_text']):
                raise ValueError('Native footer visible in drawing area')
            r.update(stream_identical=True,technical_words_identical=True,available_area_pixels_identical_144dpi=True)
        for i,p in enumerate(dst):p.get_pixmap(matrix=fitz.Matrix(1.3,1.3)).save(qa/f'page-{i+1}.png')
    return {'integrity':'PASS','layout':'PASS automatic viewport/text checks; visual review recorded separately',
            'electrical_approval':'OPEN','pages':records,'output_sha256':sha(output)}

def build(request_path,bundle_path,fmt='A3'):
    request,bundle,paths,profile,detections,csv_check,report_check=inspect_bundle(request_path,bundle_path)
    case=Path(request_path).resolve().parent
    data=document_data(request,bundle,fmt,case);code=data['output_name']
    extension_hash=digest({'model':data['engineering'],'cover':data['cover'],'symbols':data['symbols'],'registry':data['registry']})
    out=output_root();out.mkdir(exist_ok=True)
    target_dir=out/code
    request_hash=digest(request)
    if (target_dir/'manifest.json').exists():
        prior=read(target_dir/'manifest.json')
        if prior['request_sha256']!=request_hash or prior['native_bundle_sha256']!=digest(bundle) or prior.get('extension_sha256')!=extension_hash:
            raise ValueError('Same filename with changed request/exports: increment document revision')
    with tempfile.TemporaryDirectory(prefix='v5-build-',dir=out) as temp:
        work=Path(temp);qa=work/'qa';qa.mkdir()
        write(work/'document-variables.json',data)
        frames=render_frames(data,work)
        final=work/(code+'.pdf');records=compose(data,frames,paths['pdf'],detections,final)
        qa_report=verify(data,paths['pdf'],profile,final,records,qa)
        write(qa/'engineering-graph.json',engineering.validate(data['engineering'],data['symbols'],data['registry']))
        write(qa/'preservation.json',qa_report);write(qa/'csv-reconciliation.json',csv_check)
        write(qa/'native-report-checks.json',report_check)
        if (root()/'research/design-basis.json').exists():
            from .checks import evaluate
            write(qa/'engineering-screening.json',evaluate(case))
        dependencies=[Path(request_path).resolve(),Path(bundle_path).resolve(),*paths.values(),root()/'profiles'/(bundle['profile']+'.json'),root()/'docs/documentor.toml',root()/'docs/template_metadata.json',root()/'assets/logo-grid-society.svg']
        dependencies+=sorted((root()/'docs/templates').rglob('*.html'))
        dependencies += [case/'cover.json',case/'engineering.json',root()/'profiles/native-symbols.json',root()/'sources/registry.json',root()/'research/tisystem-capabilities.json']
        if data['cover'].get('stamp'):dependencies.append(confined(root(),data['cover']['stamp']))
        dependencies += [root()/s['path'] for s in data['registry'].values()]
        manifest={'backend':'bticino','extension_sha256':extension_hash,'document':code,'status':'DRAFT','registered':False,'published':False,'request_sha256':request_hash,
                  'native_bundle_sha256':digest(bundle),'created_at':datetime.now(timezone.utc).isoformat(),
                  'source_model_revision':bundle['native_revision'],'document_revision':request['document']['revision'],
                  'dependencies':{str(p.relative_to(root())):sha(p) for p in dependencies},
                  'engine':{p.name:sha(p) for p in sorted(Path(__file__).parent.glob('*.py'))},
                  'pymupdf':fitz.VersionBind,'files':{str(p.relative_to(work)):sha(p) for p in sorted(work.rglob('*')) if p.is_file()}}
        write(work/'manifest.json',manifest)
        target_dir.mkdir(exist_ok=True)
        for p in sorted(work.rglob('*')):
            if p.is_file():
                dest=target_dir/p.relative_to(work);dest.parent.mkdir(exist_ok=True,parents=True);p.replace(dest)
    return target_dir/(code+'.pdf')

def verify_package(package):
    package=Path(package).resolve();manifest=read(package/'manifest.json')
    for name,h in manifest['files'].items():
        if sha(confined(package,name))!=h:raise ValueError('Output package changed: '+name)
    for name,h in manifest['dependencies'].items():
        if sha(confined(root(),name))!=h:raise ValueError('Rebuild required: '+name)
    for name,h in manifest['engine'].items():
        if sha(confined(Path(__file__).parent,name))!=h:raise ValueError('BTicino engine changed: '+name)
    return {'status':'PASS','document':manifest['document'],'files':len(manifest['files']),
            'scope':'Package and build-dependency integrity, not electrical approval'}
