from pathlib import Path
import json
C=Path(__file__).resolve().parents[1];root=C.parents[2];state=json.loads((C/'WORK_STATE.json').read_text())
assert not state['W25_complete'] and state['selected_final_candidate'] is None
path=root/'W25_CLOSURE_PROGRESS.md';history=C/'reports/progress_before_20261101_refresh.md'
if not history.exists():history.write_bytes(path.read_bytes())
text=f'''# W25 實體檢查與修復進度

截至 2026-11-01，W25 **尚未完成**。已驗證合併路由的原生 DRC、全線連通與天線均通過，正在執行最終同版 GDS、RC／STA、核心 LVS、活動、IR／EM 及填充驗證。狀態更新時間：{state['updated_utc']}。

| 工作 | 已核對結果 | 尚待完成 |
| --- | --- | --- |
| 訊號繞線 | `signal_manual51_a` 的精確來源已通過獨立全區與逐點完整上下文檢查：DRC 0；全部 41,337 條訊號／時脈線均為單一金屬／via／端點連通分量；新匯出與已查來源的線路 bytes、元件、邏輯、PG、guides 及障礙均一致 | 與已驗證供電版及新天線二極體合併後再做同版驗收 |
| 合併路由／天線 | 20 顆真實二極體及一處 4 µm M2→M3 jumper 已實作；`antenna_manual_a` 的獨立全區／逐點上下文 DRC 0，全部 41,337 條線連通，7,572 個二極體端點已覆蓋，上層天線 0。精確來源 SHA256：`8760c5097c44429fff8b4574bce447f17705a7853450693d1d354a6d678cabeb` | 已啟動最終 filler／GDS／RCX／STA；其餘最終同版檢查仍待完成 |
| 完整 GDS LI1 間距 | Post-A 完整規則找到 43 個 `li.3`，已拒絕驗收；依實際 GDS 導體歸屬加入 57 個小範圍 LI1 矩形，寬度／間距規則重播為 43→0 | 修補 ODB 的整體原生檢查、Post-B 完整規則、核心 LVS 及 RC／STA 均須重跑 |
| 供電幾何 | PG_F 的兩處 M5 電源／地線相接已確認並拒絕。PG_G 的原生 DRC、電源／地線接觸、完整 GDS 幾何 DRC、125-port 核心 LVS 均為 0，版圖完整性與四組 IR／EM 通過；合併到 51-driver 訊號後的原生 DRC 亦為 0 | 新增天線二極體與最終實際網表／活動後仍須再驗 |
| 核心 LVS 方法 | 原始 F 基準：125 個獨立 SRAM 端點、LVS 0；刻意移錯 pin 的反向控制：44 個 LVS 錯誤。兩個有警告的標準元件正向匹配、兩個接錯控制均失敗 | 最終實際候選核心 LVS 0；完整 SRAM 內部與 foundry LVS 不在此方法涵蓋範圍 |
| 訊號電氣 | 真正 DRC 0 的 50-driver 版新抽 RC 後發現 max RC slew／cap 11／1，已以第 51 顆等價驅動修復。`driver51_rc_a`／`driver51_sta_a` 三組 RC 均 slew／cap 0，最差 setup 5.69349 ns、hold 0.152270 ns；涵蓋明示的 3.05 µm LI1 導線 | 最終 PG／二極體幾何仍須重抽 RC 與重跑 STA |
| reset／CDC、工作負載與活動 | B 版新網表通過 97 週期、8 種 reset 解除相位與 idle／mixed／DOT64 RV32I／DOT64 custom。每個工作負載均映射全部 41,337 條線，SRAM 輸入無未映射或 X／Z 時間 | 最終網表重播；保留訊號 X／Z 時間比例約 5.51–5.54%，不當作已知零活動；零延遲模擬不涵蓋 SDF／類比亞穩態簽核 |
| IR／EM 開發篩檢 | PG_G 的 14／28 mW 每 SRAM、VPWR／VGND 四組平均電流篩檢均為 0 違規，峰值門檻利用率約 0.885 | 最終實際網表／活動仍須重跑；無封裝、熱解、局部擁擠與 SRAM 內部 EM 簽核 |
| 填充與密度 | 開發基準的 7 個數值門檻圖層各 1,053 個視窗通過；8 個填充圖層均在 5 nm 網格；FOM 幾何與完整 BEOL 填充互動 DRC 0，六層違規控制均被偵測 | 最終訊號／PG／二極體版重新生成填充並重查 |
| DFT／pad／ESD | 已有審查與需求；依使用者確認，範圍不含 scan／MBIST／pad ring 硬體實作 | 納入最終問題與需求清單 |

完整製造 GDS 保留所有 SRAM mask-add/drop 圖層。普通 Magic 匯入無法完整支援這些圖層，因此核心 LVS 使用另外產生、逐 pin 對照實際金屬的 pin-interface 視圖；此視圖不能用於製造交付、DRC、天線、RCX 或密度分析。完整 GDS 的 268 個完全重疊、無文字子實例已去重，39 個製造／用途圖層與所有文字均維持相同。

`DRT-0349` 的 LEF58 規則支援缺口、合格 SRAM SS／FF 模型、完整 foundry／SRAM 內部檢查、封裝與晶片量測均保留為覆蓋限制。負向控制亦確認目前 RCX 不處理 `dbFill`，不可宣稱合格的填充後 PEX／時序簽核。

正式 ASIC PPA 比較尚未開始。Notion 依原約定等待 W25 與 PPA 全部完成後，再分別交付。

可恢復狀態：[WORK_STATE.json]({C.as_posix()}/WORK_STATE.json)。主要新證據：[訊號獨立檢查]({C.as_posix()}/reports/signal_gap_independent.json)、[全部訊號連通]({C.as_posix()}/reports/signal_gap_all_connectivity.json)、[精確匯出]({C.as_posix()}/reports/manual_export_binding.json)、[新網表功能結果]({C.as_posix()}/functional/short_b/result.json)、[活動映射]({C.as_posix()}/functional/short_b/activity_coverage.json)、[PG_G 幾何]({C.as_posix()}/reports/pg_g_geometry_binding.json)、[PG_G 接觸檢查]({C.as_posix()}/reports/pg_g_contacts.json)。
'''
path.write_text(text,encoding='utf-8');print(path)
