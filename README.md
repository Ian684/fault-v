# Fault-V：面向邊緣 AI 推論的 RISC-V 自訂指令 SoC

Fault-V 是一顆 32 位元 RV32I 多週期處理器，加上 12 條面向量化神經網路的自訂指令（INT8／INT4 內積、飽和運算、再量化），並整合 DMA、DOT4 加速器與 18 顆 2 KiB SRAM（共 36 KiB）。整個流程只使用開源的 SkyWater SKY130 製程與開源 EDA 工具，從 RTL 做到通過投片前驗證的版圖。

> 這是研究用的投片前設計，沒有實際製造，也沒有經過 foundry 簽核。限制見下方。

## 主要結果

| 項目 | 結果 |
|---|---|
| DOT64（64 次 INT8 乘加） | 自訂指令讓執行週期從 21,708 降到 1,022、能量從 28.9 µJ 降到 1.36 µJ（皆約 21.2 倍；比較基準是沒有硬體乘法器的 RV32I） |
| 晶片功耗 | 約 33 mW（25 MHz、TT、mixed 工作負載） |
| 投片前檢查（H0） | KLayout DRC 0、LVS 0、天線 0、三種 RC 的 STA 違規 0、IR／EM 與金屬密度通過 |
| 第二個實體版本（H1） | 縮小 SRAM 間通道，晶片面積 −3.7%，通過與 H0 相同的全部檢查 |

## 資料夾

| 資料夾 | 內容 |
|---|---|
| `final/design/` | 最終晶片 RTL、測試台、SRAM 模擬模型、合成後網表 `mapped_top.v`、Vivado 測試腳本（`run_xsim.ps1`、`run_regression.ps1`） |
| `final/layout/` | H0／H1 版圖的 OASIS 檔（核心版圖與加 dummy fill 的版圖），以及與 GDSII 的等價檢查結果 |
| `final/results/` | PPA 正式比較、W25 結案報告、H1 結案結果、各項檢查的 JSON |
| `final/scripts/` | 產生上述結果的腳本（W25 結案、H1 簽核與結案、電源 via 修補、交付包建置） |
| `final/macros/` | SRAM 的 LEF、TT Liberty 與模擬模型 |
| `history/` | 開發過程，依完成順序：Decoder → 控制 FSM → 資料路徑 → CPU 系統 → FPGA → 自訂指令 → 擴充 → ASIC 合成、佈局、繞線 |
| `docs/notion/` | 各階段的設計筆記 |
| `docs/competition/` | 2026 全國智慧運算與量子資訊創新應用競賽書面報告 |

GDSII、SPEF、DEF 與完整交付包（含 SHA256 清單與自我檢查腳本）檔案太大，放在 GitHub Releases。

## 重現

- **RTL 測試**（Windows、Vivado 2022.2）：在 `final/design/` 執行 `run_xsim.ps1` 與 `run_regression.ps1`（744 次 SoC 整合測試）。
- **閘級測試**：`final/design/scripts/run_gate_linux.sh`，使用固定版本的 LibreLane Docker image。
- **實體設計與檢查**：使用 LibreLane 3.0.16（固定 image digest，見 `final/design/toolchain_identity.json`）、OpenSTA 3.1、sky130A PDK（ciel 版本 `8afc8346a57fe1ab7934ba5a6056ea8b43078e71`）。腳本使用原專案的目錄結構，路徑需依環境調整。

## 限制

- SRAM 只有 TT 1.8 V 25 °C 時序模型，功耗是不分讀寫的解析模型。
- 時序只做 TT；沒有 fill-aware PEX；IR／EM 只做靜態、平均電流分析。
- 沒有 pad ring、ESD 與 DFT 硬體，沒有 foundry 簽核，沒有實際製造與量測。

## 授權

第三方檔案（SkyWater SKY130 PDK 衍生的模型、OpenRAM SRAM 巨集）依其原授權，見 `final/design/licenses/`。本專案自己的程式碼與文件採用 MIT 授權，見 `LICENSE`。
