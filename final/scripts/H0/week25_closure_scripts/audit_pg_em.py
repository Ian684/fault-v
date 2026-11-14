"""Join every native EM branch to its exported resistor, including merged via cuts."""
from pathlib import Path
from collections import defaultdict
import csv,hashlib,json,math,re,sys
C=Path(__file__).resolve().parents[1]
tag_pattern=sys.argv[1] if len(sys.argv)>1 else 'pg_ir_{budget}_d'
runtime_record=C/(sys.argv[2] if len(sys.argv)>2 else 'reports/runtime_pg_via_b_odb.json')
report=C/(sys.argv[3] if len(sys.argv)>3 else 'reports/pg_em_resistor_audit.json')
tlef=C.parent/'pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef'
WIRE_LIMIT={};CUT_LIMIT={}
for match in re.finditer(r'^LAYER (\w+)\n(.*?)^END \1',tlef.read_text(),re.M|re.S):
    name,body=match.groups();value=re.search(r'DCCURRENTDENSITY AVERAGE ([\d.]+)',body)
    if value:(WIRE_LIMIT if 'TYPE ROUTING' in body else CUT_LIMIT)[name]=float(value[1])
assert WIRE_LIMIT['met1']==2.8 and CUT_LIMIT['via4']==2.49
BETWEEN={frozenset(('li1','met1')):'mcon',**{frozenset(('met'+str(n),'met'+str(n+1))):'via'+(str(n) if n>1 else '') for n in range(1,5)}}
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def node(text):
    match=re.fullmatch(r'Node_(li1|met[1-5])_(-?\d+)_(-?\d+)',text)
    return (match[1],int(match[2]),int(match[3])) if match else None
def key(a,b):return tuple(sorted((a,b)))
def assess(a,b,current,resistance,rc):
    if a[0]!=b[0]:
        layer=BETWEEN[frozenset((a[0],b[0]))]
        factor=rc[layer]/resistance;cuts=round(factor)
        assert cuts>=1 and math.isclose(factor,cuts,rel_tol=2e-5),(layer,factor,resistance)
        metric=current*1000/cuts;limit=CUT_LIMIT[layer]
        return layer,metric/limit,{'effective_cuts':cuts,'mA_per_cut':metric,'limit_mA_per_cut':limit}
    layer=a[0];length=max(abs(a[1]-b[1]),abs(a[2]-b[2]))/1000
    assert length>0
    width=rc[layer]*length/resistance;assert width>0
    metric=current*1000/width;limit=WIRE_LIMIT[layer]
    return layer,metric/limit,{'native_effective_width_um':width,'mA_per_um':metric,'limit_mA_per_um':limit}
fixture_rc={'via4':.38,'met4':.047}
assert assess(('met4',0,0),('met5',0,0),.008,.0475,fixture_rc)[2]['effective_cuts']==8
assert assess(('met4',0,0),('met5',0,0),.008,.095,fixture_rc)[2]['effective_cuts']==4
assert assess(('met4',0,0),('met5',0,0),.008,.38,fixture_rc)[1]>1
assert math.isclose(assess(('met4',0,0),('met4',30000,0),.016,.47,fixture_rc)[2]['native_effective_width_um'],3)
results={};all_failures=[]
for budget in ('0p014','0p028'):
    case={}
    for net in ('VPWR','VGND'):
        folder=C/'runs'/tag_pattern.format(budget=budget)/'1-openroad-irdropreport'
        log=(folder/'openroad-irdropreport.log').read_text()
        rc={name:float(value) for name,value in re.findall(r'^\s+(\w+): ([0-9.eE+-]+) Ohm per (?:cut|square)',log,re.M)}
        assert rc['via4']==.38 and len(rc)>=11
        spice=folder/f'network-{net}.spice';em=folder/f'em-{net}.csv'
        resistors={};reached_sinks=False;total_resistors=0
        with spice.open() as f:
            for line in f:
                if line.strip()=='* Sinks':reached_sinks=True;break
                if not re.match(r'R\d+ ',line):continue
                _,a,b,value=line.split();total_resistors+=1;a=node(a);b=node(b)
                if a is None or b is None:continue
                k=key(a,b);assert k not in resistors,('Duplicate resistor node pair',k)
                resistors[k]=float(value.removeprefix('R='));assert resistors[k]>0
        assert reached_sinks and total_resistors>300000
        maxima={};counts=defaultdict(int);cut_counts=defaultdict(lambda:defaultdict(int));failures=[];near_limit=[];rows=0
        with em.open(newline='') as f:
            for row in csv.DictReader(f):
                points=[(row[f'Node{i} Layer'],*(round(float(row[f'Node{i} {xy} location'])*1000) for xy in ('X','Y'))) for i in (0,1)]
                a,b=points;resistance=resistors[key(a,b)]
                current=abs(float(row['Current']))
                layer,ratio,detail=assess(a,b,current,resistance,rc)
                record={'node0':a,'node1':b,'current_A':current,'resistance_ohm':resistance,**detail,'utilization':ratio,'conservative_utilization':ratio*1.001}
                counts[layer]+=1;rows+=1
                if 'effective_cuts' in detail:cut_counts[layer][detail['effective_cuts']]+=1
                if layer not in maxima or ratio>maxima[layer]['utilization']:maxima[layer]=record
                if record['conservative_utilization']>1:failures.append({'layer':layer,**record})
                if record['conservative_utilization']>.9:near_limit.append({'layer':layer,**record})
        case[net]={'all_EM_rows_joined_to_exact_native_resistor':True,'rows':rows,'total_native_resistors':total_resistors,'branches_by_layer':dict(counts),'effective_cut_histograms':{k:dict(v) for k,v in cut_counts.items()},'worst_per_layer':maxima,'violations':failures,'near_limit_branches_over_90_percent':near_limit,'resistance_map':rc,'source_SHA256':{'EM':sha(em),'resistor_export':sha(spice),'ODB':json.loads(runtime_record.read_text())['sha256']},'full_SPICE_load_export_complete':False}
        all_failures.extend({'case':budget,'net':net,**v} for v in failures)
        print('PG_EM',budget,net,'rows',rows,'failures',len(failures),'worst',max(v['utilization'] for v in maxima.values()),flush=True)
    results[budget]=case
record={'cases':results,'violations':all_failures,'native_average_current_screen_pass':not all_failures,'temperature_C':90,'rounding_margin':.001,'native_source_manifest':'controls/pinned_psm_source/manifest.json','scope':'Controlled original F-baseline load A/B on the specified PG geometry; actual repair counts are recorded in its geometry binding. Native resistor values resolve merged cut counts and effective parallel wire widths; CSV current is never blindly divided by eight. PDK explicit comments supply average mA/cut and mA/um at Tj90C. Uniform native resistor current sharing; local crowding, temperature solution, package and SRAM internal EM are not qualified. Native SPICE exporter fails at sink section; complete resistor sections only are used and every EM row must join exactly. Final 50-driver candidate still requires fresh power/activity validation.'}
record['techLEF_sha256']=sha(tlef)
if tag_pattern.startswith('final_ir_'):
    record['scope']=record['scope'].replace('Controlled original F-baseline load A/B on the specified PG geometry; actual repair counts are recorded in its geometry binding.','Final common-candidate load A/B, using fresh final-netlist mixed-workload VCD and fresh nominal RC with 14/28mW per-SRAM assumptions.').replace('Final 50-driver candidate still requires fresh power/activity validation.','Native runs must log W25_FINAL_IR_INPUT_HASHES_VERIFIED for actual ODB/SPEF/VCD binding. This is a research average-current screen with the listed model and physical coverage limits.')
    for budget in ('0p014','0p028'):
        log=(C/'runs'/tag_pattern.format(budget=budget)/'1-openroad-irdropreport/openroad-irdropreport.log').read_text()
        assert 'W25_FINAL_IR_INPUT_HASHES_VERIFIED' in log
report.write_text(json.dumps(record,indent=2)+'\n')
assert not all_failures,'Native average-current violations remain'
