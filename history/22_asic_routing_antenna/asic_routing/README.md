# Fault-V ASIC Routing

本工作區接續 Placement／CTS，將既有 CPU 的訊號與 clock 連接實作為金屬導線，補齊 SRAM 接腳天線模型並修復上層 antenna，再使用 OpenRCX 實際萃取的寄生參數驗證 TT 時序。正式結果只能由 accepted_summary.json 與其指定的檢查證據判定。

- Routing_Notion.md：設計筆記，適合貼入 Notion；不混入進度與測試紀錄。
- Verification_Report.md：驗收通過後才產生，列出實際結果與未完成的簽核。
- selected_flow.json：正式選用的 routing 方法、來源、設定與重跑範圍。
- handoff_state.json：實際 ODB／DEF／網表／SDC／三份 extracted SPEF。
- input_identity.json、technology_identity.json：凍結輸入、工具與使用模型的 SHA-256。
- MANIFEST.sha256.json：交付包全部檔案的 SHA-256。

## 離線核對

解壓後頂層為 routing/：

```powershell
python .\routing\scripts\check_delivery.py
```

此命令檢查完整檔案集合、逐檔 SHA、驗收證據與交接路徑；不會重新執行 EDA。ZIP 另經 CRC 與每個封存項目的 SHA 核對。

## 正式繞線的重跑入口

需要 Docker、Python 3 與 technology_identity.json 指定版本的 PDK。PDK 和固定容器 image 不含在 ZIP；sta_tool/ 包含本流程的 OpenSTA 3.1.0 binary 與 Tcl runtime。將解壓的 routing/ 與 pdk/ 放在同一個 ASIC 根目錄，容器將該根目錄掛至 /work。

請從封存包的工作副本重跑：

```bash
cd ~/fault-v-asic/routing
bash scripts/run_selected.sh routing_reproduce
```

本機 Windows 工作區為 `E:/Codex/Fault_V_W24_Transfer/work/fault-v-asic/routing`，使用 WSL 的 Ubuntu-D：

```powershell
wsl -d Ubuntu-D --cd /mnt/e/Codex/Fault_V_W24_Transfer/work/fault-v-asic/routing --exec bash scripts/run_selected.sh routing_reproduce
```

本機 WSL 記憶體約 15.5 GiB；選用執行資源由 selected_flow.json 記錄。請一次執行一個重型 EDA 工作，保留已完成快照與錯誤紀錄。

入口會拒絕不合法或已使用的 run tag，先核對 frozen inputs 與 PDK，再從實際凍結的部分佈線 ODB 執行 Detailed Routing、router DRC、antenna 重檢、OpenRCX、OpenSTA 3.1.0、幾何／實體金屬連通／供電／RC 覆蓋／時序與獨立全晶片 routing DRC。輸入已包含原生插入的天線二極體、cached pin access、嚴格避讓與零溢位 guides。天線必須為0且其餘檢查全部通過，才回報重跑成功；原選定版本的驗收摘要保留。執行紀錄位於 ASIC 根目錄 logs/，新增檔案後原交付 manifest 不再適用。

這個入口**從 selected_flow.json 指定、隨包凍結的實體輸入開始**；輸入可能已保留部分詳細走線，具體範圍以該檔與 Verification_Report.md 為準。它不會從 RTL 重建整個設計。選用的 global_run、routed_run、CLI、原生 Tcl、config 與 state 均列在 selected_flow.json 並核對 SHA。提供重跑入口不代表已完成第二次獨立 Detailed Routing；實際執行覆蓋依 Verification_Report.md 記錄。

上游另保留原始 CTS ODB、標準 clock rules、global_electrical 修整輸入與 buffer／hold 修整方法。reports/preparation_reproduction.json 記錄從原始 CTS 重跑前置流程的結果；這是前置流程重現，不保證相同 detailed-routing 幾何。舊 scripts/run_all.sh 保留為基準前置流程的歷史入口，不是正式選用繞線的重跑入口。

## 工具與電氣條件

使用 technology_identity.json 固定的 LibreLane／OpenROAD image。Global Routing 的容量調整與macro避讓依選定config及原生報告記錄，Detailed Routing 受技術 LEF 規則約束。原 CTS 13 條 net 的 NDR assignments 改為標準金屬寬度／間距，clock 接收端點與相位語意、40 ns SDC 與 SRAM 40 ps transition 上限保留。相關 ODB 與變更清單見 reports/clock_routing_rules.json。

放置估算通過不能替代繞線後分析。前置流程採 500 µm 長線修整與 30% slew／capacitance 裕量；RSZ-0065 提示較短分段可能增加 buffer 與延遲，這是通過約束的基準，不宣稱最佳 PPA。

繞線後若實際 SPEF 出現違規，依真實 driver 與 hold endpoint 調整等價元件，必要時以非反相 buffer 分段長 clock 分支。續跑可能使用保留既有 signal／clock 導線的原生 checkpoint，並由 router 重新建立 pin access；這不等同從無詳細導線的輸入完整重繞。實際來源、保留導線證據、重跑範圍與最終方法，以正式 selected_flow.json 和驗收報告為準；尚未產生 accepted_summary.json 時不得視為已通過。

內嵌 STA 的 mixed-threshold 問題已獨立重現，驗收使用未修改的 OpenSTA 3.1.0；binary、runtime 與 probe 證據隨包。LibreLane 階段名稱沿用 STAPrePNR 包裝器，實際 state 與 source report 指向 routed netlist 及 extracted SPEF，不以 estimated RC 代替。

## 獨立 routing DRC

除 router 最終計數外，另外以新 OpenROAD process 重讀正式 ODB、執行全晶片 DRC。原生 checker 的分析分區邊界可能造成 same-net li1 NS Metal／Spacing 回報；每筆以置中的完整上下文重查，只有符合此類別且複查消失者才分類為分區問題。其他回報全部保留為未解，必須為 0。

已知有兩處真實 met1 短路的保留快照用於負向驗證：兩處都必須在上下文檢查中持續被偵測，且把此錯誤快照送入正式門檻時必須拒絕。固定的校準回執與 native helper SHA 隨包；正式 ODB 仍逐次重新檢查，不沿用舊的通過結論。報告同時列出原始、分區問題與未解筆數，不把原始回報隱藏為 0。

## 簽核範圍

目前涵蓋 TT／1.8 V／25°C、nominal extracted RC、router 支援的 LEF routing 規則與上層 antenna closure。SRAM 的 gate／diffusion 資料取自原始 GDS，gate 面積另由 SPICE 獨立核對；查證證據在 reports/antenna_model/。新增 PDK 被動二極體的型別、模型、端點與 PG 接線逐顆檢查，原有元件與功能接線保留。三份 min／nom／max SPEF 不等於完整多 PVT 時序；部分 LEF58 規則尚未完整支援，SRAM 內部 foundry antenna signoff 亦未涵蓋。

完整製程 DRC／LVS、filler／metal density、IR／EM、reset recovery／removal、DFT、pad／ESD、封裝與實體晶片量測仍待後續。本工作區是核心級 routing 交付，不宣稱已可直接送廠。
