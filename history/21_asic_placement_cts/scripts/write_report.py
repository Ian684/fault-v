"""Write the evidence report from the accepted release, separate from design notes."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
s=json.loads((R/"accepted_summary.json").read_text())
assert s["run"]=="placement_release" and s["accepted"]
g=json.loads((R/"reports/placement_release/placement_checks.json").read_text())
t=json.loads((R/"reports/placement_release/timing_checks.json").read_text())
candidate=json.loads((R/"reports/placement_candidate/timing_checks.json").read_text())
cg=json.loads((R/"reports/placement_candidate/placement_checks.json").read_text())
a=json.loads((R/"reports/input_driver_anchors.json").read_text())
lock=json.loads((R/"input_identity.json").read_text())
repro={"pass":g["pass"] and t["pass"] and candidate["pass"] and cg["pass"],
"candidate":"placement_candidate","fresh_release":"placement_release",
"source_floorplan_sha256":a["source_sha256"],
"fresh_pipeline":"anchor_inputs -> GlobalPlacement through STAMidPNR-2 -> post-CTS electrical repair -> corrected STA -> physical/connectivity checks -> guarded acceptance",
"frozen_input_count":len(lock["sha256"]),
"candidate_netlist_sha256":cg["netlist_sha256"],
"release_netlist_sha256":g["netlist_sha256"],
"netlist_byte_identical":cg["netlist_sha256"]==g["netlist_sha256"],
"scope":"Both runs must independently pass; identical PnR bytes are not an acceptance requirement."}
assert repro["pass"]
(R/"reports/reproduction.json").write_text(json.dumps(repro,indent=2)+"\n")
text=f"""# Fault-V Placement／CTS 驗收報告

完成標準元件放置、Clock Tree Synthesis、CTS 後修整，並從凍結的原始輸入完整重跑驗收。正式輸出為 `placement_release`；候選版為 `placement_candidate`。這是 **TT、放置估算 RC、propagated clock** 的階段驗收，尚非繞線後或送廠簽核。

## 1．正式結果

| 項目 | 結果 |
| --- | --- |
| Clock | 40 ns／25 MHz，uncertainty 0.25 ns |
| Timing corner | `nom_tt_025C_1v80`，1.8 V／25°C |
| 最差 setup 裕量 | **{s['setup_ws_ns']:.6f} ns** |
| 最差 hold 裕量 | **{s['hold_ws_ns']:.6f} ns** |
| Setup／Hold TNS | 均為 0 |
| Setup／Hold 違規 | 均為 0 |
| Max slew／Max capacitance 違規 | 均為 0 |
| SRAM 受限輸入最大 slew | **{s['max_macro_input_slew_ns']*1000:.2f} ps**；上限 40 ps |
| 最大 slew 接腳 | `{s['max_macro_input_slew_pin']}` |
| 供電網路連通性違規 | 0；VPWR／VGND 均通過 OpenROAD PSM |
| 寄生參數 | 實體工具 `estimate_parasitics -placement -spef_file` 輸出；尚未經 routing extraction |

沒有把正裕量換算為保證的最高工作頻率；未涵蓋其他 PVT 與實際導線 RC。

## 2．幾何、連接與時脈

| 檢查 | 證據與結果 |
| --- | --- |
| 全部元件 | {s['instances']:,} 個 instances；所有標準元件均 placed／fixed |
| Macro | 18 顆 SRAM；位置與方向和來源 floorplan 完全一致 |
| 外部訊號接腳 | 108 個，位置與金屬形狀保留 |
| 放置合法性 | 自訂 row／overlap／core boundary 檢查與 OpenROAD `check_placement` 均通過 |
| 標準元件總面積 | {s['stdcell_area_um2']:,.4f} µm²，包含 tap、endcap、CTS／修整元件 |
| SRAM 總面積 | {s['macro_area_um2']:,.4f} µm² |
| Flip-flops | 2925，未新增架構狀態 |
| Clock sinks | 2961：2925 個 FF CLK＋36 個 SRAM clock pins |
| 實際使用的 clock buffers | {s['active_clock_buffer_count']}，由 `clk` 沿實際正相 buffer 網路追蹤統計 |
| Clock buffer 深度 | {s['clock_buffer_depth_range'][0]}～{s['clock_buffer_depth_range'][1]} 級 |
| 電源幾何 | 和來源 floorplan 的 special wires／vias 完全一致 |
| PG 接腳 | {g['connected_pg_iterms']:,} 個實例 PG 接腳檢查，連接至正確電源網路 |

`clock_named_or_clock_master_instances` 包含資料路徑中使用的 clock 類元件，不能當作 CTS 的實際 buffer 數；本表使用從根時脈可達的有效 buffer 數。SRAM 第二讀取埠停用，但其 `clk1` 仍受時脈樹驅動。

連接證明以實際 Liberty 的 BUF／INV 功能及元件邏輯／FF signatures 為依據，建立帶相位的連通分組。保持 **{g['nonbuffer_instances']:,} 個非透明元件、{g['nonbuffer_endpoints']:,} 個功能端點、{g['connected_components']:,} 組連接**。只允許功能一致的驅動尺寸變體、正確的 buffer／inverter 鏈與已確認沒有輸出負載的 CTS dummy cells。{g['resized_nonbuffer_cells']} 個非透明元件更換驅動尺寸，功能 signatures 一致。

額外在記憶體中故意繞過 SRAM 鏈的一級 inverter，驗證相位錯誤確實被偵測，隨後恢復原連接。這不是 RTL formal equivalence；本階段未重跑全部 CPU RTL 程式或帶延遲 gate-level 模擬。

## 3．SRAM 電氣修整

來源 floorplan 的 234 個 address／write-mask 驅動鏈經過實體放置後，長導線使原始兩級 BUF 鏈無法維持 40 ps 輸入限制。先量測候選 cell 組合，再採 **BUF_4 → INV_16 → INV_16**，將末兩級靠近 SRAM pin 固定在合法 rows。兩次反相保持原有資料極性。另為 576 個 `dout0` 接腳加入 BUF_4，隔離長負載。

局部 buffer 電路是組合邏輯，不增加 FF、ISA 功能或 FSM cycle。保留原始 SDC 與 Liberty；沒有提高 40 ps 上限，也沒有以 false path 排除 SRAM 受限接腳。最後一次原生電氣修整處理了普通邏輯網路的剩餘負載問題。

`reports/input_driver_anchors.json` 記錄每個元件的實際位置、接腳距離，以及來源／衍生 ODB 的 SHA-256。最後一級到 macro pin 的最大 Manhattan 距離約 {a['max_last_pin_manhattan_um']:.3f} µm；SRAM 讀出接腳到隔離 buffer 的最大距離約 {a['max_readout_pin_manhattan_um']:.3f} µm。

## 4．時序工具與 RC 覆蓋

固定容器內的 OpenROAD 使用內嵌 STA 2.7.0。小型回歸測試在同一個 driver 接到 32 個相同 SRAM 負載時，重現混合 slew threshold 的轉換異常：相同負載的 slew 從約 0.46854 ns 失真至約 3498.22 ns。隨包、未修改 upstream 的 OpenSTA 3.1.0 對同一測試得到 32 個一致的約 0.46854 ns。原始紀錄在 `reports/threshold_regression.json` 及兩份 probe logs。

實體最佳化仍由固定版 OpenROAD 執行；**驗收數值只使用 OpenSTA 3.1.0**。後者讀入 CTS 後網表、同一份 TT libraries、實體工具輸出的估算 SPEF 與既定 SDC，明確設定並查驗 propagated clocks。報告內可看到實際 clock buffers 與 network delay；不採用理想時脈或零線電容來宣稱通過。

LibreLane 階段名稱沿用 `STAPrePNR` 包裝器，其名稱不代表本次分析輸入。實際輸入與依據記錄於 `sta_state_placement_release.json` 和 `runs/placement_release_sta310/`。

寄生覆蓋報告列出 {t['unannotated_unused_output_drivers']} 個未標註的輸出 drivers，逐一對照 OpenDB 確認沒有有效負載，包括未使用的 SRAM 第二埠輸出與 CTS dummy 輸出。**有效輸出缺少 RC 為 0，部分未標註 drivers 為 0**，不是直接忽略 coverage 警告。

## 5．重現與交付

| 項目 | 紀錄 |
| --- | --- |
| 來源 floorplan ODB SHA-256 | `{a['source_sha256']}` |
| 正式網表 SHA-256 | `{s['netlist_sha256']}` |
| 凍結輸入 | {len(lock['sha256'])} 個：設計輸入、設定、正式腳本、STA runtime |
| 關鍵 PDK | 另驗證 4 個技術 LEF／cell LEF／TT Liberty 檔案的 SHA-256 |
| 候選版 | 幾何、連接、PG、時序與電氣檢查均通過 |
| 全新重跑 | 從原始 floorplan 重新建立局部鏈，再完整執行放置／CTS／修整／驗收，全部通過 |
| 重跑網表 | {'與候選版位元組相同' if repro['netlist_byte_identical'] else '允許放置最佳化差異；獨立通過全部驗收'} |
| 交付核對 | `scripts/check_delivery.py` 核對 manifest、輸入鎖定、正式 tag 與 handoff 路徑 |
| 繞線輸入 | `handoff_state.json` 的 ODB／DEF／網表／SDC；不攜帶舊的估算 SPEF |

`logs/placement_release_all.log` 保留全流程完成紀錄；各工具 command、resolved config、metrics、state、報告與正式 views 保留於交付包。單次中間時序中使用內嵌 STA 的結果僅保留作診斷，不取代本報告的更正分析。

## 6．仍待後續處理

- 尚未 Global／Detailed Routing；放置階段 RUDY 的可繞線性估算未達目標，不能視為已證明可繞通。下一階段需檢查擁塞，必要時調整擺放或邊界。
- 只有 TT／1.8 V／25°C 的 SRAM 模型，尚未完成 SS／FF、多角落或 foundry-qualified signoff。
- reset_n false path 沿用既定約束；未宣稱 recovery／removal 或 reset-domain crossing 已簽核。
- SRAM LEF 的 59 個 inputs 缺 antenna gate metadata，64 個 outputs 缺 diffusion metadata；繞線／antenna 流程仍須處理。
- 尚未完整 DRC／LVS、antenna closure、實際金屬 RC extraction、IR drop／EM、製造測試、pad／ESD／封裝整合或實體晶片量測。
- 此階段未產出新的 FPGA bitstream；現有 FPGA 功能驗證不等於 ASIC 製造簽核。

下一個工程階段是 Routing，並以繞線後的 RC 重新做時序與電氣修整。
"""
(R/"Verification_Report.md").write_text(text,encoding="utf-8",newline="\n")
print("Wrote accepted release report and reproduction evidence")
