# Fault-V：運算單元擴充架構

## 1．整體架構

Fault-V 維持 32-bit、多周期、單指令依序執行。基礎 RV32I、兩讀一寫 Register File、16 KiB 指令記憶體、16 KiB 資料記憶體與 UART／GPIO MMIO 架構延續既有設計。

自訂擴充命名為 **XFaultVDSP v1.1**，包含原有四條與新增八條，共十二條指令。原有四條的編碼與數值語意維持相容，DOT4 的內部運算改為四乘法器並行。

```text
指令記憶體 → IR → Decoder → FSM
                   │         │
                   ▼         ▼
             Register File：兩讀一寫
                   │
              A／B 暫存器
                   │
       累加指令：多一拍讀舊 rd → CustomAcc
                   │
                   ▼
          Custom Execution Unit
          四個 signed 16×16 乘法器
          內積加法樹、累加、逐 byte 飽和
          INT32×INT16 比例乘法與量化
                   │
               CustomResult
                   │
                WB MUX → rd

CPU 資料介面 → 位址解碼 → 資料 RAM／UART TX／GPIO／完成狀態
```

核心不加入第三個 Register File 讀取埠、隱藏累加器、指令流水線或多筆未完成運算。ARM／AXI UART Lite／Ethernet 是 PYNQ-Z2 的操作與觀察平台。

## 2．六個延伸方向與具體選擇

| 方向 | 本版實作 | 設計選擇 |
| --- | --- | --- |
| 共用／並行乘法器 | DOT4 的四個乘積並行計算 | 四個 16×16 乘法器；其他指令重用這四個單元 |
| MAC／DOT4ACC | MAC16、DOT4ACC | 舊 rd 是明確的累加來源；多一拍讀取，結果 modulo 2³² |
| Packed 飽和 | ADD8SAT、SUB8SAT | 四個 signed INT8 lane 各自飽和；不傳遞 lane 間 carry |
| 更完整量化 | RQNT8 | signed INT32×INT16、可變右移、nearest 捨入、zero-point、INT8 飽和 |
| INT16 雙 lane | DOT2SAT | 兩組 signed INT16 內積；精確 33-bit 和再限制到 INT32 |
| INT4／混合 signed | DOT8、DOT4SU | 八組 signed INT4；以及四組 signed INT8×unsigned INT8 |

每個方向選定上述具體功能。量化格式、飽和政策及資料型別都由這份規格定義；不宣稱涵蓋所有量化框架或所有混合格式。

## 3．指令數值語意

lane 0 位於最低位。除 packed 輸出外，內積、乘法及量化結果都寫成一個 32-bit 整數。

| 指令 | 數值語意 | 寬度與溢位 |
| --- | --- | --- |
| DOT4 | 四組 signed INT8 乘積之和 | 18-bit 和，範圍 −65024～65536，符號擴展成 INT32 |
| MUL16 | 來源低 16-bit 的 signed 乘積 | 精確 INT32；來源高 16-bit 忽略 |
| ADDSAT | signed INT32 加法 | 33-bit 和，限制到 −2147483648～2147483647 |
| QNT8 | rs1 算術右移 rs2[4:0] 後限制到 INT8 | 不做 nearest 捨入；輸出符號擴展 INT32 |
| DOT4ACC | old(rd)＋DOT4(rs1,rs2) | 保存低 32-bit；不飽和 |
| MAC16 | old(rd)＋signed(rs1[15:0])×signed(rs2[15:0]) | 保存低 32-bit；不飽和 |
| ADD8SAT | 四個 signed INT8 lane 各自相加 | 每 lane 9-bit 中間值，限制到 −128～127，再打包 |
| SUB8SAT | 四個 signed INT8 lane 各自相減 | 每 lane 9-bit 中間值，限制到 −128～127，再打包 |
| RQNT8 | 比例乘法、捨入、zero-point、INT8 飽和 | 精確 48-bit 乘積，49-bit 捨入與偏移中間值；輸出符號擴展 INT32 |
| DOT2SAT | 兩組 signed INT16 乘積之和 | 33-bit 和；例如 0x80008000×0x80008000 的和為 2147483648，輸出 0x7FFFFFFF |
| DOT8 | 八組 signed INT4 乘積之和 | 範圍 −448～512，符號擴展成 INT32 |
| DOT4SU | 四組 signed INT8×unsigned INT8 乘積之和 | rs1 signed、rs2 unsigned；範圍 −130560～129540，18-bit 和 |

所有指令沒有記憶體副作用。來源先保存，rd 可以等於 rs1／rs2。x0 讀值為零，忽略寫回；累加指令的 rd=x0 時累加來源也為零，指令仍提交一次。

## 4．RQNT8 的完整定義

```text
rs1：signed INT32 輸入 x
rs2[15:0] ：signed INT16 multiplier m
rs2[20:16]：unsigned shift s，0～31
rs2[28:21]：signed INT8 zero-point z
rs2[31:29]：忽略；產生控制字時建議填零

p = x × m                 // 精確 signed 48-bit
q = round_nearest_away(p / 2^s)
y = clamp(q + z, -128, 127)
rd = sign_extend_32(y)
```

`round_nearest_away` 表示取最近整數，恰好一半時朝遠離零方向捨入。先對乘積取絕對值；s>0 時加 2^(s−1)，再右移 s 位，最後恢復正負號。s=0 時不加捨入偏置。

例如 multiplier=1、shift=1、zero-point=0：x=3 得 2，x=−3 得 −2。若 zero-point=5，x=3 得 7。所有限制都在比例乘法、捨入及加 zero-point 之後進行。

這個控制字把比例和 shift 合併成一個來源，便於維持兩讀一寫。相同量化參數可在迴圈外準備一次。

## 5．編碼與 Decoder

所有指令使用 R-type、custom-0 opcode `0x0B`。Mask 為 `0xFE00707F`；rd、rs1、rs2 不影響功能比對。

| 指令 | funct7 | funct3 | Match |
| --- | --- | --- | --- |
| DOT4 | 0 | 000 | 0x0000000B |
| MUL16 | 0 | 001 | 0x0000100B |
| ADDSAT | 0 | 010 | 0x0000200B |
| QNT8 | 0 | 011 | 0x0000300B |
| DOT4ACC | 1 | 000 | 0x0200000B |
| MAC16 | 1 | 001 | 0x0200100B |
| ADD8SAT | 1 | 010 | 0x0200200B |
| SUB8SAT | 1 | 011 | 0x0200300B |
| RQNT8 | 1 | 100 | 0x0200400B |
| DOT2SAT | 1 | 101 | 0x0200500B |
| DOT8 | 1 | 110 | 0x0200600B |
| DOT4SU | 1 | 111 | 0x0200700B |

funct7=0 僅允許 funct3=0～3；funct7=1 允許 funct3=0～7；其餘組合非法。非法指令停止並記錄 HALT_ILLEGAL，不發出執行單元請求、不寫回、不 retire。

Decoder 輸出 `IC_CUSTOM`、`WB_CUSTOM`、`rd_write` 及 4-bit `custom_op`。內部 op 編號依上表順序為 0～11。這是專案私有擴充，標準 M／V 擴充仍未加入。

```assembly
# DOT4ACC x5,x6,x7：x5 = old(x5) + DOT4(x6,x7)
.insn r 0x0b, 0, 1, x5, x6, x7

# RQNT8 x5,x6,x7：x7 保存量化控制字
.insn r 0x0b, 4, 1, x5, x6, x7
```

## 6．CPU Datapath 與累加來源

```text
一般 custom：Decode → CUSTOM_START → CUSTOM_WAIT → CUSTOM_COMMIT → Fetch
累加 custom：Decode → CUSTOM_ACC_READ → CUSTOM_START → CUSTOM_WAIT → CUSTOM_COMMIT → Fetch
```

| 暫存器／控制 | 功能與更新時機 |
| --- | --- |
| A、B | Decode 結束時保存 rs1、rs2 |
| CustomAcc | 僅在 CUSTOM_ACC_READ 的 edge 保存舊 rd |
| RF 第二讀取地址 MUX | CUSTOM_ACC_READ 選 rd；其他狀態選 rs2 |
| CustomResult | WAIT 中 response handshake 的 edge 保存結果 |
| WB_CUSTOM | COMMIT edge 把 CustomResult 寫回 rd |
| PC／retire | 只有正常 COMMIT 時更新 PC=InstrPC+4、提交一次 |

A／B 先保存後，第二個 Register File 讀取埠可以暫時讀 rd。讀取舊 rd 的 edge、接受運算請求的 edge、保存結果的 edge、寫回的 edge 分開，避免讀到舊的中間暫存值。

兩條累加指令的三個數值來源是 rs1、rs2、old(rd)，語意明確；CustomAcc 只服務目前這條指令。

## 7．執行單元介面

| 訊號 | 相對 custom_exec 方向 | 定義 |
| --- | --- | --- |
| clk／rst | 輸入 | 核心共用 clock；高有效同步 reset |
| req_valid／req_ready | 輸入／輸出 | 上升緣同時為 1 時接受請求 |
| req_op | 輸入，4-bit enum | 0～11，依指令表順序 |
| req_a／req_b | 輸入，各 32-bit | 已保存的 rs1、rs2 |
| req_acc | 輸入，32-bit | 累加指令的舊 rd；其他指令忽略 |
| rsp_valid／rsp_ready | 輸出／輸入 | 上升緣同時為 1 時取走結果 |
| rsp_result | 輸出，32-bit | 指令結果 |

接受時鎖存 op、a、b、acc。忙碌或持有未取走結果時 req_ready=0；回應遇到 backpressure 時 valid 與結果保持不變。取走後才回 IDLE，下一筆請求在後續 edge 接受。

等待期間 CPU 不取下一條指令，也不發起資料交易。CPU 根據握手判斷完成，不以固定倒數推斷結果有效。

## 8．硬體共用與運算延遲

四個乘法器都有獨立、保留階層的 `fault_v_mul16` 實例。RTL 使用一般 signed 乘法；`use_dsp` 是 FPGA 合成提示。建置時核對實際四個 DSP48E1，不能只依 RTL 運算子數量判斷。

| 運算 | 乘法器使用方式 | 以接受 edge E0 為起點的結果有效時刻 |
| --- | --- | --- |
| DOT4／DOT4ACC／DOT4SU | 四個 lane 同時計算，經加法樹合併 | E1 後 |
| MUL16／MAC16 | 使用第 0 個乘法器 | E1 後 |
| DOT2SAT | 使用第 0、1 個乘法器 | E1 後 |
| ADD8SAT／SUB8SAT／ADDSAT／QNT8 | 使用加減、比較、移位邏輯 | E1 後 |
| DOT8 | 前四個 nibble 和後四個 nibble 分兩拍 | E2 後 |
| RQNT8 | 第一拍算比例乘積，第二拍捨入、加 zero-point、飽和 | E2 後 |

RQNT8 用兩個現有 16×16 乘法器精確計算 INT32×INT16。把 x 拆成 signed high16 與 signed low16；low16 的 bit15=1 時補回 m×65536，再於 48-bit 合併，補償低半部的 signed 解讀。

單元延遲與整條 CPU 指令 cycle 不同。於 IMEM_DELAY=1 的基準協定，一拍單元指令需要 8 cycles；DOT4ACC／MAC16 多一拍讀 rd，共 9；兩拍單元的 DOT8／RQNT8 也為 9。記憶體等待會另外增加取指時間。

## 9．Reset 與錯誤行為

Reset edge 清除 CPU 狀態、A／B、CustomAcc、CustomResult、執行單元狀態與中間結果。reset 為高時抑制握手與提交。讀舊 rd、第一拍運算、第二拍運算、有效回應或 COMMIT 前都可能被中斷；中斷的指令不得提交。

解除 reset 後從 PC=0 重新取指，不回傳 reset 前的結果。RAM 不因 CPU reset 清空，已完成的寫入不回滾；程式必須初始化自己使用的資料。

## 10．自我檢查程式與周邊

`custom_demo.mem` 放入指令 ROM，CPU 自行準備資料、執行內積／FIR／量化／飽和與新增指令邊界案例，再逐項比較預期答案。

| 周邊 | Fault-V MMIO 位址 | 用途 |
| --- | --- | --- |
| program_status | 0x20000000 | 0 未完成，1 成功，2 自我檢查失敗 |
| UART TX data／status | 0x20000100／0x20000104 | 傳送結果字串；忙碌時等待 |
| GPIO output／input | 0x20000200／0x20000204 | LED 與數位輸入 |

成功時輸出 `DSP OK\r\n`，GPIO=5，status=1，最後 EBREAK。比較失敗時 GPIO=15、status=2，RAM offset 0x7FC 保存失敗編號。只有 status=2 時該編號有效；其他硬體 fault 看 halt_cause、fault_pc、fault_addr。

PYNQ-Z2 平台以 PS FCLK0 提供 50 MHz，TX 每 bit 434 clocks，接到 PL UART Lite RX，再由 ARM／Ethernet 觀察。BTN0 只重置 Fault-V。FPGA 檔案必須以同一次建置的 bit／hwh 配對；外部 Pmod 電氣傳輸需另行驗證。

## 11．效能比較方法

保留原先六組工作負載與量測邊界，對照共用乘法器版和本版。另為八條新增指令各建一組 16 筆資料的純 RV32I／custom 成對程式。

兩種程式在相同擴充 CPU 上執行。純 RV32I 版不使用 custom 或標準 M 指令；乘法用可提早結束的 shift-and-add，packed 運算逐 lane 展開，飽和以比較與分支實作。

開始計數於 PC=0 取指請求被接受的 cycle；停止於下一次取指到 kernel_end 之前。包含 kernel 初始化、Load／Store、打包、分支與單元等待，排除 testbench 載入資料、reset、完成回報、EBREAK 與 UART。

記憶體模式為 IMEM／DMEM 延遲 1／1 和 4／7，每個程式 reset 後重跑。逐項比對全部結果，記錄 cycle、retire、Load、Store 與 custom 次數；時間以參考頻率換算。

RQNT8 的 RV32I benchmark 選用乘積能精確放進 signed INT32 的明列資料，降低基準程式複雜度；這組效能結果只代表該資料。完整 48-bit 乘積語意另以單元與 CPU 測試檢查，不據此宣稱所有量化輸入有相同加速比。

整合後資源包含 CPU、記憶體、周邊與 ARM 介接；並行版新增其他運算功能且示範 ROM 內容不同，不能把資源差值全算成單獨 DOT4 的成本。ASIC 面積與功耗需要另選元件庫與製程分析。

## 12．驗收條件

| 層級 | 要滿足的條件 |
| --- | --- |
| 數值 | 十二條指令與獨立整數參考模型一致；檢查符號、極值、截斷、lane 隔離、捨入、zero-point |
| 握手 | 輸入鎖存、忙碌不重複接受、結果 backpressure 穩定、回應取走一次 |
| CPU | 舊 rd 讀取正確；x0、rd=rs1／rs2、相依與連續指令正確；只在提交時寫回與更新 PC |
| Reset | 每種運算的所有有效運算階段可取消；重啟後不帶入舊累加值與回應 |
| 原功能 | 原 RV32I、Load／Store、UART／GPIO、錯誤與壓力回歸通過 |
| 程式 | 所有輸出逐項正確；故意破壞結果能走失敗路徑 |
| 效能 | 量測邊界一致，純 RV32I 編碼檢查，重跑一致，FSM cycle 公式與兩種延遲差值符合 |
| FPGA | 四個 DSP 結構符合設計；50 MHz setup／hold／pulse-width 及路由符合約束；警告明列 |
| 實板 | 載入新配對檔案後，UART、狀態、LED／BTN0 行為符合規格 |

## 13．檔案與操作

在交付資料夾執行：

```powershell
python .\generate.py
python .\build_extension_benchmarks.py
powershell -ExecutionPolicy Bypass -File .\run_regression.ps1
powershell -ExecutionPolicy Bypass -File .\run_custom.ps1
powershell -ExecutionPolicy Bypass -File .\run_benchmark.ps1
powershell -ExecutionPolicy Bypass -File .\run_payload.ps1
powershell -ExecutionPolicy Bypass -File .\run_build.ps1
python .\make_delivery.py
```

生成、模擬及建置不會自動下載板子。完整 RTL 在 `rtl/`；試驗程式與資料在 `programs/`；測試在 `verify/`；實際測試、效能、資源與未驗證範圍留在獨立的 `Verification_Report.md` 與 `results.csv`。

## 14．RTL 整合重點

```systemverilog
// CPU 第二讀取埠於額外狀態讀 old(rd)。A/B 已在 Decode 保存。
assign custom_accumulate = (custom_op == CUSTOM_DOT4ACC || custom_op == CUSTOM_MAC16);
assign rf_rs2_addr = (state == ST_CUSTOM_ACC_READ) ? rd_addr : rs2_addr;

always_ff @(posedge clk) begin
    if (rst) custom_acc <= 32'b0;
    else if (custom_acc_we) custom_acc <= rs2_data;
end

// FSM 的累加準備階段
// ST_DECODE: ab_we=1，累加類別選 ST_CUSTOM_ACC_READ
// ST_CUSTOM_ACC_READ: custom_acc_we=1，下一狀態 ST_CUSTOM_START
// ST_CUSTOM_START: 有效握手後才進 ST_CUSTOM_WAIT
// ST_CUSTOM_WAIT: response 握手保存 CustomResult
// ST_CUSTOM_COMMIT: WB_CUSTOM、PC+4、retire
```

完整 `custom_exec.sv` 如下，與交付 RTL 保持一致。

```systemverilog
`timescale 1ns/1ps
module custom_exec(
 input logic clk,rst,req_valid,
 output logic req_ready,
 input fault_v_pkg::custom_op_t req_op,
 input logic [31:0] req_a,req_b,req_acc,
 output logic rsp_valid,
 input logic rsp_ready,
 output logic [31:0] rsp_result
);
 import fault_v_pkg::*;
 typedef enum logic [2:0] {EU_IDLE,EU_EXEC,EU_DOT8_SECOND,EU_REQUANT,EU_RESPONSE} unit_state_t;
 unit_state_t state;
 custom_op_t op_hold;
 logic [31:0] a_hold,b_hold,acc_hold;
 logic signed [15:0] mul_a[0:3],mul_b[0:3];
 wire signed [31:0] product[0:3];
 logic signed [7:0] lane_a[0:3],lane_b[0:3];
 logic signed [3:0] nib_a[0:3],nib_b[0:3];
 logic signed [8:0] byte_sum[0:3];
 logic [31:0] packed_sat;
 logic signed [17:0] dot_sum,partial_dot;
 logic signed [32:0] pair_sum,wide_sum;
 logic signed [31:0] shifted;
 logic signed [47:0] scaled_next,scaled_hold,low_term,high_term,correction;
 logic [48:0] magnitude,rounded_magnitude,round_bias;
 logic signed [48:0] rounded_value,requant_value;
 logic signed [7:0] zero_point;
 logic [4:0] shift_count;
 integer lane_base;
 assign req_ready=!rst && state==EU_IDLE;
 assign rsp_valid=!rst && state==EU_RESPONSE;
 for(genvar k=0;k<4;k++)begin: multipliers
  (* keep_hierarchy="yes" *) fault_v_mul16 u_multiplier(.a(mul_a[k]),.b(mul_b[k]),.product(product[k]));
 end
 always_comb begin
  lane_base=(state==EU_DOT8_SECOND)?4:0;packed_sat=0;
  for(integer k=0;k<4;k++)begin
   lane_a[k]=$signed(a_hold[k*8+:8]);lane_b[k]=$signed(b_hold[k*8+:8]);
   nib_a[k]=$signed(a_hold[(k+lane_base)*4+:4]);nib_b[k]=$signed(b_hold[(k+lane_base)*4+:4]);
   mul_a[k]={{8{lane_a[k][7]}},lane_a[k]};mul_b[k]={{8{lane_b[k][7]}},lane_b[k]};
   if(op_hold==CUSTOM_DOT4SU)mul_b[k]={8'b0,b_hold[k*8+:8]};
   if(op_hold==CUSTOM_DOT8)begin
    mul_a[k]={{12{nib_a[k][3]}},nib_a[k]};mul_b[k]={{12{nib_b[k][3]}},nib_b[k]};
   end
   if(op_hold==CUSTOM_SUB8SAT)
    byte_sum[k]=$signed({lane_a[k][7],lane_a[k]})-$signed({lane_b[k][7],lane_b[k]});
   else byte_sum[k]=$signed({lane_a[k][7],lane_a[k]})+$signed({lane_b[k][7],lane_b[k]});
   if(byte_sum[k]>9'sd127)packed_sat[k*8+:8]=8'h7f;
   else if(byte_sum[k]< -9'sd128)packed_sat[k*8+:8]=8'h80;
   else packed_sat[k*8+:8]=byte_sum[k][7:0];
  end
  if(op_hold inside {CUSTOM_MUL16,CUSTOM_MAC16,CUSTOM_DOT2SAT,CUSTOM_RQNT8})begin
   mul_a[0]=$signed(a_hold[15:0]);mul_b[0]=$signed(b_hold[15:0]);
   mul_a[1]=$signed(a_hold[31:16]);
   mul_b[1]=(op_hold==CUSTOM_RQNT8)?$signed(b_hold[15:0]):$signed(b_hold[31:16]);
  end
  // Each INT8/INT4 product fits 18 bits; the 18-bit sum cannot overflow.
  dot_sum=$signed(product[0][17:0])+$signed(product[1][17:0])+$signed(product[2][17:0])+$signed(product[3][17:0]);
  pair_sum=$signed({product[0][31],product[0]})+$signed({product[1][31],product[1]});
  wide_sum=$signed({a_hold[31],a_hold})+$signed({b_hold[31],b_hold});
  shifted=$signed(a_hold) >>> b_hold[4:0];
  // Exact INT32*INT16 from signed low/high 16-bit products plus low sign correction.
  low_term={{16{product[0][31]}},product[0]};high_term={product[1],16'b0};
  correction=a_hold[15]?{{16{b_hold[15]}},b_hold[15:0],16'b0}:48'sd0;
  scaled_next=low_term+high_term+correction;
  shift_count=b_hold[20:16];zero_point=$signed(b_hold[28:21]);
  magnitude=scaled_hold[47]?-$signed({scaled_hold[47],scaled_hold}):{1'b0,scaled_hold};
  round_bias=49'd0;
  if(shift_count!=0)round_bias=49'd1 << (shift_count-1'b1);
  rounded_magnitude=(magnitude+round_bias) >> shift_count;
  rounded_value=scaled_hold[47]?-$signed(rounded_magnitude):$signed(rounded_magnitude);
  requant_value=rounded_value+$signed({{41{zero_point[7]}},zero_point});
 end
 always_ff @(posedge clk)begin
  if(rst)begin
   state<=EU_IDLE;op_hold<=CUSTOM_DOT4;a_hold<=0;b_hold<=0;acc_hold<=0;
   partial_dot<=0;scaled_hold<=0;rsp_result<=0;
  end else case(state)
   EU_IDLE:if(req_valid && req_ready)begin
    a_hold<=req_a;b_hold<=req_b;acc_hold<=req_acc;op_hold<=req_op;
    partial_dot<=0;state<=EU_EXEC;
   end
   EU_EXEC:begin
    state<=EU_RESPONSE;
    case(op_hold)
     CUSTOM_DOT4,CUSTOM_DOT4SU:rsp_result<={{14{dot_sum[17]}},dot_sum};
     CUSTOM_DOT4ACC:rsp_result<=acc_hold+{{14{dot_sum[17]}},dot_sum};
     CUSTOM_MUL16:rsp_result<=product[0];
     CUSTOM_MAC16:rsp_result<=acc_hold+product[0];
     CUSTOM_ADDSAT:begin
      if(wide_sum>33'sd2147483647)rsp_result<=32'h7fffffff;
      else if(wide_sum< -33'sd2147483648)rsp_result<=32'h80000000;
      else rsp_result<=wide_sum[31:0];
     end
     CUSTOM_QNT8:begin
      if(shifted>32'sd127)rsp_result<=32'd127;
      else if(shifted< -32'sd128)rsp_result<=32'hffffff80;
      else rsp_result<=shifted;
     end
     CUSTOM_ADD8SAT,CUSTOM_SUB8SAT:rsp_result<=packed_sat;
     CUSTOM_DOT2SAT:begin
      if(pair_sum>33'sd2147483647)rsp_result<=32'h7fffffff;
      else if(pair_sum< -33'sd2147483648)rsp_result<=32'h80000000;
      else rsp_result<=pair_sum[31:0];
     end
     CUSTOM_DOT8:begin partial_dot<=dot_sum;state<=EU_DOT8_SECOND;end
     CUSTOM_RQNT8:begin scaled_hold<=scaled_next;state<=EU_REQUANT;end
     default:rsp_result<=0;
    endcase
   end
   EU_DOT8_SECOND:begin
    rsp_result<={{14{partial_dot[17]}},partial_dot}+{{14{dot_sum[17]}},dot_sum};state<=EU_RESPONSE;
   end
   EU_REQUANT:begin
    if(requant_value>49'sd127)rsp_result<=32'd127;
    else if(requant_value< -49'sd128)rsp_result<=32'hffffff80;
    else rsp_result<=requant_value[31:0];
    state<=EU_RESPONSE;
   end
   EU_RESPONSE:if(rsp_valid && rsp_ready)state<=EU_IDLE;
   default:state<=EU_IDLE;
  endcase
 end
endmodule
(* keep_hierarchy="yes", use_dsp="yes" *)
module fault_v_mul16(input logic signed [15:0] a,b,output logic signed [31:0] product);
 assign product=a*b;
endmodule
```
