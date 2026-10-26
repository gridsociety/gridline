import xml.etree.ElementTree as E
import math
def at(**kw):return {k:str(v) for k,v in kw.items()}

def svgtext(parent,x,y,s,size=15,bold=False,color='#111111'):
    for i,line in enumerate(s.splitlines()):
        t=E.SubElement(parent,'text',at(x=x,y=y+i*(size+5),fill=color,**{'font-family':'Arial','font-size':size,'font-weight':'bold' if bold else 'normal'}));t.text=line

def explicit_dashes(parent):
    # MuPDF's SVG importer drops dash arrays. Emit the actual dash geometry.
    for index,e in enumerate(list(parent)):
        explicit_dashes(e)
        if not e.get('stroke-dasharray'):continue
        if e.tag=='rect':
            x,y,w,h=[float(e.get(k)) for k in ['x','y','width','height']]
            pts=[(x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y)]
        elif e.tag=='polyline':pts=[tuple(map(float,z.split(','))) for z in e.get('points').split()]
        else:continue
        dash,gap=map(float,e.get('stroke-dasharray').split())
        g=E.Element('g',{k:v for k,v in e.attrib.items() if k.startswith('data-')})
        for a,b in zip(pts,pts[1:]):
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            if not length:continue
            start=0
            while start<length:
                end=min(start+dash,length)
                E.SubElement(g,'line',**at(x1=a[0]+dx*start/length,y1=a[1]+dy*start/length,x2=a[0]+dx*end/length,y2=a[1]+dy*end/length,stroke=e.get('stroke','#111111'),**{'stroke-width':e.get('stroke-width','1.5')}))
                start+=dash+gap
        parent.remove(e);parent.insert(index,g)

def symbol(parent,definition,x,y,o):
    g=E.SubElement(parent,'g',transform=f'translate({x} {y}) rotate({90*o})')
    for e in definition.find('description'):
        tag=e.tag;s=e.get('style','');kw={'stroke':'#111111','stroke-width':'1.5','fill':'#111111' if 'filling:black' in s else 'white' if 'filling:white' in s else 'none'}
        if 'line-style:dashed' in s:kw['stroke-dasharray']='7 4'
        if tag in ['line','rect','ellipse']:
            keys={'line':['x1','x2','y1','y2'],'rect':['x','y','width','height','rx','ry'],'ellipse':[]}[tag]
            if tag=='ellipse':
                xx,yy,ww,hh=[float(e.get(k)) for k in ['x','y','width','height']]
                E.SubElement(g,'ellipse',at(cx=xx+ww/2,cy=yy+hh/2,rx=ww/2,ry=hh/2,**kw))
            else:E.SubElement(g,tag,{**{k:e.get(k) for k in keys if e.get(k) is not None},**kw})
        elif tag=='polygon':
            pts=[];i=1
            while e.get(f'x{i}') is not None:pts.append(e.get(f'x{i}')+','+e.get(f'y{i}'));i+=1
            if e.get('closed')!='false' and pts:pts.append(pts[0])
            E.SubElement(g,'polygon' if e.get('closed')!='false' else 'polyline',points=' '.join(pts),**kw)
        elif tag=='arc':
            xx,yy,ww,hh,st,an=[float(e.get(k)) for k in ['x','y','width','height','start','angle']]
            pts=[]
            for i in range(65):
                t=math.radians(st+an*i/64);pts.append(f'{xx+ww/2+ww/2*math.cos(t)},{yy+hh/2-hh/2*math.sin(t)}')
            E.SubElement(g,'polyline',points=' '.join(pts),**kw)
        elif tag=='text':svgtext(g,float(e.get('x')),float(e.get('y')),e.get('text',''),float(e.get('font','Arial,9').split(',')[1]))
        elif tag in ['terminal','dynamic_text','input']:pass
        else:raise ValueError('Unsupported primitive '+tag)
    return g
