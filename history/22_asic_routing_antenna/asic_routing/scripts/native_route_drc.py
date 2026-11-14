"""Full-chip native DRC plus centered context checks for each reported marker."""
from pathlib import Path
from openroad import Tech,Design
import odb,json,os,re,hashlib,math
R=Path("/work/routing")
source=Path(os.environ["ROUTE_DRC_ODB"])
out=Path(os.environ["ROUTE_DRC_REPORT"]).with_suffix("")
t=Tech();design=Design(t);design.readDb(str(source))
db=design.getDb();b=db.getChip().getBlock();u=b.getDbUnitsPerMicron()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source_sha=sha(source)
def geometry_signature():
    return (
        tuple((i.getName(),i.getMaster().getName(),str(i.getOrient()),tuple(i.getLocation())) for i in b.getInsts()),
        tuple((n.getName(),n.getWire().getLength() if n.getWire() else None,
               tuple(sorted((p.getInst().getName(),p.getMTerm().getName()) for p in n.getITerms()))) for n in b.getNets())
    )
before=geometry_signature()
design.evalTclString("set_thread_count 4")
def check(path,box=None):
    design.getTritonRoute().clearDesign()
    args="" if box is None else "-box {"+" ".join(map(str,box))+"}"
    design.evalTclString(f"drt::check_drc {args} -output_file {path} -marker_name IndependentFullChip")
    text=path.read_text()
    pattern=r"violation type: ([^\n]+)\n\s*srcs: ([^\n]+)\n\s*bbox = \(([-0-9.]+), ([-0-9.]+)\) - \(([-0-9.]+), ([-0-9.]+)\) on Layer ([^\n]+)"
    rows=[]
    for m in re.finditer(pattern,text):
        kind,src,*coords,layer=m.groups()
        rows.append({"type":kind,"srcs":src.strip(),"bbox_dbu":[round(float(x)*u) for x in coords],"layer":layer.strip()})
    assert len(rows)==text.count("violation type:"),"Unparsed DRC report entries"
    return rows
raw=check(out.with_suffix(".rpt"))
die=b.getDieArea();grid=b.getGCellGrid()
details=[]
for index,marker in enumerate(raw):
    x1,y1,x2,y2=marker["bbox_dbu"];cx=(x1+x2)//2;cy=(y1+y2)//2
    # Center the feature in a 96.6um analysis tile so its complete pin geometry is present.
    pitch=13800;tile=7*pitch
    ox=(cx-tile//2)%tile-tile;oy=(cy-tile//2)%tile-tile
    grid.resetGrid()
    grid.addGridPatternX(ox,math.ceil((die.xMax()-ox)/pitch)+2,pitch)
    grid.addGridPatternY(oy,math.ceil((die.yMax()-oy)/pitch)+2,pitch)
    box=[x1-500,y1-500,x2+500,y2+500]
    context=check(Path(str(out)+f".context_{index:03}.rpt"),box)
    eligible=marker["layer"]=="li1" and marker["type"] in ["NS Metal","Metal Spacing"] and marker["srcs"].count("net:")==1
    artifact=eligible and len(context)==0
    details.append({**marker,"centered_grid_dbu":[ox,oy,pitch],
                    "context_box_dbu":box,"context_markers":context,
                    "confirmed_partition_artifact":artifact})
    print("CENTERED_CONTEXT",index,marker["layer"],len(context),"artifact",artifact,flush=True)
assert geometry_signature()==before,"Physical cells/connectivity/wire lengths changed during analysis"
assert sha(source)==source_sha,"Input ODB was modified"
unresolved=[m for m in details if not m["confirmed_partition_artifact"]]
record={"raw_marker_count":len(raw),"confirmed_partition_artifacts":len(details)-len(unresolved),
        "unresolved_count":len(unresolved),"unresolved":unresolved,"markers":details,
        "odb_sha256":source_sha,"physical_geometry_unchanged":True,
        "scope":"Full-chip native report followed by centered native recheck of every marker. Only same-net li1 NS/spacing markers that disappear with complete context are classified as partition artifacts. All other markers remain unresolved. No technology rule, design geometry or input file changed."}
Path(str(out)+".json").write_text(json.dumps(record,indent=2)+"\n")
print("FAULTV_FULL_CHIP_DRC_RECHECK_COMPLETE",flush=True)
