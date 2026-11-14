# Fault-V Floorplan／Power Plan 驗收報告

## 結論與範圍

完成核心區域、18 顆 SRAM 固定配置、row cut、tap／endcap、PDN 與核心訊號腳配置。完整流程及重新執行的重現流程均通過，對應本專案 Floorplan＋Power Plan 階段。

採用 run：`floorplan_accepted`。獨立重現 run：`floorplan_reproduce`。
另以 handoff_state.json 實際載入最終 views 執行 OpenROAD.DumpRCValues，流程成功，供下一階段交接。
本報告不代表完成晶片簽核或可直接送廠。

## 實際結果

| 檢查 | 結果／證據 |
| --- | --- |
| 實作區外框 | 2500 × 3300 µm，8.25 mm² |
| Core bbox | (80.04, 81.60)－(2419.60, 3217.76) µm |
| SRAM | 18 顆，R0，位置與規格一致，全部固定 |
| SRAM 合計面積 | 5,121,692.532 µm² |
| 重疊／越界 | 巨集含 20 µm halo 無重疊，全部位於 core 內 |
| Placement rows | 4192 段，均未侵入 SRAM halo |
| 實際合法 row 面積 | 1,357,331.7888 µm²；這是 row site 面積，不是 core 減 SRAM 的簡單差值 |
| 實際 ODB instances | 57,359 |
| 原功能元件 | 29,466，含 18 SRAM；其餘 29,448 功能性標準元件尚未 placement |
| 新增實體元件 | 19,509 tap＋8,384 decap endcaps |
| 標準元件幾何面積 | 356,823.472 µm²，包含本次 tap／endcap，不含 SRAM |
| 功能連線一致性 | 初始匯入 ODB 與最終 ODB 的 29,466 個 instance/master、109,529 個訊號 ITerm、108 個訊號 BTerm 一致 |
| 邏輯電源接線 | 全部 190,382 個 POWER／GROUND ITerm 接到正確電源網 |
| SRAM 電源腳 | 36 個，vccd1／vssd1 接線逐一檢查 |
| 功能性邊界 pin | 108 bit 全部定位；另有 VPWR／VGND block pins |
| PDN 連通性 | VPWR＝0 問題；VGND＝0 問題 |
| PDN 交會缺 via 警告 | 0；不是關閉警告或跳過檢查 |
| PDN via instances | VPWR 9,956；VGND 9,962；via instance 不是單一 cut 數 |
| 重現性 | 最終 run_floorplan.sh 以新 tag 跑完同一流程與自動檢查 |

上述 instance／面積以實際最終 OpenDB 重新統計。原始 flow metrics 中部分 instance 計數沿用較早步驟，並未包含所有 endcaps；原始檔保留，不據此誤報最終數量。

標準元件尚未擺放，因此「所有 PG ITerm 邏輯接線正確」不等於所有功能性標準元件都已完成實體供電接觸。現階段確認已建立的 PDN 形狀連通及已固定 SRAM 的供電；placement 後還要再檢查。

## PDN 修正

初版水平 offset＝30 µm 出現兩筆 PDN-0110，原因是交會區域太小、無法放入 via。曾檢查列對齊方案，該方案仍產生警告，因此沒有採用。

最後保留 met4／met5 線寬 3 µm、pitch 150 µm，水平 offset 改為 35 µm。單步 PDN 檢查、完整流程、重新執行流程都達到零 PDN-0110、零 power-grid violations。

沒有改 RTL、自訂指令語意、時序約束或 SRAM 原始 views。

## 輸入與工具

- 輸入 mapped netlist SHA256：`88b35c08aa99b400a6bd72d7d1128b2d63fd8e9a04ae0f441698587c29f036f0`。
- 12 個設計輸入／腳本的 SHA256 見 `input_identity.json`；檢查器會核對。
- PDK：sky130A，revision `8afc8346a57fe1ab7934ba5a6056ea8b43078e71`。
- 標準元件庫：sky130_fd_sc_hd。
- SRAM：sky130_sram_2kbyte_1rw1r_32x512_8，沿用既有 LEF／GDS／TT Liberty。
- Docker：`ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302`。
- LibreLane 3.0.16；OpenROAD `dcf36133a369abc8f3c5e5738cd4d82e4903c0e0`。
- 已使用之技術 LEF、標準元件 LEF 與 TT Liberty 的雜湊記於 `technology_identity.json`。
- 本階段未執行新的 STA；沒有以 OpenROAD 內嵌 STA 結果覆蓋前階段 OpenSTA 3.1.0 的驗收結果。

## 保留警告與未完成項目

| 項目 | 狀態與後續處理 |
| --- | --- |
| SRAM antenna metadata | 原始 LEF 的 59 個 input pins 缺 gate antenna 資料、64 個 output pins 缺 diffusion antenna 資料；兩個警告保留，不能虛填數值消除。後續需取得適當資料或依合格交付流程處理 |
| Corner | SRAM 僅有 TT 1.8 V／25°C model；未完成 SS／FF、多 corner 簽核 |
| Placement／CTS／routing | 29,448 個功能性標準元件尚未擺放，無實體時脈樹、訊號線與 SPEF |
| Timing／電氣 | 尚無 placement／CTS／routing 後的 setup、hold、slew、cap 驗收 |
| IR drop／EM | 未分析實際活動率、封裝電源源點與電流；不能將 PDN 連通通過稱為電源完整性通過 |
| DRC／LVS／antenna | 未完成完整版圖簽核；幾何與 PSM 檢查不取代這些項目 |
| I/O／pad ring／ESD／封裝 | 邊界 pin 已定位，尚未完成獨立晶片整合 |
| 製造測試 | 尚未加入或驗收 scan／DFT |
| 功能驗證 | 本次做 ODB 逐端點結構一致性檢查；未重新跑全部 RTL／gate 程式，也不宣稱 RTL formal equivalence |

## 證據位置

- `reports/floorplan_accepted/floorplan_checks.json`：從實際 ODB 擷取的幾何、接線與計數。
- `reports/floorplan_reproduce/floorplan_checks.json`：重新執行結果。
- `logs/floorplan_accepted.log`、`logs/floorplan_accepted_checks.log`。
- `logs/floorplan_reproduce.log`、`logs/floorplan_reproduce_checks.log`。
- `runs/floorplan_accepted/11-openroad-generatepdn/`：PDN log、VPWR／VGND error reports。
- `runs/floorplan_accepted/final/`：ODB、DEF、功能／powered netlist、SDC 與原始 metrics。
- `figures/Floorplan_PDN.png／.svg`：由實際 ODB 幾何生成，不是手工想像的 floorplan。

原始工作區保留早期嘗試與失敗紀錄；交付包以最終採用版本及重現證據為準。
