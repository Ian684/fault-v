from pathlib import Path
from collections import Counter
import hashlib,json,sys,odb
sys.path.insert(0,'/work/routing/scripts')
from temporary_fixed_routes import load
C=Path('/work/week25_closure');source=Path('/runtime_final/antenna_restore4.odb');reference=Path('/runtime_final/focus_pg.odb')
db,b=load(source);rd,rb=load(reference)
proof=json.loads((C/'reports/antenna_restore4/result.json').read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(source)==proof['output_sha256'] and sha(reference)==proof['reference_original_signal_sha256']
def terms(w):
    result=Counter();d=odb.dbWireDecoder();d.begin(w)
    while True:
        op=d.next()
        if op==d.END_DECODE:break
        if op==d.ITERM:
            p=d.getITerm();assert p;result['ITERM',p.getInst().getName(),p.getMTerm().getName()]+=1
        elif op==d.BTERM:
            p=d.getBTerm();assert p;result['BTERM',p.getName()]+=1
    return result
rows={}
for name in proof['restored_unaffected_nets']:
    a=terms(b.findNet(name).getWire());z=terms(rb.findNet(name).getWire());assert a==z,(name,a,z)
    rows[name]={'native_terminal_opcode_count':sum(a.values()),'all_terminals_resolve_to_same_named_cell_pin_or_port':True}
total=sum(v['native_terminal_opcode_count'] for v in rows.values())
out=C/'reports/antenna_restore4_term_binding.json';out.write_text(json.dumps({'source_sha256':sha(source),'nets':rows,'embedded_terminal_opcode_count':total,'all_present_embedded_terminal_names_agree':True,'no_embedded_terminal_IDs_to_rebind':total==0,'scope':'These restored wires contain geometry only when the count is zero. Physical copper/pin connectivity and final full-GDS core LVS remain the binding authorities.'},indent=2)+'\n')
print('RESTORED_TERMINAL_OPCODE_INVENTORY',total,rows,flush=True)
