from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
C=Path(__file__).resolve().parents[1];root=C.parents[2]
read=lambda p:json.loads((C/p).read_text())
dr=read('reports/native_group_w_independent.json');cn=read('reports/native_group_w_all_connectivity.json');selection=read('reports/final_route_selection_c.json');proof=read('reports/native_group_w/result.json');inv=read('reports/final_route_c_invariants.json')
assert dr['unresolved_count']==proof['antenna_nets']==0 and cn['all_signal_geometry_connected'] and cn['checked_multi_terminal_signal_clock_nets']==41337
with (C/'inputs/native_group_w.odb').open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
assert digest==proof['output_sha256']==dr['odb_sha256']==cn['source_sha256']==selection['source_sha256']==inv['source_sha256']
state=read('WORK_STATE.json');state.update(updated_utc=datetime.now(timezone.utc).isoformat(),status='common_candidate_selected_full_GDS_and_final_checks_running',W25_complete=False,foundry_signoff_complete=False,selected_common_candidate_sha256=digest)
state['in_progress']=['Selected group W source '+digest+': independent full/context DRC unresolved 0, all 41337 multi-terminal signal/clock nets connected, antenna net/pin 0; exact export and original-cell/graph/PG binding passed.', 'Five LI1 branches replaced with inside-pin LI1 + M1/M2, only four newly inserted passive diodes relocated/flipped into checked empty native rows. All original cells/connectivity and PG geometry remain unchanged.', 'focus_post_b full real-macro GDS DRC, fresh RCX/3-RC TT STA running. Core-interface LVS, stream/PG audit, fresh GLS/activity, final IR/EM and regenerated fill/density remain gated on same-source results.']
(C/'WORK_STATE.json').write_text(json.dumps(state,indent=2)+'\n')
(root/'W25_CLOSURE_PROGRESS.md').write_text('''# W25 核心檢查進度

W25 尚未完成，最終共同候選已選定，正在完整 GDS 與後續指定檢查。

Group W 已通過：全晶片原生／完整鄰域 DRC 未解 0、41,337 條多端訊號／時脈網路全部連通、上層 antenna net／pin 0、確切匯出與原元件／接線／供電幾何一致性。五條長 LI1 支線已替換成接腳內 LI1＋M1／M2 接法，其中四顆新增被動二極體搬移／翻轉至經檢查的空 row。

目前 focus_post_b 執行完整實際 SRAM 幾何的 GDS DRC 與 fresh RCX／三 RC TT STA。其後同版 gate 包含核心／125-pin SRAM 介面 LVS、stream／via／PG 接觸、filler 後原生 DRC／連通、reset／CDC 與四工作負載活動，以及最終靜態 IR／平均 EM、重新產生 fill／density／BEOL 互動與證據封存。全部通過前 W25_complete 維持 false。

失敗與診斷試跑保留；未豁免真實 short、minimum-width 或 spacing。完整製程／SRAM 內部、多 PVT、fill-aware PEX、類比 reset／CDC 與封裝可靠度限制須列入最終報告。DFT／pad／ESD 僅審查與需求。W25 與正式 PPA 均完成前不交付 Notion。
''')
print('VERIFIED_W_COMMON_CANDIDATE_CHECKPOINT',digest)
