from pathlib import Path
import hashlib,json,re
C=Path(__file__).resolve().parents[1]
base=C/'runs/probe_rc_a/3-openroad-rcx/nom/fault_v_asic_top.nom.spef'
control=C/'runs/fill_rcx_control_a/1-openroad-rcx/nom/fault_v_asic_top.nom.spef'
def electrical(p):
    text=p.read_text();start=text.index('*NAME_MAP')
    body=text[start:];caps=re.findall(r'^\*D_NET\s+(\S+)\s+(\S+)',body,re.M)
    assert len(caps)>40000
    return body,caps
a,ac=electrical(base);b,bc=electrical(control)
record={'source':json.loads((C/'reports/fill_rcx_control_input.json').read_text()),'baseline_spef_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'control_spef_sha256':hashlib.sha256(control.read_bytes()).hexdigest(),'nets_checked':len(ac),'electrical_body_exactly_equal':a==b,'net_capacitances_exactly_equal':ac==bc,'dbFill_sensitivity_demonstrated':a!=b,'post_fill_PEX_qualified':False,'scope':'Negative control adds five enormous dbFill rectangles without changing any net, cell, PG or signal wire. Equality demonstrates this pinned extraction flow is insensitive to dbFill. This does not establish a numeric timing margin for real floating fill.'}
assert a==b and ac==bc,'Unexpected extractor sensitivity: inspect changed parasitics before drawing a conclusion'
(C/'reports/fill_rcx_sensitivity.json').write_text(json.dumps(record,indent=2)+'\n')
print('DBFILL_SENSITIVITY',record['dbFill_sensitivity_demonstrated'],'nets',len(ac),'identical electrical SPEF body',a==b)
