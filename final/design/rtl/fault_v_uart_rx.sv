`timescale 1ns/1ps
module fault_v_uart_rx #(parameter integer CLKS_PER_BIT=217)(
 input logic clk,rst,rx,
 output logic valid,frame_error,
 output logic [7:0] data
);
 logic rx_meta,rx_sync;
 typedef enum logic [1:0] {IDLE,START,DATA,STOP} rx_state_t;
 rx_state_t state;
 integer timer;
 logic [2:0] bit_index;
 logic [7:0] shift_data;
 always_ff @(posedge clk)begin
  if(rst)begin
   rx_meta<=1;rx_sync<=1;state<=IDLE;timer<=0;bit_index<=0;shift_data<=0;
   valid<=0;frame_error<=0;data<=0;
  end else begin
   rx_meta<=rx;rx_sync<=rx_meta;valid<=0;frame_error<=0;
   case(state)
    IDLE:if(!rx_sync)begin timer<=CLKS_PER_BIT/2-1;state<=START;end
    START:if(timer!=0)timer<=timer-1;
     else if(rx_sync)state<=IDLE;
     else begin timer<=CLKS_PER_BIT-1;bit_index<=0;state<=DATA;end
    DATA:if(timer!=0)timer<=timer-1;
     else begin
      shift_data[bit_index]<=rx_sync;timer<=CLKS_PER_BIT-1;
      if(bit_index==7)state<=STOP;else bit_index<=bit_index+1'b1;
     end
    STOP:if(timer!=0)timer<=timer-1;
     else begin
      state<=IDLE;if(rx_sync)begin data<=shift_data;valid<=1;end else frame_error<=1;
     end
    default:state<=IDLE;
   endcase
  end
 end
endmodule
