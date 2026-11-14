`timescale 1ns/1ps
module tb_reset;
    logic clk=0,locked=0,btn_reset=0;
    wire rst;
    always #20 clk=~clk;
    fault_v_reset #(.HOLD_BITS(4)) dut(.*);
    integer checks=0;
    task automatic check(input logic expected,input string description);
        if (rst!==expected) $fatal(1,"FAIL %s rst=%b",description,rst);
        checks++;
        $display("PASS reset %0d: %s",checks,description);
    endtask
    task automatic release_check;
        for(integer i=0;i<17;i++) begin @(posedge clk); #1;check(1,"release held");end
        repeat(2) @(posedge clk); #1;check(0,"release after 3 sync + 15 count + 1 output edges");
    endtask
    initial begin
        #1 check(1,"initial reset");
        #2 locked=1;
        release_check();
        #7 btn_reset=1;@(posedge clk);#1 check(1,"button synchronous core reset");
        @(negedge clk);btn_reset=0;
        repeat(6) @(posedge clk);
        #1 check(1,"delay during release");
        #2 btn_reset=1;@(posedge clk);#1 check(1,"bounce assertion");
        @(negedge clk);btn_reset=0;
        release_check();
        #7 locked=0;@(posedge clk);#1 check(1,"lock loss resets at next available edge");
        repeat(4) @(posedge clk);
        #1 check(1,"lock absent holds reset");
        @(negedge clk);locked=1;
        release_check();
        $display("ALL 60 RESET CHECKS PASSED");
        if(checks!=60) $fatal(1,"Unexpected check count %0d",checks);
        $finish;
    end
    initial begin #20000;$fatal(1,"reset timeout");end
endmodule
