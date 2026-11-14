module tb_fault_v_soc;
    timeunit 1ns; timeprecision 1ps;
    import fault_v_pkg::*;
    logic clk=0;
    always #5 clk=~clk;
    // Batch script runs from sim/. For the Vivado GUI, set this to the absolute programs directory.
    localparam string IMAGE_DIR="../programs/";
    logic [8:0] done=0;
    for (genvar g=0;g<9;g=g+1) begin: cases
        localparam integer ID=(g<3)?0:g-2;
        localparam string FILE_NAME=(g<3)?"integration.mem":(g==3)?"illegal.mem":
            (g==4)?"misaligned.mem":(g==5)?"unmapped_store.mem":(g==6)?"fetch_error.mem":
            (g==7)?"unmapped_mmio.mem":"software_fail.mem";
        logic rst=1,halted,retire_valid,retire_rd_we;
        logic [31:0] program_status,fault_pc,fault_addr,pc,retire_pc,retire_instruction,retire_rd_data;
        logic [4:0] retire_rd_addr;
        halt_cause_t halt_cause,expected_cause;
        cpu_state_t state;
        logic [31:0] gold_pc[0:511],gold_inst[0:511],gold_data[0:511],gold_next[0:511];
        logic [4:0] gold_rd[0:511];
        logic [31:0] gold_regs[0:31],gold_ram[0:4095];
        logic [31:0] expected_fault_pc,expected_fault_addr,expected_status,previous_pc,previous_next;
        logic previous_commit;
        integer expected_count,expected_data_count,retired,fetches,data_requests,data_responses,cycles;
        logic [31:0] saved_tail;
        fault_v_soc #(.IMEM_FILE({IMAGE_DIR,FILE_NAME}),.IMEM_DELAY(g+1),.DMEM_DELAY(g*2+1)) dut(.*);
        task automatic must(input logic condition,input string label_text);
            if (condition!==1'b1) $fatal(1,"FAIL soc=%0d %s pc=%h retired=%0d",g,label_text,pc,retired);
        endtask
        task automatic load_expected(input integer id);
            for (integer k=0;k<4096;k=k+1) gold_ram[k]=0;
            `include "program_expectations.svh"
        endtask
        always @(posedge clk) begin
            if (rst) begin
                retired=0; fetches=0; data_requests=0; data_responses=0;
                previous_pc=0; previous_commit=0;
            end else begin
                if (previous_commit) must(pc===previous_next,"next PC");
                else must(pc===previous_pc,"PC held until commit");
                if (dut.imem_req_valid && dut.imem_req_ready) fetches=fetches+1;
                if (dut.dmem_req_valid && dut.dmem_req_ready) data_requests=data_requests+1;
                if (dut.dmem_rsp_valid && dut.dmem_rsp_ready) data_responses=data_responses+1;
                must(!((dut.u_imem.busy || dut.imem_rsp_valid) && (dut.u_dmem.busy || dut.dmem_rsp_valid)),"single outstanding system transaction");
                if (retire_valid) begin
                    must(retired<expected_count,"no extra commits");
                    must(retire_pc===gold_pc[retired] && retire_instruction===gold_inst[retired],"instruction trace");
                    must(retire_rd_we== (gold_rd[retired]!=0),"write enable");
                    must(retire_rd_addr===gold_rd[retired] && retire_rd_data===gold_data[retired],"writeback trace");
                    previous_next=gold_next[retired]; retired=retired+1;
                end
                previous_pc=pc; previous_commit=retire_valid;
            end
        end
        initial begin
            load_expected(ID);
            for (integer run_id=0;run_id<((g<3)?2:1);run_id=run_id+1) begin
                @(negedge clk); rst=1;
                repeat(3) begin @(posedge clk); #1; end
                must(pc==0 && program_status==0 && !halted,"reset PC status and halt");
                if (run_id>0) must(dut.u_dmem.mem[4095]===saved_tail,"RAM retained across reset");
                @(negedge clk); rst=0; cycles=0;
                while (!halted) begin
                    @(posedge clk); #1; cycles=cycles+1;
                    if (cycles>20000) $fatal(1,"TIMEOUT soc=%0d",g);
                end
                must(retired==expected_count && fetches==expected_count+1,"commit and fetch count");
                must(data_requests==expected_data_count && data_responses==expected_data_count,"request response counts");
                must(program_status===expected_status,"software completion status");
                must(halt_cause==expected_cause && fault_pc===expected_fault_pc && fault_addr===expected_fault_addr,"fault context");
                must(pc===expected_fault_pc,"stopped PC");
                for (integer r=0;r<32;r=r+1) must(dut.u_cpu.u_regfile.regs[r]===gold_regs[r],"all architecture registers");
                for (integer m=0;m<4096;m=m+1) must(dut.u_dmem.mem[m]===gold_ram[m],"all 16 KiB data RAM");
                saved_tail=dut.u_dmem.mem[4095];
                repeat(4) begin @(posedge clk); #1; end
                must(!retire_valid && !dut.imem_req_valid && !dut.dmem_req_valid,"halt remains inactive");
                $display("PASS soc=%0d run=%0d id=%0d commits=%0d data=%0d status=%h cause=%0d pc=%h",g,run_id,ID,retired,data_requests,program_status,halt_cause,pc);
            end
            done[g]=1;
        end
    end
    initial begin
        wait (&done); #1;
        $display("ALL 12 SOC PROGRAM RUNS PASSED"); $finish;
    end
    initial begin #2000000; $fatal(1,"GLOBAL TIMEOUT SOC"); end
endmodule
