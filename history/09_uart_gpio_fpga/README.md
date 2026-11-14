# Fault-V UART/GPIO package

技術筆記：`UART_GPIO_Notion.md`。實際驗證：`UART_GPIO_Verification.md`。

PYNQ-Z2／xc7z020clg400-1，25 MHz，UART TX 約 115200 baud 8N1。

```powershell
& ./run_regression.ps1
& ./run_endpoint_regression.ps1
& ./run_xsim.ps1
& ./build_fpga.ps1
```

GUI：Vivado Tcl Console cd 至此目錄，`source create_project.tcl`。Top＝`fault_v_fpga_top`。

GPIO 控制四個 LED，UART TX 在 Pmod B pin 1（W14）。板上 USB-UART 不是這條 PL UART。沒有转接器時使用 testbench 解碼輸出。未連板驗證；ZPS7-1 平台 warning 保留。

ZIP 包含 RTL、測試、程式、約束、報告與 bitstream／DCP，不包含模擬快取及 Vivado runs 中間資料。腳本會建立缺少的工作目錄及專案。
