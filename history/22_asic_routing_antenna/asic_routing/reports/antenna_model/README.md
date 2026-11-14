# SRAM 天線模型查證

本資料只證明上層佈線使用的 SRAM 接腳模型已補齊；天線修復、DRC、實際 RC 與 TT 時序仍須由修復後的候選另行通過。

- 原始 GDS：`macros/sky130_sram_2kbyte_1rw1r_32x512_8.gds`，SHA-256 `d32efcfe8079379f94070bcbcedad7f1239e27f8996eb184141840e31c9302b2`。
- Magic 8.3.623 使用原始 sky130A 技術檔，讀取原始 GDS，再以原 LEF 註記接腳方向，實際提取 59 個 gate 與 64 個 diffusion 面積。沒有以缺資料為零，也沒有修改技術規則。
- 57 個資料／控制輸入的 gate area 為 0.600000 µm²；兩個 clock 輸入各為 0.222000 µm²。59 個值全部與原始、未裁剪 SPICE 的階層接線和電晶體 W×L 總和獨立相符。
- 64 個輸出的 diffusion area 各為 0.553900 µm²，取自 GDS 實體幾何。
- 新增的 `.antenna.lef` 只插入這 123 個面積欄位。移除新增欄位後，與原始 LEF 逐字相同，因此 SIZE、pin 金屬、方向及 OBS 全數保留。
- 候選 ODB 的 90,346 個有效輸入均有 gate 模型，18 顆 SRAM 的數值已從 ODB 回讀核對。`native_coverage.json` 記錄實際來源 SHA。
- 同一 coverage checker 對原始缺模型 ODB 必須以 exit 1 拒絕，且不得生成通過報告。已完成此反例，見 `negative_coverage.json` 與對應 log。

原始 SPICE 的完整相同副本保存在 `macros/sky130_sram_2kbyte_1rw1r_32x512_8.source.sp`；原始與交付別名的雜湊對照見 `spice_source_alias.json`。

`candidate_input.json` 證明模型補齊時，原有 68,982 個元件、功能接線、PG 幾何、41,337 條詳細導線、guides 及障礙均未變。`first_insertion_audit.json` 另確認第一輪實際加入 7,251 顆 PDK 二極體後，既有元件位置保留，新增二極體的 29,004 個電源／接地接腳均連接正確；這不是修復後路由驗收。

本模型供 OpenROAD 上層 LEF 天線檢查使用。未宣稱 SRAM 內部的完整 foundry antenna signoff，也未取代完整晶片 DRC/LVS。
