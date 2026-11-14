"""Use the pinned Tcl-to-enum mapping: 1=ALL, 0=DRC, 2=NEARDRC."""
from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/route_native_group_h.py').read_text().replace('native_group_h','native_group_i')
needle="[(11,0,8,128,0),(15,-1,16,256,0),(13,-2,16,512,2),(17,0,16,1024,0),(19,-2,32,2048,0)]"
assert code.count(needle)==1
code=code.replace(needle,"[(11,0,8,128,1),(15,-1,16,256,1),(13,-2,16,512,2),(17,0,16,1024,1),(19,-2,32,2048,1)]")
code=code.replace("'large_context_steps':step_results", "'pinned_step_mode_mapping':{'0':'DRC','1':'ALL','2':'NEARDRC'},'large_context_steps':step_results")
p=C/'scripts/route_native_group_i.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
code=(C/'scripts/run_native_group_h.sh').read_text().replace('native_group_h','native_group_i').replace('native-group-h','native-group-i').replace('antenna_native_h','antenna_native_i')
p=C/'scripts/run_native_group_i.sh';assert not p.exists();p.write_text(code,newline='\n')
print('PINNED_STEP_MODE_MAPPING_CORRECTED_FROM_TritonRoute_CPP_195_205')
