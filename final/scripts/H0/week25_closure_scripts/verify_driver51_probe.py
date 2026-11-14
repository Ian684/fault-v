from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1]
selection=json.loads((C/'reports/signal_selection.json').read_text())
assert selection['run_tag']=='signal_manual51_a'
for tag in ('driver51_rc_a','driver51_sta_a'):
    assert (C/'logs'/f'{tag}.exit').read_text().strip()=='0'
    archive=json.loads((C/'runs'/tag/'native_archive_manifest.json').read_text())
    assert archive['all_byte_exact']
m=json.loads((C/'runs/driver51_sta_a/1-openroad-staprepnr/state_out.json').read_text())['metrics']
checks={k:v for k,v in m.items() if any(s in k for s in ('violation__count','_vio__count'))}
assert checks and all(v==0 for v in checks.values()),checks
assert m['timing__setup__ws']>0 and m['timing__hold__ws']>0
rc=json.loads((C/'runs/driver51_rc_a/3-openroad-rcx/state_out.json').read_text())
spefs={}
for corner,path in rc['spef'].items():
    p=C/Path(path).relative_to('/work/week25_closure')
    with p.open('rb') as f:spefs[corner]=hashlib.file_digest(f,'sha256').hexdigest()
assert len(spefs)==3 and len(set(spefs.values()))==3
(C/'reports/driver51_electrical_probe.json').write_text(json.dumps({'source_signal_sha256':selection['source_sha256'],'reviewed_driver_count':51,'all_three_RC_slew_cap_and_setup_hold_violation_counts_zero':True,'violation_counts':checks,'worst_setup_ns':m['timing__setup__ws'],'worst_hold_ns':m['timing__hold__ws'],'fresh_SPEF_sha256':spefs,'accepted_for_final':False,'scope':'Actual DRC-clean signal candidate with fresh three-RC extraction, TT library only. Final PG/diode/common-candidate extraction and STA still required.'},indent=2)+'\n')
print('DRIVER51_THREE_RC_ELECTRICAL_PASS',m['timing__setup__ws'],m['timing__hold__ws'])
