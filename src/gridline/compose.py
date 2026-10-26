"""Compose existing engineering views; the agent owns the electrical topology."""
from pathlib import Path
import json, hashlib, re, xml.etree.ElementTree as E
from .paths import RESOURCES, project_file
from .workspace import check

def render(project,output=None):
 import fitz
 from .sheet_frame import border,titleblock,label
 from .svg_primitives import explicit_dashes
 project=Path(project).resolve()
 errors=check(project)["errors"]
 if errors:raise ValueError("Invalid project: " + "; ".join(errors))
 m=json.loads((project/'variables/drawing-set.json').read_text(encoding="utf-8"));pages=m['pages'];book=fitz.open();metrics=[]
 if not pages:raise ValueError('No pages')
 if any(p.get('kind')=='general' for p in pages[ next((i for i,p in enumerate(pages) if p.get('kind')=='detail'),len(pages)):]):raise ValueError('General sheets must precede details')
 logo=E.parse(RESOURCES/'brand/logo.svg').getroot()
 css=' '.join(e.text or '' for e in logo.iter() if e.tag.endswith('style'));rules={n:b for n,b in re.findall(r'\.([\w-]+)\s*\{([^}]+)\}',css)}
 for e in logo.iter():
  for c in e.get('class','').split():
   for item in rules.get(c,'').split(';'):
    if ':' in item:k,v=item.split(':',1);e.set(k.strip(),v.strip())
 ld=fitz.open(stream=E.tostring(logo),filetype='svg');logo_pdf=fitz.open('pdf',ld.convert_to_pdf())
 for i,s in enumerate(pages,1):
  f=project_file(project,s['source'])
  if f.suffix.lower()=='.svg':
   svg=E.parse(f).getroot()
   # Existing SVGs must use actual dash geometry or renderer-compatible dash arrays.
   for e in svg.iter():e.tag=e.tag.split('}')[-1]
   svg.set('xmlns','http://www.w3.org/2000/svg');explicit_dashes(svg)
   src=fitz.open(stream=E.tostring(svg),filetype='svg');src=fitz.open('pdf',src.convert_to_pdf());page=0
  else:src=fitz.open(f);page=s.get('source_page',0)
  clip=fitz.Rect(s['clip']) if s.get('clip') else src[page].rect
  if not src[page].rect.contains(clip) or clip.is_empty:raise ValueError('Invalid viewport '+str(clip))
  mm=72/25.4;w=s.get('width_mm',420)*mm;margin=15*mm;dw=w-2*margin-16;dh=dw*clip.height/clip.width;top=margin+42;h=top+dh+56+142+margin
  p=book.new_page(width=w,height=h);inner=border(p)
  label(p,(inner.x0+8,inner.y0+8,inner.x1-8,inner.y0+38),s['title'],16,True)
  target=fitz.Rect(inner.x0+8,top,inner.x1-8,top+dh);p.show_pdf_page(target,src,page,clip=clip)
  bt=titleblock(p,inner,s['title'],i,s.get('variant','-'),s['kind']=='detail',m,logo_pdf,len(pages))
  label(p,(inner.x0+8,bt-44,inner.x1-8,bt-26),s.get('note',''),9)
  label(p,(inner.x0+8,bt-24,inner.x1-8,bt-5),'Anteprima vettoriale - validazione elettrica e resa nativa QET distinte dalla revisione grafica.',8)
  metrics.append(dict(page=i,width_mm=round(w/mm,2),height_mm=round(h/mm,2),source_sha256=hashlib.sha256(f.read_bytes()).hexdigest(),width_fraction=round(dw/inner.width,4)))
 out=Path(output) if output else project/'out'/f"{m['code']}_{m['slug']}_{m['revision']}.pdf";out.parent.mkdir(parents=True,exist_ok=True)
 book.set_metadata(dict(title=m['title'],author='Grid Society'));book.set_toc([[1,s['title'],i] for i,s in enumerate(pages,1)])
 from .documentor_bridge import generate
 final=generate(project,book,m,pages,out)
 for i,p in enumerate(final):
  fac=min(1600/p.rect.width,2000/p.rect.height);p.get_pixmap(matrix=fitz.Matrix(fac,fac)).save(out.parent/f'{out.stem}-page-{i+1:02d}.png')
 (out.parent/(out.stem+'-qa.json')).write_text(json.dumps(metrics,indent=2))
 return out
