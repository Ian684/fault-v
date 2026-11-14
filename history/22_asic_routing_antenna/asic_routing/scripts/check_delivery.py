"""Offline integrity and routed-handoff validation, without running EDA."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
read=lambda p:json.loads(p.read_text(encoding="utf-8"))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=read(R/"MANIFEST.sha256.json")
actual={p.relative_to(R).as_posix() for p in R.rglob("*") if p.is_file() and p.name!="MANIFEST.sha256.json"}
assert actual==set(manifest),("Different delivery file set",actual^set(manifest))
for name,digest in manifest.items():assert sha(R/name)==digest,name
for name,digest in read(R/"input_identity.json")["sha256"].items():assert sha(R/name)==digest,name
repro=read(R/"reports/preparation_reproduction.json")
assert repro["pass"] and read(R/"reports/repro_prepare_repair/timing_checks.json")["pass"]
s=read(R/"accepted_summary.json")
assert s["accepted"] and s["routing_drc"]==s["global_overflow"]==0
assert s['antenna_closure'] and s['antenna_model_coverage'] and s['reported_antenna_nets']==0
tag=s["routed_run"]
selected=read(R/"selected_flow.json")
assert selected["routed_run"]==tag and selected["global_run"]==s["global_run"]
for key in ["cli","config","state"]:
    name=selected[key]
    assert name in read(R/"input_identity.json")["sha256"] and (R/name).is_file(),(key,name)
initial=read(R/selected["state"])
prefix="/work/routing/"
assert initial["odb"].startswith(prefix)
input_name=initial["odb"].removeprefix(prefix)
frozen=read(R/"input_identity.json")["sha256"]
assert input_name in frozen and (R/input_name).resolve().is_relative_to(R.resolve())
assert sha(R/input_name)==frozen[input_name]
g=read(R/"reports"/tag/"placement_checks.json")
w=read(R/"reports"/tag/"route_checks.json")
t=read(R/"reports"/tag/"timing_checks.json")
assert g["pass"] and g["negative_inversion_fault_detected"] and w["pass"] and t["pass"]
independent_drc=read(R/"reports"/tag/"full_drc_checks.json")
assert independent_drc["pass"] and independent_drc["independent_full_chip_drc"]==0 and independent_drc["negative_control_known_shorts"]==2
assert independent_drc["odb_sha256"]==w["odb_sha256"]
coverage=read(R/'reports'/tag/'antenna_model_coverage.json')
diodes=read(R/'reports'/tag/'antenna_diode_checks.json')
assert coverage['pass'] and not coverage['missing_active_input_models'] and diodes['pass']
assert coverage['source_odb_sha256']==diodes['candidate_odb_sha256']==s['odb_sha256']
assert diodes['passive_diodes']==s['antenna_protection_diodes']
assert diodes['all_diodes_in_actual_STA_netlist'] and diodes['all_diodes_in_extracted_SPEF'] and diodes['diode_input_capacitance_pf']>0
if selected.get('placement_checker')=='scripts/check_antenna_drive_placement.py':
    assert diodes['equivalent_driver_repair_verified']
    reference=read(R/selected['equivalent_driver_reference'])
    assert reference['pass'] and sha(R/reference['derived'])==reference['derived_sha256']==diodes['reference_odb_sha256']
    assert reference['allowed_resizes']['_44992_']==diodes['approved_driver_repair']
physical=read(R/'reports'/tag/'antenna_signal_connectivity.json')
assert physical['pass'] and physical['source_odb_sha256']==s['odb_sha256'] and physical['unconnected_diode_terminals']==0
controls=read(R/'reports/antenna_model/signal_gate_controls.json')
assert controls['pass'] and controls['checker_sha256']==sha(R/'scripts/check_antenna_signal_connectivity.py')
assert controls['controls']['positive']['exit_code']==0 and controls['controls']['positive']['unconnected_diode_terminals']==0
assert controls['controls']['negative']['exit_code']==1 and controls['controls']['negative']['unconnected_diode_terminals']>0
for control in controls['controls'].values():assert sha(R/control['source'])==control['source_sha256']
launch=read(R/'reports'/f'{tag}_launch.json')
assert launch['accepted'] and launch['native_exit']==launch['pipeline_exit']==0 and launch['input_sha256']==frozen[input_name]
assert read(R/selected['config'])['DRT_THREADS']==selected['threads']
assert read(R/selected['config'])['DRT_ANTENNA_REPAIR_ITERS']==selected['antenna_repair_iterations']
if selected.get('postroute_global_proof'):
    final_global=read(R/selected['postroute_global_proof'])
    assert final_global['final_global_verified'] and final_global['total_overflow']==0 and final_global['source_sha256']==s['odb_sha256']
assert 0<selected['threads']<=selected['container_cpus']==launch['threads']
for name,digest in launch['sha256'].items():assert sha(R/name)==digest,name
checks=read(R/'reports'/tag/'checks_source.json')
assert checks['odb_sha256']==s['odb_sha256']
for name,digest in checks['sha256'].items():assert sha(R/name)==digest,name
negative=read(R/'reports/antenna_model/negative_coverage.json')
assert negative['pass'] and negative['actual_exit']==1 and negative['no_acceptance_report_created']
assert negative['checker_sha256']==sha(R/'scripts/audit_antenna_metadata.py')
model=read(R/'reports/antenna_model/sram_antenna_model.json')
assert model['pass'] and model['geometry_and_pin_directions_unchanged'] and (model['gate_pins'],model['diffusion_pins'])==(59,64)
alias=read(R/'reports/antenna_model/spice_source_alias.json')
assert sha(R/alias['delivered_alias'])==alias['sha256']=='5d1de14e203f07b4a16470819d9d5ba28e5d7f79283cef23eec5462a12285e76'
assert independent_drc["raw_marker_count"]==independent_drc["confirmed_partition_artifacts"]+independent_drc["independent_full_chip_drc"]
assert (g["flip_flops"],g["clock_sink_pins"],g["fixed_macros"])==(2925,2961,18)
assert t["max_macro_input_slew_ns"]<=.04000001 and not w["active_nets_missing_wires"]
assert read(R/"reports"/f"{tag}_sta_source.json")["scope"]=="routed"
h=read(R/"handoff_state.json")
assert h["metrics"]["route__antenna_violation__count"]==s["reported_antenna_nets"]==0
prefix="/work/routing/"
for key,value in h.items():
    if key=="metrics":continue
    for path in (value.values() if isinstance(value,dict) else [value]):
        assert path.startswith(prefix)
        assert (R/path.removeprefix(prefix)).is_file(),(key,path)
assert len(h["spef"])==3
assert sha(R/h["nl"].removeprefix(prefix))==s["netlist_sha256"]==g["netlist_sha256"]
assert sha(R/h["odb"].removeprefix(prefix))==s["odb_sha256"]==w["odb_sha256"]
qa=read(R/'figures/routing_visual_qa.json')
assert qa['pass'] and qa['routed_run']==tag and qa['accepted_odb_sha256']==s['odb_sha256']
assert qa['png_sha256']==sha(R/'figures/routing.png') and qa['svg_sha256']==sha(R/'figures/routing.svg')
assert qa['wire_segments_sha256']==sha(R/'reports'/tag/'wire_segments.json')
rules=read(R/"reports/clock_routing_rules.json")
assert sha(R/"inputs/fault_v_asic_top.odb")==rules["source_sha256"]
assert sha(R/"inputs/standard_clock_rules.odb")==rules["derived_sha256"]
assert rules["cleared_clock_ndrs"]==13 and rules["clock_network_nets"]==444
print("ALL OFFLINE ROUTING DELIVERY / HASH / EXTRACTED HANDOFF CHECKS PASSED")
