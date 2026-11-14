"""Render a GDS to PNG with the SKY130 KLayout layer properties (klayout -zz -r, read only).
Env: GDS, OUT, LYP, WIDTH (px), BG (hex colour), LAYERS (optional comma list of layer/datatype to keep visible)."""
import os
import pya

gds, out, lyp = os.environ['GDS'], os.environ['OUT'], os.environ['LYP']
width = int(os.environ.get('WIDTH', '3000'))
view = pya.LayoutView()
view.set_config('background-color', os.environ.get('BG', '#000000'))
view.set_config('grid-visible', 'false')
view.set_config('text-visible', 'false')
view.set_config('bitmap-oversampling', '2')
cv_index = view.load_layout(gds, 0)
view.load_layer_props(lyp)
view.max_hier()
keep = os.environ.get('LAYERS')
if keep:
    wanted = {tuple(int(x) for x in s.split('/')) for s in keep.split(',')}
    it = view.begin_layers()
    while not it.at_end():
        lp = it.current()
        node = lp.dup()
        node.visible = (lp.source_layer, lp.source_datatype) in wanted
        view.set_layer_properties(it, node)
        it.next()
cell = view.cellview(cv_index).cell
box = cell.dbbox()
height = int(width * box.height() / box.width())
view.zoom_box(box)
view.save_image_with_options(out, width, height, 0, 0, 0, box, False)
print('RENDERED', out, width, height, box)
