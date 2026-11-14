from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parent
log=(R/'logs/final_build.log').read_text(encoding='utf-8-sig')
assert 'EXTENSION B FPGA BUILD PASSED' in log and 'INTEGRATED DSP COUNT: 4' in log
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
identity={n:digest(R/n) for n in ['fault_v_extension_b.bit','fault_v_extension_b.hwh']}
sources=[p for folder in ['rtl','board','constraints'] for p in (R/folder).glob('*') if p.is_file()]
sources.extend(R/n for n in ['programs/applications_demo.mem','build.tcl','create_project.tcl','ps_preset.tcl'])
identity['sources']={str(p.relative_to(R)).replace('\\','/'):digest(p) for p in sources}
(R/'fpga_identity.json').write_text(json.dumps(identity,indent=2))
print('Recorded successful FPGA image and build-source identity.')
