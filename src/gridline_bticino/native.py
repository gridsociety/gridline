"""Recognize native vector frames and expose their technical interior unchanged."""
from __future__ import annotations
from .context import root
from collections import Counter
import hashlib
import re
import fitz
from .model import italian_number

MM=72/25.4

def segments(page):
    horizontal=[];vertical=[]
    def add(a,b):
        if abs(a.y-b.y)<.02:horizontal.append((min(a.x,b.x),a.y,max(a.x,b.x)))
        if abs(a.x-b.x)<.02:vertical.append((a.x,min(a.y,b.y),max(a.y,b.y)))
    for drawing in page.get_drawings():
        for item in drawing['items']:
            if item[0]=='l':add(item[1],item[2])
            elif item[0]=='re':
                r=item[1]
                for a,b in [(r.tl,r.tr),(r.bl,r.br),(r.tl,r.bl),(r.tr,r.br)]:add(a,b)
    return horizontal,vertical

def unique(values,message,tolerance=.1):
    if not values or max(values)-min(values)>tolerance:raise ValueError(message)
    return sum(values)/len(values)

def detect(page,profile,expected_kind=None):
    if page.rotation or page.cropbox!=page.mediabox:
        raise ValueError('Source page rotation/crop is not supported')
    if any(abs(a-b)>profile['page_tolerance_pt'] for a,b in zip((page.rect.width,page.rect.height),profile['page_size_pt'])):
        raise ValueError('Unrecognized native page size')
    if profile['producer_contains'] not in (page.parent.metadata.get('producer') or ''):
        raise ValueError('Unrecognized native PDF producer')
    h,v=segments(page)
    words=page.get_text('words')
    label_rows=[]
    for label in profile['coordinate_labels']:
        matches=[w for w in words if w[4]==label and 10<w[1]<25 and w[3]<36]
        if len(matches)!=1:raise ValueError('Unrecognized coordinate header')
        label_rows.append(matches[0])
    row_bottom=unique([w[3] for w in label_rows],'Coordinate labels not aligned',.2)
    top=unique([y for x,y,z in h if z-x>800 and 0<y-row_bottom<3 and profile['top_border_range_pt'][0]<=y<=profile['top_border_range_pt'][1]],'Ambiguous technical top border')
    anchors=[]
    for label in profile['footer_anchors']:
        low,high=profile['bottom_border_range_pt']
        found=[r for r in page.search_for(label) if low<=r.y0<=high+1]
        if len(found)!=1:raise ValueError('Missing or ambiguous native footer')
        anchors.append(found[0].y0)
    footer_y=unique(anchors,'Footer anchors not aligned',.3)
    bottom=unique([y for x,y,z in h if z-x>800 and 0<footer_y-y<1 and profile['bottom_border_range_pt'][0]<=y<=profile['bottom_border_range_pt'][1]],'Ambiguous technical bottom border')
    boundaries=[]
    for name in ('left','right'):
        low,high=profile[name+'_border_range_pt']
        lines=[(x,a,b) for x,a,b in v if low<=x<=high and a>=top-.5 and b<=bottom+.5]
        x=unique([x for x,a,b in lines],f'Ambiguous {name} border',.15)
        intervals=sorted((a,b) for _,a,b in lines)
        reach=top
        for a,b in intervals:
            if a-reach>1:raise ValueError('Broken native frame boundary')
            reach=max(reach,b)
        if reach<bottom-.5:raise ValueError('Incomplete native frame boundary')
        boundaries.append(x)
    clip=fitz.Rect(boundaries[0],top,boundaries[1],bottom)
    if not 480<clip.height<490 or not 772<clip.width<776:
        raise ValueError('Unsupported technical frame proportions')
    # Any partly cut glyph would risk losing technical data; stop instead.
    for w in words:
        wr=fitz.Rect(w[:4])
        if not (wr & clip).is_empty and not clip.contains(wr):
            raise ValueError(f'Crop would cut text: {w[4]}')
    text=page.get_text(clip=clip)
    kind='legend' if profile['legend_anchor'] in text else 'single_line'
    if kind=='single_line' and not all(x in text for x in profile['single_line_anchors']):
        raise ValueError('Unrecognized technical content')
    if expected_kind and kind!=expected_kind:raise ValueError('Native page type does not match manifest')
    if any(s in text for s in profile['forbidden_visible_text']):
        raise ValueError('Vendor furniture leaked into technical viewport')
    return {'clip_pt':list(clip),'kind':kind,'source_stream_sha256':hashlib.sha256(page.read_contents()).hexdigest(),
            'technical_words':len(page.get_text('words',clip=clip)),
            'anchors':{'coordinate_header_bottom_pt':row_bottom,'footer_text_top_pt':footer_y}}

def available(fmt):
    w,h={'A3':(420,297),'A4':(297,210)}[fmt]
    # Shared cartiglio: 9 mm frame, 15 mm fascia, bottom 10.3 mm.
    # 1 mm clearance from frame and title block; no header/notice/source line.
    return fitz.Rect(10*MM,10*MM,(w-10)*MM,(h-26.3)*MM)

def fit(source,space):
    scale=min(space.width/source.width,space.height/source.height)
    w,h=source.width*scale,source.height*scale
    return fitz.Rect(space.x0+(space.width-w)/2,space.y0+(space.height-h)/2,
                     space.x0+(space.width+w)/2,space.y0+(space.height+h)/2)

def text_sizes(page,clip):
    sizes=Counter(round(s['size'],3) for b in page.get_text('dict',clip=clip)['blocks'] if 'lines' in b
                  for line in b['lines'] for s in line['spans'] if s['text'].strip())
    return sizes.most_common(1)[0][0]

def check_native_reports(request,source,report):
    """Qualify the observed TiSystem Iz discrepancy without rewriting the table."""
    findings=[];records=[]
    for circuit in request['design']['circuits']:
        label=circuit['id']+' '+circuit['label']
        matches=[(p,p.search_for(label)) for p in source if p.search_for(label)]
        if len(matches)!=1 or len(matches[0][1])!=1:raise ValueError('Circuit description missing/ambiguous in native PDF')
        page,positions=matches[0];left=positions[0].x0
        iz=page.search_for('Iz [A]')
        if len(iz)!=1:raise ValueError('Native Iz row cannot be identified')
        vals=[w[4] for w in page.get_text('words') if abs(w[0]-left)<1 and abs(w[1]-iz[0].y0)<2]
        if len(vals)!=1:raise ValueError('Native circuit Iz cell cannot be identified')
        drawing_value=italian_number(vals[0])
        rp=[p for p in report if label in p.get_text()]
        if len(rp)!=1:raise ValueError('Circuit report missing/ambiguous')
        text=rp[0].get_text()
        m=re.search(r'Portata Iz \[A\]:\s*([\d.,]+)',text)
        k=re.search(r'K temperatura:\s*([\d.,]+)',text)
        if not m or not k:raise ValueError('Report Iz/temperature factor missing')
        report_value,factor=italian_number(m[1]),italian_number(k[1])
        records.append({'circuit':circuit['id'],'drawing_Iz_A':drawing_value,'report_Iz_A':report_value,
                        'report_K_temperature':factor,'ratio_consistent':abs(drawing_value*factor-report_value)<.01})
        if abs(drawing_value-report_value)>.01:
            findings.append('TISYSTEM_IZ_EXPORT_DIFFERENCE')
    return {'status':'REVIEW' if findings else 'PASS','findings':sorted(set(findings)),'circuits':records,
            'scope':'Observed Iz fields; cause inferred from factor, not manufacturer-confirmed semantics'}
