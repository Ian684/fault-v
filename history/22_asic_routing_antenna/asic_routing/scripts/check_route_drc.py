"""Fresh full-chip DRC, using the immutable, already-tested negative-control calibration."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(__file__).resolve().parents[1]
tag=sys.argv[1];assert tag.replace("_","").isalnum()
out=R/"reports"/tag;out.mkdir(parents=True,exist_ok=True)
image="ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302"
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
source=R/"runs/routed_final/1-openroad-detailedrouting/drt_iter52.odb"
actual=R/"runs"/tag/"final/odb/fault_v_asic_top.odb"
locks=read(R/"input_identity.json")["sha256"]
for name in ["reports/drc_gate_negative_test.json","reports/drc_gate_negative/full_drc_calibration.json"]:
    assert sha(R/name)==locks[name],("Changed calibration evidence",name)
negative=read(R/"reports/drc_gate_negative_test.json")
calibration=read(R/"reports/drc_gate_negative/full_drc_calibration.json")
assert negative["image"]==image
assert negative["passed"] and negative["expected_exit_code"]==1 and not negative["accepted_receipt_created"]
assert sha(source)==negative["source_odb_sha256"]==calibration["odb_sha256"]
assert sha(R/"scripts/native_route_drc.py")==negative["native_checker_sha256"]
assert calibration["physical_geometry_unchanged"] and calibration["unresolved_count"]==2
assert all(m["type"]=="Short" and m["layer"]=="met1" and m["context_markers"] for m in calibration["unresolved"])
assert "_10901_" in str(calibration["unresolved"]) and "net2689" in str(calibration["unresolved"])
report=out/"full_drc_selected.rpt"
log=R.parent/"logs"/f"{tag}_full_drc_selected.log"
assert not report.exists() and not report.with_suffix(".json").exists() and not list(out.glob("full_drc_selected.context_*.rpt")),"Refuse stale DRC outputs; use a fresh run tag"
with log.open("w") as f:
    subprocess.run(["docker","run","--rm","--user","1000:1000","--cpus=4",
        "-e","ROUTE_DRC_ODB=/work/routing/"+actual.relative_to(R).as_posix(),
        "-e","ROUTE_DRC_REPORT=/work/routing/"+report.relative_to(R).as_posix(),
        "-v",str(R.parent)+":/work","-w","/work/routing",image,
        "openroad","-no_init","-no_splash","-exit","-python","scripts/native_route_drc.py"],
        stdout=f,stderr=subprocess.STDOUT,check=True)
native_log=log.read_text()
assert "[ERROR" not in native_log,native_log[-4000:]
assert "FAULTV_FULL_CHIP_DRC_RECHECK_COMPLETE" in native_log
selected=read(report.with_suffix(".json"))
assert selected["physical_geometry_unchanged"] and selected["odb_sha256"]==sha(actual)
assert selected["unresolved_count"]==0,(tag,selected["unresolved_count"])
record={"pass":True,"run":tag,"independent_full_chip_drc":0,
        "raw_marker_count":selected["raw_marker_count"],
        "confirmed_partition_artifacts":selected["confirmed_partition_artifacts"],
        "negative_control_known_shorts":2,"odb_sha256":sha(actual),
        "calibration_odb_sha256":sha(source),"image":image,
        "scope":"Fresh native full-chip DRC with centered-context checks of every marker; calibration reused only with matching source/checker/evidence SHA-256. No technology waiver. Not foundry DRC/LVS."}
(out/"full_drc_checks.json").write_text(json.dumps(record,indent=2)+"\n")
print("ALL CALIBRATED INDEPENDENT FULL-CHIP ROUTING DRC CHECKS PASSED")
