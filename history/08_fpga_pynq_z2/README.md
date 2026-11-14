# Fault-V FPGA package

先閱讀 `FPGA_Integration_Notion.md`；實際驗證結果在 `FPGA_Integration_Verification.md`。

目標 PYNQ-Z2／xc7z020clg400-1，Vivado 2022.2。

PowerShell 進入此目錄後：

```powershell
& ./run_regression.ps1
& ./run_endpoint_regression.ps1
& ./run_xsim.ps1
& ./build_fpga.ps1
```

腳本可傳入 `-VivadoBin` 改變安裝路徑。

GUI：Vivado Tcl Console 先 cd 到此目錄，再 `source create_project.tcl`。Design Top 是 `fault_v_fpga_top`。不要同時加入其他版本的同名 RTL。

`build/fault_v_fpga_top.bit` 是 FPGA 配置檔。ZIP 不含可重新產生的模擬快取、Vivado runs 中間資料與 `.xpr`；用脚本建立專案。本機已建立的 `.xpr` 在 `build/project/fault_v_z2.xpr`。

時序目標為 25 MHz。未接板驗證；PL-only 的 ZPS7-1 平台 warning 保留，實板仍须確認 PHY clock 及 Zynq 配置條件。

FPGA memory 調整不改 CPU 指令／握手規格。其他核心 RTL 與前一套驗證版本相同。來源及交付物 SHA256 見 `manifest_sha256.csv`。
