from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/route_native_group_a.py').read_text().replace('native_group_a','native_group_b')
needle="design.evalTclString('detailed_route_debug -snapshot_dir /runtime_final/native_group_b_snapshots')"
assert code.count(needle)==1
code=code.replace(needle,"Path('/runtime_final/native_group_b_snapshots').mkdir(exist_ok=False)\n"+needle)
needle="design.evalTclString('detailed_route -or_seed 29 -or_k 5 -no_pin_access -droute_end_iter 20 -drc_report_iter_step 1 -verbose 1 -output_drc '+str(out/'router.drc'))"
assert code.count(needle)==1
code=code.replace(needle,"reply="+needle+"\nprint('NATIVE_DETAILED_ROUTE_REPLY',repr(reply),flush=True)\nassert reply in ('',None),reply")
p=C/'scripts/route_native_group_b.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_GROUP_B_WITH_SNAPSHOT_AND_TCL_ERROR_GUARDS_READY')
