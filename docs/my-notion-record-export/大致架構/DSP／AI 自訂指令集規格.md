# DSP／AI 自訂指令集規格

## 1．設計目的

在既有 32-bit、多周期、依序執行的 RV32I 核心中加入自訂執行單元，加速整數內積、濾波、飽和與量化運算。此擴充稱為 **XFaultVDSP v1.0**，是 Fault-V 專案自行定義的非標準擴充名稱。

第一版選定四條指令：DOT4、MUL16、ADDSAT、QNT8。所有指令讀取 rs1、rs2，寫入 rd；沿用兩讀一寫 Register File，沒有隱藏累加器，也不讀取 rd 的舊值。

| 項目 | 規格 |
| --- | --- |
| 基礎核心 | 保留 RV32I、多周期 FSM、單一 clock、無 Pipeline |
| 指令長度 | 32-bit；正常完成後 PC = InstrPC + 4 |
| 資料格式 | INT8、INT16、INT32；signed 均採二補數 |
| 來源／目的 | 兩個 32-bit 來源暫存器、一個 32-bit 目的暫存器 |
| x0 | 讀取為 0，寫入忽略；仍須正常完成指令與更新 PC |
| 記憶體副作用 | 自訂指令本身不讀寫記憶體或 MMIO |
| 溢位處理 | 每條指令單獨定義；不新增 overflow flag 或 CSR |
| 非法編碼 | 沿用 HALT_ILLEGAL；不得寫回或當成 NOP |
| 標準擴充 | 不因此宣稱支援 RISC-V M、V 或任何標準 DSP 擴充 |

## 2．工作負載與指令選擇

| 工作負載 | 固定規模／數學定義 | 使用的自訂指令 |
| --- | --- | --- |
| INT8 向量內積 | N = 64；sum(a[i] × b[i])；輸出 signed INT32 | DOT4，跨組累加用一般 ADD |
| INT8 八抽頭 FIR | 23 個輸入、8 個係數、16 個輸出；y[n] = sum(x[n+k] × h[k])，k = 0～7 | 每個輸出用兩次 DOT4，再用 ADD |
| FIR 輸出量化 | 對每個 FIR 輸出做 signed 算術右移 3，再限制到 -128～127 | QNT8 |
| INT16 八抽頭 FIR | 23 個 INT16 輸入、8 個係數、16 個 INT32 輸出 | MUL16，累加用 ADD |
| INT32 飽和加法 | 64 對 INT32 數值，涵蓋正／負溢位及一般加法 | ADDSAT |

FIR 係數依上述公式順序存放。若使用傳統 y[n] = sum(h[k] × x[n-k]) 的描述，須自行反轉視窗／係數順序，不能混用兩種定義。

量化採 zero-point = 0、不做四捨五入的固定右移與飽和；不是完整 AI 框架的 requantization，也沒有額外比例乘法。

## 3．四條指令的精確語意

以下 R[x] 表示暫存器 x 的 32-bit 資料；S8、S16、S32 表示把對應位寬解讀成 signed。

| 指令 | 輸入 | 精確計算 | 32-bit 寫回 |
| --- | --- | --- | --- |
| DOT4 rd, rs1, rs2 | 各有四個 packed signed INT8 | sum(S8(R[rs1][8i+7:8i]) × S8(R[rs2][8i+7:8i]))，i = 0～3 | 精確內積，以二補數 INT32 寫回 |
| MUL16 rd, rs1, rs2 | 各取低 16-bit 作 signed INT16 | S16(R[rs1][15:0]) × S16(R[rs2][15:0]) | 精確 signed INT32 乘積；忽略兩來源高 16-bit |
| ADDSAT rd, rs1, rs2 | 兩個 signed INT32 | 用 signed 33-bit 算 a + b，限制到 [-2147483648, 2147483647] | 範圍內為精確加法；溢位時寫入對應上下限 |
| QNT8 rd, rs1, rs2 | rs1 為 signed INT32；shift = rs2[4:0] | t = S32(R[rs1]) 算術右移 shift，再限制到 [-128,127] | 把 signed INT8 結果符號擴展成 INT32 |

QNT8 的 rs2[31:5] 一律忽略，shift 只會是 0～31。算術右移向負無限方向取整，例如 -3 右移 1 得到 -2。結果不是 packed 四個 byte；若要存成 INT8，使用 SB 寫入低 byte。

### Packed INT8 的排列

```
rs1[31:24]  rs1[23:16]  rs1[15:8]  rs1[7:0]
    a3          a2          a1         a0

DOT4 = a0*b0 + a1*b1 + a2*b2 + a3*b3
```

例：rs1 = 0x04030201 表示 [1,2,3,4]；rs2 = 0x08070605 表示 [5,6,7,8]，結果為 70，即 0x00000046。

從 little-endian 記憶體以對齊 LW 載入時，最低地址的 byte 對應 lane 0。自訂指令不會自動完成記憶體載入或資料打包。

### 中間位寬

- signed INT8 乘積使用 signed 16-bit；四個乘積總和範圍為 -65024～65536，累加至少需要 signed 18-bit，再符號擴展成 32-bit。
- signed INT16 乘積使用 signed 32-bit，不需截斷；例如 -32768 × -32768 = 1073741824。
- ADDSAT 必須先保留 33-bit 加法結果，不能先做 32-bit wrap 再判斷是否飽和。
- QNT8 必須先以 signed INT32 右移，再比較上下限；不可先取低 8-bit。
- 多次 DOT4 或 MUL16 的總和若用一般 ADD 累加，仍遵守 32-bit 截斷；自訂指令不會自動保護整個迴圈的累加溢位。

## 4．為什麼不先加入 MAC 或 DOT4ACC

`rd = old_rd + rs1 × rs2` 同時需要 rs1、rs2、old_rd 三個值。目前 Register File 只有兩個讀取埠，這種定義需要額外讀取階段、第三個讀取埠，或另設累加器。

第一版使用兩條指令完成乘加：

```
DOT4 temporary, packed_a, packed_b
ADD accumulator, accumulator, temporary
```

這讓資料來源、暫存器重疊與寫回規則保持清楚。MAC／DOT4ACC 是後续可評估的擴充。

## 5．指令格式與編碼

使用 R-type 欄位配置及 custom-0 opcode `0001011`（0x0B）。RISC-V 將 custom-0～custom-3 指定為自訂擴充空間；本專案自行定義其內部 funct 欄位。[RISC-V 官方 opcode map](https://docs.riscv.org/reference/isa/v20260120/unpriv/rv-32-64g.html)

```
31           25 24       20 19       15 14    12 11       7 6         0
+--------------+-----------+-----------+--------+----------+-----------+
| funct7 = 0   |    rs2    |    rs1    | funct3 |    rd    | 0001011   |
+--------------+-----------+-----------+--------+----------+-----------+
```

| 指令 | funct7 | funct3 | opcode | Match | Mask |
| --- | --- | --- | --- | --- | --- |
| DOT4 | 0000000 | 000 | 0001011 | 0x0000000B | 0xFE00707F |
| MUL16 | 0000000 | 001 | 0001011 | 0x0000100B | 0xFE00707F |
| ADDSAT | 0000000 | 010 | 0001011 | 0x0000200B | 0xFE00707F |
| QNT8 | 0000000 | 011 | 0001011 | 0x0000300B | 0xFE00707F |

解碼條件：`(instruction & mask) == match`。此版本中其他 funct7 或 funct3 = 100～111 都是非法指令；保留給未來的欄位，不能先接受為合法。

以 rd=x5、rs1=x6、rs2=x7 為例：

| 指令 | 32-bit machine word |
| --- | --- |
| DOT4 x5,x6,x7 | 0x0073028B |
| MUL16 x5,x6,x7 | 0x0073128B |
| ADDSAT x5,x6,x7 | 0x0073228B |
| QNT8 x5,x6,x7 | 0x0073328B |

## 6．Assembly 寫法

工具鏈尚未增加自訂 mnemonic 時，使用 GNU assembler 的 `.insn r opcode, funct3, funct7, rd, rs1, rs2`。[GNU assembler 官方文件](https://sourceware.org/binutils/docs/as/RISC_002dV_002dFormats.html)

```nasm
# DOT4 x5,x6,x7
.insn r 0x0b, 0, 0, x5, x6, x7

# MUL16 x5,x6,x7
.insn r 0x0b, 1, 0, x5, x6, x7

# ADDSAT x5,x6,x7
.insn r 0x0b, 2, 0, x5, x6, x7

# QNT8 x5,x6,x7：x7[4:0] 保存移位量
.insn r 0x0b, 3, 0, x5, x6, x7
```

自製 Python 程式生成器可直接使用 `encode(op, rd, rs1, rs2)` 產生 machine word。`.word` 也可放入固定編碼，但必須留意目的與來源暫存器已寫死在 word 中。既有 CPU 在尚未整合 Decoder 與執行單元前，執行這些 word 會進入非法指令停止。

## 7．CPU 與自訂執行單元的連接規則

```
IR → Decoder → custom_op
                   │
RegFile → A、B ─────┴→ Custom Execution Unit → CustomResult
                                                  │
                                                WB MUX → rd
FSM：Decode → CUSTOM_START → CUSTOM_WAIT → CUSTOM_COMMIT → Fetch
```

| 訊號 | 方向：以執行單元為基準 | 定義 |
| --- | --- | --- |
| clk / rst | 輸入 | 與核心同一 clock、高有效同步 reset |
| req_valid | 輸入 | CPU 提供有效運算請求 |
| req_ready | 輸出 | 單元能接受請求 |
| req_op | 輸入，2-bit | 00 DOT4、01 MUL16、10 ADDSAT、11 QNT8 |
| req_a / req_b | 輸入，各 32-bit | Decode 保存的 A、B |
| rsp_valid | 輸出 | 有可取走的運算結果 |
| rsp_ready | 輸入 | CPU 願意接收結果 |
| rsp_result | 輸出，32-bit | 指令規定的結果 |

請求只在 `req_valid && req_ready` 的 clock edge 接受一次。等待期間 CPU 保持請求內容，已接受後不再重複發送。單元在收到請求時鎖存輸入，最多一筆未完成運算。

回應只在 `rsp_valid && rsp_ready` 的 edge 取走；如果 CPU 還沒取走，rsp_valid 與結果必須保持穩定。CPU 在該 edge 保存 CustomResult，下一個 CUSTOM_COMMIT 才寫回 rd、更新 PC 並產生一次 retire。

Reset 丟棄未完成請求與待取回應；req_ready 回到可接受狀態、rsp_valid 清為 0。解除 reset 後不得寫回 reset 前的舊結果。自訂運算等待期間不啟動新的取指、記憶體交易或其他指令。

rd 可等於 rs1／rs2；兩個來源必須在寫回前已保存，因此別名不會改變本次輸入。無論 rd 是否為 x0，PC、retire 與執行流程都正常完成。

### 第一版硬體配置基準

優先使用一個共用 signed 16×16 乘法器。MUL16 使用一次；DOT4 把每個 INT8 符號擴展後依序計算四個 lane，累加到 signed 18-bit 暫存器。ADDSAT 使用 33-bit 加法與限制邏輯；QNT8 使用算術移位及限制邏輯。

ISA 不保證固定 cycle 數；硬體可能因輸出暫存或時序需求增加 cycle。多周期 FSM 必須等待握手完成，不能假設結果下一拍必定有效。

| 既有模組 | 整合時的改動 |
| --- | --- |
| Decoder | 辨認四種 custom-0 編碼，輸出 IC_CUSTOM／custom_op |
| Register File | 維持兩讀一寫，不增加第三個讀取埠 |
| A／B | Decode 保存來源，供執行單元使用 |
| CustomResult | 新增 32-bit 結果暫存器 |
| Writeback MUX | 新增 WB_CUSTOM；現有 2-bit 選擇共有四種可用來源 |
| FSM | 新增 START／WAIT／COMMIT；原 4-bit 狀態編碼已有 15 種，加入三種後須擴為至少 5-bit |
| ALU／imm_gen | 維持既有語意；自訂指令不使用一般立即數 |
| PC／retire | 只在自訂指令正常提交時更新一次 |

FPGA 可以讓工具映射到 DSP slice；ASIC 則需用所選元件庫實作。CPU 公用 RTL 不應依賴僅有 FPGA 可用的乘法器 primitive。

## 8．固定測試資料與預期答案

完整輸入保存在 `benchmark_vectors.json`。DOT64 的資料由 `a[i] = ((37i+11) mod 256)-128`、`b[i] = ((19i+7) mod 256)-128` 產生，i=0～63。預期內積：60256。

INT8 FIR 輸入：`x[i] = ((29i+5) mod 256)-128`，i=0～22；係數 `[3,-2,1,4,-4,2,-1,3]`。

```
FIR8 INT32 輸出：
[-129,45,-549,-119,-457,741,-109,-191,
 495,-99,75,-519,-89,-427,771,-79]

QNT8，shift=3：
[-17,5,-69,-15,-58,92,-14,-24,
 61,-13,9,-65,-12,-54,96,-10]
```

INT16 FIR 與 SATADD64 的完整輸入、預期答案也保存在同一 JSON；選定的 FIR16 資料之累加結果均在 signed INT32 範圍內。

## 9．Benchmark 的公平比較規則

RV32I 基準程式不能使用 MUL、DIV 或任何自訂指令；INT8／INT16 乘法採軟體 shift-and-add，正確處理最小負數的絕對值。飽和與量化以既有加法、比較、分支和算術移位完成。

內積 N=64 可以用對齊 LW 取得每四個 byte。FIR 視窗每次前進 1 byte，不能假設每個視窗都能直接使用兩次對齊 LW；核心不支援未對齊 word 存取。可預先打包對齊視窗，或在 CPU 用 byte 載入／移位／OR 組合。

| 比較項目 | 計算規則 |
| --- | --- |
| Kernel 比較 | 兩版本使用相同預先打包資料；基準版從相同 word 擷取 lane，將已排除的打包成本明列 |
| End-to-end 比較 | 從相同原始陣列開始，CPU 做的載入、打包、量化及輸出存取都計入 |
| 量測區間 | 固定起訖標記，排除 UART 印字；兩版本使用相同規則 |
| 正確性 | 完整輸出陣列逐項一致，不能只看最終 LED |
| Cycle | 以 testbench 外部 clock 計數，不依賴目前未支援的標準 cycle CSR |
| 指令數 | 由 retire 訊號計算，與 cycle 分別記錄 |
| 時間 | execution_time = cycles / clock_frequency |
| 加速比 | baseline_time / custom_time；只有相同頻率時才可直接用 cycle 比例 |
| 硬體成本 | FPGA LUT／FF／DSP／BRAM、通過時序的 clock；ASIC 之後再比較面積與時序 |

ADDSAT 或 QNT8 的多周期開銷可能大於簡單軟體序列；不預設每条指令都會加速。是否保留、並行化或縮短延遲，應由實測工作負載的收益決定。

## 10．驗收標準

| 層級 | 必须符合的條件 |
| --- | --- |
| 指令規格 | 編碼、來源／目的、signed、位寬、飽和、移位與 x0 行為沒有未定義項目 |
| 參考模型 | directed 邊界值與獨立 oracle 一致；編解碼、非法欄位、暫存器別名可檢查 |
| 執行單元 RTL | 四條指令與模型一致；包含 backpressure、連續請求與運算中 reset |
| CPU 整合 | 每次只提交一次；不提前寫回；x0／PC／retire／非法指令正確；原 RV32I 回歸持續通過 |
| 程式驗證 | DOT64、FIR8＋量化、FIR16、SATADD64 的全部輸出吻合固定答案 |
| FPGA | 資源報告、時序與實板程式結果可重現 |
| 效能 | 保留真實 cycle、clock、時間與硬體成本；沒有實測就不填加速倍數 |

Python 模型驗證只代表語意與資料檢查，不等於執行單元 RTL、CPU、FPGA 或 ASIC 已驗收。硬體實作需逐層符合上表。

## 11．檔案與操作

| 檔案 | 用途 |
| --- | --- |
| [reference.py](http://reference.py/) | 指令語意、encoder／decoder、暫存器提交與 shift/add 基準模型 |
| verify_spec.py | directed／隨機 oracle、完整寄存器組合、非法編碼與工作負載核對 |
| directed_vectors.json | RTL 可沿用的邊界輸入与預期 32-bit 結果 |
| encoding.json | funct、match、mask 與機器碼示例 |
| benchmark_vectors.json | 完整工作負載輸入、預期答案；cycle／speedup 為 null |
| Specification_Verification.md | 實際模型執行紀錄；與技術筆記分開 |

在本資料夾執行：

```powershell
python .\verify_spec.py
```

這些 Python 程式不修改已驗證的 CPU RTL，也不會下載或重置 FPGA。

## 12．可以延伸的方向

| 延伸方向 | 可增加的功能 | 適合的應用／驗證 | 需要增加的設計 | 建議順序 |
| --- | --- | --- | --- | --- |
| 共用乘法器→並行乘法器 | DOT4 一次計算四個乘積 | 相同內積／FIR 的 cycle、頻率與面積比較 | 四乘法器、加法樹，可能需額外暫存級 | 先完成共用版再比較 |
| MAC／DOT4ACC | 乘加或內積直接累加 | FIR、全連接層 | 明確第三來源；多拍讀取／第三讀埠／累加器擇一，以及溢位規則 | 第二階段 |
| Packed 飽和運算 | 四個 INT8 加減／min／max | 音訊限制、逐元素 AI 運算 | 每 lane 獨立飽和，禁止 lane 間 carry 串接 | 第二階段 |
| 更完整的量化 | 比例乘法、rounding、zero-point | 小型量化模型 | 中間位寬、捨入規則、正負邊界與框架 golden model | 第二階段 |
| INT16 雙 lane 內積 | 一次運算兩組 INT16 | 高精度固定點 DSP | 至少 33-bit 內積、寫回截斷／飽和或雙暫存器規則 | 第二階段 |
| INT4／混合 signed 格式 | 八 lane INT4、INT8×UINT8 | 更低位寬模型 | 格式編碼、lane 擷取、符號及 zero-point 定義 | 工作負載需要時 |
| 卷積／小型全連接層 | 以 DOT4 做多個神經元或卷積視窗 | 軟體端完整推論 kernel | 資料布局、視窗打包、bias／activation 與 golden outputs | 基本 benchmark 完成後 |
| FIR／IIR／FFT 固定點 | 增加複數乘法、飽和與縮放 | 感測、音訊、頻域運算 | 固定點格式、穩定性、精度與累加溢位分析 | DSP 專題延伸 |
| Scratchpad／DMA | 降低搬資料與 CPU 載入成本 | 大量向量與串流 | 匯流排仲裁、握手、邊界、reset、資料一致性 | 算力瓶頸確認後 |
| 流水化或獨立加速器 | 允許多筆運算重疊 | 高吞吐量串流 | backpressure、交易標籤、結果順序及新的控制策略 | 較後階段 |
| ASIC PPA 比較 | 比較不同單元與資料寬度 | 同工作負載的面積／速度／功耗取捨 | 選定 PDK、元件庫、時序約束；功耗需合理 activity | 進入 ASIC 流程時 |

優先延伸共用版與並行 DOT4 的比較，能直接展示軟體、微架構與硬體成本的取捨。以上都是未來候選，沒有自動納入 XFaultVDSP v1.0 的編碼與驗收範圍。