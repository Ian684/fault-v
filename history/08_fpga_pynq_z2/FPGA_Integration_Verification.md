# Fault-V FPGA 整合驗證紀錄

驗證日期：2026-10-10。工具：Vivado／XSim 2022.2，Windows。目標：PYNQ-Z2，`xc7z020clg400-1`。

**結果：RTL 回歸、板卡外層模擬、綜合、放置、繞線、時序及 bitstream 產生通過。尚未連接實板配置或觀察 LED。保留一項 ZPS7-1 平台 warning，不能宣稱獨立上電開機已驗證。**

## 1．實際功能驗證

| 項目 | 結果 | 證據 |
| --- | --- | --- |
| ISA／程式 | 1372 次全部通過；兩種等待模式各 40/40 指令名稱覆蓋 | `logs/verification_results.log` |
| SoC 程式 | 12 次通過 | `logs/soc_results.log` |
| 記憶體端點 | 16 筆交易通過 | `logs/endpoint_results.log` |
| Reset 外層 | 60 項檢查通過；HOLD_BITS＝4 | `logs/tb_reset.log` |
| FPGA Top | 上電及 BTN0 重跑，共兩次通過；使用 MMCM／BUFG 的 UNISIM 模型 | `logs/tb_fpga_top.log` |

兩次 FPGA Top 都得到：175 次 retire、33 筆資料請求、status＝1、halt＝EBREAK（9）、停止 PC＝0xCC、LED＝0110。測試另外檢查 RAM 的 Fibonacci 結果、subword 寫入、函式結果及 stack 最後一個 word。

Top 模擬直接量測核心 clock 週期為 40 ns；未把實際 MMCM 替換為理想 25 MHz clock。模擬使用短版 reset delay；實作使用預設 18-bit counter。

## 2．實際 FPGA 建置

| 項目 | 結果 | 證據 |
| --- | --- | --- |
| Synthesis | 成功；有可重新開啟的 DCP | `logs/build.log`、`build/fault_v_synth.dcp` |
| Placement／Routing | 成功；2758/2758 可繞線 nets 全部完成，0 routing errors | `logs/route_status.rpt` |
| Routed checkpoint | 成功產生並重新開啟核對 | `build/fault_v_routed.dcp`、`logs/audit.log` |
| Bitstream | 成功，4,045,676 bytes | `build/fault_v_fpga_top.bit` |
| Black boxes／Latches | 0／0 | `logs/audit.log`、`logs/route_utilization.rpt` |
| Methodology | 0 violations | `logs/methodology.rpt` |
| DRC | 0 Error、0 Critical Warning；1 Warning：ZPS7-1 | `logs/drc.rpt` |
| 實板 | 未執行 | 無板上測試紀錄 |

沒有把 DRC 的嚴重程度降級，也沒有以 false path 排除 CPU 內部資料路徑。

## 3．繞線後資源

| 資源 | 使用 | 可用 | 使用率 |
| --- | ---: | ---: | ---: |
| LUT | 1644 | 53200 | 3.09% |
| FF | 1416 | 106400 | 1.33% |
| RAMB36 | 8 | 140 | 5.71% |
| DSP | 0 | 220 | 0% |
| BUFG | 2 | 32 | 6.25% |
| MMCM | 1 | 4 | 25% |

指令記憶體及資料記憶體各映射為 4 個 RAMB36。來源：`logs/route_utilization.rpt`、`logs/route_hierarchy.rpt`。這些是 FPGA 元件數量，不能換算成 ASIC 面積或閘數。

## 4．繞線後時序

| 指標 | 結果 |
| --- | ---: |
| 核心 clock | 25.000 MHz／40.000 ns |
| 板上輸入 clock | 125.000 MHz／8.000 ns |
| WNS | +24.314 ns |
| TNS／Setup failing endpoints | 0 ns／0 |
| WHS | +0.056 ns |
| THS／Hold failing endpoints | 0 ns／0 |
| WPWS | +2.000 ns |
| Pulse-width failing endpoints | 0 |
| 無 clock 的內部端點 | 0 |
| 未約束的內部端點 | 0 |
| 未連到來源的 generated clock | 0 |
| 組合／latch loops | 0／0 |

`logs/route_timing.rpt` 回報 `All user specified timing constraints are met.`；`logs/clocks.rpt` 確認 MMCM 衍生時脈。

外部 BTN0 沒有同步 input delay，四個 LED 沒有同步 output delay；五個端口皆有文件中說明的外部 false-path 約束。這不是意外漏掉的 CPU 內部端點。沒有在本次驗證探索最大工作頻率。

## 5．修改與警告

| 項目 | 處理／限制 |
| --- | --- |
| 第一輪綜合崩潰 | Vivado 最佳化階段出現 EXCEPTION_ACCESS_VIOLATION。保存於 `logs/first_attempt_synthesis.log`；不列為通過 |
| FPGA 記憶體結構 | 將無 reset 的 RAM clocked read 與 status／reset 回應分離，加入 block RAM 屬性；修改後完整回歸通過 |
| BRAM 非同步控制警告 REQP-1839 | 原版 reset 直接進入 BRAM enable；改為獨立 button／lock 同步鏈與同步 rst 輸出，最終報告已無此警告 |
| LUTAR-1 reset 毛刺警告 | 原先兩個非同步來源經 LUT 合併；改為兩組同步鏈，最終 Methodology 0 violations |
| ZPS7-1 | 仍保留：設計未加入 PS7，工具要求 PS7 以提供正確預設配置。未將此 warning 當作已完成的上電／平台整合 |
| 其他綜合 warning | 主要是未使用的 imm_gen opcode bits、load 中間位元裁剪、未使用 debug／trace 輸出裁剪；功能測試與結構核對通過 |

此設計以 PL 為範圍；實板必須確認配置可用、PHY 125 MHz clock 沒有被拉入 reset，以及所採開機模式的 Zynq 狀態。若要由 PYNQ Linux 使用 overlay 或支援獨立上電啟動，仍需補 PS 設定／初始化並實測。

## 6．證據範圍

已驗證的是目前 RTL、初始化影像、Z2 裝置及 XDC 約束組合。除了 `fault_v_memory.sv`，其餘 12 個核心／SoC RTL 與前一套驗證版本相同；新增三個 board RTL。

沒有進行 post-route timing simulation、實板量測、長時間板上壓力測試、UART／GPIO 周邊測試或 ASIC 簽核。本次時序證據是 Vivado 的 routed static timing analysis。

可重現命令與各項预期 marker 在 Notion 技術文件中。來源、影像及交付物 SHA256 由 `manifest_sha256.csv` 對應，避免把其他版本的 RTL 與此 bitstream 混用。
