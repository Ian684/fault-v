from pathlib import Path
import hashlib,json,shutil
C=Path(__file__).resolve().parents[1]
source=C.parent/'pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.tech/magic/sky130A-GDS.tech'
text=source.read_text();old='slots   0 4080 1600 0 4080 1600 1360 0';new='slots   0 4080 800 0 4080 800 1360 0'
assert text.count(old)==1
tech=C/'controls/sky130A-GDS-dense-FOM.tech';tech.write_text(text.replace(old,new))
folder=C/'dense_fom_trial';assert not folder.exists();folder.mkdir()
mag=C/'full_fill_development/fault_v_asic_top_fill_pattern_0_0.mag.evidence'
shutil.copyfile(mag,folder/'fault_v_asic_top_fill_pattern_0_0.mag')
shutil.copyfile(C/'full_fill_development/generate_fill_dist.tcl',folder/'generate_fill_dist.tcl')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(C/'reports/dense_fom_trial_input.json').write_text(json.dumps({'source_tech_sha256':sha(source),'derived_tech_sha256':sha(tech),'flattened_input_sha256':sha(mag),'single_parameter_change':{'before':old,'after':new},'unchanged':'All existing diffusion/poly/implant/well keepouts, all other FOM/poly generation operations and all LI/MET1-5 fill operations. Original PDK files unchanged.','rule_source':'https://skywater-pdk.readthedocs.io/en/main/rules/errors.html','FOM_dummy_public_screen_um':{'minimum_width':.5,'maximum_width':25,'minimum_spacing':.4},'accepted':False,'scope':'One-tile experiment: denser 4.08um FOM squares on 0.8um spacing. Must pass exact density and independent fill geometry screens before any adoption.'},indent=2)+'\n')
print('One-parameter FOM density trial prepared',flush=True)
