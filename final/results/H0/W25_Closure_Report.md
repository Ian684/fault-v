# W25 核心指定檢查結案報告

本輪完成的是使用者確認的研究核心範圍：STA、開源規則 DRC、核心／SRAM 介面 LVS、上層 antenna、reset／CDC 數位檢查、fill／density、靜態 IR／平均電流 EM，以及 DFT／pad／ESD 審查與需求。下列結果使用同一個最終候選；沒有將不同試跑的通過結果拼接成最終驗收。

W25 研究範圍已完成；完整 foundry signoff、合格 SRAM 多 PVT 與內部驗證、fill-aware PEX、製造與封裝可靠度仍有明確阻擋項，不能據此直接投片。正式 PPA 比較尚未完成，W26 正式交付尚未開始。

## 同版檢查結果

| 檢查 | 實際結果 | 證據 |
| --- | --- | --- |
| 原生 DRC | 全晶片與完整鄰域重查後未解 0；填入 filler 後再次為 0 | reports/final_filled_independent.json |
| 完整幾何核心 GDS | 開源 KLayout DRC 0；18 顆 SRAM 的 39 層製造幾何與選定宏一致；全部標準元件及 via 幾何／數量已核對 | reports/final_post_verified.json；reports/final_macro_audit.json；reports/final_stdcell_audit.json |
| 核心 LVS | Netgen error 0；18 顆 SRAM 各有完整 125 個不重複介面端點；SRAM 內部為 opaque | reports/final_core_verified.json；reports/final_core_lvs_view.json |
| LVS 校準 | 原方法正控制 0；刻意移開一個 SRAM pin 的負控制 44 errors，未把空宏或缺 port 的假通過列入驗收 | reports/core_lvs_method_verified.json |
| 連通與供電幾何 | 41,337 條多端訊號／時脈網路全部幾何連通，7,572 個 diode terminals；VPWR／VGND 無面積、邊緣或點接觸 | reports/final_core_verified.json；reports/final_pg_contacts.json |
| 上層 antenna | 違規 net 0、pin 0；未涵蓋 SRAM 內部 | reports/final_post_verified.json |
| STA | fresh 網表與三份不同 RC SPEF；TT 25°C／1.8V 下 min／nom／max RC 的 setup、hold、slew、cap 違規全部 0 | reports/final_post_verified.json |
| Reset／CDC | 97 cycles、8 個 reset 解除相位通過；精確入口例外保留，同步器階間仍計時 | functional/final_a/result.json；../week25_signoff/constraints_reviewed.sdc |
| 活動 | idle、mixed、dot64_rv32i、dot64_custom 均通過；各 41,337 條 routed nets 映射 100%，SRAM 輸入無未知時間；其餘 X/Z 比例保留 | functional/final_a/activity_coverage.json |
| Fill／density | 7 個有明確數值門檻的層，每層 1,053 個視窗全部通過；8 層 dummy 均為 5nm grid，FOM 20 tiles 通過，完整 post-fill BEOL 互動標記 0 | reports/final_fill_verified.json |
| 靜態 IR／平均 EM | 14／28mW 每 SRAM 兩種假設、VPWR／VGND 共四組；所有 native resistor／CSV 分支平均 EM 通過；合併 rail drop 低於事先記錄的 90mV 研究預算 | reports/final_ir_verified.json |

## 時序與供電數值

| TT RC 條件 | Setup 最差 slack（ns） | Hold 最差 slack（ns） |
| --- | ---: | ---: |
| nom_tt_025C_1v80 | 6.674249 | 0.197764 |
| min_tt_025C_1v80 | 8.431027 | 0.197282 |
| max_tt_025C_1v80 | 5.693490 | 0.152270 |

| 活動工作負載 | Cycles | Routed-net 映射 | 依 net 時間加權 X/Z | 有切換 routed nets |
| --- | ---: | ---: | ---: | ---: |
| idle | 256 | 100.00% | 5.5398% | 446 |
| mixed | 1159 | 100.00% | 5.5148% | 21451 |
| dot64_rv32i | 21708 | 100.00% | 5.5091% | 8940 |
| dot64_custom | 1022 | 100.00% | 5.5086% | 15349 |

X/Z 主要與未使用 SRAM 輸出等四態模型行為有關，沒有改為零活動；100% 映射不代表 100% 活動皆為已知值。IR 使用 mixed 的實際活動，SRAM 絕對功耗另採明列的假設負載。

min／nom／max 是 RC 變動，全部使用 TT，不是 SS／FF。

| SRAM 功耗假設 | VPWR 最差 drop（mV） | VGND 最差 rise（mV） | 保守合併（mV） | 最大平均 EM 利用率 |
| --- | ---: | ---: | ---: | ---: |
| 0p014 W／顆 | 15.7100 | 14.4713 | 30.1813 | 0.465730 |
| 0p028 W／顆 | 29.6520 | 27.2998 | 56.9518 | 0.884873 |

90mV 是本專案在最終 IR 前記錄的 1.8V、5% 合併 rail 研究篩檢預算，不是 foundry 限值，也沒有驗證 nominal Liberty 對 droop 的適用性。理想外緣供電、SRAM 假設負載與完整 resistor 區段均明列；native SPICE sink export 的 map::at 限制仍保留。

## 修復前後對照

| 問題 | 修復前 | 最終結果 |
| --- | --- | --- |
| 最大 RC 電氣 | 原始 filler 核心 451 slew／45 cap | 51 個已核對布林等價 driver 調整後，三 RC 均 0；使用新 RCX |
| LI1 支線 | Group M 完整 GDS 有 23 項 li.3 自身間距問題 | 五條支線改成接腳內 LI1＋M1／M2；其中四顆新增被動二極體移至合法 row；完整 GDS DRC 0 |
| Antenna | 51-driver source 有 18 條違規 | 新增 20 顆被動二極體及經驗證的兩個局部金屬橋後，上層 net／pin 0 |
| 供電 cut 電流 | 原單切孔 via4 存在平均電流超限；其他 PG 試跑亦出現幾何短路 | PG_G 同版重驗通過核心幾何、LVS、四組平均 IR／EM |
| 密度 | 早期數值密度或 FOM minimum 不足 | 最終候選重新產生 fill，全部有數值限值的視窗及指定互動規則通過 |

失敗試跑保留為診斷資料，沒有採用其零計數。包含 group Q 的 51 個新增原生違規、錯用 manual mode 的內部零值、只有抽象／空 SRAM 的 GDS，以及未完成的全網路重繞。

## 規則、模型與交付限制

| 項目 | 已有覆蓋 | 未覆蓋與影響 |
| --- | --- | --- |
| 規則與工具 | pinned LibreLane 3.0.16、OpenROAD dcf36133、OpenSTA 3.1、Magic 8.3.623、Netgen 1.5.316、KLayout 0.30.7 與同一份 SKY130A PDK | 開源工具結果不等於 foundry 核可；DRT-0349 的 LEF58_ENCLOSURE 缺 CUTCLASS 規則未由 router 完整涵蓋 |
| SRAM | 18×2KiB＝36KiB；選定 GDS／LEF／TT Liberty 有來源與 SHA；移除無接點孤立 M2 stripe 5.9668µm²、其餘 38 層不變，重複無標籤子實例去重後 39 層幾何保持 | SRAM 為研究修改版；未取得 qualified SS／FF、內部 DRC／LVS／antenna 與 foundry qualification |
| LVS | 核心／真實介面 pin 模型、125 ports、正負控制；完整標準元件與路由 | SRAM 內部 opaque；LVS-only view 不能用作製造、DRC、密度、RCX 或 antenna 的版圖 |
| 填充與 RCX | 最終 GDS fill 與互動／密度已重驗；RCX 五個巨大 fill 的負控制表明 41,337 個 net bodies 不變 | 現用 RCX 不支援已驗證的 fill-aware PEX，沒有 post-fill 電氣簽核；POLY 未有本流程數值密度限值 |
| Reset／CDC | 單主時鐘結構、精確外部入口與同步鏈、數位功能及階間時序 | 無 SDF、tau／T0、MTBF、類比 recovery／removal、多 PVT 或獨立 CDC／RDC signoff；reset 需在供電與時鐘穩定後有效至少 80ns |
| IR／EM | 實際 mixed 活動、fresh nominal RC、兩種 SRAM budget、每個 native branch 與 cut 數／有效線寬核對；Tj90°C 平均限值 | 無 package RLC、transient、熱解、局部擁擠、脈衝／AC 與 SRAM 內部簽核 |

## DFT、pad／ESD 與封裝審查

本輪依使用者選定僅完成審查與需求。2,925 個 FF、19 種 scan 候選已盤點；scan_in／out／enable／test_mode、shift／capture 約束、ATPG／fault simulation、18-bank MBIST／byte mask／故障注入與可讀 fail 記錄均已有後續驗收需求；沒有 scan chain、MBIST 實作或製造 coverage 數字。完整審查見 ../week25_signoff/Reset_CDC_DFT_Review.md。

Pad／ESD 規劃為 1.8V 核心、候選 3.3V wrapped I/O 與 48 接點 wire-bond 需求預算。現有 108 個訊號端點含 96 位 debug，48 接點需另外實作 UART 診斷讀回；現版尚未具備。電源／地分域、clamp／回灌／供電順序／latch-up／bond 回流須隨核可 wrapper 檢查。HBM 2kV／CDM 250V 僅為待核定目標，沒有通過額定。完整需求見 ../week25_signoff/Pad_ESD_Package_Review.md。

上述模型、製程、填充抽取、類比可靠度與晶片介面實作，是進入實際製造前的阻擋項；本輪沒有付費投片或封裝。

## 最終候選與重現

- Routed ODB SHA256：`6e98b1bcb56b4455e97a7ac5d54a902ec7607878912ca2d2e70dc9b8bd584125`。
- Filler ODB SHA256：`2a17870d03436f8f8839b88324f93d6410f98509937557296da2af5cb964e7c2`。
- 完整核心 GDS SHA256：`67bcff916921d52cba6ca20ff2eccf32a37f3c867a88d764063f11c513a678d5`。
- 最終 dummy-filled GDS：`final_fill/filled.gds.gz`，SHA256 `84ffab595850075e55e8ad6def4ae5d36bea79e6fd2d865da4ee84dfb7c151bd`。
- 網表 SHA256：`cdbbfc46696534b7a5729c5c5f20a8de82b5923597f93cb53ec67f3f5f0e4175`；約束 `../week25_signoff/constraints_reviewed.sdc`。
- 機器可讀結論：reports/W25_closure_result.json；證據 manifest：W25_Evidence_Manifest.json。
- 流程與驗證入口：Reproduce_W25.md；各 native flow 的 E 槽封存逐檔與 native 原檔 byte-exact 比對。

W25 與正式 PPA 均完成後才分別交付 Notion；本輪不提前交付。
