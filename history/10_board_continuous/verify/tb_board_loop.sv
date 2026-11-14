`timescale 1ns/1ps
module tb_board_loop;
    import fault_v_pkg::*;
    logic clk=0;
    always #5 clk=~clk;
    logic rst=1;
    wire [3:0] gpio_out;
    wire halted,uart_tx;
    wire [31:0] program_status;
    halt_cause_t halt_cause;
    fault_v_soc #(.IMEM_FILE("../programs/board_loop.mem"),.DMEM_DELAY(3)) dut(
        .clk(clk),.rst(rst),.gpio_in(2'b0),.gpio_out(gpio_out),.uart_tx(uart_tx),
        .halted(halted),.halt_cause(halt_cause),.program_status(program_status),
        .fault_pc(),.fault_addr(),.pc(),.state(),.retire_valid(),.retire_rd_we(),
        .retire_pc(),.retire_instruction(),.retire_rd_data(),.retire_rd_addr());
    task automatic must(input logic ok,input string message);
        if(ok!==1'b1)$fatal(1,"FAIL board loop: %s",message);
    endtask
    task automatic reset_core;
        @(negedge clk);rst=1;repeat(5)@(posedge clk);#1;
        must(gpio_out==0 && !halted && program_status==0,"reset clears visible state");
        @(negedge clk);rst=0;
    endtask
    task automatic check_sweep(input integer round_id,input logic[3:0] expected);
        wait(gpio_out==expected);#1;
        must(!halted,"CPU still executing");
        for(integer i=0;i<4096;i++)
            must(dut.u_dmem.mem[i]==(round_id-1)*4096+i,"full RAM sweep contents");
        wait(program_status==1);#1;
        $display("PASS BOARD LOOP sweep=%0d LED=%h RAM_words=4096",round_id,gpio_out);
    endtask
    initial begin
        reset_core();check_sweep(1,5);check_sweep(2,10);
        reset_core();check_sweep(1,5);
        // A corrupted read must take the real software fail path.
        reset_core();
        wait(dut.dmem_rsp_valid && !dut.dmem_req_write && dut.dmem_req_addr==32'h10000000);
        @(negedge clk);force dut.dmem_rsp_data=32'hdeadbeef;
        @(posedge clk);#1;release dut.dmem_rsp_data;
        wait(halted);#1;
        must(gpio_out==15 && program_status==2 && halt_cause==HALT_EBREAK,"injected corruption visible failure");
        repeat(10)@(posedge clk);must(!dut.dmem_req_valid,"halt prevents further transactions");
        $display("PASS BOARD LOOP injected read corruption LED=f status=2");
        $display("ALL BOARD LOOP CHECKS PASSED; 3 FULL RAM SWEEPS; RESET RESTART; INJECTED FAILURE");
        $finish;
    end
    initial begin #300000000;$fatal(1,"Board loop timeout");end
endmodule
