`timescale 1ns/1ps
module fault_v_loader #(parameter integer CLKS_PER_BIT=217, TIMEOUT_CLKS=25000000)(
 input logic clk,rst,rx,
 output logic running,boot_error,boot_valid,
 output logic [31:0] boot_addr,boot_wdata,
 output logic [3:0] boot_wstrb,
 input logic boot_ready
);
 wire byte_valid,frame_error;
 wire [7:0] byte_data;
 fault_v_uart_rx #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_rx(
  .clk(clk),.rst(rst),.rx(rx),.valid(byte_valid),.frame_error(frame_error),.data(byte_data));
 typedef enum logic [3:0] {SYNC0,SYNC1,SYNC2,SYNC3,LENGTH0,LENGTH1,PAYLOAD,CRC,FILL,EXECUTE} loader_state_t;
 loader_state_t state;
 logic [15:0] word_count,word_index;
 logic [1:0] byte_index;
 logic [31:0] word_buffer,crc_value,crc_received;
 integer timeout_count;
 function automatic logic [31:0] crc_byte(input logic [31:0] crc,input logic [7:0] value);
  logic [31:0] c;
  c=crc^{24'b0,value};
  for(integer i=0;i<8;i++)c=c[0]?(c>>1)^32'hedb88320:c>>1;
  return c;
 endfunction
 assign boot_valid=!rst && (state==FILL || (state==PAYLOAD && byte_valid && byte_index==3 && !frame_error));
 assign boot_addr={14'b0,word_index,2'b0};
 assign boot_wdata=state==FILL?32'b0:{byte_data,word_buffer[23:0]};
 assign boot_wstrb=4'hf;
 always_ff @(posedge clk)begin
  if(rst)begin
   running<=0;boot_error<=0;state<=SYNC0;word_count<=0;word_index<=0;byte_index<=0;
   word_buffer<=0;crc_value<=32'hffffffff;crc_received<=0;timeout_count<=0;
  end else if(!running)begin
   if(byte_valid)timeout_count<=0;
   else if(state!=SYNC0 && state!=FILL)timeout_count<=timeout_count+1;
   if(state==FILL && boot_ready)begin
    if(word_index==4095)begin state<=EXECUTE;running<=1;end
    else word_index<=word_index+1'b1;
   end
   if(byte_valid)case(state)
    SYNC0:if(byte_data==8'h46)begin state<=SYNC1;boot_error<=0;end
    SYNC1:state<=byte_data==8'h56 ? SYNC2:SYNC0;
    SYNC2:state<=byte_data==8'h01 ? SYNC3:SYNC0;
    SYNC3:state<=byte_data==0?LENGTH0:SYNC0;
    LENGTH0:begin word_count[7:0]<=byte_data;state<=LENGTH1;end
    LENGTH1:begin
     word_count[15:8]<=byte_data;word_index<=0;byte_index<=0;crc_value<=32'hffffffff;crc_received<=0;
     if({byte_data,word_count[7:0]}==0 || {byte_data,word_count[7:0]}>4096)begin state<=SYNC0;boot_error<=1;end
     else state<=PAYLOAD;
    end
    PAYLOAD:begin
     crc_value<=crc_byte(crc_value,byte_data);
     word_buffer[byte_index*8+:8]<=byte_data;
     if(byte_index==3)begin
      if(!boot_ready)begin state<=SYNC0;boot_error<=1;end
      else if(word_index+1==word_count)begin byte_index<=0;state<=CRC;end
      else begin word_index<=word_index+1'b1;byte_index<=0;end
     end else byte_index<=byte_index+1'b1;
    end
    CRC:begin
     crc_received[byte_index*8+:8]<=byte_data;
     if(byte_index==3)begin
      if({byte_data,crc_received[23:0]}==~crc_value)begin
       if(word_count==4096)begin state<=EXECUTE;running<=1;end
       else begin state<=FILL;word_index<=word_count;end
      end
      else begin state<=SYNC0;boot_error<=1;end
     end else byte_index<=byte_index+1'b1;
    end
    FILL:begin end
    default:state<=SYNC0;
   endcase
   if(frame_error || (!byte_valid && state!=SYNC0 && state!=FILL && timeout_count==TIMEOUT_CLKS-1))begin
    state<=SYNC0;running<=0;boot_error<=1;timeout_count<=0;
   end
  end
 end
endmodule
