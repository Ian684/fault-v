from pathlib import Path
import odb,json,re,hashlib,collections
R=Path("/work/routing")
source=R/"runs/routed_cached_local/final/odb/fault_v_asic_top.odb"
before=hashlib.sha256(source.read_bytes()).hexdigest()
s=(R/"runs/routed_cached_local_sta310/1-openroad-staprepnr/nom_tt_025C_1v80/checks.rpt").read_text()
parts=re.split(r"\n(max slew|max capacitance|max fanout)\n",s[s.index("report_check_types"):])
sections={parts[i]:parts[i+1] for i in range(1,len(parts),2)}
row_re=r"(?m)^(\S+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+\(VIOLATED\)"
rows={key:[{"pin":pin,"limit":float(limit),"actual":float(actual),"slack":float(slack)} for pin,limit,actual,slack in re.findall(row_re,body)] for key,body in sections.items()}
assert len(rows["max slew"])==133 and len(rows["max capacitance"])==12,{k:len(v) for k,v in rows.items()}
db=odb.dbDatabase.create();odb.read_db(db,str(source));b=db.getChip().getBlock()
result={}
for kind,entries in rows.items():
 nets={};unresolved=[]
 for row in entries:
  if "/" not in row["pin"]:unresolved.append(row["pin"]);continue
  instname,pinname=row["pin"].rsplit("/",1)
  inst=b.findInst(instname) or b.findInst(instname.replace("\\",""))
  if not inst:unresolved.append(row["pin"]);continue
  pin=inst.findITerm(pinname);assert pin and pin.getNet(),row["pin"]
  net=pin.getNet();name=net.getName()
  record=nets.setdefault(name,{"net":name,"sig_type":str(net.getSigType()),"violated_pins":[],"drivers":[{"instance":t.getInst().getName(),"pin":t.getMTerm().getName(),"master":t.getInst().getMaster().getName()} for t in net.getITerms() if str(t.getMTerm().getIoType())=="OUTPUT"]})
  record["violated_pins"].append(row)
 assert not unresolved,unresolved
 drivers={x["instance"] for n in nets.values() for x in n["drivers"]}
 summary={"pin_violations":len(entries),"unique_nets":len(nets),"driver_instances":len(drivers),"clock_type_nets":sum(n["sig_type"]=="CLOCK" for n in nets.values()),"three_moved_cells_also_drivers":sorted(drivers & {"_30188_","_37463_","_37409_"})}
 result[kind]={"summary":summary,"nets":list(nets.values())}
 print("MRC_SUMMARY",kind,json.dumps(summary))
out={"source":str(source.relative_to(R)),"source_sha256":before,"reports":result,"scope":"Read-only mapping of actual OpenSTA3.1.0 extracted-RC violations to OpenDB nets and drivers. No acceptance."}
(R/"reports/cached_mrc_inventory.json").write_text(json.dumps(out,indent=2)+"\n")
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
