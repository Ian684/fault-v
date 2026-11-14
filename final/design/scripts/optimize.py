from pathlib import Path
import re,json,shutil
R=Path(__file__).resolve().parent.parent
p=R/'rtl/fault_v_memory.sv';s=p.read_text(encoding='utf8')
if 'BANK_BITS' not in s:
 s=s.replace('localparam integer BANKS=WORDS/512;','localparam integer BANKS=WORDS/512;\n localparam integer BANK_BITS=$clog2(BANKS);')
 s=s.replace('logic [31:0] read_bank;','logic [BANK_BITS-1:0] read_bank;')
 s=s.replace('read_bank<=word_index>>9;','read_bank<=word_index[9+:BANK_BITS];')
p.write_text(s,encoding='utf8')
p=R/'rtl/fault_v_mem_arbiter.sv';s=p.read_text(encoding='utf8')
if 'end\n always_comb begin\n  m_req_ready' not in s:s=s.replace('  m_req_ready=0;',' end\n always_comb begin\n  m_req_ready=0;',1)
p.write_text(s,encoding='utf8')
p=R/'rtl/fault_v_asic_top.sv';p.write_text(p.read_text(encoding='utf8').replace("debug_status={16'b0","debug_status={19'b0"))
p=R/'rtl/fault_v_soc.sv';s=p.read_text(encoding='utf8').replace("(32'h20000300>>5)","27'h1000018").replace("(32'h20000400>>5)","27'h1000020");p.write_text(s,encoding='utf8')
p=R/'rtl/uart_tx.sv';p.write_text(p.read_text(encoding='utf8').replace('count==CLKS_PER_BIT-1',"count==CW'(CLKS_PER_BIT-1)"))
print('Narrowed SRAM selector; separated arbiter decode and explicit widths.')
