"""Generate the report only from an accepted routed/extracted result."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
read=lambda p:json.loads(p.read_text(encoding="utf-8"))
s=read(R/"accepted_summary.json")
assert s["accepted"] and s["routing_drc"]==s["global_overflow"]==0
assert s['antenna_closure'] and s['antenna_model_coverage'] and s['reported_antenna_nets']==0
tag=s["routed_run"];global_tag=s["global_run"]
selected=read(R/"selected_flow.json");assert selected["routed_run"]==tag
drc=read(R/"reports"/tag/"full_drc_checks.json")
assert drc["pass"] and drc["independent_full_chip_drc"]==0 and drc["negative_control_known_shorts"]==2
g=read(R/"reports"/tag/"placement_checks.json")
w=read(R/"reports"/tag/"route_checks.json")
t=read(R/"reports"/tag/"timing_checks.json")
coverage=read(R/'reports'/tag/'antenna_model_coverage.json')
diodes=read(R/'reports'/tag/'antenna_diode_checks.json')
assert coverage['pass'] and diodes['pass'] and coverage['source_odb_sha256']==s['odb_sha256']
physical=read(R/'reports'/tag/'antenna_signal_connectivity.json')
assert physical['pass'] and physical['source_odb_sha256']==s['odb_sha256'] and physical['unconnected_diode_terminals']==0
gr=read(R/"reports"/global_tag/"global_checks.json")
rules=read(R/"reports/clock_routing_rules.json")
locks=read(R/"input_identity.json")
source=read(R/"inputs/source_placement_summary.json")
repro=read(R/"reports/preparation_reproduction.json")
assert repro["pass"]
parent_t_path=R/"reports"/global_tag/"timing_checks.json"
parent_t=read(parent_t_path) if parent_t_path.exists() else None
if parent_t is None:
    parent_note="本次上游 Global Routing 用於產生同一電路的 guides 並確認零 overflow，未將其列為時序／電氣驗收。最終只使用重繞後的實際 extracted SPEF；前置負載預檢亦不替代本次驗收。"
elif parent_t["pass"]:
    parent_note="上游 Global RC 電氣預檢通過；最終驗收仍使用實際 routed SPEF。"
else:
    parent_note=(f"上游全 guides 的 Global RC 估算仍有 {parent_t['design__max_slew_violation__count']} 筆 slew、"
                 f"{parent_t['design__max_cap_violation__count']} 筆 capacitance 違規；未將這份估算列為電氣通過。"
                 "本次採保留既有導線的局部重繞，實際金屬不等同全新 guides 的整體估算。"
                 "最終驗收只接受正式 routed netlist 與實際 extracted SPEF 的零時序／電氣違規，不沿用該估算結論。")
text=f"""# Fault-V Routing 驗收報告

正式版本為 `{tag}`，使用的原生零溢位 Global Routing 為 `{global_tag}`。完成詳細繞線、上層天線修復、OpenRCX 萃取、TT 時序及電氣檢查。**本報告的 0 routing DRC 與 antenna closure 涵蓋工具支援的上層 LEF 規則，並非完整製程簽核。**

## 1．正式結果

| 項目 | 結果 |
| --- | --- |
| Clock／Corner | 40 ns／25 MHz；nom_tt_025C_1v80，1.8 V／25°C |
| 上游 Global Routing | 水平、垂直及總 overflow 均為 0；正式走線方案另見實作決策 |
| Router DRC | 0 |
| 上層 antenna 違規 nets | 0；修復後重新檢查 |
| 天線模型覆蓋 | {coverage['counts']['modeled_active_input_pins']:,} 個有效輸入；缺模型 0；每顆 SRAM 的 59 個 gate／64 個 diffusion 值已核對 |
| 新增 PDK 天線二極體 | {diodes['passive_diodes']:,} 顆；原有元件位置與接線保留 |
| 二極體實體連通 | {physical['diode_terminals']:,} 個 DIODE 端點與原訊號端點由實際金屬／via 組成同一連通分量；未連通 0 |
| 獨立全晶片 routing DRC 複查 | 原始 {drc['raw_marker_count']} 筆；{drc['confirmed_partition_artifacts']} 筆經逐筆置中複查確認為分區問題，未解 0 筆；已知兩處真實短路可被偵測 |
| Setup 最差裕量 | {s['setup_ws_ns']:.6f} ns |
| Hold 最差裕量 | {s['hold_ws_ns']:.6f} ns |
| Setup／Hold TNS 與違規數 | 均為 0 |
| Max slew／Capacitance 違規 | 均為 0 |
| SRAM addr0／wmask0 最大 slew | {s['max_macro_input_slew_ns']*1000:.2f} ps；限制 40 ps |
| 寄生參數 | OpenRCX 實際走線萃取；nominal RC 用於本次 TT 驗收 |
| Active signal／clock nets | {w['active_signal_clock_nets']:,}；全部具有 routed wires |
| 本層級 signal／clock wire 長度 | {w['native_wire_length_um']:,.3f} µm，不含 SRAM 內部與 PG 金屬 |
| Signal／clock via 實例數 | {w['decoded_vias']:,} |
| Power grid | VPWR／VGND 連通性通過；不是 IR／EM 簽核 |

## 2．實體配置與功能連接

| 項目 | 結果 |
| --- | --- |
| Instances | {g['instances']:,} |
| SRAM macros | 18 顆，位置與方向保持不變 |
| Flip-flops | 2925，未增加 CPU 架構狀態 |
| Clock sinks | 2961：2925 個 FF CLK＋36 個 SRAM clock pins |
| Active clock buffers | {g['active_clock_buffer_count']}；深度 {g['clock_buffer_depth_range'][0]}～{g['clock_buffer_depth_range'][1]} 級 |
| Signal pins | 108 個，位置與金屬形狀保留 |
| Standard-cell area | {g['stdcell_area_um2']:,.4f} µm²，包含實體與修整元件 |
| SRAM area | {g['macro_area_um2']:,.4f} µm² |
| PG geometry | 與來源 floorplan 的 special wires／vias 完全一致 |
| Placement | row、core boundary、重疊及 OpenROAD check_placement 通過 |

使用實際 Liberty 功能檢查 BUF／INV 相位與元件 signatures；{g['nonbuffer_instances']:,} 個非透明元件、{g['nonbuffer_endpoints']:,} 個功能端點及 {g['connected_components']:,} 組連接保持一致。驅動尺寸變體須具有相同邏輯／FF signatures；新 CTS dummy 僅在確認沒有輸出負載時排除。新增被動二極體先逐顆確認為未修改 PDK 的 CORE ANTENNACELL、僅一個 DIODE 訊號端及正確供電，再從功能端點中排除；所有既有端點、元件位置、PG 幾何及完整實體合法性仍需通過檢查。

另故意繞過一級 SRAM inverter，確認 checker 會偵測相位錯誤，隨後恢復。這是帶相位的連接證明，**不是 RTL formal equivalence**；本次沒有修改 ISA／FSM，也未重跑完整 Assembly 或 FPGA 實板回歸。

## 3．最終實作決策

CTS 原始 13 條 net 的非預設 routing-rule assignments 改為標準寬度／間距。保留 clock 接收端點與相位語意、40 ns SDC、SRAM 局部鏈、固定 macro 位置與供電骨架，再重新確認 clock 時序及電氣。變更清單與前後 ODB SHA 在 `reports/clock_routing_rules.json`。

Global Routing 採 `GRT_ADJUSTMENT=0`，表示不額外按比例扣除容量；macro避讓擴充為 {selected.get('global_macro_extension_gcells',0)} 個GCell。**這些設定不改變實體間距規則。**資源 {gr['resources']:,}、需求 {gr['demand']:,}、使用率 {gr['usage_pct']:.2f}%，各層 overflow 均為 0。先完成二極體放置及嚴格轉角限制，再產生零溢位導引線；最終詳細金屬另以原生與獨立全晶片 DRC、實體連通及實際 RC 驗證。

放置估算 RC 通過不足以保證繞線後電氣。本流程在 Global Routing 後先修整一般邏輯驅動與 hold，必要時再進行不重新鏡射元件的局部電氣修整；規劃階段以 OpenSTA 3.1.0 估算風險，最終以實際走線萃取值重新檢查。這些修改不增加指令 cycle。前置修整採 500 µm 長線修整門檻與 30% 電氣修整裕量；工具曾提示 RSZ-0065，較短分段可能增加導線延遲及 buffer 數量。本版以通過約束為基準，未宣稱最佳 PPA，後續再比較這項取捨。

{selected['routing_method_zh']}

SRAM 接腳資料由原始 GDS 與 sky130A Magic 技術檔提取；59 個輸入 gate 面積另與未裁剪 SPICE 階層的 W×L 總和全部相符，64 個輸出 diffusion 面積取自實體 GDS。新 LEF 只增加面積欄位，原尺寸、pin 金屬與 OBS 逐字保留。原始缺模型 ODB 送入相同 coverage 閘門時已如預期被拒絕，且沒有通過回執。查證過程、來源 SHA 與反例見 `reports/antenna_model/`。

## 4．時序、RC 與覆蓋

{parent_note}

使用隨包的未修改 OpenSTA 3.1.0，讀入正式 routed netlist、原始 SDC、TT standard-cell／SRAM Liberty 與 OpenRCX nominal SPEF，並明確確認 propagated clocks。32 個相同 SRAM 負載的 threshold regression 及內嵌 STA 2.7.0 的既有問題證據保留於 `reports/threshold_regression.json` 與 probe logs。

LibreLane 使用 `STAPrePNR` 包裝器名稱，但實際輸入由 `sta_state_{tag}.json` 明確指向 routed netlist 與 extracted SPEF，沒有以 placement-estimated RC 取代最終驗收。

寄生覆蓋列出 {t['unannotated_unused_output_drivers']} 個未標註、但已確認沒有有效負載的輸出，包括未使用的 SRAM 第二埠及 dummy 輸出。有效輸出缺少 RC 為 0，部分未標註 drivers 為 0。

另提供 min／max 導線 RC SPEF，**不等於已完成 SS／FF 的元件與 SRAM PVT 時序簽核**。本報告不宣稱最高頻率或實際應用能耗。

Wire decoder 的分支／via／POINT_EXT／patch 測試通過，分別記錄中心線長度與含端點延伸效果的 OpenDB 原生長度，表格採原生統計；同時核對所有 active nets 具有 wires。詳細 router 的 DRC 與 connectivity 過程保留原始紀錄；這不取代 foundry LVS。

## 5．交付與重現

| 項目 | 證據 |
| --- | --- |
| 輸入 Placement 網表 SHA-256 | `{source['netlist_sha256']}` |
| 最終網表 SHA-256 | `{s['netlist_sha256']}` |
| 最終 ODB SHA-256 | `{s['odb_sha256']}` |
| 凍結輸入／正式腳本／runtime | {len(locks['sha256'])} 個 SHA-256 |
| 使用 PDK／RC 模型 | 9 個關鍵檔案另行核對 SHA-256 |
| 實際驗證 | 各工具階段、幾何、連接、PG、RC 覆蓋與時序均已執行 |
| 重跑入口 | `bash scripts/run_selected.sh routing_reproduce`，保留來源輸入與固定工具版本 |
| 離線交付核對 | `python scripts/check_delivery.py`；另逐檔核對 ZIP CRC 與 SHA-256 |

交付包含正式 ODB、DEF、功能／供電網表、SDC、三份 extracted SPEF、設定與報告。先前中斷或仍有 DRC 的嘗試均未列入驗收；本報告只接受 {tag}。選用來源、原生 Tcl、設定及狀態記錄於 selected_flow.json，並核對 SHA-256。{selected['reproduction_scope_zh']}

負向校準先前已在獨立 OpenROAD process 中重讀已知錯誤快照，確認兩處真實 met1 短路在全晶片與置中上下文檢查中持續被偵測，並確認將錯誤快照送入正式門檻時會被拒絕。本次只有在來源 ODB、native checker、容器 image 與校準證據的 SHA-256 全部相符時，才重用該校準回執；正式 ODB 仍在新的 OpenROAD process 內執行全晶片 DRC，並對每筆回報進行置中上下文複查。只有同 net 的 li1 NS Metal／Spacing 回報在完整上下文中消失時，才記為分區問題，其餘未解回報必須為 0。詳細證據在 reports/{tag}/full_drc_checks.json 及原始報告。這項檢查仍不等於 foundry DRC／LVS。


另已從原始 CTS ODB 重新執行標準 clock rules、Global Routing、buffer／hold 修整與 Global RC 驗證，結果為零 overflow、零時序／slew／capacitance 違規；setup WS {repro['setup_ws_ns']:.6f} ns、hold WS {repro['hold_ws_ns']:.6f} ns。此項僅重跑前置流程，結果另存於 `reports/preparation_reproduction.json`，不宣稱重建相同 detailed-routing 幾何。

## 6．尚未完成的簽核

- Router 讀取技術 LEF 時出現 DRT-0349（LEF58_ENCLOSURE 缺 CUTCLASS）；不能把 routing DRC=0 解讀為這些未完整支援規則也已簽核。
- 上層 antenna 已在完整 pin 模型覆蓋下達到 0；這不涵蓋 SRAM 內部完整 foundry antenna signoff。
- 完整製程 DRC／LVS、filler／metal density、多 PVT、IR／EM、CDC／reset、DFT、pad／ESD／封裝及實體晶片量測尚待後續。
- reset_n 既定 false path 不代表 recovery／removal 已簽核；實作仍屬核心級，尚不是可直接送廠的完整晶片。

配置圖使用實際 routed centerlines，省略 PG 與 via 多邊形。後續進行瓶頸量測與設計優化時，若更動 RTL 或實體電路，需重新驗證相應 ASIC 流程。
"""
(R/"Verification_Report.md").write_text(text,encoding="utf-8",newline="\n")
print("Wrote accepted routed/extracted report")
