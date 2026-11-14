"""Write a copy of an OASIS layout with one top-cell met1 (68/20) polygon removed, for the XOR negative control.
Usage: python3 make_xor_negative.py <in.oas> <out.oas> <info.json>"""
import json, sys
import pya
src, dst, info = sys.argv[1:4]
ly = pya.Layout(); ly.read(src)
c = ly.top_cell(); li = ly.find_layer(68, 20)
victim = next(s for s in c.shapes(li).each() if not s.is_text() and s.bbox().width() > 2000 and s.bbox().height() > 100)
box = victim.bbox(); desc = str(victim)
c.shapes(li).erase(victim)
ly.write(dst)
open(info, 'w').write(json.dumps({'removed': desc, 'bbox_dbu': [box.left, box.bottom, box.right, box.top]}, indent=2) + '\n')
print('NEG_WRITTEN', desc)
