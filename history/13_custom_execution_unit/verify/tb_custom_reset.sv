`timescale 1ns/1ps
module tb_custom_reset;
    import fault_v_pkg::*;
    logic clk=0,rst=1;
    always #5 clk=~clk;
    wire halted,uart_tx,retire_valid;
    wire [3:0] gpio_out;
    wire [31:0] pc;
    halt_cause_t halt_cause;cpu_state_t state;
    fault_v_soc dut(.clk(clk),.rst(rst),.gpio_in(2'b0),.gpio_out(gpio_out),.uart_tx(uart_tx),
        .halted(halted),.halt_cause(halt_cause),.program_status(),.pc(pc),.state(state),
        .fault_pc(),.fault_addr(),.retire_valid(retire_valid),.retire_rd_we(),
        .retire_pc(),.retire_instruction(),.retire_rd_data(),.retire_rd_addr());
    integer commits=0,passed=0;
    always @(posedge clk)if(rst)commits=0;else if(retire_valid && dut.u_cpu.ir[6:0]==7'h0b)commits++;
    task automatic must(input logic ok,input string msg);
        if(ok!==1'b1)$fatal(1,"FAIL custom reset %s",msg);
    endtask
    task automatic prepare;
        @(negedge clk);rst=1;@(posedge clk);#1;
        dut.u_imem.mem[0]=32'h040300b7; // LUI x1,0x04030
        dut.u_imem.mem[1]=32'h20108093; // ADDI x1,x1,513 => 04030201
        dut.u_imem.mem[2]=32'h08070137;
        dut.u_imem.mem[3]=32'h60510113; // 08070605
        dut.u_imem.mem[4]=32'h0020828b; // DOT4 x5,x1,x2
        dut.u_imem.mem[5]=32'h00100073;
        @(negedge clk);rst=0;
    endtask
    initial begin
        for(integer mode=0;mode<7;mode++)begin
            prepare();
            if(mode==0)wait(state==ST_CUSTOM_START);
            else if(mode<=4)begin wait(state==ST_CUSTOM_WAIT);repeat(mode-1)@(posedge clk);end
            else if(mode==5)wait(dut.u_cpu.custom_rsp_valid);
            else wait(state==ST_CUSTOM_COMMIT);
            @(negedge clk);rst=1;#1;
            must(!retire_valid && !dut.u_cpu.custom_req_valid && !dut.u_cpu.custom_rsp_ready,"reset gates custom side effects");
            @(posedge clk);#1;must(pc==0 && dut.u_cpu.custom_result==0 && !dut.u_cpu.custom_rsp_valid,"clean reset state");
            prepare();wait(halted);#1;
            must(halt_cause==HALT_EBREAK && dut.u_cpu.u_regfile.regs[5]==70 && commits==1,"restart exact result and one commit");
            passed++;
        end
        $display("ALL %0d CUSTOM CPU RESET STAGES PASSED",passed);$finish;
    end
    initial begin #50000;$fatal(1,"Custom CPU reset timeout");end
endmodule
