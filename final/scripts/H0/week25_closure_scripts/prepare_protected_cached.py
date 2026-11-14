from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1]
proof=json.loads((C/'reports/protected_route_input.json').read_text())
stage=json.loads((C/'reports/runtime_protected_guided_odb.json').read_text())
pins=json.loads((C/'reports/cached_all_pins.json').read_text())
assert proof['derived_sha256']==stage['sha256'] and proof['protected_routes']==40305
assert pins['all_native_preferences_valid'] and proof['normalization_roundtrip_all_wire_bytes_exact']
state=json.loads((C/'protected_route_state.json').read_text());state['odb']='/runtime/protected_guided.odb';state['metrics']={}
for key in ('spef','gds','klayout_gds','def'):state.pop(key,None)
(C/'protected_cached_state.json').write_text(json.dumps(state,indent=2)+'\n')
script=(C/'scripts/cached_detailed.tcl').read_text().replace('-droute_end_iter 64','-droute_end_iter 24')
assert '-no_pin_access' in script and '\npin_access\n' not in script
(C/'scripts/protected_cached_detailed.tcl').write_text(script,newline='\n')
cli=(C/'scripts/cached_route_cli.py').read_text().replace('scripts/cached_detailed.tcl','scripts/protected_cached_detailed.tcl')
(C/'scripts/protected_cached_cli.py').write_text(cli,newline='\n')
record={'accepted':False,'source_sha256':stage['sha256'],'protected_routes':40305,'native_cached_AP_audit':pins,'temporary_status_only':True,'normalization_and_unfiltered_DRC_required':True,'max_iterations':24,'scope':'Controlled retry: keep validated native pin access rather than regenerate it around temporarily FIXED routes. Must restore original ROUTED wire bytes and pass independent full geometry checks before promotion.'}
(C/'reports/protected_cached_input.json').write_text(json.dumps(record,indent=2)+'\n')
print('Protected cached-AP retry prepared; 40305 exact routes protected, 1032 rerouted; not accepted.')
