from pathlib import Path
import shutil
R=Path(__file__).resolve().parent.parent
s=(R/'reference/tb_streams.sv').read_text(encoding='utf8')
s=s.replace('module tb_streams;','module tb_asic_streams;')
s=s.replace('  logic rst=1;','''  logic boot_valid=0;logic [31:0] boot_addr=0,boot_wdata=0;
  logic [3:0] boot_wstrb=15;wire boot_ready;
  logic [31:0] imem_image[0:4095],ram_image[0:4095],scratch_image[0:1023];
  integer image_fd,image_words,image_scan;
  logic rst=1;''')
s=s.replace('.clk(clk),.rst(rst),.gpio_in', '.clk(clk),.rst(rst),.boot_valid(boot_valid),.boot_addr(boot_addr),.boot_wdata(boot_wdata),.boot_wstrb(boot_wstrb),.boot_ready(boot_ready),.gpio_in')
start=s.index('     for(integer k=0;k<4096;k++)dut.u_imem.mem[k]=0;')
end=s.index('     repeat(3)@(posedge clk);',start)
s=s[:start]+'''     image_fd=$fopen($sformatf("%s.imem",stem),"r");must(image_fd!=0,"instruction file");
     image_words=0;
     while(!$feof(image_fd))begin
      image_scan=$fscanf(image_fd,"%h",imem_image[image_words]);if(image_scan==1)image_words++;
     end
     $fclose(image_fd);
     $readmemh($sformatf("%s.ram",stem),ram_image);
     $readmemh($sformatf("%s.sp",stem),scratch_image);
     @(negedge clk);boot_valid=1;
     for(integer k=0;k<image_words+4096+1024;k++)begin
      if(k<image_words)begin boot_addr=k*4;boot_wdata=imem_image[k];end
      else if(k<image_words+4096)begin boot_addr=32'h10000000+(k-image_words)*4;boot_wdata=ram_image[k-image_words];end
      else begin boot_addr=32'h10010000+(k-image_words-4096)*4;boot_wdata=scratch_image[k-image_words-4096];end
      @(posedge clk);must(boot_ready,"fixture write uses real SRAM boot port");@(negedge clk);
     end
     boot_valid=0;
'''+s[end:]
s=s.replace('dut.u_dmem.mem[index]', 'peek(0,index)').replace('dut.u_scratch.mem[index]', 'peek(1,index)')
case0='\n'.join(f'     {i}:return dut.u_dmem.banks[{i}].u_sram.mem[index%512];' for i in range(8))
case1='\n'.join(f'     {i}:return dut.u_scratch.banks[{i}].u_sram.mem[index%512];' for i in range(2))
fn='''  function automatic logic [31:0] peek(input integer region,index);
   if(region==0)case(index/512)
'''+case0+'''
     default:return 32'bx;
    endcase
   else case(index/512)
'''+case1+'''
     default:return 32'bx;
    endcase
  endfunction
'''
s=s.replace('  integer id,inject,',fn+'  integer id,inject,')
(R/'verify/tb_asic_streams.sv').write_text(s)
print('Prepared 744 ASIC SRAM-backed SoC runs using the real boot write interface.')
