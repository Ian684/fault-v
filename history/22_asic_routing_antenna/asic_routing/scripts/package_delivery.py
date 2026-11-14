"""Package only the accepted routing result, its actual inputs and reproducible evidence."""
from pathlib import Path
import json,hashlib,shutil,subprocess,sys,stat,zipfile
R=Path(__file__).resolve().parents[1]
assert len(sys.argv)==2, "Supply the absolute delivery output directory"
out=Path(sys.argv[1])
assert out.is_absolute() and out.is_dir(), "Delivery output directory must already exist"
dst=out/"asic_routing"
read=lambda p:json.loads(p.read_text(encoding="utf-8"))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=read(R/"accepted_summary.json")
tag=s["routed_run"];global_tag=s["global_run"];selected=read(R/"selected_flow.json")
assert s["accepted"] and tag==selected["routed_run"] and global_tag==selected["global_run"]
assert s["routing_drc"]==s["global_overflow"]==0
assert not dst.exists(),"Do not merge a delivery with stale files"
dst.mkdir()
def copy(name):
    target=dst/name;target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(R/name,target)
for directory in ["macros","sta_tool","figures"]:
    shutil.copytree(R/directory,dst/directory)
for name in sorted(set(read(R/"input_identity.json")["sha256"])|{"inputs/standard_clock_rules.odb"}):copy(name)
rootfiles=["config_global.json","config_repair.json","config_detailed.json","config_sta.json","constraints.sdc","initial_state.json","initial_state_original.json","technology_identity.json","input_identity.json","accepted_summary.json","handoff_state.json","repair_state_global_buffered.json","sta_state_global_buffered.json",f"sta_state_{tag}.json","selected_flow.json","README.md","Routing_Notion.md","Verification_Report.md"]
for name in rootfiles+selected["extra_root_files"]:copy(name)
for name in selected.get("extra_files",[]):copy(name)
scripts={n for n in read(R/"input_identity.json")["sha256"] if n.startswith("scripts/")}
scripts.update("scripts/"+n for n in ["render_routing.py","write_report.py","package_delivery.py","run_selected.sh"])
for name in scripts:copy(name)
for name in ["clock_routing_rules.json","decoder_probe.log","threshold_regression.json","embedded_sta_threshold_probe.log","threshold_probe_sta310.log","global_buffered_sta_source.json",f"{tag}_sta_source.json","preparation_reproduction.json","repro_prepare_repair_sta_source.json","interrupted_route_attempt.json"]:
    copy("reports/"+name)
parent_sta_source=R/"reports"/f"{global_tag}_sta_source.json"
if parent_sta_source.is_file():copy(parent_sta_source.relative_to(R).as_posix())
for report_tag in dict.fromkeys(["global_buffered",global_tag,tag,"repro_prepare_repair"]):
    shutil.copytree(R/"reports"/report_tag,dst/"reports"/report_tag,dirs_exist_ok=True)
# Keep the real repair input; its prior electrical violations are not an accepted result.
for run_tag in dict.fromkeys(["global_electrical","global_buffered","global_buffered_sta310",global_tag,global_tag+"_sta310",tag,tag+"_sta310","repro_prepare_repair","repro_prepare_repair_sta310"]):
    run=R/"runs"/run_tag
    for p in run.rglob("*"):
        if not p.is_file():continue
        rel=p.relative_to(run)
        if rel.parts[0]=="final" or p.suffix in [".json",".log",".rpt",".tcl",".drc",".xml",".guide"] or p.name=="COMMANDS" or p.name=="estimated_global.spef":
            copy(p.relative_to(R).as_posix())
logs=dst/"logs";logs.mkdir()
for log_tag in dict.fromkeys(["global_buffered",global_tag,tag,"preparation_reproduction","repro_prepare"]+selected["diagnostic_logs"]):
    for p in (R.parent/"logs").glob(log_tag+"*.log"):shutil.copy2(p,logs/p.name)
for name in selected["diagnostic_reports"]:copy(name)
manifest={p.relative_to(dst).as_posix():sha(p) for p in sorted(dst.rglob("*")) if p.is_file()}
(dst/"MANIFEST.sha256.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8",newline="\n")
subprocess.run([sys.executable,str(dst/"scripts/check_delivery.py")],check=True)
archive=out/"Fault_V_ASIC_Routing.zip"
assert not archive.exists(),"Do not overwrite an existing archive"
with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(dst.rglob("*")):
        if not p.is_file():continue
        rel=p.relative_to(dst).as_posix()
        info=zipfile.ZipInfo.from_file(p,"routing/"+rel,strict_timestamps=False)
        info.create_system=3
        executable=rel.endswith(".sh") or rel in ["sta_tool/sta","sta_tool/sta.bin"]
        info.external_attr=((stat.S_IFREG|(0o755 if executable else 0o644))<<16)
        info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert len(z.namelist())==len(manifest)+1
    for name,digest in manifest.items():assert hashlib.sha256(z.read("routing/"+name)).hexdigest()==digest,name
digest=sha(archive)
archive.with_suffix(".zip.sha256").write_text(digest+"  "+archive.name+"\n",encoding="ascii")
print(json.dumps({"files":len(manifest)+1,"archive":str(archive),"size_bytes":archive.stat().st_size,"sha256":digest,"checks":"offline handoff, frozen inputs, ZIP CRC, every archived SHA-256"},indent=2))
