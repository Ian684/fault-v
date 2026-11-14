`timescale 1ns/1ps
module tb_fpga_top;
    import fault_v_pkg::*;
    logic clk125=0,btn_reset=0;
    logic [1:0] sw=1;
    wire [3:0] led;
    wire uart_tx;
    integer received=0,runs=0;
    realtime last_edge=0;
    string expected="Fault-V OK";
    always #4 clk125=~clk125;
    fault_v_fpga_top #(.IMEM_FILE("../programs/peripheral_demo.mem"),.RESET_HOLD_BITS(4)) dut(.*);
    task automatic must(input logic good,input string description);
        if(good!==1'b1)$fatal(1,"FAIL FPGA peripherals: %s",description);
    endtask
    always @(posedge dut.clk) begin
        if(dut.locked && last_edge>0)must(($realtime-last_edge>39.99)&&($realtime-last_edge<40.01),"25MHz");
        last_edge=$realtime;
    end
    initial forever begin
        logic [7:0] value;
        @(negedge uart_tx);#4340;
        must(uart_tx==0,"UART start bit middle");
        #8680;
        for(integer b=0;b<8;b++)begin value[b]=uart_tx;#8680;end
        must(uart_tx==1,"UART stop bit middle");
        if(received%12<10)must(value==expected.getc(received%12),"UART message text byte");
        else if(received%12==10)must(value==8'h0d,"UART CR byte");
        else must(value==8'h0a,"UART LF byte");
        received++;$display("PASS UART byte %0d: %h",received,value);
    end
    task automatic run_program(input integer round_id,input logic[1:0] switches);
        wait(!dut.rst);wait(dut.u_soc.halted);#1;
        must(dut.u_soc.program_status==1 && dut.u_soc.halt_cause==HALT_EBREAK,"CPU success");
        must(led==5,"program controls LED 0x5");
        must(dut.u_soc.u_dmem.mem[0]==switches,"switch read saved to RAM");
        must(received==round_id*12,"exactly twelve serial bytes per run, drained before halt");
        repeat(20)@(posedge dut.clk);
        must(!dut.u_soc.dmem_req_valid && uart_tx==1,"halt and UART idle");
        runs++;$display("PASS FPGA PERIPHERAL run=%0d bytes=%0d gpio=%h input=%h status=1",runs,received,led,switches);
    endtask
    initial begin
        run_program(1,1);
        #7 btn_reset=1;repeat(5)@(posedge dut.clk);#1;must(led==0,"reset clears GPIO");
        sw=2;#7 btn_reset=0;
        run_program(2,2);
        $display("ALL 2 FPGA PERIPHERAL PROGRAM RUNS PASSED; 24 UART BYTES PASSED");$finish;
    end
    initial begin #4000000;$fatal(1,"FPGA peripheral timeout");end
endmodule
