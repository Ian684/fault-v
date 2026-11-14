module tb_control_path;
    timeunit 1ns;
    timeprecision 1ps;
    import fault_v_pkg::*;
    logic clk=0,rst;
    always #5 clk=~clk;
    logic [31:0] pc,instr_pc,ir,a_reg,b_reg,aluout,mdr;
    logic branch_taken;
    logic [4:0] rs1_addr,rs2_addr,rd_addr;
    instr_class_t instr_class;
    alu_op_t alu_op;
    imm_sel_t imm_sel;
    alu_src_a_t alu_src_a;
    alu_src_b_t alu_src_b;
    branch_op_t branch_op;
    mem_size_t mem_size;
    wb_sel_t wb_sel;
    logic load_unsigned,rd_write,illegal;
    logic imem_req_valid,imem_req_ready,imem_rsp_valid,imem_rsp_err,imem_rsp_ready;
    logic [31:0] imem_req_addr,imem_rsp_data;
    logic dmem_req_valid,dmem_req_ready,dmem_req_write,dmem_rsp_valid,dmem_rsp_err,dmem_rsp_ready;
    logic [31:0] dmem_req_addr,dmem_rsp_data,mem_addr,target_addr;
    logic ir_we,instr_pc_we,ab_we,aluout_we,branch_taken_we,mdr_we,reg_we,pc_we,instr_done;
    pc_sel_t pc_sel;
    cpu_state_t state;
    logic mem_pending,halted;
    halt_cause_t halt_cause;
    logic [31:0] fault_pc,fault_addr;
    logic [31:0] imm,alu_a,alu_b,alu_result,pc_next,wb_data,load_shift;
    logic branch_result;
    logic setup_we,probe;
    logic [4:0] setup_addr,probe_addr,rf_rs1,rf_rd;
    logic [31:0] setup_data,rf_data1,rf_data2,rf_wdata;
    logic rf_we;
    logic [31:0] store_data;
    logic [3:0] store_mask;
    logic model_busy;
    integer request_delay,response_delay,model_request_timer,model_response_timer;
    logic model_error;
    logic [31:0] model_read_data,captured_addr,captured_store;
    logic [3:0] captured_mask;
    logic captured_write;
    integer data_requests,fetch_requests,writes,commits,test_count=0,cycles;
    logic [31:0] last_wb;
    logic [4:0] last_rd;

    decoder u_decoder(.instruction(ir),.rs1_addr(rs1_addr),.rs2_addr(rs2_addr),.rd_addr(rd_addr),
        .instr_class(instr_class),.alu_op(alu_op),.imm_sel(imm_sel),
        .alu_src_a(alu_src_a),.alu_src_b(alu_src_b),.branch_op(branch_op),
        .mem_size(mem_size),.load_unsigned(load_unsigned),.rd_write(rd_write),.wb_sel(wb_sel),.illegal(illegal));
    control_fsm dut(.*);
    imm_gen u_imm(.instruction(ir),.imm_sel(imm_sel),.imm(imm));
    alu u_alu(.a(alu_a),.b(alu_b),.alu_op(alu_op),.result(alu_result));
    pc_reg u_pc(.clk(clk),.rst(rst),.pc_we(pc_we),.pc_next(pc_next),.pc(pc));
    assign rf_rs1=probe?probe_addr:rs1_addr;
    assign rf_we=setup_we || reg_we;
    assign rf_rd=setup_we?setup_addr:rd_addr;
    assign rf_wdata=setup_we?setup_data:wb_data;
    regfile u_rf(.clk(clk),.rst(rst),.rs1_addr(rf_rs1),.rs2_addr(rs2_addr),
        .rs1_data(rf_data1),.rs2_data(rf_data2),.rd_we(rf_we),.rd_addr(rf_rd),.rd_data(rf_wdata));
    assign mem_addr=aluout;
    assign target_addr=aluout;
    assign pc_next=(pc_sel==PC_TARGET)?aluout:(instr_pc+32'd4);

    // This is a simulation datapath harness, not the final synthesizable CPU top.
    always_comb begin
        case (alu_src_a)
            ALU_A_REG: alu_a=a_reg;
            ALU_A_PC: alu_a=instr_pc;
            default: alu_a=0;
        endcase
        alu_b=(alu_src_b==ALU_B_REG)?b_reg:imm;
        branch_result=0;
        case (branch_op)
            BR_EQ: branch_result=(a_reg==b_reg);
            BR_NE: branch_result=(a_reg!=b_reg);
            BR_LT: branch_result=($signed(a_reg)<$signed(b_reg));
            BR_GE: branch_result=($signed(a_reg)>=$signed(b_reg));
            BR_LTU: branch_result=(a_reg<b_reg);
            BR_GEU: branch_result=(a_reg>=b_reg);
            default: branch_result=0;
        endcase
        load_shift=mdr >> {aluout[1:0],3'b000};
        wb_data=aluout;
        case (wb_sel)
            WB_PC4: wb_data=instr_pc+32'd4;
            WB_LOAD: begin
                case (mem_size)
                    MEM_BYTE: begin
                        if (load_unsigned) wb_data={24'b0,load_shift[7:0]};
                        else wb_data={{24{load_shift[7]}},load_shift[7:0]};
                    end
                    MEM_HALF: begin
                        if (load_unsigned) wb_data={16'b0,load_shift[15:0]};
                        else wb_data={{16{load_shift[15]}},load_shift[15:0]};
                    end
                    default: wb_data=mdr;
                endcase
            end
            default: begin end
        endcase
        store_data=b_reg << {aluout[1:0],3'b000};
        case (mem_size)
            MEM_BYTE: store_mask=4'b0001 << aluout[1:0];
            MEM_HALF: store_mask=4'b0011 << aluout[1:0];
            default: store_mask=4'b1111;
        endcase
    end
    always_ff @(posedge clk) begin
        if (rst) begin
            ir<=0; instr_pc<=0; a_reg<=0; b_reg<=0;
            aluout<=0; mdr<=0; branch_taken<=0;
        end else begin
            if (ir_we) ir<=imem_rsp_data;
            if (instr_pc_we) instr_pc<=pc;
            if (ab_we) begin a_reg<=rf_data1; b_reg<=rf_data2; end
            if (aluout_we) begin
                if (instr_class==IC_JALR) aluout<=alu_result & 32'hfffffffe;
                else aluout<=alu_result;
            end
            if (branch_taken_we) branch_taken<=branch_result;
            if (mdr_we) mdr<=dmem_rsp_data;
        end
    end

    // One-entry memory stand-in with configurable acceptance and response delay.
    // Stores are recorded at acceptance; a response error does not undo them.
    always @(posedge clk) begin
        if (rst) begin
            model_busy<=0; model_request_timer<=0; model_response_timer<=0;
            dmem_req_ready<=0; dmem_rsp_valid<=0; dmem_rsp_err<=0; dmem_rsp_data<=0;
            data_requests<=0; fetch_requests<=0; writes<=0; commits<=0;
            last_wb<=0; last_rd<=0;
            captured_addr<=0; captured_store<=0; captured_mask<=0; captured_write<=0;
        end else begin
            if (imem_req_valid && imem_req_ready) fetch_requests<=fetch_requests+1;
            if (reg_we && rd_addr!=0) begin writes<=writes+1; last_wb<=wb_data; last_rd<=rd_addr; end
            if (instr_done) commits<=commits+1;
            if (!model_busy) begin
                if (dmem_req_valid && !dmem_req_ready) begin
                    if (model_request_timer>=request_delay) dmem_req_ready<=1;
                    else model_request_timer<=model_request_timer+1;
                end
                if (dmem_req_valid && dmem_req_ready) begin
                    model_busy<=1; model_response_timer<=response_delay;
                    dmem_req_ready<=0; data_requests<=data_requests+1;
                    captured_addr<=dmem_req_addr; captured_store<=store_data;
                    captured_mask<=store_mask; captured_write<=dmem_req_write;
                end
            end else if (!dmem_rsp_valid) begin
                if (model_response_timer==0) begin
                    dmem_rsp_valid<=1; dmem_rsp_err<=model_error; dmem_rsp_data<=model_read_data;
                end else model_response_timer<=model_response_timer-1;
            end
            if (dmem_rsp_valid && dmem_rsp_ready) begin
                model_busy<=0; dmem_rsp_valid<=0; model_request_timer<=0;
            end
        end
    end
    task automatic must(input logic cond,input string label_text);
        if (cond !== 1'b1)
            $fatal(1,"FAIL %s state=%0d pc=%h fault=%0d",label_text,state,pc,halt_cause);
    endtask
    task automatic tick; @(posedge clk); #1; endtask
    task automatic setup_case(input logic [31:0] av,bv,input int rq,rs,input logic err);
        @(negedge clk);
        rst=1; setup_we=0; probe=0; setup_addr=0; setup_data=0; probe_addr=0;
        imem_req_ready=0; imem_rsp_valid=0; imem_rsp_err=0; imem_rsp_data=0;
        request_delay=rq; response_delay=rs; model_error=err; model_read_data=32'h80ff7f01;
        tick; @(negedge clk); rst=0;
        // Test-only initialization through the actual Register File write port.
        setup_we=1; setup_addr=6; setup_data=av; tick;
        @(negedge clk); setup_addr=7; setup_data=bv; tick;
        @(negedge clk); setup_we=0;
    endtask
    task automatic fetch_word(input logic [31:0] word_value,input logic error_value);
        must(state==ST_FETCH,"fetch start");
        imem_req_ready=0; imem_rsp_valid=0;
        repeat(2) tick;
        @(negedge clk); imem_req_ready=1;
        tick;
        must(mem_pending && !imem_req_valid,"fetch request accepted");
        @(negedge clk); imem_req_ready=0;
        repeat(2) tick;
        @(negedge clk); imem_rsp_data=word_value; imem_rsp_err=error_value; imem_rsp_valid=1;
        tick;
        @(negedge clk); imem_rsp_valid=0; imem_rsp_err=0;
    endtask
    task automatic run_case(input string label_text,input logic [31:0] inst,av,bv,
                            input int expected_writes,input logic [31:0] expected_wb,expected_pc,
                            input halt_cause_t expected_cause,input logic [31:0] expected_fault_addr,
                            input int expected_requests,input logic response_error,
                            input logic [31:0] expected_bus_addr,expected_store,input logic [3:0] expected_mask);
        setup_case(av,bv,test_count%4,(test_count/4)%4,response_error);
        fetch_word(inst,0);
        cycles=0;
        while (commits==0 && !halted) begin
            tick; cycles++;
            if (cycles>100) $fatal(1,"CASE TIMEOUT %s",label_text);
        end
        must(pc===expected_pc,label_text);
        must(writes==expected_writes,"architectural write count");
        if (expected_writes!=0) begin
            must(last_rd==inst[11:7] && last_wb===expected_wb,"writeback destination/data");
            probe=1; probe_addr=inst[11:7]; #1;
            must(rf_data1===expected_wb,"actual register file value");
            probe=0;
        end
        must(data_requests==expected_requests,"exactly expected memory requests");
        must(fetch_requests==1,"one instruction request");
        if (expected_requests!=0) begin
            must(captured_addr===expected_bus_addr,"aligned external data address");
            if (captured_write)
                must(captured_store===expected_store && captured_mask===expected_mask,"store data and byte mask");
        end
        if (expected_cause==HALT_NONE) begin
            must(!halted && commits==1 && state==ST_FETCH,"normal instruction committed once");
        end else begin
            must(halted && commits==0 && halt_cause==expected_cause,"fault does not commit");
            must(fault_pc==0 && fault_addr===expected_fault_addr,"fault saved instruction/raw address");
            repeat(3) tick;
            must(writes==expected_writes && commits==0 && !imem_req_valid && !dmem_req_valid,"no post-halt actions");
        end
        probe=1; probe_addr=0; #1; must(rf_data1==0,"x0 remains zero"); probe=0;
        test_count++;
        $display("PASS %0d: %s pc=%h writes=%0d wb=%h requests=%0d cause=%0d",test_count,label_text,pc,writes,last_wb,data_requests,halt_cause);
    endtask

    initial begin
        rst=1; setup_we=0; probe=0; setup_addr=0; setup_data=0; probe_addr=0;
        imem_req_ready=0; imem_rsp_valid=0; imem_rsp_err=0; imem_rsp_data=0;
        request_delay=0; response_delay=0; model_error=0; model_read_data=0;
                run_case("ADD",32'h007302b3,32'h00000005,32'h00000003,1,32'h00000008,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("SUB",32'h407302b3,32'h00000003,32'h00000005,1,32'hfffffffe,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("SLL",32'h007312b3,32'h00000001,32'h00000020,1,32'h00000001,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("SLT",32'h007322b3,32'hffffffff,32'h00000001,1,32'h00000001,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("SLTU",32'h007332b3,32'hffffffff,32'h00000001,1,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("XOR",32'h007342b3,32'h0000000a,32'h0000000c,1,32'h00000006,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("SRL",32'h007352b3,32'h80000000,32'h00000001,1,32'h40000000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("SRA",32'h407352b3,32'h80000000,32'h00000001,1,32'hc0000000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("OR",32'h007362b3,32'h0000000a,32'h0000000c,1,32'h0000000e,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("AND",32'h007372b3,32'h0000000a,32'h0000000c,1,32'h00000008,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("ADDI",32'hffc30293,32'h0000000a,32'hdeadbeef,1,32'h00000006,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("SLTI",32'hffc32293,32'hfffffff8,32'h00000000,1,32'h00000001,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("SLTIU",32'hffc33293,32'h00000000,32'h00000000,1,32'h00000001,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("XORI",32'hffc34293,32'h12345678,32'h00000000,1,32'hedcba984,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("ORI",32'hffc36293,32'h12345678,32'h00000000,1,32'hfffffffc,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("ANDI",32'hffc37293,32'h1234567b,32'h00000000,1,32'h12345678,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("SLLI",32'h01f31293,32'h00000001,32'h00000000,1,32'h80000000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("SRLI",32'h01f35293,32'h80000000,32'h00000000,1,32'h00000001,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("SRAI",32'h41f35293,32'h80000000,32'h00000000,1,32'hffffffff,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("LUI",32'h123452b7,32'hdeadbeef,32'h00000000,1,32'h12345000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("AUIPC",32'h12345297,32'hdeadbeef,32'h00000000,1,32'h12345000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("BEQ taken",32'hfe730ee3,32'h00000005,32'h00000005,0,32'h00000000,32'hfffffffc,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("BNE taken",32'hfe731ee3,32'h00000005,32'h00000006,0,32'h00000000,32'hfffffffc,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("BLT taken",32'hfe734ee3,32'hffffffff,32'h00000001,0,32'h00000000,32'hfffffffc,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("BGE taken",32'hfe735ee3,32'h00000005,32'h00000005,0,32'h00000000,32'hfffffffc,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("BLTU taken",32'hfe736ee3,32'h00000000,32'hffffffff,0,32'h00000000,32'hfffffffc,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("BGEU taken",32'hfe737ee3,32'hffffffff,32'h00000000,0,32'h00000000,32'hfffffffc,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("JAL",32'hffdff2ef,32'h00000000,32'h00000000,1,32'h00000004,32'hfffffffc,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("JALR",32'hffc302e7,32'h00000200,32'h00000000,1,32'h00000004,32'h000001fc,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("LB",32'hffc30283,32'h10000004,32'h00000000,1,32'h00000001,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h10000000,32'h00000000,4'h0);
        run_case("LH",32'hffc31283,32'h10000004,32'h00000000,1,32'h00007f01,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h10000000,32'h00000000,4'h0);
        run_case("LW",32'hffc32283,32'h10000004,32'h00000000,1,32'h80ff7f01,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h10000000,32'h00000000,4'h0);
        run_case("LBU",32'hffc34283,32'h10000004,32'h00000000,1,32'h00000001,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h10000000,32'h00000000,4'h0);
        run_case("LHU",32'hffc35283,32'h10000004,32'h00000000,1,32'h00007f01,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h10000000,32'h00000000,4'h0);
        run_case("SB",32'hfe730e23,32'h10000004,32'ha1b2c3d4,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h10000000,32'ha1b2c3d4,4'h1);
        run_case("SH",32'hfe731e23,32'h10000004,32'ha1b2c3d4,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h10000000,32'ha1b2c3d4,4'h3);
        run_case("SW",32'hfe732e23,32'h10000004,32'ha1b2c3d4,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h10000000,32'ha1b2c3d4,4'hf);
        run_case("FENCE",32'h0ff0000f,32'h00000000,32'h00000000,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("ECALL",32'h00000073,32'h00000000,32'h00000000,0,32'h00000000,32'h00000000,HALT_ECALL,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("EBREAK",32'h00100073,32'h00000000,32'h00000000,0,32'h00000000,32'h00000000,HALT_EBREAK,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("BEQ not taken",32'hfe730ee3,32'h00000005,32'h00000006,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("BNE not taken",32'hfe731ee3,32'h00000005,32'h00000005,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("BLT not taken",32'hfe734ee3,32'h00000001,32'hffffffff,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("BGE not taken",32'hfe735ee3,32'hffffffff,32'h00000001,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("BLTU not taken",32'hfe736ee3,32'hffffffff,32'h00000000,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("BGEU not taken",32'hfe737ee3,32'h00000000,32'hffffffff,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("untaken misaligned branch",32'h00730163,32'h00000005,32'h00000006,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("taken misaligned branch",32'h00730163,32'h00000005,32'h00000005,0,32'h00000000,32'h00000000,HALT_INSTR_ALIGN,32'h00000002,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("misaligned JAL",32'h002002ef,32'h00000000,32'h00000000,0,32'h00000000,32'h00000000,HALT_INSTR_ALIGN,32'h00000002,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("JALR clears bit zero",32'h000302e7,32'h00000101,32'h00000000,1,32'h00000004,32'h00000100,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("JALR still misaligned",32'h000302e7,32'h00000103,32'h00000000,0,32'h00000000,32'h00000000,HALT_INSTR_ALIGN,32'h00000102,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("canonical NOP x0",32'h00000013,32'h00000000,32'h00000000,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("JAL to x0",32'h0040006f,32'h00000000,32'h00000000,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("Load to x0 still accesses",32'h00032003,32'h10000000,32'h00000000,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h10000000,32'h00000000,4'h0);
        run_case("LB upper negative byte",32'h00030283,32'h10000003,32'h00000000,1,32'hffffff80,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h10000000,32'h00000000,4'h0);
        run_case("LBU upper byte",32'h00034283,32'h10000003,32'h00000000,1,32'h00000080,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h10000000,32'h00000000,4'h0);
        run_case("LH upper negative halfword",32'h00031283,32'h10000002,32'h00000000,1,32'hffff80ff,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h10000000,32'h00000000,4'h0);
        run_case("LHU upper halfword",32'h00035283,32'h10000002,32'h00000000,1,32'h000080ff,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h10000000,32'h00000000,4'h0);
        run_case("SB upper byte mask",32'h00730023,32'h10000003,32'ha1b2c3d4,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h10000000,32'hd4000000,4'h8);
        run_case("SH upper halfword mask",32'h00731023,32'h10000002,32'ha1b2c3d4,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h10000000,32'hc3d40000,4'hc);
        run_case("misaligned LW",32'h00032283,32'h10000002,32'h00000000,0,32'h00000000,32'h00000000,HALT_LOAD_ALIGN,32'h10000002,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("misaligned SW",32'h00732023,32'h10000002,32'h00000000,0,32'h00000000,32'h00000000,HALT_STORE_ALIGN,32'h10000002,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("misaligned LH",32'h00031283,32'h10000001,32'h00000000,0,32'h00000000,32'h00000000,HALT_LOAD_ALIGN,32'h10000001,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("misaligned SH",32'h00731023,32'h10000001,32'h00000000,0,32'h00000000,32'h00000000,HALT_STORE_ALIGN,32'h10000001,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("narrow MMIO load rejected",32'h00030283,32'h20000000,32'h00000000,0,32'h00000000,32'h00000000,HALT_LOAD_ACCESS,32'h20000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("narrow MMIO store rejected",32'h00731023,32'h20000000,32'h00000000,0,32'h00000000,32'h00000000,HALT_STORE_ACCESS,32'h20000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("word MMIO load accepted",32'h00032283,32'h20000000,32'h00000000,1,32'h80ff7f01,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h20000000,32'h00000000,4'h0);
        run_case("word MMIO store accepted",32'h00732023,32'h20000000,32'ha1b2c3d4,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,1,0,32'h20000000,32'ha1b2c3d4,4'hf);
        run_case("load response error",32'h00032283,32'h10000000,32'h00000000,0,32'h00000000,32'h00000000,HALT_LOAD_ACCESS,32'h10000000,1,1,32'h10000000,32'h00000000,4'h0);
        run_case("byte response error raw fault address",32'h00030283,32'h10000003,32'h00000000,0,32'h00000000,32'h00000000,HALT_LOAD_ACCESS,32'h10000003,1,1,32'h10000000,32'h00000000,4'h0);
        run_case("store response error",32'h00732023,32'h10000000,32'ha1b2c3d4,0,32'h00000000,32'h00000000,HALT_STORE_ACCESS,32'h10000000,1,1,32'h10000000,32'ha1b2c3d4,4'hf);
        run_case("illegal instruction",32'hffffffff,32'h00000000,32'h00000000,0,32'h00000000,32'h00000000,HALT_ILLEGAL,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("MUL unsupported",32'h027302b3,32'h00000000,32'h00000000,0,32'h00000000,32'h00000000,HALT_ILLEGAL,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("CSR unsupported",32'h300312f3,32'h00000000,32'h00000000,0,32'h00000000,32'h00000000,HALT_ILLEGAL,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);
        run_case("FENCE reserved fields",32'hffff8f8f,32'h00000000,32'h00000000,0,32'h00000000,32'h00000004,HALT_NONE,32'h00000000,0,0,32'h00000000,32'h00000000,4'h0);

        // A committed jump's link is preserved if the following target fetch fails.
        setup_case(0,0,0,0,0);
        fetch_word(32'h010002ef,0); // jal x5,+16
        while (commits==0) tick;
        must(pc==16 && last_wb==4 && writes==1,"jump before target fetch fault");
        @(negedge clk); fetch_word(32'h00000013,1);
        must(halted && halt_cause==HALT_FETCH_ACCESS && fault_pc==16 && fault_addr==16,"fault belongs to target fetch");
        must(pc==16 && commits==1 && writes==1 && last_wb==4,"prior jump not rolled back");
        probe=1; probe_addr=5; #1; must(rf_data1==4,"link survives subsequent fetch error"); probe=0;
        test_count++;
        $display("PASS %0d: target fetch error preserves committed link",test_count);

        $display("ALL %0d CONTROL PATH CASES PASSED",test_count);
        $finish;
    end
    initial begin #100000; $fatal(1,"TIMEOUT tb_control_path"); end
endmodule
