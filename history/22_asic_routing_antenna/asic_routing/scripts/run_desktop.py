"""Run the frozen, unaccepted physical candidate on the replacement computer."""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,subprocess,sys,time
R=Path(__file__).resolve().parents[1]
IMAGE="ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302"
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def resources(cpus,available_mb):
 threads=min(16,cpus);memory=min(12000,available_mb-1024)
 assert threads>=1 and memory>=6000,("WSL needs at least about7GiB available; adjust its memory limit or close other workloads",available_mb)
 return threads,memory
assert resources(32,30000)==(16,12000) and resources(8,7500)==(8,6476)
try:resources(8,5000)
except AssertionError:pass
else:raise AssertionError("Low-memory guard failed")
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--check-only",action="store_true")
args=parser.parse_args()
s=json.loads((R/"Transfer_State.json").read_text())
assert s["accepted"] is False and s["global_run"]=="global_cold_corner_keepout"
assert s["cli"]=="scripts/cold_corner_keepout_cli.py" and s["config"]=="config_corner_reguide.json" and s["state"]=="cold_corner_keepout_state.json"
assert s["candidate_odb"]=="inputs/cold_corner_keepout_reguide.odb" and sha(R/s["candidate_odb"])==s["candidate_sha256"]
subprocess.run([sys.executable,str(R/"scripts/check_inputs.py")],check=True)
state=json.loads((R/s["state"]).read_text());assert state["odb"]=="/work/routing/"+s["candidate_odb"]
c=json.loads((R/s["config"]).read_text())
assert c["CLOCK_PERIOD"]==40 and c["DRT_OPT_ITERS"]==64 and c["ERROR_ON_TR_DRC"] is True and c["DRT_ANTENNA_REPAIR_ITERS"]==0
g=json.loads((R/"reports"/s["global_run"]/"global_checks.json").read_text())
assert g["pass"] and g["total_overflow"]==0 and sha(R/"runs"/s["global_run"]/"final/odb/fault_v_asic_top.odb")==g["odb_sha256"]
daemon=json.loads(subprocess.check_output(["docker","info","--format","{{json .}}"],text=True))
assert daemon["NCPU"]>=1 and daemon["MemTotal"]>0
subprocess.run(["docker","image","inspect",IMAGE],check=True,stdout=subprocess.DEVNULL)
for cid in subprocess.check_output(["docker","ps","-q"],text=True).split():
 info=json.loads(subprocess.check_output(["docker","inspect",cid],text=True))[0]
 assert not any(Path(m["Source"]).resolve()==R.parent.resolve() for m in info["Mounts"] if m["Type"]=="bind"),("Another job uses this project",info["Name"])
version=subprocess.check_output(["docker","run","--rm","--memory=500m","--cpus=1",IMAGE,"openroad","-version"],text=True)
assert "dcf36133a369abc8f3c5e5738cd4d82e4903c0e0" in version,version
available=int(next(x.split()[1] for x in Path("/proc/meminfo").read_text().splitlines() if x.startswith("MemAvailable:")))//1024
threads,memory=resources(min(os.cpu_count() or 1,daemon["NCPU"]),min(available,daemon["MemTotal"]//(1024*1024)))
subprocess.run(["docker","run","--rm","--memory=1000m","--cpus=1","--user",str(os.getuid())+":"+str(os.getgid()),"-v",str(R.parent)+":/work","-w","/work/routing",IMAGE,"python3","scripts/check_inputs.py"],check=True)
report={"accepted":False,"check_only":args.check_only,"observed_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"root":str(R.parent),"cpu_count":os.cpu_count(),"docker_cpu_count":daemon["NCPU"],"docker_total_mb":daemon["MemTotal"]//(1024*1024),"actual_container_bind_hash_check":True,"mem_available_mb":available,"threads":threads,"memory_mb":memory,"image":IMAGE,"openroad_version":version.strip(),"candidate_sha256":s["candidate_sha256"],"scope":"Environment, frozen inputs, actual global-overflow source and pinned tool version only; no detailed-routing/timing/DRC acceptance."}
print(json.dumps(report,indent=2),flush=True)
if args.check_only:raise SystemExit(0)
tag="routed_desktop_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
assert re.fullmatch(r"[A-Za-z0-9_]+",tag)
log=R.parent/"logs"/(tag+".log");checks=R.parent/"logs"/(tag+"_checks.log")
run_config=R/("config_"+tag+".json");meta=R/"reports"/(tag+"_launch.json")
assert not any(p.exists() for p in [log,checks,run_config,meta,R/"runs"/tag,R/"reports"/tag])
c["DRT_THREADS"]=threads
# Only parallelism changes for the faster machine; keep every physical rule and gate.
original=json.loads((R/s["config"]).read_text())
assert {k:v for k,v in c.items() if k!="DRT_THREADS"}=={k:v for k,v in original.items() if k!="DRT_THREADS"}
run_config.write_text(json.dumps(c,indent=2)+"\n")
report.update({"run":tag,"global_run":s["global_run"],"cli":s["cli"],"state":s["state"],"config":run_config.name,"config_sha256":sha(run_config),"native_log":str(log),"checks_log":str(checks),"started_unix":time.time()})
meta.write_text(json.dumps(report,indent=2)+"\n")
cmd=["docker","run","--rm","--name","faultv-desktop-"+tag,"--user",str(os.getuid())+":"+str(os.getgid()),"--memory="+str(memory)+"m","--memory-swap="+str(memory)+"m","--cpus="+str(threads),"-v",str(R.parent)+":/work","-w","/work/routing",IMAGE,"python3",s["cli"],"--pdk-root","/work/pdk","--with-initial-state","/work/routing/"+s["state"],"--run-tag",tag,run_config.name]
print("RUN",tag,"\nLOG",log,"\nCHECKS",checks,flush=True)
with log.open("w") as f:result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
report["native_exit"]=result.returncode
(R.parent/"logs"/(tag+".exit")).write_text(str(result.returncode)+"\n")
if result.returncode==0:
 print("Native flow finished; running actual RC/timing/connectivity/independent DRC checks.",flush=True)
 with checks.open("w") as f:result=subprocess.run(["bash","scripts/run_checks.sh",s["global_run"],tag,"routed"],cwd=R,stdout=f,stderr=subprocess.STDOUT)
 report["checks_exit"]=result.returncode
report["finished_unix"]=time.time()
accepted=R/"accepted_summary.json"
if result.returncode==0:
 assert accepted.exists()
 a=json.loads(accepted.read_text());assert a["accepted"] is True and a["routed_run"]==tag
 report["accepted"]=True
meta.write_text(json.dumps(report,indent=2)+"\n")
print("EXIT",result.returncode,"ACCEPTED",report["accepted"],"RUN",tag,flush=True)
if result.returncode:print((checks if checks.exists() else log).read_text(errors="replace")[-4500:])
raise SystemExit(result.returncode)
