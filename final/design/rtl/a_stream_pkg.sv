`timescale 1ns/1ps
package fault_v_stream_pkg;
 localparam logic [31:0] MAIN_BASE=32'h10000000,MAIN_END=32'h10004000;
 localparam logic [31:0] SCRATCH_BASE=32'h10010000,SCRATCH_END=32'h10011000;
 localparam logic [7:0] JOB_OK=0,JOB_LENGTH=1,JOB_ALIGN=2,JOB_RANGE=3,
 JOB_OVERLAP=4,JOB_CONFLICT=5,JOB_READ=6,JOB_WRITE=7,JOB_TAG=8;
 function automatic logic valid_region(input logic [31:0] base,bytes);
  logic [32:0] endpoint;
  endpoint={1'b0,base}+{1'b0,bytes};
  return bytes!=0 && base[1:0]==0 &&
   ((base>=MAIN_BASE && endpoint<={1'b0,MAIN_END}) ||
    (base>=SCRATCH_BASE && endpoint<={1'b0,SCRATCH_END}));
 endfunction
 function automatic logic overlaps(input logic [31:0] a,alen,b,blen);
  return alen!=0 && blen!=0 && {1'b0,a}<{1'b0,b}+{1'b0,blen} && {1'b0,b}<{1'b0,a}+{1'b0,alen};
 endfunction
 function automatic logic in_region(input logic [31:0] addr,base,bytes);
  return bytes!=0 && addr>=base && {1'b0,addr}<{1'b0,base}+{1'b0,bytes};
 endfunction
endpackage
