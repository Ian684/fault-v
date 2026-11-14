from pathlib import Path
import csv,hashlib,json
C=Path(__file__).resolve().parents[1];W=C.parent/'week25_signoff'
result={'cases':{},'selection_threshold_A':.0012,'scope':'Native PDNSim met4/met5 branch currents, using explicit outer-edge supply scenario. PDK annotations specify mA per via at Tj90C; no thermal/current-crowding qualification.'}
for budget in ('0p014','0p028'):
    case={}
    for net in ('VPWR','VGND'):
        path=W/f'runs/ir_{budget}_20261030_b/1-openroad-irdropreport/em-{net}.csv';rows={};edges=[]
        with path.open(newline='') as f:
            for r in csv.DictReader(f):
                if {r['Node0 Layer'],r['Node1 Layer']}!={'met4','met5'}:continue
                tag='Node0' if r['Node0 Layer']=='met4' else 'Node1'
                x,y=(round(float(r[tag+' '+v+' location'])*1000) for v in ('X','Y'))
                key=f'{x},{y}';current=abs(float(r['Current']))
                rows[key]=max(rows.get(key,0),current)
                other='Node1' if tag=='Node0' else 'Node0'
                xx,yy=(round(float(r[other+' '+v+' location'])*1000) for v in ('X','Y'))
                edges.append({'lower_xy':[x,y],'upper_xy':[xx,yy],'current_A':current})
        assert len(rows)>300
        with path.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        case[net]={'source_sha256':digest,'branches':rows,'edges':edges,'over_2p49mA':sum(v>.00249 for v in rows.values()),'over_1p2mA':sum(v>.0012 for v in rows.values())}
    result['cases'][budget]=case
(C/'controls/pg_via_currents.json').write_text(json.dumps(result,indent=2)+'\n')
print({b:{n:{k:v for k,v in r.items() if k not in ('branches','edges','source_sha256')} for n,r in c.items()} for b,c in result['cases'].items()},flush=True)
