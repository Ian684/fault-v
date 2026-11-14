`timescale 1ns/1ps
module tb_fpga_top;
    import fault_v_pkg::*;
    logic clk125=0,btn_reset=0;
    wire [3:0] led;
    always #4 clk125=~clk125;
    // Shortened release delay only; actual MMCM/BUFG models remain in the test.
    fault_v_fpga_top #(.IMEM_FILE("../programs/integration.mem"),.RESET_HOLD_BITS(4)) dut(.*);
    integer commits=0,transactions=0,runs=0;
    realtime last_edge=0;
    task automatic must(input logic good,input string description);
        if (good!==1'b1) $fatal(1,"FAIL %s",description);
    endtask
    always @(posedge dut.clk) begin
        if (dut.locked && last_edge>0) must(($realtime-last_edge>39.99)&&($realtime-last_edge<40.01),"25 MHz period");
        last_edge=$realtime;
        if (dut.rst) begin commits=0;transactions=0;end
        else begin
            if (dut.u_soc.retire_valid) commits=commits+1;
            if (dut.u_soc.dmem_req_valid && dut.u_soc.dmem_req_ready) transactions=transactions+1;
        end
    end
    task automatic execute_program;
        wait(!dut.rst);
        wait(dut.halted);
        #1;
        must(dut.program_status==1,"status success");
        must(dut.halt_cause==HALT_EBREAK,"expected EBREAK");
        must(dut.fault_pc==32'hcc,"stop address");
        must(commits==175,"175 retired instructions");
        must(transactions==33,"33 data transactions");
        must(led[3:1]==3'b011,"halt and success LEDs");
        must(dut.u_soc.u_dmem.mem[9]==34,"Fibonacci result");
        must(dut.u_soc.u_dmem.mem[12]==32'h123400ef,"byte/halfword writes");
        must(dut.u_soc.u_dmem.mem[16]==176,"function result");
        must(dut.u_soc.u_dmem.mem[4095]==32'h40,"last RAM word and stack");
        repeat(8) @(posedge dut.clk);
        must(commits==175 && transactions==33,"halt holds transactions and commits");
        runs=runs+1;
        $display("PASS FPGA run=%0d commits=%0d data=%0d status=%h halt=%0d pc=%h led=%b",runs,commits,transactions,dut.program_status,dut.halt_cause,dut.fault_pc,led);
    endtask
    initial begin
        execute_program();
        #7 btn_reset=1;
        @(posedge dut.clk);#1 must(dut.rst,"registered core reset assertion");
        repeat(5) @(posedge dut.clk);
        #1 must(dut.program_status==0 && !dut.halted && dut.pc==0,"core synchronous reset");
        #3 btn_reset=0;
        repeat(5) @(posedge dut.clk);
        #1 must(dut.rst,"release delay remains active");
        #2 btn_reset=1; #6 btn_reset=0;
        repeat(5) @(posedge dut.clk);
        #1 must(dut.rst,"button bounce restarts delay");
        execute_program();
        $display("ALL 2 FPGA TOP PROGRAM RUNS PASSED");
        $finish;
    end
    initial begin #200000; $fatal(1,"FPGA test timeout");end
endmodule
