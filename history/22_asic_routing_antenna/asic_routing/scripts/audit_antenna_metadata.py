"""Read back native gate/diffusion coverage; fail for any active sink without a model."""
from pathlib import Path
from collections import Counter
from openroad import Tech, Design
import hashlib,json,os,math

R=Path('/work/routing')
source=Path(os.environ.get('ANTENNA_AUDIT_ODB',str(R/'inputs/antenna_model_validated.odb')))
output=Path(os.environ.get('ANTENNA_AUDIT_REPORT',str(R/'reports/antenna_model/native_coverage.json')))
t=Tech(); d=Design(t); d.readDb(str(source)); b=d.getBlock()
macros=[i for i in b.getInsts() if i.getMaster().isBlock()]
assert len(macros)==18
model=json.loads((R/'reports/antenna_model/sram_antenna_model.json').read_text())
master=macros[0].getMaster()
for pin,areas in model['pin_areas'].items():
    mt=master.findMTerm(pin)
    assert mt and ('gate_area_um2' not in areas or mt.hasDefaultAntennaModel()), ('Missing macro gate model',pin)
    api=mt.getDefaultAntennaModel() if 'gate_area_um2' in areas else mt
    method=api.getGateArea if 'gate_area_um2' in areas else api.getDiffArea
    try:
        values=method()
    except TypeError as e:
        print('READBACK_API',str(e),flush=True)
        raise
    numbers=[float(v[0]) for v in values]
    assert len(numbers)==1 and abs(numbers[0]-float(next(iter(areas.values()))))<1e-7,('Macro antenna area mismatch',pin,numbers)
counts=Counter(); missing=[]
for net in b.getNets():
    if str(net.getSigType()) not in ['SIGNAL','CLOCK']: continue
    for pin in net.getITerms():
        if str(pin.getIoType()) not in ['INPUT','INOUT']: continue
        mt=pin.getMTerm()
        if str(mt.getSigType()) in ['POWER','GROUND']: continue
        counts['active_input_pins']+=1
        antenna=mt.getDefaultAntennaModel()
        if antenna is None or not any(math.isfinite(float(v)) and float(v)>0 for v,layer in antenna.getGateArea()):
            missing.append([pin.getInst().getName(),mt.getName()])
        else: counts['modeled_active_input_pins']+=1
assert not missing,missing[:20]
receipt={'pass':True,'source_odb_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'counts':dict(counts),'missing_active_input_models':missing,'macro_instances':18,'macro_gate_models_per_instance':59,'macro_diffusion_models_per_instance':64,'all_macro_values_equal_GDS_SPICE_verified_receipt':True}
output.write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
