"""Require zero overflow explicitly; a successful router process alone is insufficient."""
from pathlib import Path
import json,re,sys,hashlib
R=Path(__file__).resolve().parents[1]
tag=sys.argv[1]
assert tag.replace("_","").isalnum()
paths=sorted((R/"runs"/tag).glob("*-openroad-*/*.log"),key=lambda p:int(p.parent.name.split("-")[0]))
log="\n".join(p.read_text(encoding="utf-8") for p in paths if "Final congestion report:" in p.read_text(encoding="utf-8"))
assert log,"Missing global-routing reports"
rows=re.findall(r"Total\s+(\d+)\s+(\d+)\s+([0-9.]+)%\s+(\d+)\s*/\s*(\d+)\s*/\s*(\d+)",log)
assert rows, "Missing explicit final global-congestion table"
resource,demand,usage,h,v,total=rows[-1]
assert int(h)==int(v)==int(total)==0,("Unresolved global congestion",rows[-1])
assert "GRT-0115" not in log
final=R/"runs"/tag/"final"
assert (final/"odb/fault_v_asic_top.odb").is_file()
s={"pass":True,"run":tag,"resources":int(resource),"demand":int(demand),"usage_pct":float(usage),"horizontal_overflow":int(h),"vertical_overflow":int(v),"total_overflow":int(total),"odb_sha256":hashlib.sha256((final/"odb/fault_v_asic_top.odb").read_bytes()).hexdigest()}
out=R/"reports"/tag;out.mkdir(parents=True,exist_ok=True)
(out/"global_checks.json").write_text(json.dumps(s,indent=2)+"\n")
print(json.dumps(s,indent=2))
