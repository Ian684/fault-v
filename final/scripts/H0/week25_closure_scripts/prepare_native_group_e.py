from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/route_native_group_b.py').read_text().replace('native_group_b','native_group_e')
code=code.replace("source=Path('/runtime/antenna_native12.odb')", "source=Path('/runtime_final/native_group_c.odb')")
code=code.replace("reports/antenna_iter12_probe.json", "reports/native_group_c/result.json",1).replace("['source_sha256']", "['output_sha256']",1)
code=code.replace("dirty={'net3347','net5547','net4319','net6170','net2682','net8704'}", "dirty={'net3347','net5547','net4319','net6170','net2682','net8704','net3311','net3177','net4842'}")
code=code.replace('-or_seed 29 -or_k 5','-or_seed 43 -or_k 7')
p=C/'scripts/route_native_group_e.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_GROUP_E_MEASURED_M3_M4_BLOCKERS_RELEASED')
