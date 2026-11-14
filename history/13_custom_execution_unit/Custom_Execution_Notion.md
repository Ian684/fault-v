# Fault-V：DSP／AI 執行單元與 CPU 整合

## 1．整體架構

CPU 維持 32-bit、多周期、單指令依序執行。四條自訂指令接到獨立的 `custom_exec`，共用原本的兩讀一寫 Register File；不加入第三個讀取埠、隱藏累加器或 Pipeline。

```text
IR → Decoder ───────────────→ custom_op
 │                             │
 └→ rs1／rs2 → Register File → A／B 暫存器
                                  │
                                  ▼
                          Custom Execution Unit
                         共用 signed 16×16 乘法器
                         18-bit DOT4 累加器
                         33-bit 飽和加法
                         算術右移＋INT8 限制
                                  │
                                  ▼
                            CustomResult
                                  │
                    WB MUX：WB_CUSTOM
                                  │
                                  ▼
                          Register File 的 rd

FSM：Decode → CUSTOM_START → CUSTOM_WAIT → CUSTOM_COMMIT → Fetch
```

自訂指令等待期間，PC 保持不變、不取下一條指令、不發起資料記憶體交易。正常提交時才寫回 rd，更新 PC = InstrPC + 4，並產生一次 retire。

## 2．四條指令

| 指令 | 語意 | 位寬與邊界 |
| --- | --- | --- |
| DOT4 | 兩個來源各拆成四個 signed INT8，逐 lane 相乘再加總 | lane 0 = bits 7:0；乘積 16-bit，累加 18-bit，再符號擴展成 INT32；範圍 -65024～65536 |
| MUL16 | 取 rs1／rs2 低 16-bit，解讀成 signed INT16 後相乘 | 高 16-bit 忽略；精確 signed INT32 乘積 |
| ADDSAT | signed INT32 相加後飽和 | 用 signed 33-bit 判斷，限制到 -2147483648～2147483647 |
| QNT8 | rs1 做算術右移，再限制到 INT8 範圍 | shift = rs2[4:0]，高位忽略；限制到 -128～127，再符號擴展成 INT32；不做四捨五入 |

例如 `DOT4(0x04030201,0x08070605)` 得到 70。`QNT8(-3,1)` 得到 -2；算術右移對負數向負無限方向取整。

所有指令讀 rs1、rs2，寫 rd，沒有記憶體副作用。rd 可等於 rs1／rs2，因為來源已在 Decode 保存。x0 永遠讀到 0，忽略寫回，但指令仍正常完成。

多次 DOT4／MUL16 的跨組累加使用一般 ADD，仍遵守 32-bit 截斷；不會自動對整個運算提供飽和保護。

## 3．編碼與 Decoder

R-type，opcode 使用 custom-0 = `0x0B`，funct7 必須為 0。

| 指令 | funct3 | Match | Mask | x5,x6,x7 範例 |
| --- | --- | --- | --- | --- |
| DOT4 | 000 | 0x0000000B | 0xFE00707F | 0x0073028B |
| MUL16 | 001 | 0x0000100B | 0xFE00707F | 0x0073128B |
| ADDSAT | 010 | 0x0000200B | 0xFE00707F | 0x0073228B |
| QNT8 | 011 | 0x0000300B | 0xFE00707F | 0x0073328B |

合法條件為 opcode=0x0B、funct7=0、funct3=0～3。Decoder 輸出 `IC_CUSTOM`、`rd_write=1`、`WB_CUSTOM` 與 2-bit custom_op；非法欄位維持 HALT_ILLEGAL，不啟動單元、不寫回、不提交。

這是專案自訂擴充 XFaultVDSP v1.0，不因此取得標準 M／V 擴充。custom opcode 空間依 [RISC-V 官方 opcode map](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv-32-64g.html)。

## 4．執行單元介面

| 訊號 | 相對執行單元的方向 | 定義 |
| --- | --- | --- |
| clk／rst | 輸入 | 核心共用 clock，高有效同步 reset |
| req_valid／req_ready | 輸入／輸出 | 有效請求與可接受狀態 |
| req_op | 輸入，custom_op_t，2-bit | 00 DOT4、01 MUL16、10 ADDSAT、11 QNT8 |
| req_a／req_b | 輸入，各 32-bit | 已保存的兩個來源值 |
| rsp_valid／rsp_ready | 輸出／輸入 | 有效結果與 CPU 願意取走結果 |
| rsp_result | 輸出，32-bit | 指令規定的結果 |

請求只在 `req_valid && req_ready` 的上升緣接受，並鎖存 req_a／req_b。運算期間及等待回應被取走期間，req_ready=0；最多一筆未完成運算。

回應只在 `rsp_valid && rsp_ready` 的上升緣被取走。如果 rsp_ready=0，rsp_valid 與 rsp_result 必須保持不變。取走後回到 IDLE，下一次請求需在後續 clock edge 接受；不是同拍消耗與接受的流水化單元。

rst=1 時兩個握手輸出被抑制；reset edge 清除單元狀態、輸入、累加器與結果。解除 reset 後，不得回傳 reset 前的結果。

## 5．單元狀態與延遲

| 狀態 | 動作 | 下一步 |
| --- | --- | --- |
| EU_IDLE | req_ready=1；接受時保存來源、lane=0、accumulator=0 | 依 req_op 選運算狀態 |
| EU_DOT | 取當前 lane，符號擴展為 16-bit，相乘並累加 | lane 0～2 前進；lane 3 保存結果後進 EU_RESPONSE |
| EU_MUL | 計算兩個低 16-bit signed 值的乘積 | 保存結果，進 EU_RESPONSE |
| EU_ADD | 計算 signed 33-bit 和，判斷上下限 | 保存飽和結果，進 EU_RESPONSE |
| EU_QNT | 算術右移，判斷 -128／127 範圍 | 保存 INT32 符號擴展結果，進 EU_RESPONSE |
| EU_RESPONSE | rsp_valid=1，等待 CPU 取走 | handshake 後回 EU_IDLE |

以接受請求的 edge 為 E0，DOT4 在 E4 後提供 rsp_valid，其他三條在 E1 後提供。這是本版單元的運算延遲，不是整條 CPU 指令的 cycle 數。

乘法放在獨立的 `fault_v_mul16` 模組，透過 keep_hierarchy 保留階層，避免工具把 DOT4 的乘加融合成另一個乘法器。這是共用同一顆乘法器的結構要求，而非只計算 RTL 中乘法運算子的數量。DOT4 把每個 INT8 符號擴展為 INT16；MUL16 直接取低 16-bit。RTL 不直接引用 FPGA DSP primitive；use_dsp 是合成提示。建置腳本核對整體設計恰好使用一個 DSP48E1；其他製程的工具需要依其元件庫重新檢查乘法器結構。

## 6．CPU FSM 與寫回

| CPU 狀態 | 控制與資料動作 | 轉移條件 |
| --- | --- | --- |
| ST_DECODE | 合法 IC_CUSTOM 時保存 A、B | 進 ST_CUSTOM_START |
| ST_CUSTOM_START | req_valid=1；PC、RegFile 保持不變 | req_ready=1 的 edge 進 WAIT |
| ST_CUSTOM_WAIT | rsp_ready=1；不重發請求 | rsp_valid=1 的 edge 保存 CustomResult，進 COMMIT |
| ST_CUSTOM_COMMIT | WB_CUSTOM 寫回 rd；PC+4；instr_done=1 | 進 FETCH |

WAIT 保存結果與 COMMIT 寫回使用不同 edge，因此不會在保存結果的同一 edge 讀到舊 CustomResult。

| 元件 | 整合方式 |
| --- | --- |
| fault_v_pkg.sv | 新增 custom_op_t、IC_CUSTOM、WB_CUSTOM；cpu_state_t 改 5-bit，18 種狀態 |
| decoder.sv | 新增 custom-0 解碼；其他指令原有行為保留 |
| custom_exec.sv | 獨立運算單元 |
| control_fsm.sv | 三個 custom 狀態、請求／回應與 custom_result_we |
| fault_v_cpu.sv | 實例化單元、新增 CustomResult 暫存器與 WB MUX 來源 |
| Register File／ALU／imm_gen | 原有模組維持兩讀一寫與既有語意 |
| PC／retire | 只有 COMMIT 才更新／提交；x0 不產生 rd write trace |

本版單元在 idle 時會立即允許請求，但 FSM 仍依 req_ready 決定前進。未來改變單元延遲時，CPU 不依固定倒數計算完成時間。

## 7．同步 reset 與執行中取消

Reset 同時作用到 CPU FSM、CustomResult、Register File 與 custom_exec。START、DOT4 lane 運算、有效回應等待、COMMIT 前，都可能被 reset 中斷。被中斷的指令不得提交，解除 reset 後從 PC=0 重新啟動。

RAM 不因 reset 清空；已完成的資料寫入也不回滾。測試程式重新初始化所需輸入，不能依賴 reset 自動清空資料 RAM。

## 8．完整自我檢查程式

`custom_demo.mem` 放進 16 KiB 指令記憶體，使用既有 RV32I 與四條自訂指令。程式在 CPU 執行時自行填入資料 RAM，再逐項核對結果。

| 工作 | 計算方式 | 結果保存：相對 0x10000000 的 byte offset |
| --- | --- | --- |
| DOT64 | 64 個 INT8；16 次 DOT4，以 ADD 累加 | 0x080：60256 |
| FIR8 | 八抽頭、16 個輸出；每個輸出兩次 DOT4 | 0x180～0x1BF：16 個 INT32 |
| QNT8 | 每個 FIR8 結果右移 3 並限制範圍 | 0x1C0～0x1FF：16 個符號擴展 INT32 |
| FIR16 | 八抽頭、16 個輸出；LH、MUL16、ADD | 0x380～0x3BF：16 個 INT32 |
| SATADD64 | 64 對 INT32 的飽和加法 | 0x400～0x4FF：64 個 INT32 |
| Directed 邊界值 | 14 個固定邊界案例 | 0x600～0x637：14 個 INT32 |
| 失敗編號 | 比較失敗時保存當前檢查編號 | 0x7FC |

FIR8 的滑動視窗可能不對齊 word，所以以 LBU、SLLI、OR 在 CPU 打包四個 byte；不發起未對齊 LW。內積資料每四個 byte 一組，可直接用對齊 LW。

每次核對使用短距離 BEQ 跳過失敗處理跳躍，再用 JAL 跳到統一 fail 路徑，避免長程式超出 B-type 分支位移範圍。生成器檢查所有 branch／JAL 位移與 ROM 容量。

| 結果 | 行為 |
| --- | --- |
| 全部比較相同 | UART 輸出 DSP OK 加 CR/LF，GPIO=5，program_status=1，最後 EBREAK |
| 比較失敗 | 保存檢查編號，GPIO=15，program_status=2，最後 EBREAK；不輸出成功字串 |
| 其他 CPU fault | 沿用 halt_cause／fault_pc／fault_addr；不假設所有故障都能跑到軟體 fail |

失敗編號只有在 program_status=2 時有效；RAM 保留舊內容，reset 不保證把該編號清零。

完整預期結果在 `programs/expected_outputs.json`，完整 benchmark 輸入與答案在 `programs/benchmark_vectors.json`。這個程式用來核對功能，尚不是軟體基準與自訂版本的效能比較。

## 9．測試與驗收條件

| 測試 | 需要確認的行為 |
| --- | --- |
| tb_custom_exec | 指令結果對 Python 模型、精確運算延遲、輸入鎖存、0～6 拍回應 backpressure、重置取消 |
| tb_custom_cpu | 兩組記憶體延遲；retire PC／word／rd／data、x0、來源目的重疊、相依指令、非法欄位與全部暫存器 |
| tb_custom_reset | START、四個 DOT4 等待位置、response 待取走、COMMIT 前重置；重新執行只提交一次 |
| tb_custom_program | 原始 mem 的全部 127 個輸出；每輪 270 次自訂提交；UART、成功狀態與重複 reset 重跑 |
| Fault injection | 破壞第一與晚期的運算結果，確認 error jump、失敗編號與 LED／status |
| 原 ISA 回歸 | 40 個指令名稱、既有 directed／程式／錯誤案例與兩組記憶體延遲 |
| 周邊／壓力回歸 | UART、GPIO、MMIO 錯誤、等待交易與執行中重置 |
| tb_payload | FPGA wrapper 的 50 MHz／434 分頻、run 控制、BTN reset 與三次 DSP 字串 |
| FPGA build | 合成／佈線完成、setup／hold／pulse width 符合約束、DRC 條件與 IP 設定核對 |
| 實板 | 正確載入配對 bit／hwh，三次收到 DSP OK，UART 錯誤為 0，status=1、halted=1、cause=9 |

有限 directed／隨機測試不是完整輸入空間的形式證明。Wrapper RTL 模擬不包含實際 PS7、AXI UART Lite 的硬體行為或外部 Pmod 電氣傳輸；這些需實板測試或其他獨立驗證。

## 10．FPGA 設定與 ARM 介面

PYNQ-Z2 使用 SD 開機 Linux，再用 PYNQ Overlay 載入配對的 `fault_v_custom.bit` 與 `fault_v_custom.hwh`。CPU、AXI GPIO 與 UART Lite 使用 PS FCLK0 的 50 MHz。Fault-V TX 每 bit 434 clocks，接到 PL 內 UART Lite RX，再由 ARM／Ethernet 顯示。

| ARM 位址 | 功能 |
| --- | --- |
| 0x42C00000 | UART Lite RX FIFO |
| 0x42C00008 | RX 有效 bit 0；錯誤 bits 7:5 |
| 0x42C0000C | 寫 3 清除 TX／RX FIFO |
| 0x41200000 | run bit 0：0 保持 CPU reset，1 開始執行 |
| 0x41200008 | CPU debug status |

debug status：bits 1:0 為 program_status，bit 2 為 halted，bits 12:9 為 halt_cause。正常示範結束值為 0x00001205。ARM AXI 位址與 Fault-V 自己的 MMIO 位址是不同介面。

BTN0 只重置 Fault-V，不重新啟動 Linux。載入 overlay 會替換目前 PL 設計；斷電後不自動保留此設計。Ethernet 接收方式不需外接 USB-to-UART 轉接器，但不因此證明 Pmod 接腳的電氣傳輸。

## 11．檔案與執行方式

在 `outputs/custom_core` 資料夾執行：

```powershell
# 重新產生 deterministic 程式與測試向量
python .\generate.py

# 單元、原 ISA／周邊／壓力回歸
powershell -ExecutionPolicy Bypass -File .\run_regression.ps1

# 自訂 CPU、重置與完整工作負載
powershell -ExecutionPolicy Bypass -File .\run_custom.ps1

# FPGA wrapper 的 RTL 模擬
powershell -ExecutionPolicy Bypass -File .\run_payload.ps1

# FPGA 合成與 implementation
powershell -ExecutionPolicy Bypass -File .\run_build.ps1

# 板子可用時：上傳、載入並驗證
python .\deploy_and_receive.py
```

最後一個命令需要 paramiko、Z2 的 SSH 與 PYNQ root 權限；預設連線設定在 remote_access.py。生成與模擬不會下載 FPGA。

| 檔案 | 用途 |
| --- | --- |
| rtl/ | 完整整合後 CPU／SoC RTL，含 custom_exec |
| board/、constraints/ | 50 MHz PS 平台的 payload／reset 與 Z2 接腳約束 |
| generate.py、build_custom.py | 產生模型向量、Assembly、mem 與固定預期答案 |
| programs/custom_demo.S／.mem | 自我檢查程式與 FPGA 指令映像 |
| verify/ | 新增測試與原有回歸向量 |
| build.tcl／create_project.tcl／ps_preset.tcl | FPGA 平台與建置流程 |
| receive_on_board.py | ARM 上的 UART／debug 驗收 |
| deploy_and_receive.py | 電腦透過 SSH 上傳與執行 |
| Fault_V_Custom.ipynb | 板上 Jupyter 操作入口 |
| Verification_Report.md | 實際執行結果、時序、資源、限制；與筆記分開 |

## 12．下一步的效能與延伸

使用同一份輸入，建立不含 MUL 或 custom 指令的 RV32I shift/add 軟體版本，量測與本版 custom 程式相同 kernel 的 cycle、頻率、時間與硬體成本。UART 輸出不應放進核心運算量測區間；資料打包是否計入需一致。

11 種延伸仍依路線圖逐項評估。最直接的下一個硬體比較是「共用一個乘法器」與「並行四個乘法器的 DOT4」；指令語意與測試答案可沿用，內部延遲與資源則重新量測。ASIC PPA 需選定製程與元件庫後分析，FPGA 資源與時序不能直接視為 ASIC 結果。

## 13．完整 custom_exec 與共用乘法器 RTL

```systemverilog
`timescale 1ns/1ps
module custom_exec (
    input logic clk, rst,
    input logic req_valid,
    output logic req_ready,
    input fault_v_pkg::custom_op_t req_op,
    input logic [31:0] req_a, req_b,
    output logic rsp_valid,
    input logic rsp_ready,
    output logic [31:0] rsp_result
);
    import fault_v_pkg::*;
    typedef enum logic [2:0] {EU_IDLE,EU_DOT,EU_MUL,EU_ADD,EU_QNT,EU_RESPONSE} unit_state_t;
    unit_state_t state;
    logic [31:0] a_hold,b_hold;
    logic [1:0] lane;
    logic signed [17:0] accumulator,dot_sum;
    logic signed [15:0] multiply_a,multiply_b;
    logic signed [7:0] lane_a,lane_b;
    logic signed [31:0] product,shifted;
    logic signed [32:0] wide_sum;
    assign req_ready=!rst && state==EU_IDLE;
    assign rsp_valid=!rst && state==EU_RESPONSE;
    (* keep_hierarchy="yes" *) fault_v_mul16 u_multiplier(.a(multiply_a),.b(multiply_b),.product(product));
    always_comb begin
        lane_a=a_hold[(lane*8)+:8];
        lane_b=b_hold[(lane*8)+:8];
        multiply_a=$signed(a_hold[15:0]);
        multiply_b=$signed(b_hold[15:0]);
        if(state==EU_DOT) begin
            multiply_a={{8{lane_a[7]}},lane_a};
            multiply_b={{8{lane_b[7]}},lane_b};
        end
        dot_sum=accumulator+product;
        wide_sum=$signed({a_hold[31],a_hold})+$signed({b_hold[31],b_hold});
        shifted=$signed(a_hold) >>> b_hold[4:0];
    end
    always_ff @(posedge clk) begin
        if(rst) begin
            state<=EU_IDLE; a_hold<=0; b_hold<=0; lane<=0;
            accumulator<=0; rsp_result<=0;
        end else begin
            case(state)
                EU_IDLE: if(req_valid && req_ready) begin
                    a_hold<=req_a; b_hold<=req_b; lane<=0; accumulator<=0;
                    case(req_op)
                        CUSTOM_DOT4: state<=EU_DOT;
                        CUSTOM_MUL16: state<=EU_MUL;
                        CUSTOM_ADDSAT: state<=EU_ADD;
                        CUSTOM_QNT8: state<=EU_QNT;
                    endcase
                end
                EU_DOT: begin
                    accumulator<=dot_sum;
                    if(lane==3) begin
                        rsp_result<={{14{dot_sum[17]}},dot_sum}; state<=EU_RESPONSE;
                    end else lane<=lane+1'b1;
                end
                EU_MUL: begin rsp_result<=product; state<=EU_RESPONSE; end
                EU_ADD: begin
                    if(wide_sum>33'sd2147483647) rsp_result<=32'h7fffffff;
                    else if(wide_sum< -33'sd2147483648) rsp_result<=32'h80000000;
                    else rsp_result<=wide_sum[31:0];
                    state<=EU_RESPONSE;
                end
                EU_QNT: begin
                    if(shifted>32'sd127) rsp_result<=32'd127;
                    else if(shifted< -32'sd128) rsp_result<=32'hffffff80;
                    else rsp_result<=shifted;
                    state<=EU_RESPONSE;
                end
                EU_RESPONSE: if(rsp_valid && rsp_ready) state<=EU_IDLE;
                default: state<=EU_IDLE;
            endcase
        end
    end
endmodule

// Separate hierarchy prevents MAC extraction from cloning the multiplier.
(* keep_hierarchy="yes", use_dsp="yes" *)
module fault_v_mul16(
    input logic signed [15:0] a,b,
    output logic signed [31:0] product
);
    assign product=a*b;
endmodule
```
