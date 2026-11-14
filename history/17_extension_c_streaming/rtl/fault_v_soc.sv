`timescale 1ns/1ps
module fault_v_soc #(
    parameter string IMEM_FILE="",
    parameter integer IMEM_DELAY=1,
    parameter integer DMEM_DELAY=1,
    parameter integer UART_CLKS_PER_BIT=217
) (
    input logic clk,rst,
    input logic [1:0] gpio_in,
    output logic [3:0] gpio_out,
    output logic uart_tx,
    output logic [31:0] program_status,
    output logic halted,
    output fault_v_pkg::halt_cause_t halt_cause,
    output logic [31:0] fault_pc,fault_addr,pc,
    output fault_v_pkg::cpu_state_t state,
    output logic retire_valid,retire_rd_we,
    output logic [31:0] retire_pc,retire_instruction,retire_rd_data,
    output logic [4:0] retire_rd_addr
);
    import fault_v_stream_pkg::*;
    logic imem_req_valid,imem_req_ready,imem_rsp_valid,imem_rsp_err,imem_rsp_ready;
    logic [31:0] imem_req_addr,imem_rsp_data;
    logic dmem_req_valid,dmem_req_ready,dmem_req_write,dmem_rsp_valid,dmem_rsp_err,dmem_rsp_ready;
    logic [31:0] dmem_req_addr,dmem_req_wdata,dmem_rsp_data;
    logic [3:0] dmem_req_wstrb;
    logic [31:0] unused_status,scratch_unused_status;
    logic bus_pending,selected_scratch,lock_rsp_valid;
    logic [2:0] selected_target,request_target;
    wire selected_io=selected_target==1;
    logic ram_req_ready,ram_rsp_valid,ram_rsp_err,ram_rsp_ready;
    logic io_req_ready,io_rsp_valid,io_rsp_err,io_rsp_ready;
    logic [31:0] ram_rsp_data,io_rsp_data;
    logic sp_req_ready,sp_rsp_valid,sp_rsp_err,sp_rsp_ready;
    logic [31:0] sp_rsp_data;
    logic dma_cfg_ready,dma_cfg_valid,dma_cfg_err,dma_cfg_rsp_ready;
    logic acc_cfg_ready,acc_cfg_valid,acc_cfg_err,acc_cfg_rsp_ready;
    logic [31:0] dma_cfg_data,acc_cfg_data;
    logic dma_busy,acc_busy;
    logic [31:0] dma_a,dma_b,dma_dst,dma_count,acc_a,acc_b,acc_dst,acc_count;
    logic [2:0] m_req_valid,m_req_write,m_req_ready,m_rsp_valid,m_rsp_err,m_rsp_ready;
    logic [2:0][31:0] m_req_addr,m_req_wdata,m_rsp_data;
    logic [2:0][3:0] m_req_wstrb;
    logic b_req_valid,b_req_write,b_req_ready,b_rsp_valid,b_rsp_ready,b_rsp_err,arb_pending;
    logic [31:0] b_req_addr,b_req_wdata,b_rsp_data;
    logic [3:0] b_req_wstrb;
    logic [1:0] arb_owner;
    wire io_hit=(dmem_req_addr[31:4]==28'h2000010) || (dmem_req_addr[31:4]==28'h2000020);
    wire dma_hit=dmem_req_addr[31:5]==(32'h20000300>>5);
    wire acc_hit=dmem_req_addr[31:5]==(32'h20000400>>5);
    wire cpu_locked=(dma_busy && (in_region(dmem_req_addr,dma_a,dma_count<<2) || in_region(dmem_req_addr,dma_dst,dma_count<<2))) ||
                    (acc_busy && (in_region(dmem_req_addr,acc_a,acc_count<<2) || in_region(dmem_req_addr,acc_b,acc_count<<2) || in_region(dmem_req_addr,acc_dst,4)));
    wire scratch_hit=b_req_addr>=SCRATCH_BASE && b_req_addr<SCRATCH_END;
    wire ram_req_valid=b_req_valid && !scratch_hit;
    wire sp_req_valid=b_req_valid && scratch_hit;
    wire io_req_valid=dmem_req_valid && !bus_pending && request_target==1;
    wire dma_cfg_req_valid=dmem_req_valid && !bus_pending && request_target==2;
    wire acc_cfg_req_valid=dmem_req_valid && !bus_pending && request_target==3;
    always_comb begin
        request_target=0;
        if(io_hit)request_target=1;
        else if(dma_hit)request_target=2;
        else if(acc_hit)request_target=3;
        else if(cpu_locked)request_target=4;
        dmem_req_ready=0;dmem_rsp_valid=0;dmem_rsp_err=0;dmem_rsp_data=0;
        if(!rst && !bus_pending)case(request_target)
            0:dmem_req_ready=m_req_ready[0];
            1:dmem_req_ready=io_req_ready;
            2:dmem_req_ready=dma_cfg_ready;
            3:dmem_req_ready=acc_cfg_ready;
            4:dmem_req_ready=!lock_rsp_valid;
            default:begin end
        endcase
        if(!rst && bus_pending)case(selected_target)
            0:begin dmem_rsp_valid=m_rsp_valid[0];dmem_rsp_err=m_rsp_err[0];dmem_rsp_data=m_rsp_data[0];end
            1:begin dmem_rsp_valid=io_rsp_valid;dmem_rsp_err=io_rsp_err;dmem_rsp_data=io_rsp_data;end
            2:begin dmem_rsp_valid=dma_cfg_valid;dmem_rsp_err=dma_cfg_err;dmem_rsp_data=dma_cfg_data;end
            3:begin dmem_rsp_valid=acc_cfg_valid;dmem_rsp_err=acc_cfg_err;dmem_rsp_data=acc_cfg_data;end
            4:begin dmem_rsp_valid=lock_rsp_valid;dmem_rsp_err=1;end
            default:begin end
        endcase
    end
    assign m_req_valid[0]=!rst && dmem_req_valid && !bus_pending && request_target==0;
    assign m_req_write[0]=dmem_req_write;assign m_req_addr[0]=dmem_req_addr;
    assign m_req_wdata[0]=dmem_req_wdata;assign m_req_wstrb[0]=dmem_req_wstrb;
    assign m_rsp_ready[0]=!rst && bus_pending && selected_target==0 && dmem_rsp_ready;
    assign io_rsp_ready=!rst && bus_pending && selected_target==1 && dmem_rsp_ready;
    assign dma_cfg_rsp_ready=!rst && bus_pending && selected_target==2 && dmem_rsp_ready;
    assign acc_cfg_rsp_ready=!rst && bus_pending && selected_target==3 && dmem_rsp_ready;
    assign b_req_ready=scratch_hit?sp_req_ready:ram_req_ready;
    assign b_rsp_valid=selected_scratch?sp_rsp_valid:ram_rsp_valid;
    assign b_rsp_err=selected_scratch?sp_rsp_err:ram_rsp_err;
    assign b_rsp_data=selected_scratch?sp_rsp_data:ram_rsp_data;
    assign sp_rsp_ready=b_rsp_ready && selected_scratch;
    assign ram_rsp_ready=b_rsp_ready && !selected_scratch;
    always_ff @(posedge clk)begin
        if(rst)begin bus_pending<=0;selected_target<=0;selected_scratch<=0;lock_rsp_valid<=0;end
        else begin
            if(dmem_req_valid && dmem_req_ready)begin
                bus_pending<=1;selected_target<=request_target;
                if(request_target==4)lock_rsp_valid<=1;
            end
            if(dmem_rsp_valid && dmem_rsp_ready)begin bus_pending<=0;if(selected_target==4)lock_rsp_valid<=0;end
            if(b_req_valid && b_req_ready)selected_scratch<=scratch_hit;
        end
    end
    fault_v_mem_arbiter u_arb(.clk(clk),.rst(rst),.m_req_valid(m_req_valid),.m_req_write(m_req_write),.m_req_addr(m_req_addr),
        .m_req_wdata(m_req_wdata),.m_req_wstrb(m_req_wstrb),.m_req_ready(m_req_ready),.m_rsp_valid(m_rsp_valid),.m_rsp_err(m_rsp_err),
        .m_rsp_data(m_rsp_data),.m_rsp_ready(m_rsp_ready),.req_valid(b_req_valid),.req_write(b_req_write),.req_addr(b_req_addr),
        .req_wdata(b_req_wdata),.req_wstrb(b_req_wstrb),.req_ready(b_req_ready),.rsp_valid(b_rsp_valid),.rsp_err(b_rsp_err),
        .rsp_data(b_rsp_data),.rsp_ready(b_rsp_ready),.pending(arb_pending),.owner(arb_owner));
    fault_v_dma u_dma(.clk(clk),.rst(rst),.cfg_req_valid(dma_cfg_req_valid),.cfg_req_write(dmem_req_write),
        .cfg_req_addr(dmem_req_addr),.cfg_req_wdata(dmem_req_wdata),.cfg_req_wstrb(dmem_req_wstrb),
        .cfg_req_ready(dma_cfg_ready),.cfg_rsp_valid(dma_cfg_valid),.cfg_rsp_err(dma_cfg_err),.cfg_rsp_data(dma_cfg_data),.cfg_rsp_ready(dma_cfg_rsp_ready),
        .mem_req_valid(m_req_valid[1]),.mem_req_write(m_req_write[1]),.mem_req_addr(m_req_addr[1]),.mem_req_wdata(m_req_wdata[1]),.mem_req_wstrb(m_req_wstrb[1]),
        .mem_req_ready(m_req_ready[1]),.mem_rsp_valid(m_rsp_valid[1]),.mem_rsp_err(m_rsp_err[1]),.mem_rsp_data(m_rsp_data[1]),.mem_rsp_ready(m_rsp_ready[1]),
        .acc_busy(acc_busy),.acc_a(acc_a),.acc_b(acc_b),.acc_dst(acc_dst),.acc_count(acc_count),.busy(dma_busy),.src_a(dma_a),.src_b(dma_b),.dst(dma_dst),.count(dma_count));
    fault_v_accelerator u_acc(.clk(clk),.rst(rst),.cfg_req_valid(acc_cfg_req_valid),.cfg_req_write(dmem_req_write),
        .cfg_req_addr(dmem_req_addr),.cfg_req_wdata(dmem_req_wdata),.cfg_req_wstrb(dmem_req_wstrb),
        .cfg_req_ready(acc_cfg_ready),.cfg_rsp_valid(acc_cfg_valid),.cfg_rsp_err(acc_cfg_err),.cfg_rsp_data(acc_cfg_data),.cfg_rsp_ready(acc_cfg_rsp_ready),
        .mem_req_valid(m_req_valid[2]),.mem_req_write(m_req_write[2]),.mem_req_addr(m_req_addr[2]),.mem_req_wdata(m_req_wdata[2]),.mem_req_wstrb(m_req_wstrb[2]),
        .mem_req_ready(m_req_ready[2]),.mem_rsp_valid(m_rsp_valid[2]),.mem_rsp_err(m_rsp_err[2]),.mem_rsp_data(m_rsp_data[2]),.mem_rsp_ready(m_rsp_ready[2]),
        .dma_busy(dma_busy),.dma_a(dma_a),.dma_dst(dma_dst),.dma_count(dma_count),.busy(acc_busy),.src_a(acc_a),.src_b(acc_b),.dst(acc_dst),.count(acc_count));
    fault_v_cpu u_cpu(.*);
    fault_v_memory #(.BASE_ADDR(0),.READ_ONLY(1),.INIT_FILE(IMEM_FILE),.RESPONSE_DELAY(IMEM_DELAY)) u_imem(
        .clk(clk),.rst(rst),.req_valid(imem_req_valid),.req_ready(imem_req_ready),
        .req_write(1'b0),.req_addr(imem_req_addr),.req_wdata(32'b0),.req_wstrb(4'b0),
        .rsp_valid(imem_rsp_valid),.rsp_ready(imem_rsp_ready),.rsp_data(imem_rsp_data),
        .rsp_err(imem_rsp_err),.program_status(unused_status));
    fault_v_memory #(.BASE_ADDR(32'h10000000),.WITH_STATUS(1),.RESPONSE_DELAY(DMEM_DELAY)) u_dmem(
        .clk(clk),.rst(rst),.req_valid(ram_req_valid),.req_ready(ram_req_ready),
        .req_write(b_req_write),.req_addr(b_req_addr),.req_wdata(b_req_wdata),.req_wstrb(b_req_wstrb),
        .rsp_valid(ram_rsp_valid),.rsp_ready(ram_rsp_ready),.rsp_data(ram_rsp_data),
        .rsp_err(ram_rsp_err),.program_status(program_status));
    fault_v_memory #(.BASE_ADDR(32'h10010000),.WORDS(1024),.RESPONSE_DELAY(DMEM_DELAY)) u_scratch(
        .clk(clk),.rst(rst),.req_valid(sp_req_valid),.req_ready(sp_req_ready),.req_write(b_req_write),.req_addr(b_req_addr),
        .req_wdata(b_req_wdata),.req_wstrb(b_req_wstrb),.rsp_valid(sp_rsp_valid),.rsp_ready(sp_rsp_ready),
        .rsp_data(sp_rsp_data),.rsp_err(sp_rsp_err),.program_status(scratch_unused_status));
    fault_v_io #(.UART_CLKS_PER_BIT(UART_CLKS_PER_BIT)) u_io(
        .clk(clk),.rst(rst),.req_valid(io_req_valid),.req_ready(io_req_ready),
        .req_write(dmem_req_write),.req_addr(dmem_req_addr),.req_wdata(dmem_req_wdata),.req_wstrb(dmem_req_wstrb),
        .rsp_valid(io_rsp_valid),.rsp_ready(io_rsp_ready),.rsp_data(io_rsp_data),.rsp_err(io_rsp_err),
        .gpio_in(gpio_in),.gpio_out(gpio_out),.uart_tx(uart_tx));
endmodule
