"""Request contract, naming and immutable binding to native exports."""
from __future__ import annotations
from .context import root
import csv
from datetime import date
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import re


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def confined(root,value):
    result=(Path(root)/value).resolve()
    if not result.is_relative_to(Path(root).resolve()):
        raise ValueError(f'Path outside allowed workspace: {value}')
    return result

def finite(value, positive=False):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0 or (positive and value==0):
        raise ValueError(f'Invalid numeric value: {value!r}')
    return value

def validate_request(data):
    if data['schema_version']!=1:
        raise ValueError('Unsupported request schema')
    doc=data['document']
    for key in ('company','project','discipline','family'):
        if not re.fullmatch(r'[A-Z][A-Z0-9-]{0,23}',doc[key]):
            raise ValueError(f'Invalid document identifier: {key}')
    if doc['company']!='GS' or doc['status']!='DRAFT' or doc['approver']:
        raise ValueError('Grid Society unapproved DRAFT workflow only')
    if type(doc['sequence']) is not int or not 1<=doc['sequence']<=999 or not re.fullmatch(r'P\d{1,3}',doc['revision']):
        raise ValueError('Invalid sequence/revision')
    date.fromisoformat(doc['date'])
    if not all(doc[k].strip() for k in ('designer','customer','title','project_name')):
        raise ValueError('Missing document identification')
    for field in ('scope','change_description'):
        if field in doc and (not isinstance(doc[field],str) or not doc[field].strip()):
            raise ValueError('Invalid document description: '+field)
    design=data['design'];finite(design['voltage_V'],True)
    if not design['circuits']:
        raise ValueError('No circuits requested')
    ids=[];missing=[]
    for c in design['circuits']:
        if not re.fullmatch(r'[A-Z][A-Z0-9_-]{0,31}',c['id']):
            raise ValueError('Invalid circuit ID')
        ids.append(c['id'])
        for field,unit in [('power','kW'),('length','m')]:
            q=c[field]
            if q['unit']!=unit or q['status'] not in ('confirmed','assumed','proposed','missing') or not q['source'].strip():
                raise ValueError(f'Invalid quantity/provenance: {c["id"]}.{field}')
            if q['value'] is None:
                if q['status']!='missing':raise ValueError('Null must be explicitly missing')
                missing.append(c['id']+'.'+field)
            else:
                finite(q['value'],True)
                if q['status']=='missing':raise ValueError('Missing quantity has a value')
        if not 0<finite(c['cos_phi'],True)<=1:
            raise ValueError('Invalid cos phi')
        for field in ('phase_section_mm2','neutral_section_mm2','pe_section_mm2','requested_breaker_A'):
            if c[field] is not None:finite(c[field],True)
        if c['phases'] not in ('L1L2L3N','L1L2L3','L1N','L2N','L3N') or not all(c[k].strip() for k in ('label','from','to','installation')):
            raise ValueError('Missing topology/installation data')
    if len(ids)!=len(set(ids)):
        raise ValueError('Duplicate persistent circuit ID')
    return missing

def document_code(data):
    d=data['document']
    return f'{d["company"]}-{d["project"]}-{d["discipline"]}-{d["family"]}-{d["sequence"]:03d}'

def filename(data,fmt):
    if fmt not in ('A3','A4'):raise ValueError('Unsupported sheet format')
    return f'{document_code(data)}_{data["document"]["revision"]}_{fmt}_DRAFT'

def italian_number(text):
    text=text.strip()
    if not text:return None
    if not re.fullmatch(r'[+-]?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?',text):
        raise ValueError(f'Invalid Italian numeric field: {text}')
    return float(Decimal(text.replace('.','').replace(',','.')))

def validate_exports(request,bundle,case):
    missing=validate_request(request)
    if missing:raise ValueError('Resolve required native inputs before building: '+', '.join(missing))
    if bundle['schema_version']!=1 or bundle['profile']!='tisystem-technical-a4-v1':
        raise ValueError('Unsupported native export adapter')
    if bundle['design_sha256']!=digest(request['design']):
        raise ValueError('Native exports belong to a different design; recalculate and capture new exports')
    paths={}
    for key in ('pdf','csv','report','project'):
        item=bundle['files'][key];path=confined(case,item['path'])
        if sha(path)!=item['sha256']:raise ValueError(f'Native {key} changed since capture')
        paths[key]=path
    return paths

def reconcile_csv(request,bundle,path):
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f,delimiter=';'))
    indexed={}
    for row in rows:
        key=(row['Quadro'],row['Linea'])
        if key in indexed:raise ValueError('Duplicate native board/line')
        indexed[key]=row
    mapping=bundle['circuit_map']
    keys=[(m['board'],m['native_line']) for m in mapping]
    if len(keys)!=len(set(keys)) or len({m['id'] for m in mapping})!=len(mapping):
        raise ValueError('Duplicate circuit mapping')
    if set(indexed)!=set(keys):raise ValueError('Unmapped or missing native circuits')
    actual={}
    for m in mapping:
        row=indexed[m['board'],m['native_line']]
        if row['Codice articolo']!=m['expected_device']:
            raise ValueError('Device identity differs from captured map')
        actual[m['id']]=row
    checks=[]
    def match(cid,field,value,expected):
        if value is None or abs(value-expected)>0.005:
            raise ValueError(f'{cid}: {field} differs from requested value ({value} != {expected})')
        checks.append({'id':cid,'field':field,'actual':value,'expected':expected,'status':'PASS'})
    for c in request['design']['circuits']:
        if c['id'] not in actual:raise ValueError('Requested circuit absent from export')
        row=actual[c['id']];power=row['Potenza totale']
        if not power.endswith(' kW'):raise ValueError('Unexpected native power unit')
        match(c['id'],'power_kW',italian_number(power[:-3]),c['power']['value'])
        match(c['id'],'length_m',italian_number(row['Lunghezza linea a valle (m)']),c['length']['value'])
        match(c['id'],'cos_phi',italian_number(row['Cos ø']),c['cos_phi'])
        if row['Fasi della linea']!=c['phases']:raise ValueError('Native phases mismatch')
        if c['requested_breaker_A'] is not None:
            match(c['id'],'In_A',italian_number(row['Corrente nominale In (A)']),c['requested_breaker_A'])
        for field,col in [('phase_section_mm2','Sezione di fase (mm²)'),('neutral_section_mm2','Sezione di neutro (mm²)'),('pe_section_mm2','Sezione di PE (mm²)')]:
            if c[field] is None:continue
            m=re.fullmatch(r'1 x (\d+(?:,\d+)?)',row[col].strip())
            if not m:raise ValueError('Unsupported cable configuration; qualify a new adapter')
            match(c['id'],field,italian_number(m[1]),c[field])
    return {'status':'PASS','scope':'Requested CSV fields and native circuit identities; not electrical approval','checks':checks,'native_rows':actual}
