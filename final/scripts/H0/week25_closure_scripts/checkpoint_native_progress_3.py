from pathlib import Path
from datetime import datetime,timezone
import json
C=Path(__file__).resolve().parents[1];root=C.parents[2]
state=json.loads((C/'WORK_STATE.json').read_text())
state.update(updated_utc=datetime.now(timezone.utc).isoformat(),status='active_four_added_passive_diode_relocation',W25_complete=False,foundry_signoff_complete=False)
state['in_progress']=[
 'Group P: native/context unresolved 0, all 41337 multi-terminal signal/clock nets connected, 7572 diode terminals, antenna 0; source SHA4028c63683b00402ee608f3d84ee2b3d26b1725caf99f765c0be574a0526db34.',
 'Group M actual full GDS has 23 LI1 self-spacing notches, all associated with five long newly added diode LI1 branches. These are real, not waived.',
 'Group R found one of five inside-pin mcon/M1/M2 replacements. Four remaining diode locations are boxed in by existing M1/M2 wiring.',
 'Group V replays the one checked R branch and searches empty same-phase rows for only ANTENNA_7559/7560/7567/7572, retaining all original cells, logical connectivity, PG and unaffected wire bytes.',
 'The same final candidate must still pass full native/context and full GDS DRC, core/pin-interface LVS, fresh 3-RC TT STA, GLS/activity, IR/EM and regenerated fill/density gates.'
]
state['not_promoted']+=['Group Q: 29 LI1 gap patches remove projected GDS notches but create 51 real independent native violations (33 Short and 18 spacing); rejected.', 'Group I mode1=ALL full local worker produced 38866 internal DRVs and was stopped; no accepted candidate.', 'Groups T/U guard failures: diode OBS were required; corrected in V with transformed actual native OBS. No output ODB was produced.']
(C/'WORK_STATE.json').write_text(json.dumps(state,indent=2)+'\n')
text='''# W25 核心檢查進度

W25 尚未完成，仍沒有通過全部共同版本檢查的最終候選。

Group P 已通過獨立原生／context DRC（未解 0）、41,337 條多端訊號／時脈網路幾何連通及上層天線 0。其完整 GDS 來源仍有 23 項 LI1 自身間距問題，已定位為五條新增二極體支線形成的狹縫。

Group Q 的間隙補金屬雖消除投影 GDS 標記，卻造成 51 項真實原生 DRC，已拒絕採用。Group R 找到其中一顆的接腳內合法 mcon／M1／M2 接法，其餘四顆被既有 M1／M2 線包圍。Group V 正僅搬移這四顆新增被動二極體至合法空位，逐一驗證放置與接線；既有邏輯元件、網路連接及供電幾何不變。

Group I 大視窗重繞已停止，沒有選用；所有失敗與診斷證據保留。沒有豁免真實 short、minimum-width 或 spacing 違規。

接線修復後仍須在同一候選上完成完整 GDS DRC、核心介面 LVS、新 RCX／三 RC 條件 TT STA、功能與活動、IR／EM、最終密度／填充及證據封存。模型／規則、SRAM 內部、fill-aware PEX、類比 reset／CDC、封裝可靠度限制需逐項列明。DFT／pad／ESD 依指定範圍完成審查與需求，不含硬體實作。W25 與正式 PPA 都完成前不交付 Notion。
'''
assert root.name=='Fault_V_W24_Transfer',root
(root/'W25_CLOSURE_PROGRESS.md').write_text(text)
print('CURRENT_PROGRESS_RECORDED',state['updated_utc'])
