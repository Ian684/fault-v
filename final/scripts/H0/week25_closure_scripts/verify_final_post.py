"""Fail closed on any final-source DRC, antenna, extraction or timing mismatch."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
C=Path(__file__).resolve().parents[1]
def read(p):return json.loads((C/p).read_text())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def local(s):
    p=C/Path(s).relative_to('/work/week25_closure');assert p.resolve().is_relative_to(C.resolve());return p
def archive(tag):
    assert (C/'logs'/(tag+'.exit')).read_text().strip()=='0'
    root=C/'runs'/tag;manifest=read('runs/'+tag+'/native_archive_manifest.json');assert manifest['all_byte_exact'] and manifest['canonical_paths_preserved']
    for name,row in manifest['files'].items():
        p=root/name;assert p.resolve().is_relative_to(root.resolve()) and p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],str(p)
    return len(manifest['files'])
selection=read('reports/final_route_selection_c.json');stage=read('reports/runtime_final_route_c_odb.json')
assert selection['source_sha256']==stage['sha256'] and selection['independent_DRC']==selection['antenna_nets']==0
assert selection['all_signal_geometry_connected'] and selection['reviewed_driver_count']==51
archives={tag:archive(tag) for tag in ('focus_post_b','focus_post_sta_b')}
initial=read('runs/focus_post_b/1-openroad-fillinsertion/state_in.json');assert initial['odb']=='/runtime/final_route_c.odb'
drc=read('runs/focus_post_b/3-klayout-drc/state_out.json');ant=read('runs/focus_post_b/4-openroad-checkantennas/state_out.json')
assert drc['metrics']['klayout__drc_error__count']==0
tree=ET.parse(C/'runs/focus_post_b/3-klayout-drc/reports/drc.klayout.lyrdb').getroot()
assert tree.tag=='report-database' and len(tree.findall('categories/category'))>100 and not tree.findall('items/item')
assert ant['metrics']['antenna__violating__nets']==ant['metrics']['antenna__violating__pins']==0
rc=read('runs/focus_post_b/5-openroad-rcx/state_out.json');sta=read('runs/focus_post_sta_b/1-openroad-staprepnr/state_out.json');sta_in=read('runs/focus_post_sta_b/1-openroad-staprepnr/state_in.json')
assert sta_in['nl']==rc['nl']==drc['nl']==ant['nl'] and sta_in['spef']=={f'{key}_tt_025C_1v80':rc['spef'][key+'_*'] for key in ('nom','min','max')}
spefs={k:sha(local(v)) for k,v in rc['spef'].items()};assert len(spefs)==len(set(spefs.values()))==3
m=sta['metrics'];counts={k:v for k,v in m.items() if any(s in k for s in ('violation__count','_vio__count'))}
assert len(counts)>=28 and all(v==0 for v in counts.values()),counts
timing={corner:{kind:m[f'timing__{kind}__ws__corner:{corner}'] for kind in ('setup','hold')} for corner in ('nom_tt_025C_1v80','min_tt_025C_1v80','max_tt_025C_1v80')}
assert all(v>0 for row in timing.values() for v in row.values())
record={'source_route_sha256':selection['source_sha256'],'filled_ODB_sha256':sha(local(rc['odb'])),'full_geometry_core_GDS_sha256':sha(local(rc['gds'])),'fresh_netlist_sha256':sha(local(rc['nl'])),'fresh_SPEF_sha256':spefs,'open_core_DRC':0,'top_level_antenna_nets':0,'top_level_antenna_pins':0,'all_three_RC_electrical_and_timing_violation_counts_zero':True,'timing_slacks_ns':timing,'violation_counts':counts,'fresh_archived_files_verified':archives,'all_W25_gates_complete':False,'scope':'Exact common-candidate full-geometry core open-rule DRC, top-level antenna and fresh min/nom/max-RC TT timing/electrical screens. SRAM internal/foundry rule coverage and qualified multi-PVT/post-fill extraction are not inferred; final LVS/stream/connectivity/activity/IR/fill gates are separate.'}
p=C/'reports/final_post_verified.json';assert not p.exists();p.write_text(json.dumps(record,indent=2)+'\n')
print('FINAL_POST_COMMON_CANDIDATE_VERIFIED',record['full_geometry_core_GDS_sha256'],timing,flush=True)
