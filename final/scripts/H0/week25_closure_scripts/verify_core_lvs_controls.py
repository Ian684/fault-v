"""Require real named macro ports, zero positive LVS errors and a failing physical-pin control."""
from pathlib import Path
import json,re,sys
C=Path(__file__).resolve().parents[1];positive,negative=sys.argv[1:3]
for tag in (positive,negative):assert re.fullmatch('[a-z0-9_]+',tag)
model=json.loads((C/'reports'/sys.argv[3]).read_text());expected=set(model['pin_names']);assert len(expected)==125
results={}
for kind,tag in [('positive',positive),('negative',negative)]:
    assert (C/'logs'/f'{tag}.exit').read_text().strip()=='0','Run/archive incomplete'
    assert json.loads((C/'runs'/tag/'native_archive_manifest.json').read_text())['all_byte_exact']
    run=C/'runs'/tag;ext=run/'1-magic-spiceextraction/extraction/sky130_sram_2kbyte_1rw1r_32x512_8.ext'
    ports=re.findall(r'^port "([^"\n]+)"\s+(\d+)\s',ext.read_text(),re.M)
    required=expected if kind=='positive' else expected-{'din0[0]'}
    assert {p for p,i in ports}==required,(tag,'Unexpected physical macro port declarations')
    assert len({i for p,i in ports})==len(required),(tag,'Port indices are not independent')
    state=json.loads((run/'2-netgen-lvs/state_out.json').read_text());metrics=state['metrics']
    assert metrics['magic__illegal_overlap__count']==0
    results[kind]={'run':tag,'unique_declared_macro_ports':len(required),'LVS_errors':metrics['design__lvs_error__count'],'net_differences':metrics['design__lvs_net_difference__count'],'pin_differences':metrics['design__lvs_unmatched_pin__count']}
assert results['positive']['LVS_errors']==0,results
assert results['negative']['LVS_errors']>0,('Moved physical pin was not detected',results)
record={'validated_hierarchical_core_LVS_method':True,'positive':results['positive'],'intentional_pin_shift_negative_control':results['negative'],'manufacturing_source_GDS_sha256':model['manufacturing_source_GDS_sha256'],'scope':'Validated SRAM pin-interface blackbox method on the specified controlled development baseline. No SRAM interior or foundry qualification; final signal candidate must regenerate its view and pass actual positive core LVS.'}
(C/'reports/core_lvs_method_verified.json').write_text(json.dumps(record,indent=2)+'\n');print('CORE_LVS_METHOD_VERIFIED',results,flush=True)
