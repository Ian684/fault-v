"""Select PG_F only after independent geometry, actual GDS/core LVS and four EM cases pass."""
from pathlib import Path
import hashlib,json,re
C=Path(__file__).resolve().parents[1]
def read(p):return json.loads((C/p).read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
tags=['pg_f_stream_a','pg_f_core_lvs_a','pg_f_ir_0p014_a','pg_f_ir_0p028_a']
for tag in tags:
    assert (C/'logs'/f'{tag}.exit').read_text().strip()=='0',tag
    assert read(f'runs/{tag}/native_archive_manifest.json')['all_byte_exact'],tag
dr=read('reports/pg_f_independent.json');binding=read('reports/pg_f_geometry_binding.json');runtime=read('reports/runtime_pg_compact_f_odb.json')
digest=sha(C/'inputs/pg_compact_f.odb');assert digest==dr['odb_sha256']==binding['output_sha256']==runtime['sha256'] and dr['unresolved_count']==0
gds=C/'runs/pg_f_stream_a/1-klayout-streamout/fault_v_asic_top.gds'
assert read('runs/pg_f_stream_a/2-klayout-drc/state_out.json')['metrics']['klayout__drc_error__count']==0
assert (C/'logs/pg_f_stream_audits.exit').read_text().strip()=='0'
macro=read('reports/pg_f_macro_audit.json');std=read('reports/pg_f_stdcell_audit.json');vias=read('reports/pg_f_native_vias.json')
assert macro['all_selected_manufacturing_layers_exact'] and all(len(layers)==39 for layers in macro['masters'].values())
assert std['stream_GDS_sha256']==sha(gds) and std['all_component_counts_match_fresh_DEF'] and std['all_used_standard_cell_polygon_layers_match_library'] and std['all_route_via_counts_and_geometry_match_native_ODB']
view=read('reports/pg_f_core_lvs_view.json');assert sha(gds)==view['manufacturing_source_GDS_sha256']
metrics=read('runs/pg_f_core_lvs_a/2-netgen-lvs/state_out.json')['metrics']
assert metrics['design__lvs_error__count']==metrics['magic__illegal_overlap__count']==0
ext=(C/'runs/pg_f_core_lvs_a/1-magic-spiceextraction/extraction/sky130_sram_2kbyte_1rw1r_32x512_8.ext').read_text()
ports=re.findall(r'^port "([^"\n]+)"\s+(\d+)\s',ext,re.M)
assert {n for n,i in ports}==set(view['pin_names']) and len({i for n,i in ports})==125
method=read('reports/core_lvs_method_verified.json');assert method['validated_hierarchical_core_LVS_method'] and method['intentional_pin_shift_negative_control']['LVS_errors']>0
em=read('reports/pg_f_em_resistor_audit.json');assert em['native_average_current_screen_pass'] and not em['violations']
assert len(em['cases'])==2 and all(len(case)==2 for case in em['cases'].values())
assert all(net['source_SHA256']['ODB']==digest and not net['violations'] for case in em['cases'].values() for net in case.values())
record={'variant':'PG_F','source_sha256':digest,'source_ODB':'inputs/pg_compact_f.odb','independent_native_DRC':0,'full_GDS_open_DRC':0,'hierarchical_core_LVS_errors':0,'unique_declared_SRAM_ports':125,'four_controlled_average_EM_cases_pass':True,'manufacturing_GDS_sha256':sha(gds),'accepted_for_final':False,'scope':'Controlled original F-baseline PG selection. SRAM pin-interface core LVS only, explicit public/open rule coverage and 14/28mW per-macro load assumptions. Final 50-driver signal candidate requires rebasing and every common-candidate gate; no foundry/package/SRAM internal qualification.'}
p=C/'reports/selected_pg.json';assert not p.exists();p.write_text(json.dumps(record,indent=2)+'\n');print('PG_F_CONTROLLED_BASELINE_VERIFIED',digest,flush=True)
