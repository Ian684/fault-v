# 選型依據與環境檢查

查核日期：2026-10-16，Asia/Taipei。本檔是選型查核，不是安裝、合成或簽核報告。

讀取現有 extension_c 的 fault_v_memory.sv、regfile.sv、custom_exec.sv、fault_v_dot_pipeline.sv、board/fault_v_payload.sv。確認需要處理 FPGA BRAM 初始化、讀寫時序、乘法屬性與 PS7 平台外殼。

唯讀環境檢查：Ubuntu-22.04、WSL2、x86_64、14個邏輯CPU；可見RAM 7684 MiB、swap 2048 MiB；Linux根檔案系統可用753 GiB。PATH找到Docker，沒有找到Nix、LibreLane、Yosys。未執行工具安裝或smoke test，未更改系統設定與既有RTL。

主方案依現有資源選開放PDK。工具精確tag、Open PDKs hash、SRAM views雜湊在首次相容性與smoke test通過後固定。Nix與前端選擇仍需實際安裝驗證。

SRAM候選目錄列有GDS、LEF、Verilog、SPICE及TT Liberty；未在該目錄看到SS／FF Liberty。TT僅供初步整合；不得假充多角落簽核。LEF尺寸乘18推得5.121692532 mm²，只計巨集，不含晶片整合成本。

來源連結及架構決定見ASIC_Preselection_Notion.md。既有extension_c成果不變。
