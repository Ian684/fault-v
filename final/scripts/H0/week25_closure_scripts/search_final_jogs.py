"""Apply bounded fine-grid jog search to the completed four-short checkpoint."""
from pathlib import Path
import hashlib,json
C=Path('/work/week25_closure');source=C/'scripts/search_local_jogs.py';code=source.read_text()
replacements=[
 ('/route_b/1-openroad-detailedrouting/drt_iter20.odb','/route_b/1-openroad-detailedrouting/native_final.odb'),
 ("out=C/'reports/local_jogs_a'","out=C/'reports/final_jogs_a'"),
 ("if q[-1]!='li1')==9","if q[-1]!='li1')==4"),
 ('for step in (1,-1,2,-2,3,-3,4,-4):','for delta in (280,-280,300,-300,320,-320,340,-340,460,-460,230,-230,200,-200,140,-140,60,-60):'),
 ('delta=step*pitch;an=','an='),
 ('graph=odb.dbWireGraph();graph.decode(w)','_,ids=primitives(w);graph=odb.dbWireGraph();graph.decode(w)'),
 ('/runtime_final/local_jogs.odb','/runtime_final/final_jogs.odb'),
 ("C/'inputs/local_jogs.odb'","C/'inputs/final_jogs.odb'"),
]
for old,new in replacements:assert code.count(old)==1,old;code=code.replace(old,new)
target=C/'controls/final_jogs_impl.py';assert not target.exists();target.write_text(code,newline='\n')
(C/'reports/final_jogs_source.json').write_text(json.dumps({'base_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'source_checkpoint':'short_cover_b native_final, 4 native DRVs','all_whole_chip_DRC_and_terminal_connectivity_guards_retained':True},indent=2)+'\n')
exec(compile(code,str(target),'exec'),{'__file__':str(target),'__name__':'__main__'})
