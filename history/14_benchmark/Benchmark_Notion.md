# Fault-V：RV32I 與 DSP／AI 自訂指令效能比較

## 1．比較目的與範圍

使用相同的多周期 Fault-V 核心、相同資料與記憶體配置，比較純 RV32I 軟體運算與四條自訂指令。兩種程式都在同一個具備自訂單元的 CPU RTL 上執行；RV32I 版完全不使用自訂指令或標準 M 的乘除法。

Cycle 與退休指令數由 XSim 中的實際 RTL 執行量測。時間以 50 MHz 換算，50 MHz 取自相同核心既有 FPGA 平台的時序與實板 clock 驗證；不是把本次 benchmark 放到 Z2 上的秒錶或硬體計數器量測。

## 2．工作負載

| 名稱 | 定義 | 比較範圍 |
| --- | --- | --- |
| DOT64 | 兩組 64 個 signed INT8 內積；答案 60256 | 同一份連續 byte 陣列；RV32I 每對 LB＋軟體乘法，custom 每四對 LW＋DOT4 |
| FIR8_RAW | signed INT8 八抽頭 FIR，23 個輸入、16 個 INT32 輸出 | 原始 byte 資料；custom 的 LBU／移位／OR 視窗打包也計入 |
| FIR8_PACKED | 相同 FIR 運算，輸入視窗預先打包為兩個對齊 word | 僅 kernel；兩版讀相同預打包資料，排除產生視窗的前處理成本 |
| FIR16 | signed INT16 八抽頭 FIR、16 個 INT32 輸出 | 相同 halfword 陣列；MUL16 對比軟體乘法 |
| QNT16 | 對 16 個 FIR8 結果算術右移 3，再限制到 INT8 範圍 | 同樣從 INT32 陣列讀取，寫入符號擴展 INT32 結果 |
| SATADD64 | 64 對 signed INT32 的飽和加法 | 同一份陣列，包含一般加法與正／負溢位 |

FIR 定義為 y[n] = sum(x[n+k] × h[k])，k=0～7，n=0～15。完整資料在 programs/benchmark_vectors.json；記憶體初始化在 programs/inputs.mem。

FIR 的係數在量測區間內載入一次，八個 tap 在程式中展開，外層輸出迴圈仍於 CPU 執行。兩版都避免每個輸出重新從 RAM 載入所有係數。

## 3．RV32I 軟體基準

| 功能 | 軟體實作 |
| --- | --- |
| Signed 乘法 | 先判斷符號、對 INT8／INT16 來源取絕對值，以 shift-and-add 計算，乘數為 0 時提早結束，再恢復符號 |
| 飽和加法 | 一般 ADD，再以 XOR／signed branch 判斷溢位，選 INT32 上下限 |
| INT8 量化 | SRA、兩個界限比較與必要的限制值寫入 |
| 函式呼叫成本 | 以上運算 inline 展開，不額外加入 JAL／JALR 呼叫與返回開銷 |

這是可讀、可重現的手寫基準，不宣稱是最佳化到極限的 RV32I 實作。Signed 乘法的 early-exit 路徑和加減／限制分支會受資料影響，因此加速比是這份資料與這個實作的結果，不是指令的固定通用加速倍數。

## 4．量測邊界

1. 資料在 testbench 載入 RAM，reset 與此步驟不計入。
2. 第一個 PC=0 的取指請求被接受的 cycle 開始計數，包含 kernel 的指標、係數與迴圈初始化。
3. 完成最後一條 kernel 指令的 cycle 仍計入。
4. 下一次取指到 kernel_end 標記時停止，該次取指與標記指令不計入。
5. 之後的成功狀態寫入、EBREAK 與所有 testbench 比對排除。

Kernel 的載入、輸出 Store、分支、資料打包與 custom 等待全部計入。程式不輸出 UART，避免串列通訊時間影響比較。量測不需要 CPU 支援標準 cycle／instret CSR。

每個程式都核對完整輸出陣列、custom 提交次數、輸出 Store 次數及正常 EBREAK；每個配置重置後執行兩次，cycle、退休指令與資料交易數應完全一致。

## 5．記憶體配置

| 模式 | IMEM RESPONSE_DELAY | DMEM RESPONSE_DELAY | 用途 |
| --- | ---: | ---: | --- |
| 0 | 1 | 1 | 目前 SoC 基準參數 |
| 1 | 4 | 7 | 檢查等待較長時的收益與量測一致性 |

參數不等於一次完整存取的 CPU cycle 數，還有 request／response 與 FSM 階段。兩版在同一模式比較，不跨模式直接計算加速比。

## 6．模式 0 的結果

下表的時間都是 cycle / 50 MHz 換算值。

| 工作負載 | RV32I cycles | Custom cycles | RV32I 指令數 | Custom 指令數 | RV32I μs | Custom μs | 加速比 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DOT64 | 21,671 | 1,033 | 3,526 | 137 | 433.42 | 20.66 | 20.98× |
| FIR8_RAW | 20,206 | 4,046 | 3,269 | 553 | 404.12 | 80.92 | 4.99× |
| FIR8_PACKED | 20,782 | 1,550 | 3,429 | 201 | 415.64 | 31.00 | 13.41× |
| FIR16 | 50,518 | 3,818 | 8,321 | 495 | 1010.36 | 76.36 | 13.23× |
| QNT16 | 1,216 | 864 | 184 | 120 | 24.32 | 17.28 | 1.41× |
| SATADD64 | 6,614 | 4,342 | 985 | 585 | 132.28 | 86.84 | 1.52× |

## 7．模式 1 的結果

| 工作負載 | RV32I cycles | Custom cycles | RV32I 指令數 | Custom 指令數 | RV32I μs | Custom μs | 加速比 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| DOT64 | 33,023 | 1,642 | 3,526 | 137 | 660.46 | 32.84 | 20.11× |
| FIR8_RAW | 30,925 | 6,581 | 3,269 | 553 | 618.50 | 131.62 | 4.70× |
| FIR8_PACKED | 31,405 | 2,453 | 3,429 | 201 | 628.10 | 49.06 | 12.80× |
| FIR16 | 76,393 | 6,215 | 8,321 | 495 | 1527.86 | 124.30 | 12.29× |
| QNT16 | 1,960 | 1,416 | 184 | 120 | 39.20 | 28.32 | 1.38× |
| SATADD64 | 10,721 | 7,249 | 985 | 585 | 214.42 | 144.98 | 1.48× |

## 8．如何解讀

- DOT64 和 FIR16 的收益較大，因為一條乘法／內積指令取代多個位元迴圈與分支。
- FIR8_RAW 包含 CPU 實際打包成本，比 FIR8_PACKED 更接近從原始資料開始的 kernel 使用情境。
- 模式 0 下，custom FIR8_RAW 為 4046 cycles，預打包版為 1550 cycles；減少的 2496 cycles 不代表前處理免費，而是打包移到量測範圍外。
- RV32I 的預打包 FIR 需要移位擷取 signed lane，雖然少讀 RAM，仍可能比直接 LB 稍慢；不能把 RAW／PACKED 當成相同端到端成本。
- QNT8 與 ADDSAT 的收益較小：本來的 RV32I 序列較短，Load／Store、迴圈與自訂握手占比較高。
- 記憶體等待增加後，加速比會改變。不能只以 DOT4 的四個 lane 推論一定四倍，也不能把 FPGA 軟體跑測試的秒數當成 CPU 執行時間。

## 9．公式與一致性檢查

```text
execution_time = cycles / clock_frequency
speedup = baseline_time / custom_time
同頻率時：speedup = rv32i_cycles / custom_cycles
```

依目前 FSM，基礎 ALU／Branch／Jump 的每次執行為 IMEM_DELAY+5 cycles；Load 再加 DMEM_DELAY+3，Store 再加 DMEM_DELAY+2。DOT4 比基礎指令再多 5 cycles，其餘三種 custom 多 2 cycles。

```text
C = (IMEM_DELAY+5)*退休指令數
  + (DMEM_DELAY+3)*Load 交易數
  + (DMEM_DELAY+2)*Store 交易數
  + custom 額外執行週期
```

這個公式用來獨立核對計數器邊界，不用來替代 RTL 量測。兩模式的差值還必須符合：

```text
C_mode1 - C_mode0 = 3*退休指令數 + 6*(Loads+Stores)
```

## 10．頻率與硬體資源

| 項目 | 相同核心既有 FPGA 平台的參考值 |
| --- | --- |
| 板卡／時脈 | PYNQ-Z2，50 MHz |
| LUT／Registers | 2760／2697 |
| BRAM／DSP | 8 BRAM tiles／1 DSP |
| Setup／Hold slack | WNS 7.756 ns／WHS 0.064 ns |
| ROM 映像 | 前一階段的 DSP 自我檢查程式，不是本次 12 個 benchmark 映像 |

兩種程式使用相同具備 custom unit 的 RTL，因此本次沒有比較「拆掉 custom unit 的較小 CPU」與「擴充 CPU」的硬體成本。上表是已有綜合／實板證據的參考平台，不是兩種新程式映像各自重新綜合後的資源結果；ROM 內容與重新佈線可能影響資源與時序。

hardware_reference/ 保留該平台的報告與實板 clock 證據。ASIC 面積、頻率與功耗需要指定製程後另行分析，不能由 FPGA LUT／DSP 數直接代換。

## 11．檔案與執行

在 outputs/benchmark 資料夾執行：

```powershell
python .\build_benchmarks.py
powershell -ExecutionPolicy Bypass -File .\run_benchmark.ps1
python .\make_results.py
```

| 檔案 | 用途 |
| --- | --- |
| rtl/ | 與已驗證自訂 CPU 相同的 16 個 RTL 檔 |
| programs/*.S／*.mem | 六個工作負載、各兩種版本的 Assembly 與機器碼 |
| programs/inputs.mem | 所有測試共用的原始資料／預打包資料 |
| programs/manifest.json | 量測結束位址、預期 custom 數與完整輸出 |
| verify/tb_benchmark.sv | Cycle／retire／資料交易量測與功能檢查 |
| logs/tb_benchmark.log | 原始 RTL 量測輸出 |
| results.csv／results.json | 完整數值、重複測量與比較資料 |
| hardware_reference/ | 前一平台的頻率、資源與實板證據，與 benchmark 量測分開 |
| Verification_Report.md | 實際驗證紀錄與限制 |

本套腳本不重新下載 FPGA。本次結果是 RTL cycle benchmark；若要新增實板效能量測，需要能讀到量測計數的硬體介面，並載入對應 benchmark 映像。

## 12．後續延伸的選擇

先以這份數據作為共用乘法器版本的基準，再比較四乘法器並行 DOT4。也應優先處理 FIR 視窗的資料排列與打包，而不是只增加運算單元。每項延伸都需保留相同資料、量測邊界、完整答案與硬體成本，才能判斷收益來自指令、資料搬移或前處理。
