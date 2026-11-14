from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1];file=C/'reports/native_group_n/progress.json';raw=file.read_bytes();n=json.loads(raw)
assert len(n['repairs'])==2 and {r['net'] for r in n['repairs']}=={'net6033','_10658_'} and n['attempts'][-1]['antenna_nets']==1
f=json.loads((C/'reports/antenna_stubs_f/result.json').read_text());m=json.loads((C/'reports/native_group_m/result.json').read_text())
assert f['antenna_nets']==2 and m['antenna_nets']==3
old=[r for r in f['accepted'] if r['net']=='net6330'];new=[r for r in m['accepted'] if r['net']=='net6330'];assert len(old)==len(new)==1 and old[0]['diode']==new[0]['diode']=='ANTENNA_7569'
record={'source_M_sha256':m['output_sha256'],'source_F_sha256':f['output_sha256'],'N_prefix_file_sha256':hashlib.sha256(raw).hexdigest(),'repairs':n['repairs'],'last_observed_trial':n['attempts'][-1],'M_6330_branch':new[0],'F_6330_branch':old[0],'accepted_for_final':False,'scope':'Immutable replay data only. Actual source O must independently pass DRC, connectivity, antenna, GDS/core LVS and all remaining final gates.'}
p=C/'controls/antenna_o_replay.json';assert not p.exists();p.write_text(json.dumps(record,indent=2)+'\n');print('O_REPLAY_PREFIX_FROZEN',record['N_prefix_file_sha256'],flush=True)
