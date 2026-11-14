from pathlib import Path
import json,hashlib,zipfile
R=Path(__file__).resolve().parent.parent
required={
 "logs/tb_mem_arbiter.log":"ALL 6000 ARBITER TRANSACTIONS PASSED",
 "logs/tb_sram_banks.log":"ALL 4 SRAM BANK MODES PASSED",
 "logs/tb_asic_boot.log":"MAXIMUM IMAGE",
 "logs/tb_asic_streams.log":"ALL STREAM SCENARIO RUNS PASSED",
 "logs/tb_loader_priority.log":"ALL LOADER ERROR PRIORITY CHECKS PASSED",
 "logs/tb_gate.log":"ALL MAPPED GATE PROGRAM CHECKS PASSED"
}
for p,marker in required.items():
 s=(R/p).read_text(encoding="utf8")
 assert marker in s and "Fatal:" not in s,(p,"acceptance marker missing")
m=json.loads((R/"reports/tt_delivery_reload/final/metrics.json").read_text())
for key in ["design__max_slew_violation__count","design__max_cap_violation__count","timing__setup_vio__count","timing__hold_vio__count"]:
 assert m[key]==0,(key,m[key])
assert m["timing__setup__ws"]>0 and m["timing__hold__ws"]>0
final_hash=hashlib.sha256((R/"mapped_top.v").read_bytes()).hexdigest()
assert final_hash==json.loads((R/"reports/gate_input_identity.json").read_text())["mapped_top.v"]
assert final_hash==json.loads((R/"reports/identity_check.json").read_text())["mapped_netlist_sha256"]
assert final_hash==json.loads((R/"eco/connectivity_proof.json").read_text())["netlist_sha256"]
for rel in ["eco/connectivity_proof.json","reports/threshold_regression.json","reports/opensta_upstream_tests.json","reports/delivery_selfcheck.json"]:
 assert json.loads((R/rel).read_text())["pass"],rel
for rel,h in json.loads((R/"source_identity.json").read_text()).items():
 assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==h,rel
assert (R/"Verification_Report.md").stat().st_size>1000
assert all(x not in (R/"ASIC_Synthesis_Notion.md").read_text(encoding="utf8") for x in ["Week","Day","W20"])
skip={"sim","sim_priority","gate_sim","gate_sim_linux","__pycache__",".Xil"}
files=[p for p in R.rglob("*") if p.is_file() and not any(x in skip for x in p.relative_to(R).parts) and p.name!="MANIFEST.json"]
manifest={str(p.relative_to(R)).replace("\\","/"):{"bytes":p.stat().st_size,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)}
(R/"MANIFEST.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf8")
dest=R.parent/"Fault_V_ASIC_Synthesis_STA.zip"
with zipfile.ZipFile(dest,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(files)+[R/"MANIFEST.json"]:
  z.write(p,"Fault_V_ASIC_Synthesis_STA/"+str(p.relative_to(R)).replace("\\","/"))
with zipfile.ZipFile(dest) as z:
 assert z.testzip() is None
 for rel,item in manifest.items():
  assert hashlib.sha256(z.read("Fault_V_ASIC_Synthesis_STA/"+rel)).hexdigest()==item["sha256"],rel
print("PASS archive CRC and every manifest SHA-256;",len(files),"files;",dest.stat().st_size,"bytes")
print("SHA256",hashlib.sha256(dest.read_bytes()).hexdigest())
