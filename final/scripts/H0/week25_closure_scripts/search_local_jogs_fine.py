"""Use manufacturing-grid offsets where a whole routing-track move is too large."""
from pathlib import Path
import hashlib,json
C=Path('/work/week25_closure');source=C/'scripts/search_local_jogs.py';code=source.read_text()
replacements=[
 ("out=C/'reports/local_jogs_a'","out=C/'reports/local_jogs_fine'"),
 ('for step in (1,-1,2,-2,3,-3,4,-4):',"for delta in ((60,-60,80,-80,100,-100,140,-140,180,-180,220,-220,280,-280,340,-340,460,-460) if marker[0]=='Metal Spacing' else (280,-280,300,-300,320,-320,340,-340,460,-460,230,-230,200,-200,140,-140,60,-60)):"),
 ('delta=step*pitch;an=', 'an='),
 ('graph=odb.dbWireGraph();graph.decode(w)','_,ids=primitives(w);graph=odb.dbWireGraph();graph.decode(w)'),
 ('/runtime_final/local_jogs.odb','/runtime_final/local_jogs_fine.odb'),
 ("C/'inputs/local_jogs.odb'","C/'inputs/local_jogs_fine.odb'"),
]
for old,new in replacements:assert code.count(old)==1,old;code=code.replace(old,new)
target=C/'controls/local_jogs_fine_impl.py';assert not target.exists();target.write_text(code,newline='\n')
(C/'reports/local_jogs_fine_source.json').write_text(json.dumps({'base_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'manufacturing_grid_nm':5,'all_offsets_integer_multiples_of_grid':True,'whole_chip_DRC_and_connectivity_guards_retained':True},indent=2)+'\n')
exec(compile(code,str(target),'exec'),{'__file__':str(target),'__name__':'__main__'})
