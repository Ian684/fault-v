`timescale 1ns/1ps
module fault_v_fpga_top #(
    parameter string IMEM_FILE="integration.mem",
    parameter integer RESET_HOLD_BITS=18
)(input wire clk125, input wire btn_reset, output wire [3:0] led);
    import fault_v_pkg::*;
    wire clk,locked,rst;
    logic [23:0] heartbeat=0;
    wire [31:0] program_status,fault_pc,fault_addr,pc;
    wire halted;
    halt_cause_t halt_cause;
    cpu_state_t state;
    fault_v_clock u_clock(.clk125(clk125),.clk(clk),.locked(locked));
    fault_v_reset #(.HOLD_BITS(RESET_HOLD_BITS)) u_reset(.*);
    fault_v_soc #(.IMEM_FILE(IMEM_FILE)) u_soc(
        .clk(clk),.rst(rst),.program_status(program_status),.halted(halted),
        .halt_cause(halt_cause),.fault_pc(fault_pc),.fault_addr(fault_addr),
        .pc(pc),.state(state),.retire_valid(),.retire_rd_we(),.retire_pc(),
        .retire_instruction(),.retire_rd_data(),.retire_rd_addr()
    );
    always_ff @(posedge clk)
        if (rst) heartbeat<=0;
        else heartbeat<=heartbeat+1'b1;
    wire success=halted && (halt_cause==HALT_EBREAK) && (program_status==32'd1);
    assign led[0]=!rst && heartbeat[23];
    assign led[1]=!rst && halted;
    assign led[2]=!rst && success;
    assign led[3]=!rst && ((halted && !success) ||
                          ((program_status!=0) && (program_status!=1)));
endmodule
