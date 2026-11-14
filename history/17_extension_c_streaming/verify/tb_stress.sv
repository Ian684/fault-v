`timescale 1ns/1ps
module tb_stress;
    import fault_v_pkg::*;
    logic clk=0;
    always #5 clk=~clk;
    logic [1:0] done=0;
    for(genvar g=0;g<2;g++)begin: cases
        logic rst=1;
        wire halted,uart_tx;
        wire [3:0] gpio_out;
        wire [31:0] program_status;
        halt_cause_t halt_cause;
        integer received=0,epoch=0,tx_writes=0,gpio_writes=0,ram_writes=0;
        integer stalls=0,retired=0,outstanding=0,requests=0,responses=0;
        logic held=0;
        logic [68:0] held_request;
        wire [68:0] request={dut.dmem_req_addr,dut.dmem_req_wdata,
                            dut.dmem_req_wstrb,dut.dmem_req_write};
        fault_v_soc #(.IMEM_FILE("../programs/stress.mem"),
            .IMEM_DELAY(g==0?1:7),.DMEM_DELAY(g==0?1:11),
            .UART_CLKS_PER_BIT(64)) dut(
            .clk(clk),.rst(rst),.gpio_in(2'b11),.gpio_out(gpio_out),.uart_tx(uart_tx),
            .halted(halted),.halt_cause(halt_cause),.program_status(program_status),
            .fault_pc(),.fault_addr(),.pc(),.state(),.retire_valid(),.retire_rd_we(),
            .retire_pc(),.retire_instruction(),.retire_rd_data(),.retire_rd_addr());
        task automatic must(input logic ok,input string message);
            if(ok!==1'b1)$fatal(1,"FAIL stress mode=%0d: %s",g,message);
        endtask
        always @(posedge rst)epoch++;
        always @(posedge clk)begin
            if(rst)begin
                received=0;tx_writes=0;gpio_writes=0;ram_writes=0;stalls=0;
                retired=0;outstanding=0;held=0;requests=0;responses=0;
            end else begin
                if(held)must(dut.dmem_req_valid && request===held_request,"request changed while waiting");
                held=dut.dmem_req_valid && !dut.dmem_req_ready;
                if(held)begin held_request=request;stalls++;end
                if(dut.dmem_rsp_valid && dut.dmem_rsp_ready)begin
                    must(outstanding==1,"response without request");outstanding--;responses++;
                end
                if(dut.dmem_req_valid && dut.dmem_req_ready)begin
                    must(outstanding==0,"multiple outstanding data requests");outstanding++;requests++;
                    if(dut.dmem_req_write)begin
                        case(dut.dmem_req_addr)
                            32'h20000100: begin
                                must(dut.dmem_req_wdata[7:0]==(tx_writes%256),"accepted UART sequence");tx_writes++;
                            end
                            32'h20000200:begin
                                must(dut.dmem_req_wdata==gpio_writes,"GPIO write sequence");gpio_writes++;
                            end
                            32'h10000000,32'h10000004:ram_writes++;
                        endcase
                    end
                end
                if(dut.retire_valid)retired++;
            end
        end
        initial forever begin
            wait(!rst);
            @(negedge uart_tx);
            begin: frame
                logic [7:0] value;
                integer token;
                token=epoch;
                #320;
                if(rst || token!=epoch)disable frame;
                must(uart_tx==0,"serial start bit");
                #640;
                for(integer bit_id=0;bit_id<8;bit_id++)begin
                    if(rst || token!=epoch)disable frame;
                    value[bit_id]=uart_tx;#640;
                end
                if(rst || token!=epoch)disable frame;
                must(uart_tx==1,"serial stop bit");
                must(value==(received%256),"decoded UART byte sequence");
                received++;
            end
        end
        task automatic reset_core;
            @(negedge clk);rst=1;
            repeat(100)@(posedge clk);
            #1;must(gpio_out==0 && uart_tx==1 && program_status==0 && !halted,"reset clears peripherals and halt");
            @(negedge clk);rst=0;
        endtask
        task automatic finish_run(input integer round_id);
            wait(halted);#1;
            must(program_status==1 && halt_cause==HALT_EBREAK,"successful program termination");
            must(received==1024 && tx_writes==1024,"exactly 1024 accepted and decoded serial bytes");
            must(gpio_writes==1024 && ram_writes==3072,"exact GPIO and RAM write counts");
            must(dut.u_dmem.mem[0]==1023 && dut.u_dmem.mem[1]==32'h03ff00ff,"final word and byte lanes");
            must(gpio_out==15 && !dut.u_io.tx_busy,"final GPIO and UART drained");
            must(outstanding==0 && requests==responses && stalls>0,"completed transactions and backpressure exercised");
            must(retired>=20480,"all loop iterations executed");
            repeat(20)@(posedge clk);
            must(!dut.dmem_req_valid && !dut.imem_req_valid,"no new requests after halt");
            $display("PASS STRESS mode=%0d run=%0d iterations=1024 bytes=%0d RAM_writes=%0d GPIO_writes=%0d stalls=%0d retired=%0d",g,round_id,received,ram_writes,gpio_writes,stalls,retired);
        endtask
        initial begin
            reset_core();
            wait(dut.u_dmem.busy);
            reset_core();
            $display("PASS STRESS mode=%0d reset during pending RAM response",g);
            wait(dut.u_io.tx_busy);repeat(10)@(posedge clk);
            reset_core();
            $display("PASS STRESS mode=%0d reset during UART frame",g);
            finish_run(1);
            reset_core();finish_run(2);
            done[g]=1;
        end
    end
    initial begin
        wait(&done);
        $display("ALL 4 STRESS PROGRAM RUNS PASSED; 4096 UART BYTES PASSED; 4 MID-EXECUTION RESETS PASSED");
        $finish;
    end
    initial begin #30000000;$fatal(1,"Stress timeout");end
endmodule
