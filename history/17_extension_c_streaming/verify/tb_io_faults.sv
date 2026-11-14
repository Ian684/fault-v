`timescale 1ns/1ps
module tb_io_faults;
    import fault_v_pkg::*;
    logic clk=0;
    always #5 clk=~clk;
    logic [7:0] done=0;
    for(genvar g=0;g<8;g++)begin: cases
        localparam integer OFFSET=(g==0||g==4)?'h100:(g==1)?'h104:(g==2||g==6)?'h204:
            (g==3)?'h108:(g==5)?'h101:'h205;
        localparam integer CAUSE=(g==0||g==3||g==6)?6:(g==1||g==2||g==4)?7:(g==5)?4:5;
        localparam integer REQUESTS=(g<4)?1:0;
        localparam string IMAGE=(g==0)?"../programs/io_fault_0.mem":(g==1)?"../programs/io_fault_1.mem":
            (g==2)?"../programs/io_fault_2.mem":(g==3)?"../programs/io_fault_3.mem":
            (g==4)?"../programs/io_fault_4.mem":(g==5)?"../programs/io_fault_5.mem":
            (g==6)?"../programs/io_fault_6.mem":"../programs/io_fault_7.mem";
        logic rst=1;
        wire halted,uart_tx;
        wire [3:0] gpio_out;
        wire [31:0] fault_pc,fault_addr,program_status;
        halt_cause_t halt_cause;
        integer requests=0;
        fault_v_soc #(.IMEM_FILE(IMAGE),.UART_CLKS_PER_BIT(4)) dut(
            .clk(clk),.rst(rst),.gpio_in(2'b0),.gpio_out(gpio_out),.uart_tx(uart_tx),
            .halted(halted),.halt_cause(halt_cause),.fault_pc(fault_pc),.fault_addr(fault_addr),
            .program_status(program_status),.pc(),.state(),.retire_valid(),.retire_rd_we(),
            .retire_pc(),.retire_instruction(),.retire_rd_data(),.retire_rd_addr());
        always @(posedge clk)if(!rst && dut.dmem_req_valid && dut.dmem_req_ready)requests++;
        initial begin
            repeat(3)@(posedge clk);@(negedge clk);rst=0;
            wait(halted);#1;
            if(halt_cause!=CAUSE || fault_pc!=8 || fault_addr!=32'h20000000+OFFSET || requests!=REQUESTS)
                $fatal(1,"FAIL IO fault %0d cause=%0d pc=%h addr=%h requests=%0d",g,halt_cause,fault_pc,fault_addr,requests);
            if(gpio_out!=0 || uart_tx!=1 || program_status!=0)$fatal(1,"Fault caused side effect");
            repeat(5)@(posedge clk);
            if(dut.dmem_req_valid)$fatal(1,"Request after halt");
            $display("PASS CPU IO fault %0d cause=%0d addr=%h requests=%0d",g,halt_cause,fault_addr,requests);
            done[g]=1;
        end
    end
    initial begin wait(&done);$display("ALL 8 CPU IO FAULT CASES PASSED");$finish;end
    initial begin #20000;$fatal(1,"CPU IO fault timeout");end
endmodule
