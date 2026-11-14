`timescale 1ns/1ps
module fault_v_io #(parameter integer UART_CLKS_PER_BIT=217)(
    input logic clk,rst,req_valid,req_write,
    input logic [31:0] req_addr,req_wdata,
    input logic [3:0] req_wstrb,
    output logic req_ready,rsp_valid,rsp_err,
    output logic [31:0] rsp_data,
    input logic rsp_ready,
    input logic [1:0] gpio_in,
    output logic [3:0] gpio_out,
    output logic uart_tx
);
    localparam logic [31:0] UART_DATA=32'h20000100,UART_STATUS=32'h20000104;
    localparam logic [31:0] GPIO_OUT=32'h20000200,GPIO_IN=32'h20000204;
    logic tx_busy;
    wire legal_tx_write=(req_addr==UART_DATA)&&req_write&&(req_wstrb==4'hf);
    wire fire=req_valid && req_ready;
    assign req_ready=!rst && !rsp_valid && !(legal_tx_write && tx_busy);
    uart_tx #(.CLKS_PER_BIT(UART_CLKS_PER_BIT)) u_tx(
        .clk(clk),.rst(rst),.start(fire && legal_tx_write),.data(req_wdata[7:0]),
        .tx(uart_tx),.busy(tx_busy));
    always_ff @(posedge clk) begin
        if (rst) begin gpio_out<=0;rsp_valid<=0;rsp_err<=0;rsp_data<=0;end
        else begin
            if (rsp_valid && rsp_ready) rsp_valid<=0;
            if (fire) begin
                rsp_valid<=1;rsp_err<=0;rsp_data<=0;
                if (req_write && req_wstrb!=4'hf) rsp_err<=1;
                else case(req_addr)
                    UART_DATA: if (!req_write) rsp_err<=1;
                    UART_STATUS: if (req_write) rsp_err<=1;
                                 else rsp_data<={30'b0,tx_busy,!tx_busy};
                    GPIO_OUT: begin
                        rsp_data<={28'b0,gpio_out};
                        if(req_write) gpio_out<=req_wdata[3:0];
                    end
                    GPIO_IN: if(req_write) rsp_err<=1;
                             else rsp_data<={30'b0,gpio_in};
                    default:rsp_err<=1;
                endcase
            end
        end
    end
endmodule
