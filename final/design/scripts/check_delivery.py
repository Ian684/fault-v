from pathlib import Path
import ast,json,re,hashlib,subprocess
R=Path(__file__).resolve().parents[1]
for p in (R/'scripts').glob('*.py'):ast.parse(p.read_text(encoding='utf8'),filename=str(p))
# A known identity-buffer fixture must compare equal; a changed sink must not.
import importlib.util,tempfile
spec=importlib.util.spec_from_file_location('eco_check',R/'scripts/check_eco.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
with tempfile.TemporaryDirectory() as d:
 a=Path(d)/'a.tsv';b=Path(d)/'b.tsv'
 a.write_text('TOP\tPORT\tin\tn0\nff\tDFF\tff/D\tn0\n')
 b.write_text('TOP\tPORT\tin\tn0\nb\tsky130_fd_sc_hd__buf_4\tb/A\tn0\nb\tsky130_fd_sc_hd__buf_4\tb/X\tn1\nff\tDFF\tff/D\tn1\n')
 assert module.partition(a)[0]==module.partition(b)[0]
 b.write_text(b.read_text().replace('ff/D\tn1','ff/D\tn2'))
 assert module.partition(a)[0]!=module.partition(b)[0]
# The cell-family names used by the connectivity proof must really be positive buffers.
lib=Path(r'D:\Codex\WSL\fault-v-asic\pdk\ciel\sky130\versions\8afc8346a57fe1ab7934ba5a6056ea8b43078e71\sky130A\libs.ref\sky130_fd_sc_hd\lib\sky130_fd_sc_hd__tt_025C_1v80.lib').read_text()
refs=set(re.findall(r'\tsky130_fd_sc_hd__buf_(\d+)\t',(R/'eco/after.tsv').read_text()))
for size in refs:
 name='sky130_fd_sc_hd__buf_'+size
 match=re.search(r'cell\s*\(\s*"?'+name+r'"?\s*\)',lib)
 assert match,name
 start=lib.index('{',match.end());depth=1;end=start+1
 while depth:
  depth+=(lib[end]=='{')-(lib[end]=='}');end+=1
 assert re.search(r'function\s*:\s*"\(?A\)?"\s*;',lib[start:end]),name
final=(R/'mapped_top.v').read_bytes()
assert final==(R/'eco/fault_v_asic_top.nl.v').read_bytes()
cfg=json.loads((R/'config.json').read_text())
assert cfg['SYNTH_ABC_BUFFERING'] and cfg['STA_EXTRA_CORNER_TCL_FILE']=='dir::scripts/repair_sram_inputs.tcl'
assert cfg['MAX_TRANSITION_CONSTRAINT']==.03
out={'pass':True,'python_syntax':True,'connectivity_checker_positive_and_negative_fixtures':True,'identity_buffer_sizes_checked_against_original_liberty':sorted(map(int,refs)),'final_netlist_sha256':hashlib.sha256(final).hexdigest()}
(R/'reports/delivery_selfcheck.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS delivery syntax, connectivity checker negative case and original Liberty buffer truth functions.')
