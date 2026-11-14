from pathlib import Path
import odb,json,hashlib
R=Path('/work/routing');source=R/'inputs/desktop_residual_four_native.odb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();proof=json.loads((R/'reports/desktop_residual_four_native_input.json').read_text(encoding='utf-8'));assert sha(source)==proof['derived_sha256']
dirty=set(proof['cleared_whole_nets']);missing_retained=0;dirty_terms=0;d=odb.dbDatabase.create();odb.read_db(d,str(source));b=d.getChip().getBlock();errors=[];error_count=0;active=0;checked=0;access_points=0;sample=None
for net in b.getNets():
 if str(net.getSigType()) in ['POWER','GROUND']:continue
 terms=[q for q in net.getITerms() if str(q.getMTerm().getSigType()) not in ['POWER','GROUND']]
 if len(terms)+len(net.getBTerms())<2:continue
 active+=1
 for term in terms:
  checked+=1;aps=list(term.getPrefAccessPoints());x,y=term.getInst().getLocation();geometries=list(term.getGeometries())
  if net.getName() in dirty:dirty_terms+=1
  if not aps:
   if net.getName() in dirty:
    error_count+=1
    if len(errors)<20:errors.append({'net':net.getName(),'pin':term.getInst().getName()+'/'+term.getMTerm().getName(),'error':'No preferred AP on cleared-net pin'})
   else:missing_retained+=1
  for ap in aps:
   access_points+=1;ax,ay=ap.getPoint();gx,gy=x+ax,y+ay;layer=ap.getLayer().getName();inside=any(l.getName()==layer and box.xMin()<=gx<=box.xMax() and box.yMin()<=gy<=box.yMax() for l,box in geometries)
   if not inside:
    error_count+=1
    if len(errors)<20:errors.append({'pin':term.getInst().getName()+'/'+term.getMTerm().getName(),'layer':layer,'computed_point':[gx,gy],'ap_point':[ax,ay],'inst_location':[x,y],'error':'AP outside actual pin'})
   elif sample is None:sample=(geometries,layer,gx,gy)
assert checked>50000 and active>0 and sample is not None
geometries,layer,x,y=sample;badx=x+b.getDieArea().dx()+1000000;negative=not any(l.getName()==layer and box.xMin()<=badx<=box.xMax() and box.yMin()<=y<=box.yMax() for l,box in geometries);assert negative
record={'pass':error_count==0,'accepted':False,'source':str(source.relative_to(R)),'source_sha256':sha(source),'active_nets':active,'validated_iterms':checked,'cleared_net_iterms_requiring_cached_AP':dirty_terms,'retained_routed_iterms_without_preferred_AP':missing_retained,'preferred_access_points':access_points,'error_count':error_count,'first_errors':errors,'negative_mismatch_control_detected':negative,'mapping':'Preferred access point coordinates plus the unchanged instance location, checked against actual transformed ITerm metal shapes.','scope':'All existing preferred APs must lie in actual unchanged pin metal. Every terminal of each cleared net additionally requires a preferred AP. Retained fully native-routed nets may lack preferred AP metadata; their wires remain unchanged. This is preparation only; native physical/RC/STA/phase/PG and independent DRC gates remain mandatory.'}
(R/'reports/desktop_residual_four_cleared_pin_access.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record,indent=2),flush=True);assert record['pass'],'Cached pin-access guard failed'
