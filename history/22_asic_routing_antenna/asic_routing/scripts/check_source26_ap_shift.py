from pathlib import Path
import odb,hashlib,json
R=Path("/work/routing")
source=R/"reports/residual_geometry26_source.odb"
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)=="fc748ae797cffc8e786019c824537c86451a0a604d3a2789945153626a36fc5c"
names={v["net"] for v in json.loads((R/"reports/residual_corner_neighbor_classes.json").read_text())["nets"]}
db=odb.dbDatabase.create();odb.read_db(db,str(source));b=db.getChip().getBlock()
outside=[];count=0
for n in b.getNets():
 if n.getName() not in names:continue
 for p in n.getITerms():
  aps=p.getPrefAccessPoints();assert aps
  x,y=p.getInst().getLocation()
  for ap in aps:
   ax,ay=ap.getPoint();gx,gy=x+ax,y+ay;layer=ap.getLayer().getName()
   count+=1
   if not any(l.getName()==layer and q.xMin()<=gx<=q.xMax() and q.yMin()<=gy<=q.yMax() for l,q in p.getGeometries()):
    outside.append({"pin":p.getInst().getName()+"/"+p.getMTerm().getName(),"point":[gx,gy],"layer":layer})
result={"accepted":False,"source_sha256":sha(source),"preferred_ap_points":count,"outside_pin_shapes":outside,"coordinate_rule":"Oriented AP plus dbInst.getLocation(), matching pinned frInst::getNoRotationTransform; do not apply cell rotation again.","supersedes":"reports/source26_neighborhood_ap_geometry.json used double rotation; its outside-point count is not evidence of invalid cache.","scope":"Point containment for affected 56 nets only; not via clearance, full-chip DRC, or timing acceptance."}
(R/"reports/source26_ap_shift_geometry.json").write_text(json.dumps(result,indent=2)+"\n")
assert count==184 and not outside,result
print(json.dumps(result,indent=2))
