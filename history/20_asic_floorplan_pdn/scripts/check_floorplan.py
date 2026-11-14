"""Validate actual floorplan geometry and unchanged functional connectivity."""
from pathlib import Path
from collections import Counter
import hashlib, json, os
import odb

R = Path(__file__).resolve().parents[1]
tag = os.environ.get("FLOORPLAN_RUN_TAG", "floorplan_accepted")
assert tag.replace("_", "").isalnum(), tag
run = R / "runs" / tag
out = R / "reports" / tag
out.mkdir(parents=True, exist_ok=True)
for name, sha in json.loads((R / "input_identity.json").read_text()).items():
    assert hashlib.sha256((R / name).read_bytes()).hexdigest() == sha, name
cfg = json.loads((R / "config.json").read_text())
assert hashlib.sha256((R / "inputs/mapped_top.v").read_bytes()).hexdigest() == "88b35c08aa99b400a6bd72d7d1128b2d63fd8e9a04ae0f441698587c29f036f0"
p = list((run / "final/odb").glob("*.odb"))
assert len(p) == 1, p
db = odb.dbDatabase.create()
odb.read_db(db, str(p[0]))
b = db.getChip().getBlock()
u = b.getDbUnitsPerMicron()
def rect(box):
    return [box.xMin()/u, box.yMin()/u, box.xMax()/u, box.yMax()/u]
def overlap(a, c):
    return a[0] < c[2]-1e-7 and c[0] < a[2]-1e-7 and a[1] < c[3]-1e-7 and c[1] < a[3]-1e-7
def inside(a, c):
    return all([a[0] >= c[0]-1e-7, a[1] >= c[1]-1e-7, a[2] <= c[2]+1e-7, a[3] <= c[3]+1e-7])
assert overlap([0,0,2,2], [1,1,3,3])
assert not overlap([0,0,1,1], [1,0,2,1])
die, core = rect(b.getDieArea()), rect(b.getCoreArea())
assert die == cfg["DIE_AREA"] and core == cfg["CORE_AREA"], (die, core)
macro_cfg = cfg["MACROS"]["sky130_sram_2kbyte_1rw1r_32x512_8"]["instances"]
macros = {}
types = Counter()
pg_pins = 0
for i in b.getInsts():
    types[i.getMaster().getName()] += 1
    for t in i.getITerms():
        st = t.getMTerm().getSigType()
        if st in ["POWER", "GROUND"]:
            expect = "VPWR" if st == "POWER" else "VGND"
            assert t.getNet() and t.getNet().getName() == expect, (i.getName(), t.getMTerm().getName())
            pg_pins += 1
    if i.getMaster().getType() == "BLOCK":
        name = i.getName().replace("\\", "")
        assert name in macro_cfg, name
        bb = rect(i.getBBox())
        assert i.isFixed() and str(i.getOrient()) == "R0", (name, i.getPlacementStatus(), i.getOrient())
        assert bb[:2] == macro_cfg[name]["location"], (name, bb)
        assert abs(bb[2]-bb[0]-683.1) < .001 and abs(bb[3]-bb[1]-416.54) < .001
        halo = [bb[0]-20,bb[1]-20,bb[2]+20,bb[3]+20]
        assert inside(halo, core), name
        assert {t.getMTerm().getName(): t.getNet().getName() for t in i.getITerms() if t.getMTerm().getSigType() in ["POWER", "GROUND"]} == {"vccd1":"VPWR","vssd1":"VGND"}
        macros[name] = {"bbox":bb,"halo":halo,"orientation":str(i.getOrient())}
assert set(macros) == set(macro_cfg) and len(macros) == 18
vals = list(macros.values())
for j, m in enumerate(vals):
    for n in vals[j+1:]:
        assert not overlap(m["halo"], n["halo"]), (m,n)
row_area = 0
for row in b.getRows():
    bb = rect(row.getBBox())
    row_area += row.getSiteCount()*row.getSite().getWidth()*row.getSite().getHeight()/u**2
    assert inside(bb, core), row.getName()
    for m in vals:
        assert not overlap(bb, m["halo"]), (row.getName(),bb,m["halo"])
# Compare all original signal connections against the first imported database.
ref = odb.dbDatabase.create()
odb.read_db(ref, str(next(run.glob("*-openroad-floorplan/fault_v_asic_top.odb"))))
rb = ref.getChip().getBlock()
def signal_map(block):
    cells, terms = {}, {}
    for i in block.getInsts():
        signal_terms = [t for t in i.getITerms() if t.getMTerm().getSigType() not in ["POWER","GROUND"]]
        if not signal_terms:
            continue
        cells[i.getName()] = i.getMaster().getName()
        for t in signal_terms:
            terms[(i.getName(),t.getMTerm().getName())] = t.getNet().getName() if t.getNet() else None
    ports = {p.getName():p.getNet().getName() if p.getNet() else None for p in block.getBTerms() if p.getSigType() not in ["POWER","GROUND"]}
    return cells, terms, ports
a, z = signal_map(rb), signal_map(b)
assert a == z, "Functional cell/port connectivity changed during floorplanning"
assert len(a[0]) == 29466 and len(a[2]) == 108
pins = {}
for t in b.getBTerms():
    if t.getSigType() in ["POWER","GROUND"]:
        continue
    boxes = []
    assert t.getBPins(), t.getName()
    for pin in t.getBPins():
        assert pin.getPlacementStatus() in ["PLACED","FIRM","LOCKED"], (t.getName(),pin.getPlacementStatus())
        for box in pin.getBoxes():
            bb=rect(box)
            assert inside(bb,die), (t.getName(),bb)
            boxes.append({"layer":box.getTechLayer().getName(),"bbox":bb})
    assert boxes
    pins[t.getName()]=boxes
shapes, counts = [], {}
for name in ["VPWR","VGND"]:
    net=b.findNet(name)
    assert net and net.getSWires() and net.getBTerms(), name
    metals=Counter();vias=Counter()
    for wire in net.getSWires():
        for s in wire.getWires():
            assert inside(rect(s),die), (name,rect(s))
            if s.isVia():
                v=s.getTechVia() or s.getBlockVia()
                vias[v.getName()]+=1
            else:
                layer=s.getTechLayer().getName()
                metals[layer]+=1
                if layer in ["met4","met5"]:
                    shapes.append({"net":name,"layer":layer,"bbox":rect(s)})
    assert metals["met1"] and metals["met4"] and metals["met5"] and vias
    counts[name]={"metal_shapes":dict(metals),"via_instances":sum(vias.values()),"via_types":dict(vias)}
metrics=json.loads((run/"final/metrics.json").read_text())
for k in ["design__power_grid_violation__count","design__power_grid_violation__count__net:VPWR","design__power_grid_violation__count__net:VGND"]:
    assert metrics[k] == 0, (k,metrics.get(k))
pdnlog=next(run.glob("*-openroad-generatepdn/openroad-generatepdn.log")).read_text()
assert "PDN-0110" not in pdnlog, "Some PDN via intersections were too small"
assert "[ERROR" not in pdnlog
macro_area=sum((m["bbox"][2]-m["bbox"][0])*(m["bbox"][3]-m["bbox"][1]) for m in vals)
std_area=sum(i.getMaster().getWidth()*i.getMaster().getHeight()/u**2 for i in b.getInsts() if i.getMaster().getType() != "BLOCK")
functional_status=Counter(i.getPlacementStatus() for i in b.getInsts() if i.getName() in a[0])
summary={"stdcell_area_um2":std_area,"functional_placement_status":dict(functional_status),"accepted":True,"run":tag,"die_um":die,"core_um":core,"macro_count":len(macros),"macro_area_um2":macro_area,"placement_row_count":len(b.getRows()),"placeable_row_area_um2":row_area,"instance_count":len(b.getInsts()),"masters":dict(types),"connected_pg_iterms":pg_pins,"macro_pg_iterms":36,"placed_signal_pins":len(pins),"functional_cell_count":len(a[0]),"functional_iterm_count":len(a[1]),"functional_port_count":len(a[2]),"power_grid_violations":metrics["design__power_grid_violation__count"],"pdn_missing_via_warnings":0,"power_geometry":counts,"macros":macros,"signal_pins":pins,"plot_shapes":shapes}
(out/"floorplan_checks.json").write_text(json.dumps(summary,indent=2)+"\n")
print("ALL FLOORPLAN GEOMETRY / POWER CONNECTION / FUNCTIONAL CONNECTIVITY CHECKS PASSED")
print(json.dumps({k:v for k,v in summary.items() if k not in ["masters","macros","signal_pins","plot_shapes","power_geometry"]},indent=2))
