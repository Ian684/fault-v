from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1]
deck=C.parent/'pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.tech/klayout/drc/sky130A_mr.drc'
text=deck.read_text();changes={}
for name,dummy in [('li',56),('m1',36),('m2',41),('m3',34),('m4',51),('m5',59)]:
    old=f'{name} = polygons({name}_wildcard)';new=old+f' | polygons({dummy}, 28)'
    assert text.count(old)==1,old;text=text.replace(old,new);changes[old]=new
target=C/'controls/sky130_fill_interaction.drc'
prefix='$floating_met = "false"\n$feol = "false"\n$beol = "true"\n$offgrid = "true"\n$seal = "false"\n$sram_exclude = "false"\n$thr = "2"\n'
target.write_text(prefix+text)
(C/'reports/fill_screen_coverage.json').write_text(json.dumps({'source_deck_sha256':hashlib.sha256(deck.read_bytes()).hexdigest(),'derived_deck_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'six_geometry_unions':changes,'scope':'Additional BEOL mask width/spacing/grid screen with drawing and dummy metal combined. Floating-net connectivity is inapplicable to deliberate dummy fill; source-only full DRC retains floating checks. FEOL dummy qualification, approved foundry density and fill-aware PEX are not established by this extra screen.'},indent=2)+'\n')
print('FILL_INTERACTION_SCREEN_PREPARED',flush=True)
