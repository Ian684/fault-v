# 規則與模型覆蓋

固定 SKY130A revision `8afc8346a57fe1ab7934ba5a6056ea8b43078e71`、sky130_fd_sc_hd；pinned LibreLane image、工具版號與規則 hash 沿用凍結的 `../signoff_precheck/reports/tool_identity.json`、`rules_models_inventory.json`。本輪輸入／腳本另列 manifest，沒有修改公開 PDK 來消除違規。

| 規則／模型 | 已有證據 | 不能推論的範圍 |
| --- | --- | --- |
| 核心 GDS DRC | KLayout FEOL、BEOL、floating metal、offgrid；sram_exclude=false、seal=false；修復後 report 0 | 有 deck 內建特定 SRAM cell 規則例外；不是完整 foundry deck，也不涵蓋封裝 seal-ring |
| Router mcon enclosure | DRT-0349 實際警告保留。nom techLEF mcon 的 BELOW 0／0、ABOVE 0.03／0.06；獨立 KLayout ct.4、791_m1.4、m1.4、m1.5 有對應幾何檢查 | 對應規則名稱不等於證明所有 LEF58／CUTCLASS 語意等價；deck 另對特定 SRAM cell 採 0.005 enclosure，未做 foundry qualification |
| 核心 LVS | Magic GDS extraction＋Netgen，125-pin LEF blackbox ×18，唯一匹配、error metric 0 | 只證明核心與 SRAM 邊界；不是 SRAM transistor-level LVS；三個 extraction feedback 保留 |
| SRAM layout | GDS／LEF／TT Liberty 與指定上游 commit 完全相同；來源紀錄在 `../week25_front/reports/upstream_SRAM_provenance.json` | Vendor 歷史 LVS match／DRC 32 不能豁免現環境的 Magic millions-marker 差異 |
| SRAM TT | 只有 TT 25°C／1.8V，analytical／Elmore，3 種 RC 均可精確匹配 | SS／FF 不以 TT 替代；缺合格多 PVT、power／noise／可靠度模型 |
| Antenna | 18 宏、123 個 active pin/macro 完整 pin area 模型下，上層 nets／pins 0 | 不覆蓋宏內部完整 foundry antenna |
| Filler | 新增 139,324 個 standard-cell filler，well/body continuity 修復；原 master／接線／位置／signal route／PG 幾何不變 | Standard-cell filler 不等於 metal dummy fill |
| Density | 原生 KLayout 金屬覆蓋上限 deck 完成；另以 exact GDS polygon union 作 global／700µm 非重疊窗口最低密度篩檢 | 未以該上限 deck 的 0 冒充最低密度通過；非重疊窗口不是正式 700µm／70µm sliding-window qualification，FOM/poly 與正式 fill flow 仍須批准規則 |
| IR／EM | 原生 PDNSim，mixed VCD 全檔標註 140,436 pins；每宏 14／28mW 的明列 budget，外緣 PG feed；電源網連通及 segment current 有報告 | 靜態、TT、理想外部電源；不是正式 PPA、動態供電、package、thermal 或 macro-internal signoff |
| 公開 EM 限制 | nom techLEF 提供 Tj=90°C 的 routing mA/µm 和 cut mA/cut；保守 wire screen 使用實際 PG 最小寬度 | 沒有宣稱 via-array cut 分流、宏內部、溫度／壽命／RMS／peak 已簽核；公開限制不是投片單位批准 |

SRAM flatten 診斷另用 KLayout 移除 hierarchy，39 層 drawing union 的 XOR 均為空、dbu=0.001µm；Magic 使用相同公開 full DRC。診斷副本沒有取代正式宏，結果由主報告記錄，任何未解差異不作自動 waiver。

正式投片計畫未指定；approved deck、waiver、合格 SRAM 多角落與內部簽核資料缺少，持續列為阻擋項。這份覆蓋表已完成資料核對，不能讀成 foundry 認證。
