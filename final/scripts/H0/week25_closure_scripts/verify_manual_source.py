"""Validate the exact native/context-clean source before export without rerouting."""
from pathlib import Path
import hashlib,json,re,sys
C=Path('/work/week25_closure')
def verify(source):
    assert source.parent==Path('/runtime_final')
    if source.name=='signal_pg_gap.odb':
        drname,cnname,inputname='signal_gap_independent.json','signal_gap_all_connectivity.json','signal_pg_gap_input.json'
    elif re.fullmatch(r'antenna_stubs_[a-z]\.odb',source.name):
        drname,cnname,inputname=source.stem+'_independent.json',source.stem+'_all_connectivity.json',source.stem+'/result.json'
    elif source.name in ('antenna_restore4.odb','antenna_jumper.odb','li1_spacing.odb') or re.fullmatch(r'native_(?:upper_[a-z]|group_[a-z])\.odb',source.name):
        drname,cnname,inputname=source.stem+'_independent.json',source.stem+'_all_connectivity.json',source.stem+'/result.json'
    else:
        assert source.name=='driver51_b.odb'
        drname,cnname,inputname='driver51_independent.json','driver51_all_connectivity.json','driver51_trial_b.json'
    dr=json.loads((C/'reports'/drname).read_text());cn=json.loads((C/'reports'/cnname).read_text());input=json.loads((C/'reports'/inputname).read_text())
    with source.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    assert digest==dr['odb_sha256']==cn['source_sha256']==input['output_sha256']
    assert dr['unresolved_count']==0 and dr['physical_geometry_unchanged'] and cn['all_signal_geometry_connected'] and cn['checked_multi_terminal_signal_clock_nets']==41337
    assert not cn['missing_wires'] and not cn['bad_nets']
    return dr['unresolved_count']
if __name__=='__main__':print(verify(Path(sys.argv[1])))
