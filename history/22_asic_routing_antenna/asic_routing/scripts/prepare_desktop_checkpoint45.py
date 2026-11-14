from pathlib import Path
import hashlib,json,odb
r=Path('/work/routing'); sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source=r/'inputs/transfer_cold_checkpoint45.odb'; global_path=r/'runs/global_followup_rc/final/odb/fault_v_asic_top.odb'
assert sha(source)=='cb92070079283ec40585d11d334e3914b6840325fe33936da825eb2a95520048'
g=json.loads((r/'reports/global_followup_rc/global_checks.json').read_text()); assert g['pass'] and g['total_overflow']==0 and sha(global_path)==g['odb_sha256']
def read(p):
 d=odb.dbDatabase.create(); odb.read_db(d,str(p)); return d,d.getChip().getBlock()
def fixed(b):
 cells={i.getName():(i.getMaster().getName(),str(i.getOrient()),tuple(i.getLocation()),str(i.getPlacementStatus())) for i in b.getInsts()}
 graph={n.getName():(str(n.getSigType()),tuple(sorted((t.getInst().getName(),t.getMTerm().getName()) for t in n.getITerms())),tuple(sorted(t.getName() for t in n.getBTerms()))) for n in b.getNets()}
 pg=[]
 for n in b.getNets():
  for sw in n.getSWires():
   for q in sw.getWires():
    pg.append((n.getName(),q.xMin(),q.yMin(),q.xMax(),q.yMax(),q.getTechVia().getName() if q.isVia() and q.getTechVia() else q.getBlockVia().getName() if q.isVia() else q.getTechLayer().getName()))
 return cells,graph,sorted(pg)
d,b=read(source); gd,gb=read(global_path); assert fixed(b)==fixed(gb),'Checkpoint differs from actual zero-overflow source cells/graph/PG'
a={'accepted':False,'source':'inputs/transfer_cold_checkpoint45.odb','source_sha256':sha(source),'derived_sha256':sha(source),'global_run':'global_followup_rc','global_source_sha256':sha(global_path),'same_cells_graph_power_geometry':True,'retained_routed_nets':sum(n.getWire() is not None for n in b.getNets()),'original_native_drc':15,'raw_diagnostic':'reports/desktop_checkpoint45_raw.json','scope':'Exact coherent physical checkpoint from the original route, not a new full route from global input. All physical geometry retained; native optimizer reinitializes. No fabricated zero, waived DRC or technology/rule changes.'}
(r/'reports/desktop_checkpoint45_input.json').write_text(json.dumps(a,indent=2)+'\n')
s=json.loads((r/'followup_cold_state.json').read_text()); s['odb']='/work/routing/inputs/transfer_cold_checkpoint45.odb'
(r/'desktop_checkpoint45_state.json').write_text(json.dumps(s,indent=2)+'\n'); print(json.dumps(a,indent=2))
