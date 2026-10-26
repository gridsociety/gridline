"""Traceable connection views. Electrical glyphs are immutable PDF clips.
SVG contains only conductors, labels, tables, boundaries and functional boxes.
Coordinates are mm in a format-independent drawing viewport.
"""
from __future__ import annotations
from .context import root
from html import escape
import math
import fitz
from .model import read,sha,confined
from .native import available,fit

MM=72/25.4
STYLES={'power':('#111',''),'measure':('#111','2 1'),'ethernet':('#16718b',''),
        'oem_link':('#555','3 1'),'dedicated_data':('#08785c','3 1'), 'dry_contact':('#222','1.4 1')}

def load(case):
    model=read(case/'engineering.json');symbols=read(root()/'profiles/native-symbols.json')
    registry=read(root()/'sources/registry.json')
    for id,s in registry.items():
        if sha(confined(root(),s['path']))!=s['sha256']:raise ValueError('Engineering source changed: '+id)
    for id,s in symbols.items():
        if s['source'] not in registry:raise ValueError('Unknown symbol source: '+id)
        path=confined(root(),registry[s['source']]['path'])
        with fitz.open(path) as src:
            if not 0<=s['page']<len(src):raise ValueError('Invalid symbol page')
            rect=fitz.Rect(s['clip'])
            if rect.is_empty or not src[s['page']].rect.contains(rect):raise ValueError('Invalid native clip')
            for point in s['ports'].values():
                if not (rect.x0<=point[0]<=rect.x1 and rect.y0<=point[1]<=rect.y1):raise ValueError('Native port outside clip')
    validate(model,symbols,registry)
    return model,symbols,registry

def geometry(n,symbols):
    if n['kind']=='symbol':
        s=symbols[n['glyph']];c=fitz.Rect(s['clip']);scale=n['h']/c.height
        # Place first terminal on the node's declared electrical axis.
        left=n['x']-(s['ports']['in'][0]-c.x0)*scale
        rect=fitz.Rect(left,n['y'],left+c.width*scale,n['y']+n['h'])
        ports={key:[left+(p[0]-c.x0)*scale,n['y']+(p[1]-c.y0)*scale] for key,p in s['ports'].items()}
        return rect,ports
    rect=fitz.Rect(n['x'],n['y'],n['x']+n['w'],n['y']+n['h'])
    return rect,{k:[n['x']+v[0]*n['w'],n['y']+v[1]*n['h']] for k,v in n['ports'].items()}

def connections(page,symbols):
    ports={n['id']+'.'+key:pt for n in page['nodes'] for key,pt in geometry(n,symbols)[1].items()}
    return {e['id']:[ports[e['from_port']],*e['via'],ports[e['to_port']]] for e in page['edges']}

def validate(model,symbols,registry):
    if model['scope']!='PRELIMINARE' or model['engineering_approval'] is not None:
        raise ValueError('Preliminary workflow cannot mark electrical approval')
    if len({p['id'] for p in model['pages']})!=len(model['pages']):raise ValueError('Duplicate view id')
    for p in model['pages']:
        def number(value):
            if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
                raise ValueError('Non-finite drawing geometry')
        for key in ('width','height'):
            number(p[key])
            if p[key]<=0:raise ValueError('Invalid drawing dimensions')
        for label in p['labels']:
            for key in ('x','y','size'):number(label[key])
        for region in p['regions']:
            for key in ('x','y','w','h'):number(region[key])
        number(p['table']['y'])
        for width in p['table']['columns']:
            number(width)
            if width<=0:raise ValueError('Invalid table column width')
        nodes=p['nodes'];ids=[n['id'] for n in nodes]
        if len(set(ids))!=len(ids):raise ValueError('Duplicate node id')
        edgeids=[e['id'] for e in p['edges']]
        if len(set(edgeids))!=len(edgeids):raise ValueError('Duplicate connection id')
        for n in nodes:
            if n['source'] not in registry or not n['status']:raise ValueError('Untraced component')
            if n['kind'] not in ('symbol','box','junction'):raise ValueError('Unsupported node type')
            if any(not isinstance(n[k],(int,float)) or isinstance(n[k],bool) or not math.isfinite(n[k]) for k in ('x','y','w','h')):
                raise ValueError('Non-finite geometry')
            if n['kind']=='symbol' and n['glyph'] not in symbols:raise ValueError('Unknown native symbol')
            rect,_=geometry(n,symbols)
            if not fitz.Rect(0,0,p['width'],p['height']).contains(rect):raise ValueError('Component outside viewport')
        try:paths=connections(p,symbols)
        except KeyError as e:raise ValueError('Missing connection port: '+str(e)) from e
        for e in p['edges']:
            if e['medium'] not in STYLES or e['source'] not in registry:raise ValueError('Untraced connection')
            for a,b in zip(paths[e['id']],paths[e['id']][1:]):
                if any(not math.isfinite(v) for v in a+b):raise ValueError('Non-finite route')
                if abs(a[0]-b[0])>.01 and abs(a[1]-b[1])>.01:raise ValueError('Non-orthogonal route: '+e['id'])
                if not all(0<=pt[0]<=p['width'] and 0<=pt[1]<=p['height'] for pt in (a,b)):raise ValueError('Route outside viewport')
        t=p['table']
        if abs(sum(t['columns'])-p['width'])>.01 or any(len(row)!=len(t['columns']) for row in [t['headers'],*t['rows']]):
            raise ValueError('Invalid table geometry')
    return {'state':'PASS','scope':'Sources, graph endpoints, orthogonal routes and geometry; no electrical calculations',
            'views':len(model['pages']),'connections':sum(len(p['edges']) for p in model['pages'])}

def svg(page,symbols):
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {page["width"]} {page["height"]}" width="100%" height="100%" preserveAspectRatio="xMidYMid meet">',
         '<g font-family="Arial, Helvetica, sans-serif" fill="#111" stroke-linecap="square">']
    def text(x,y,lines,size=3,anchor='start',weight='normal'):
        for i,line in enumerate(str(lines).split('\n')):
            out.append(f'<text x="{x}" y="{y+i*size*1.3}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}">{escape(line)}</text>')
    for r in page['regions']:
        out.append(f'<rect x="{r["x"]}" y="{r["y"]}" width="{r["w"]}" height="{r["h"]}" fill="none" stroke="#999" stroke-width=".18" stroke-dasharray="2 1"/>')
        text(r['x']+2,r['y']-2,r['text'],3,weight='bold')
    paths=connections(page,symbols)
    for e in page['edges']:
        color,dash=STYLES[e['medium']];pts=' '.join(f'{x:.5f},{y:.5f}' for x,y in paths[e['id']])
        out.append(f'<polyline points="{pts}" stroke="{color}" stroke-width=".23" fill="none" stroke-dasharray="{dash}"/>')
    for n in page['nodes']:
        if n['kind']=='symbol':continue # inserted from native PDF after Documentor
        if n['kind']=='junction':
            if n['id'] not in ('GRID','BUS'):out.append(f'<circle cx="{n["x"]}" cy="{n["y"]}" r=".6"/>')
        elif n['kind']=='box':
            out.append(f'<rect x="{n["x"]}" y="{n["y"]}" width="{n["w"]}" height="{n["h"]}" fill="white" stroke="#111" stroke-width=".23"/>')
            lines=n['text'].split('\n');size=3
            # Fit long model labels without clipping, down to a declared legibility floor.
            font=fitz.Font('helv');maxlen=max(font.text_length(t,fontsize=1) for t in lines)
            size=min(size,(n['w']-4)/max(maxlen,1))
            if size<2.5:raise ValueError('Box text too small: '+n['id'])
            text(n['x']+n['w']/2,n['y']+n['h']/2-(len(lines)-1)*size*.65+size*.32,n['text'],size,'middle')
    for l in page['labels']:text(l['x'],l['y'],l['text'],l['size'])
    t=page['table'];y=t['y'];rowh=6.1;font=fitz.Font('helv')
    for rid,row in enumerate([t['headers'],*t['rows']]):
        x=0
        for w,cell in zip(t['columns'],row):
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{rowh}" fill="{("#f0f0f0" if rid==0 else "white")}" stroke="#777" stroke-width=".16"/>')
            size=min(2.65,(w-3)/max(font.text_length(cell,fontsize=1),1))
            if size<2.35:raise ValueError('Table text too small: '+cell)
            text(x+1.5,y+4,cell,size,weight='bold' if rid==0 else 'normal');x+=w
        y+=rowh
    out.append('</g></svg>');return ''.join(out)

def place_native(page,view,fmt,symbols,registry):
    frame=fit(fitz.Rect(0,0,view['width'],view['height']),available(fmt));scale=frame.width/view['width']
    records=[]
    for n in view['nodes']:
        if n['kind']!='symbol':continue
        s=symbols[n['glyph']];rect,ports=geometry(n,symbols)
        target=fitz.Rect(frame.x0+rect.x0*scale,frame.y0+rect.y0*scale,frame.x0+rect.x1*scale,frame.y0+rect.y1*scale)
        with fitz.open(confined(root(),registry[s['source']]['path'])) as src:
            original=src[s['page']];xref=page.show_pdf_page(target,src,s['page'],clip=fitz.Rect(s['clip']),keep_proportion=True)
            if page.parent.xref_stream(xref)!=original.read_contents():raise ValueError('Original symbol operators changed')
        records.append({'node':n['id'],'glyph':n['glyph'],'source':s['source'],'source_page':s['page'],
                        'clip_pt':s['clip'],'target_pt':list(target),'native_stream_identical':True})
    return records

def verify_symbols(doc,records,symbols,registry):
    for rec in records:
        p=doc[rec['page']-1]
        for r in rec['symbols']:
            with fitz.open(confined(root(),registry[r['source']]['path'])) as src:
                original=src[r['source_page']]
                if not any(doc.xref_stream(x[0])==original.read_contents() for x in p.get_xobjects() if x[1]=='fullpage'):
                    raise ValueError('Original OEM PDF stream absent')
                c=fitz.Rect(r['clip_pt']);t=fitz.Rect(r['target_pt'])
                if abs(t.width/c.width-t.height/c.height)>1e-5:raise ValueError('Native symbol distorted')
    return {'status':'PASS','scope':'Native PDF streams and uniform glyph scale, not equipment approval','symbols':sum(len(r['symbols']) for r in records)}
