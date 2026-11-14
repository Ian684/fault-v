from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parent
snapshot_path=R/'logs/build_sources_started.json'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
identity={}
sources=[p for folder in ['rtl','board','constraints'] for p in (R/folder).glob('*') if p.is_file()]
sources.extend(R/n for n in ['programs/stream_demo.mem','build.tcl','create_project.tcl','ps_preset.tcl'])
identity['sources']={str(p.relative_to(R)).replace('\\','/'):digest(p) for p in sources}
if '--snapshot' in sys.argv:
 snapshot_path.write_text(json.dumps(identity['sources'],indent=2));print('Recorded build input snapshot.');sys.exit(0)
log=(R/'logs/final_build.log').read_text(encoding='utf-8-sig')
assert 'EXTENSION C FPGA BUILD PASSED' in log and 'INTEGRATED DSP COUNT: 8' in log
assert identity['sources']==json.loads(snapshot_path.read_text()),'Sources changed while FPGA build was running'
identity.update({n:digest(R/n) for n in ['fault_v_extension_c.bit','fault_v_extension_c.hwh']})
(R/'fpga_identity.json').write_text(json.dumps(identity,indent=2))
print('Recorded successful FPGA image and build-source identity.')
