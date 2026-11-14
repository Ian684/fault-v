# Benchmark 驗收紀錄

日期：2026-10-14（Asia/Taipei），Vivado / XSim 2022.2。

| 驗收 | 結果 |
| --- | --- |
| 程式 | 六工作負載 × RV32I／custom = 12 個映像，均在 4096-word ROM 範圍內 |
| RTL 執行 | 12 映像 × 2 記憶體模式 × 2 次重複 = 48 次，全數通過 |
| 正確性 | 每個輸出 word 對固定 golden 比對，status=1、HALT_EBREAK |
| 重複性 | 每配置兩次 cycle、retire、custom、Load、Store 數相同 |
| 基準合法性 | 所有基準 binary 靜態排除 custom-0 與 M；動態 custom retire=0；kernel 禁止 M |
| 計數邊界 | fetch 數=retire 數、exact output store 數；48 筆均符合獨立 FSM cycle 公式 |
| 記憶體差值 | 12 映像均符合 Δcycles=3*instructions+6*(loads+stores) |
| 核心來源 | 16 個 RTL SHA256 與 custom_core/rtl 相同；沒有修改硬體 |

證據：logs/tb_benchmark.log、results.json、rtl_sha256.json。

```text
ALL 48 BENCHMARK RUNS PASSED; OUTPUTS AND REPEATED COUNTS VERIFIED
```

Cycle 是 RTL 執行量測，μs 為 50 MHz 換算。50 MHz 的物理時脈與資源來自已驗證的 DSP 自我檢查 overlay，保存在 hardware_reference/；本次沒有新建 bitstream、沒有把 12 個 benchmark 映像載入 Z2、沒有實板 performance counter 結果。

基準與 custom 執行在相同擴充核心，不是 RV32I-only 小核心與 custom 核心的 PPA 比較。本次資源參考值未因不同 ROM 重新綜合，所以不填入不存在的各版本硬體資源差值。

FIR8_PACKED 排除預打包成本；FIR8_RAW 計入 CPU 視窗打包，但不包含資料從外部主機進入 RAM 的時間。兩者都屬此處明確定義的 kernel 範圍，不能用 PACKED 加速比宣稱完整系統端到端效能。

Early-exit 軟體乘法與條件分支依賴輸入資料。結果不代表最佳 RV32I 編譯器輸出、不代表其他資料集、Cache／Pipeline 核心或所有 clock／memory 配置；未量測 ASIC 功耗與面積。
