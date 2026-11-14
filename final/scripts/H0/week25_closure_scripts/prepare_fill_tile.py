from pathlib import Path
import hashlib,json,shutil
C=Path(__file__).resolve().parents[1]
proof=json.loads((C/'reports/streamed_SRAM_geometry_fixed.json').read_text())
assert proof['all_selected_manufacturing_layers_exact']
source=C/'runs/stream_fix_a/1-klayout-streamout/fault_v_asic_top.gds'
folder=C/'fill_tile_trial';folder.mkdir(exist_ok=True)
target=folder/'fault_v_asic_top.gds';assert not target.exists();shutil.copyfile(source,target)
(C/'reports/fill_tile_input.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Native PDK fill flow development: first 700um x 700um tile only, on correctly embedded macro geometry; not final post-ECO fill.'},indent=2)+'\n')
