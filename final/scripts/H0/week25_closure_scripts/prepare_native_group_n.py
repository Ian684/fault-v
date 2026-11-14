"""Reduce the three actual M2 antenna components; retain every diode branch."""
from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/repair_native_upper.py').read_text().replace('native_upper_b','native_group_n')
code=code.replace("source=Path('/runtime/antenna_native12.odb')", "source=Path('/runtime_final/native_group_m.odb')").replace('reports/antenna_iter12_probe.json','reports/native_group_m/result.json',1).replace("['source_sha256']", "['output_sha256']",1)
needle="t=Tech();design=Design(t);design.readDb(str(source))";assert code.count(needle)==1
code=code.replace(needle,"verified=json.loads((C/'reports/native_m_geometry_verified.json').read_text());assert verified['source_sha256']==sha(source) and verified['independent_native_context_DRC']==0 and verified['all_41337_signal_clock_nets_connected']\n"+needle)
start=code.index("marker=json.loads(");end=code.index('def antennas(',start);code=code[:start]+code[end:]
needle="violators=antennas('after_short')";assert code.count(needle)==1
known="""violators=antennas('baseline');assert len(violators)==3
j=json.loads((C/'reports/antenna_jumper/result.json').read_text())['accepted_local_jumper'];assert j['bridge_layer']=='met3'
n=b.findNet('net6033');g=primitives(n.getWire())[0];q=tuple(j['original_segment']);assert g[q]==1
offset=j['cut_start'][1]-q[3];span=j['cut_end'][1]-j['cut_start'][1];added,p,r=jumper(q,offset,span,3)
roi=[q[2]-4000,q[3]-4000,q[4]+4000,q[5]+4000];base=check('known6033_before',roi);install(n,g-Counter([q])+added)
new=sum((check('known6033_after',roi)-base).values());conn=connected(n) if new==0 else False;after=antennas('known6033') if conn else violators
print('KNOWN_6033_JUMPER',new,conn,len(after),flush=True)
if new==0 and conn and 'net6033' not in after and set(after)<set(violators):
    repairs.append({'net':'net6033','kind':'antenna','original_segment':q,'cut_start':p,'cut_end':r,'bridge_layer':'met3','replayed_control':'reports/antenna_jumper/result.json'});violators=after
else:install(n,g)
"""
code=code.replace(needle,known)
code=code.replace(">=3500],key=dist)", ">=1800],key=dist)")
code=code.replace('for span in (4000,2000,8000,15000):','for span in (2000,4000,800,1200,8000,15000):').replace('for offset in (700,1200,2000):','for offset in (700,350,500,1200,2000):')
needle="                    counter+=1;added,p,r=jumper(q,offset,span,top);";assert code.count(needle)==1
code=code.replace(needle,"                    if counter>=120:\n                        (out/'incomplete.json').write_text(json.dumps({'repairs':repairs,'attempts':attempts,'remaining':violators,'accepted_for_final':False},indent=2)+'\\n');raise AssertionError('Bounded antenna trial limit reached')\n"+needle)
code=code.replace("Native pin accesses retained; only explicit higher-metal local bridges changed.", "All original signal routes and checked new diode branches retained except explicit M2 higher-metal antenna jumpers.")
p=C/'scripts/repair_native_group_n.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_N_THREE_ANTENNAS_WITH_KNOWN_6033_CONTROL_PREPARED')
