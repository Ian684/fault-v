"""Tighten only native FOM slot spacing after the full 1053-window density screen."""
from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1]
source=C/'controls/sky130A-GDS-dense-FOM.tech'
target=C/'controls/sky130A-GDS-dense-FOM-b.tech'
before=b'slots   0 4080 800 0 4080 800 1360 0'
after=b'slots   0 4080 600 0 4080 600 1360 0'
raw=source.read_bytes();assert raw.count(before)==1 and not target.exists()
updated=raw.replace(before,after);assert updated.replace(after,before)==raw
target.write_bytes(updated)
previous=json.loads((C/'reports/dense_fom_native_density.json').read_text())
assert previous['layers']['FOM']['failed_windows']==19
record={'source_sha256':hashlib.sha256(raw).hexdigest(),'derived_sha256':hashlib.sha256(updated).hexdigest(),'only_change':[before.decode(),after.decode()],'previous_failed_windows':19,'public_minimum_spacing_um':.4,'new_spacing_um':.6,'accepted':False,'scope':'All other fill operations and keepouts unchanged. Full density and geometry revalidation required.'}
(C/'reports/dense_fom_b_input.json').write_text(json.dumps(record,indent=2)+'\n')
wrapper=(C/'scripts/run_dense_fom_native.sh').read_text()
wrapper=wrapper.replace('dense_fom_native','dense_fom_native_b').replace('sky130A-GDS-dense-FOM.tech','sky130A-GDS-dense-FOM-b.tech')
wrapper=wrapper.replace('faultv-w25-dense-fom-native','faultv-w25-dense-fom-native-b').replace('faultv-w25-fom-native-repair','faultv-w25-fom-native-b-repair').replace('faultv-w25-li-native-repair','faultv-w25-li-native-b-repair').replace('faultv-w25-dense-native-density','faultv-w25-dense-native-b-density')
wrapper=wrapper.replace('fom_dummy_repair_native','fom_dummy_repair_native_b').replace('li_dummy_repair_native','li_dummy_repair_native_b')
(C/'scripts/run_dense_fom_native_b.sh').write_text(wrapper,newline='\n')
print(json.dumps(record,indent=2))
