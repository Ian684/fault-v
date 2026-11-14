"""Recreate XSim-compatible simulation copies; never edits Liberty, LEF or GDS."""
from pathlib import Path
R=Path(__file__).resolve().parent.parent
name="sky130_sram_2kbyte_1rw1r_32x512_8"
src=(R/"macros/vendor"/(name+".v")).read_text(encoding="utf8")
decl="reg [DATA_WIDTH-1:0]    mem [0:RAM_DEPTH-1];"
assert src.count(decl)==1 and src.count("parameter VERBOSE = 1")==1
s=src.replace("parameter VERBOSE = 1","parameter VERBOSE = 0").replace(decl,"")
s=s.replace("  // All inputs are registers","reg [DATA_WIDTH-1:0] mem [0:RAM_DEPTH-1];\n  // All inputs are registers",1)
(R/"macros/model.v").write_text("\x60timescale 1ns/1ps\n"+s,encoding="utf8",newline="\n")
for file in ["primitives","sky130_fd_sc_hd"]:
 s=(R/"macros"/(file+".v")).read_text(encoding="utf8")
 s=s.replace("\x60default_nettype none","\x60default_nettype wire")
 if file=="sky130_fd_sc_hd":
  s="\x60ifndef UNIT_DELAY\n\x60define UNIT_DELAY #0\n\x60endif\n"+s
 (R/"macros"/(file+"_xsim.v")).write_text(s,encoding="utf8",newline="\n")
print("Simulation-only models prepared; cell truth tables and SRAM read/write behavior unchanged.")
