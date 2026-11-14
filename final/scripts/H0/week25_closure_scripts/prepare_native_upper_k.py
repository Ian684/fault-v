from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/repair_native_upper.py').read_text().replace('native_upper_b','native_upper_k')
code=code.replace("source=Path('/runtime/antenna_native12.odb')", "source=Path('/runtime_final/native_group_b.odb')")
code=code.replace("['source_sha256']", "['output_sha256']",1).replace("reports/antenna_iter12_probe.json", "reports/native_group_b/result.json",1)
needle="marker=json.loads((C/'reports/antenna_iter12_independent.json').read_text())['unresolved'];assert len(marker)==1 and marker[0]['type']=='Short'"
assert code.count(needle)==1
code=code.replace(needle,"raw=(C/'reports/native_group_b/router.drc').read_text();rows=re.findall(r'violation type: ([^\\n]+)\\n\\s*srcs: ([^\\n]+)\\n\\s*bbox = \\(([-0-9.]+), ([-0-9.]+)\\) - \\(([-0-9.]+), ([-0-9.]+)\\) on Layer ([^\\n]+)',raw);assert len(rows)==raw.count('violation type:')==2\nmarker=[{'type':kind,'srcs':src,'bbox_dbu':[round(float(v)*1000) for v in (x1,y1,x2,y2)],'layer':layer} for kind,src,x1,y1,x2,y2,layer in rows];assert all(m['type']=='Short' and 'net:net6170' in m['srcs'] for m in marker)")
code=code.replace("for name in re.findall(r'net:([^\\s]+)',marker['srcs']):", "for name in sorted(re.findall(r'net:([^\\s]+)',marker['srcs']),key=lambda n:n!='net6170'):")
p=C/'scripts/repair_native_upper_k.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('NATIVE_POST_GROUP_K_LOCAL_JUMPER_PREPARED')
