from pathlib import Path
import re,json,hashlib
R=Path(__file__).resolve().parent.parent
baseline=R/'reference'/'extension_c_rtl'
before={}
for p in baseline.glob('*.sv'):
 if p.name=='fault_v_memory.sv':continue
 text=p.read_text(encoding='utf-8-sig')
 before[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 # FPGA implementation hints do not constrain standard-cell mapping.
 text=re.sub(r'\(\*[^\n]*?(?:keep_hierarchy|use_dsp)[^\n]*?\*\)\s*','',text)
 if p.name=='fault_v_soc.sv':
  text=text.replace('input logic clk,rst,','input logic clk,rst,\n    input logic boot_valid,\n    input logic [31:0] boot_addr,boot_wdata,\n    input logic [3:0] boot_wstrb,\n    output logic boot_ready,')
  text=text.replace('    import fault_v_stream_pkg::*;','''    import fault_v_stream_pkg::*;
    wire [1:0] boot_select=boot_addr<32'h00004000 ? 0:
      (boot_addr>=32'h10000000 && boot_addr<32'h10004000)?1:
      (boot_addr>=32'h10010000 && boot_addr<32'h10011000)?2:3;
    wire [2:0] memory_boot_ready;
    assign boot_ready=boot_select==3?1'b0:memory_boot_ready[boot_select];
''')
  for target,i in [('unused_status',0),('program_status',1),('scratch_unused_status',2)]:
   old='.program_status('+target+'));'
   new='.program_status('+target+'),.boot_valid(boot_valid && boot_select=='+str(i)+'),.boot_addr(boot_addr),.boot_wdata(boot_wdata),.boot_wstrb(boot_wstrb),.boot_ready(memory_boot_ready['+str(i)+']));'
   assert text.count(old)==1,(p.name,target);text=text.replace(old,new)
 (R/'rtl'/p.name).write_text(text,encoding='utf8')
(R/'baseline_identity.json').write_text(json.dumps(before,indent=2))
print('Prepared portable RTL copies; replaced the FPGA memory and added boot write routing.')
