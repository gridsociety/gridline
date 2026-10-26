import fitz
mm=72/25.4
INK=(.12,.16,.18)
checks=[]
def label(p,r,text,size=9,bold=False,align=0):
 r=fitz.Rect(r);name='hebo' if bold else 'helv';font=fitz.Font(name);lines=[]
 for para in text.splitlines():
  current=''
  for word in para.split():
   trial=(current+' '+word).strip()
   if current and fitz.get_text_length(trial,fontname=name,fontsize=size)>r.width:
    lines.append(current);current=word
   else:current=trial
  lines.append(current)
 needed=(font.ascender-font.descender)*size+max(0,len(lines)-1)*size*1.2
 assert needed<=r.height+.1,(text,r,needed)
 for i,t in enumerate(lines):
  tw=fitz.get_text_length(t,fontname=name,fontsize=size)
  assert tw<=r.width+.1,(text,tw,r.width)
  x=r.x0+(r.width-tw)/2 if align==1 else r.x0
  p.insert_text((x,r.y0+font.ascender*size+i*size*1.2),t,fontsize=size,fontname=name,color=INK)
def line(p,a,b):p.draw_line(a,b,color=INK,width=.55)
def box(p,r):p.draw_rect(fitz.Rect(r),color=INK,width=.65)
def letter(n):
 s=''
 while n>=0:s=chr(65+n%26)+s;n=n//26-1
 return s

def border(p):
 w,h=p.rect.width,p.rect.height;o=8*mm;band=7*mm;strip=1.3*mm
 inner=fitz.Rect(o+band,o+band,w-o-band,h-o-band)
 box(p,(o,o,w-o,h-o));box(p,inner)
 nx=max(6,round(inner.width/(85*mm)));ny=max(4,round(inner.height/(75*mm)))
 dx=inner.width/nx;dy=inner.height/ny
 for i in range(nx):
  x=inner.x0+i*dx
  for y in [o,h-o-band]:
   if i%2==0:
    sy=o if y==o else h-o-strip
    p.draw_rect(fitz.Rect(x,sy,x+dx,sy+strip),color=None,fill=(0,0,0))
   line(p,(x,y),(x,y+band))
   label(p,(x,y+2,x+dx,y+band),str(i+1),10,True,1)
 for i in range(ny):
  y=inner.y0+i*dy
  for x in [o,w-o-band]:
   if i%2==0:
    sx=o if x==o else w-o-strip
    p.draw_rect(fitz.Rect(sx,y,sx+strip,y+dy),color=None,fill=(0,0,0))
   line(p,(x,y),(x+band,y))
   label(p,(x+2,y+dy/2-7,x+band-2,y+dy/2+11),letter(i),9,True,1)
 return inner

def titleblock(p,inner,title,idx,variant,detail,meta,logo_pdf,total):
 # Equal-height, independently boxed blocks at lower left and lower right.
 bottom=inner.y1;top=bottom-142;right=inner.x1;left=right-630
 box(p,(left,top,right,bottom));line(p,(left+120,top),(left+120,bottom))
 p.show_pdf_page(fitz.Rect(left+10,top+10,left+110,top+74),logo_pdf,0)
 label(p,(left+8,top+80,left+116,top+98),'GRID SOCIETY S.R.L.',9,True)
 label(p,(left+8,top+100,left+116,bottom-4),'Bergamo (BG)\nP.IVA 04696750167\nsupporto@gridsociety.com',7)
 x=left+120
 for y in [top+40,top+85,top+114]:line(p,(x,y),(right,y))
 label(p,(x+8,top+4,right-8,top+16),'OGGETTO DELLA TAVOLA',7)
 label(p,(x+8,top+17,right-8,top+38),title,10,True)
 label(p,(x+8,top+44,right-8,top+57),meta['client'],9,True)
 label(p,(x+8,top+59,right-8,top+82),meta['site']+'\nPOD '+meta.get('pod','DA DEFINIRE'),8)
 for xx in [x+240,x+375]:line(p,(xx,top+85),(xx,bottom))
 label(p,(x+8,top+88,x+236,top+111),f"{meta['code']}-{idx:03d}",9,True)
 label(p,(x+247,top+88,x+370,top+111),meta['revision']+' | '+meta['date'],8)
 label(p,(x+382,top+88,right-5,top+111),f'FOGLIO {idx:02d} / {total:02d}',10,True)
 label(p,(x+8,top+119,x+236,bottom-3),meta.get('status','PRELIMINARE')+' | SCALA NTS',9,True)
 label(p,(x+247,top+119,right-5,bottom-3),f'VISTA {"DETTAGLIO" if detail else "GENERALE"} | ALTERNATIVA {variant}',8)
 if detail:
  hx=inner.x0;hw=min(460,left-hx-24);box(p,(hx,top,hx+hw,bottom))
  label(p,(hx+8,top+5,hx+hw-8,top+23),'STORICO REVISIONI',10,True)
  line(p,(hx,top+26),(hx+hw,top+26))
  for xx in [hx+42,hx+115]:line(p,(xx,top+26),(xx,bottom))
  rows=[(r['revision'],r['date'],r['description']) for r in meta['revisions'][:5]]
  for i,(rev,date,desc) in enumerate(rows):
   yy=top+26+i*23.2
   if i:line(p,(hx,yy),(hx+hw,yy))
   label(p,(hx+6,yy+6,hx+40,yy+22),rev,8,True)
   label(p,(hx+48,yy+6,hx+113,yy+22),date,8)
   label(p,(hx+122,yy+6,hx+hw-5,yy+22),desc,8)
 return top
