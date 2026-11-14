from pathlib import Path
from datetime import datetime,timezone
import json
C=Path(__file__).resolve().parents[1];p=C/'WORK_STATE.json';r=json.loads(p.read_text())
r.update(updated_utc=datetime.now(timezone.utc).isoformat(),status='active_native_neighborhood_routing_repair',W25_complete=False,selected_final_candidate=None,physical_candidate='native_group_c completed snapshot: independent DRC 1, antenna 1; native_group_e is an unaccepted nine-net trial',route_latest_marker_count=1)
r['in_progress']=[
 'Native group C completed iteration11: independent/context DRC has one real MET2 short between net3347/net5547 at (1583.55,639.71)um; antenna net2682 remains at _30882_/A. All 41337 multi-terminal signal/clock nets connected; 7572 diode terminals.',
 'The same native iteration12 full stream has zero LI1 width/spacing replay markers; full-deck final-candidate acceptance is still pending.',
 'Native group B final iteration20 has two router-reported short markers and one antenna violation. Group C is independently verified to have fewer real markers. Whole-neighbor rollback and bounded single-net planner trials rejected.',
 'Actual local DRC identifies M3 net3311 and M4 nets3177/4842 blocking bridge sites. Native group E releases these three along with the prior six nets, preserving all other 41328 wire byte sequences after temporary routing protection.',
 'Final common-candidate full GDS DRC, core LVS, fresh three-RC STA, activity, IR/EM and regenerated fill gates remain mandatory.'
]
r['next_action']='Finish native_group_e; remove temporary FIXED status by restoring exact original protected bytes; require zero independent/context DRC, all-net connectivity and antenna. Export only verified source and use a new final_route_c runtime alias. No promotion of rejected LI1 closure.'
r['not_promoted']+= [x for x in [
 'focus_post_a: route DRC/connectivity/antenna and STA pass, but full GDS has 43 li.3 errors; rejected.',
 'li1_spacing: 57 actual-GDS patches remove the 43 LI1 rule markers but introduce 82 independently confirmed native DRC violations (including shorts/minimum width); rejected.'
] if x not in r['not_promoted']]
r.setdefault('evidence',{}).update(native12_DRC='reports/antenna_iter12_independent.json',native12_connectivity='reports/antenna_iter12_all_connectivity.json',native12_LI1_replay='reports/native12_li1_replay.rdb',li1_rejected='reports/li1_spacing_independent.json',native_group_C_DRC='reports/native_group_c_independent.json',native_group_C_connectivity='reports/native_group_c_all_connectivity.json',native_group_trial='scripts/route_native_group_e.py')
p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
progress=C.parents[2]/'W25_CLOSURE_PROGRESS.md'
progress.write_text('# W25 核心檢查進度\n\nW25 尚未完成，目前沒有通過全部共同版本檢查的最終候選。\n\n最新獨立驗證的 group C：原生 DRC 剩 1 處 M2 短路、天線 1 條；41,337 條多端訊號／時脈網路實際幾何連通。原始 native iteration12 完整 GDS 的 LI1 寬度／間距規則重播為 0；group C 後續仍須重跑完整 GDS。實際跨接試驗找出 3 條 M3／M4 阻擋線，group E 正重繞共 9 條網路，其餘 41,328 條需逐位元恢復。\n\n先前路由與 STA 通過的手工分支因完整 GDS 有 43 個 li.3 錯誤而淘汰；57 個 LI1 修補雖消除這些 GDS 標記，卻產生 82 個原生 DRC 違規，也已淘汰。沒有豁免真實 short 或 minimum-width 錯誤。\n\n路由修復後仍須在同一候選上完成完整 GDS DRC、核心介面 LVS、新 RCX／三 RC 條件 STA、功能與活動、IR／EM、最終密度／填充檢查及封存。既有規則／SRAM 角落與 fill-aware RCX 覆蓋限制保留。DFT／pad／ESD 依使用者指定完成審查與需求，不含實體實作。PPA 正式比較仍另列，兩者完成前不交付 Notion。\n',encoding='utf-8')
print('NATIVE_NEIGHBORHOOD_CHECKPOINT_WRITTEN')
