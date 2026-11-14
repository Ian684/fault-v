from pathlib import Path
import json,hashlib,re,collections,shutil
R=Path(__file__).resolve().parents[1]
L=Path(r"D:\Codex\WSL\fault-v-asic")
lint=json.loads((R/'reports/lint_categories.json').read_text())
tag='tt_delivery'
src=L/'design/runs'/tag/'01-verilator-lint/verilator-lint.log'
shutil.copy2(src,R/'reports'/tag/'verilator-lint.log')
lint[tag]=dict(collections.Counter(re.findall(r'%Warning-([A-Z0-9_]+):',src.read_text())))
assert sum(lint[tag].values())==481
(R/'reports/lint_categories.json').write_text(json.dumps(lint,indent=2)+'\n')
versions=json.loads((R/'history/baseline_toolchain_identity.json').read_text())
versions.update(evidence_verified_on='2026-10-19',opensta='3.1.0',opensta_commit='0f2529d18218b87aa0e82de444395a830d5058a1',
 opensta_original_image_version='2.7.0',opensta_source='https://github.com/The-OpenROAD-Project/OpenSTA',
 opensta_build='GCC 11, CMake 3.22, RelWithDebInfo -O2 -DNDEBUG; BUILD_TESTS=OFF; USE_TCL_READLINE=OFF',
 opensta_binary_sha256=hashlib.sha256((L/'tools/opensta_fixed/build/sta').read_bytes()).hexdigest(),
 cudd_commit='f54f533303640afd5dbe47a05ebeabb3066f2a25',
 release_run='tt_delivery_reload',synthesis_run='tt_delivery',
 mapped_netlist_sha256=hashlib.sha256((R/'mapped_top.v').read_bytes()).hexdigest(),
 eco='scripts/repair_sram_inputs.tcl',upstream_sta_tests='reports/opensta_upstream_tests.json')
(R/'toolchain_identity.json').write_text(json.dumps(versions,indent=2)+'\n',encoding='utf8')
for rel in ['tools/opensta_fixed/LICENSE','tools/cudd_3/LICENSE']:
 dest=R/'licenses'/('OpenSTA_LICENSE' if 'opensta' in rel else 'CUDD_LICENSE')
 dest.parent.mkdir(exist_ok=True);shutil.copy2(L/rel,dest)
print('PASS tool provenance and final lint evidence; no RTL or macro view modifications.')
