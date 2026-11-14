from pathlib import Path
import hashlib,json,re
C=Path(__file__).resolve().parents[1];source=C/'controls/sky130_fill_interaction.drc'
text=source.read_text();assert len(re.findall(r'^deep$',text,re.M))==1
text=re.sub(r'^deep$','tiles(70.um)\ntile_borders(5.um)',text,flags=re.M)
target=C/'controls/sky130_fill_interaction_tiled.drc';target.write_text(text)
record=json.loads((C/'reports/fill_screen_coverage.json').read_text())
record.update(execution='70um tiles with 5um overlap; local BEOL width/spacing/grid screen',tiled_deck_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),tiling_documentation='https://klayout.de/doc/about/drc_ref_global.html',long_range_area_or_topology_signoff=False)
(C/'reports/fill_tiled_screen_coverage.json').write_text(json.dumps(record,indent=2)+'\n')
print('Bounded local fill-interaction screen prepared',flush=True)
