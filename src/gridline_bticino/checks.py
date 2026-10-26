from .context import root
"""Independent screening of exported results; not an executive design engine.

BT values are read from the immutable native CSV and detailed PDF. MT inputs
are explicitly declared in design-basis.json with OEM source/conditions.
PASS describes only the named criterion and never implies equipment approval.
"""
import math
import re
import fitz
from .model import  read, finite, italian_number, sha
from .pipeline import inspect_bundle


def three_phase_current(power_kw, voltage_v, cos_phi=1):
    finite(power_kw, True); finite(voltage_v, True); finite(cos_phi, True)
    if cos_phi > 1:
        raise ValueError('cos_phi must be at most 1')
    return power_kw * 1000 / (math.sqrt(3) * voltage_v * cos_phi)


def ampacity_ok(ib, setting, iz):
    for value in (ib, setting, iz):
        finite(value, True)
    return ib <= setting <= iz


def mt_screen(data):
    for key in ('apparent_kVA','voltage_V','length_m','section_mm2','k_adiabatic',
                'fault_duration_s','fault_kA','ampacity_A','resistance_ohm_km',
                'reactance_ohm_km','cos_phi'):
        finite(data[key], True)
    if data['cos_phi'] > 1:
        raise ValueError('Invalid power factor')
    ib = three_phase_current(data['apparent_kVA'], data['voltage_V'])
    drop = math.sqrt(3)*ib*data['length_m']/1000*(
        data['resistance_ohm_km']*data['cos_phi']+
        data['reactance_ohm_km']*math.sqrt(1-data['cos_phi']**2))
    withstand = data['k_adiabatic']*data['section_mm2']/math.sqrt(data['fault_duration_s'])/1000
    return {'Ib_A':ib, 'drop_pct':drop/data['voltage_V']*100,
            'conductor_withstand_kA':withstand,
            'ampacity_status':'PASS' if ib <= data['ampacity_A'] else 'FAIL',
            'conductor_thermal_status':'PASS' if withstand >= data['fault_kA'] else 'FAIL',
            'scope':'Declared laying conditions; conductor thermal screening only. Screen/earth/relay coordination OPEN.'}


def field(text, label):
    m = re.search(re.escape(label)+r'\s*([\d.,]+)', text)
    if not m:
        raise ValueError('Native report missing field: '+label)
    return italian_number(m[1])


def evaluate(case):
    request,bundle,paths,_,_,csv,native = inspect_bundle(case/'request.json',case/'exports.json')
    basis = read(root()/'research/design-basis.json')
    iz_by_id = {c['circuit']:c['report_Iz_A'] for c in native['circuits']}
    results = []
    with fitz.open(paths['report']) as report:
        for c in request['design']['circuits']:
            ident = c['id']+' '+c['label']
            matches = [p.get_text() for p in report if ident in p.get_text()]
            if len(matches) != 1:
                raise ValueError('Ambiguous native circuit report: '+ident)
            text = matches[0];row = csv['native_rows'][c['id']]
            ib = italian_number(row['Corrente di impiego Ib (A)'])
            nominal = italian_number(row['Corrente nominale In (A)'])
            iz = iz_by_id[c['id']]
            icu = italian_number(row['Potere di interruzione (kA)'])
            fault = field(text,'Corrente di cortocircuito trifase massima [kA]:\ninizio linea')
            imin = italian_number(row['Icc F-PE - Min fine linea (kA)'])*1000
            im = field(text,'Intervento magnetico Im [A]:')
            drop = italian_number(row['c.d.t. effett. tratto/impianto (%)'].split('/')[1])
            drop_limit = field(text,'Cdt massima ammessa (%):')
            calc = three_phase_current(c['power']['value'],request['design']['voltage_V'],c['cos_phi'])
            selectivity = re.search(r'Valore di selettività:\s*(\S+)',text)
            if not selectivity:
                raise ValueError('Missing native selectivity result')
            results.append({'circuit':c['id'],'device':row['Codice articolo'],
                'Ib_native_A':ib,'Ib_independent_A':calc,'In_A':nominal,'Iz_report_A':iz,
                'Icu_kA':icu,'Icc_max_kA':fault,'Icc_min_FPE_A':imin,'Im_native_A':im,
                'voltage_drop_pct':drop,'drop_limit_pct':drop_limit,
                'checks':{
                    'Ib_reconciliation_0.2pct':'PASS' if abs(ib-calc)/calc <= .002 else 'FAIL',
                    'Ib_le_In_le_Iz':'PASS' if ampacity_ok(ib,nominal,iz) else 'FAIL',
                    'Icu_ge_Icc':'PASS' if icu >= fault else 'FAIL',
                    'voltage_drop':'PASS' if drop <= drop_limit else 'FAIL',
                    'Iccmin_ge_Im_screening':'PASS' if imin >= im else 'FAIL'},
                'native_selectivity':selectivity[1],
                'limitations':'Selectivity quoted from TiSystem. Full I²t, disconnection times, OEM curves, inrush and RCD choice remain OPEN.'})
    mt = mt_screen(basis['mt'])
    required = basis['requested_station_MW']*1000
    limits = {key:{'available_kVA':value,'required_kW_cos1':required,
                   'margin_kVA':value-required,'status':'PASS' if value >= required else 'FAIL'}
              for key,value in basis['oem_station'].items() if key.endswith(('kVA_30C','kVA_50C'))}
    return {'status':'PRELIMINARE — NOT APPROVED', 'electrical_approval':'OPEN',
            'native_checks':results,'MT':mt,'station_limits_at_1500Vdc':limits,
            'AUX_source_kVA':sum(c['power']['value']/c['cos_phi'] for c in request['design']['circuits']),
            'open':['OEM AUX consumption/inrush','Station external AUX input/isolation',
                    'PQ capability versus actual DC voltage/temperature',
                    'Three batteries to two PCS DC/rack allocation','TR-QAUX connection',
                    'MT screens, earthing, relay settings and primary AUX protection'],
            'evidence':{str(p.relative_to(root())):sha(p) for p in [*paths.values(),root()/'research/design-basis.json']},
            'scope':'Conditional numerical screening, distinct from native calculation and from visual acceptance.'}
