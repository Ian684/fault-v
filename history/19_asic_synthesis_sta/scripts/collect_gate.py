from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parent.parent
L=Path(r"D:\Codex\WSL\fault-v-asic")
raw=(L/"design/logs/tb_gate.log").read_text(encoding="utf8")
assert "ALL MAPPED GATE PROGRAM CHECKS PASSED" in raw and "FATAL" not in raw,"Gate run is not complete"
paths=["mapped_top.v","macros/model.v","macros/primitives_xsim.v","macros/sky130_fd_sc_hd_xsim.v","verify/tb_gate_accept.sv","programs/gate_program.mem","programs/short_packet.hex"]
identity={}
for rel in paths:
 a=(R/rel).read_bytes();b=(L/"design"/rel).read_bytes()
 assert a==b,rel
 identity[rel]=hashlib.sha256(a).hexdigest()
for name in ["tb_gate.log","gate_simulator_version.txt","gate_iverilog_compile.log"]:
 shutil.copy2(L/"design/logs"/name,R/"logs"/name)
shutil.copy2(L/"logs/gate_linux_console.txt",R/"logs/gate_linux_console.txt")
(R/"reports/gate_input_identity.json").write_text(json.dumps(identity,indent=2),encoding="utf8")
print("PASS final four-state gate simulation; exact netlist, model, testbench and packet input hashes match.")
