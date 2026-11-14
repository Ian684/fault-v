from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
C=Path(__file__).resolve().parents[1];p=C/'WORK_STATE.json';r=json.loads(p.read_text())
r.update(updated_utc=datetime.now(timezone.utc).isoformat(),status='active_pin_access_and_original_LI1_island_preservation',W25_complete=False,selected_final_candidate=None,physical_candidate='No common-candidate acceptance; native_group_C has independent DRC 1 / antenna 1; native_group_M is the smaller branch-only trial',route_latest_marker_count=1)
r['in_progress']=[
 'Best completed independent native/context source remains group C: one true M2 short, one net2682 antenna violation, 41337 multi-terminal signal/clock nets geometrically connected, 7572 diode terminals.',
 'Group I is actively executing larger local workers on nine whole clock/signal nets with pinned Tcl mode 1=ALL. Whole-net all-reroute is compute-heavy; no completed step/candidate yet.',
 'Group L completed: 14 of 20 local diode branches pass native local DRC with new LI1 contained in the diode pin; six branches lacked a legal route. No full-layout candidate was emitted.',
 'Group M replays those 14 checked branches and reroutes the six remaining branches, allowing simple new LI1 islands while protecting every original signal LI1 shape and requiring M1-or-higher endpoints.',
 'Final common-candidate full GDS/core LVS/RCX/three-RC STA/GLS/activity/IR/EM/regenerated fill gates remain unrun.'
]
r['next_action']='Inspect native_group_m progress/results and native_group_i step results. Only independently DRC-clean, all-net-connected and antenna-zero source may enter run_final_candidate_c.sh. final_route_c alias and focus_post_b remain unused. Never promote internal zero counts alone.'
notes=[
 'Group E: nine-net from-scratch route ended with four reported shorts / one antenna; not selected.',
 'Groups F/G: retained initial routes + local guides, with/without regenerated native pin access, still one reported short / one antenna; not selected.',
 'Group H: Tcl manual mode 0 was DRC-only, not ALL. With initially empty marker list it returned zero without repair. Raw independent report still contains the real M2 short; context check exited 137 at 4GiB. No full independent passing report exists.',
 'li1_lift_a: naive LI1-to-M1 lift has 714 raw native markers, including 324 shorts; rejected.',
 'Remote single-net plans A/B: no legal path found; no physical candidate emitted.',
 'Group K initial branch trial stopped on an uninitialized replay set; corrected under unique group L namespace.'
]
r['not_promoted'] += [n for n in notes if n not in r['not_promoted']]
r.setdefault('evidence',{}).update(active_local_route='scripts/route_native_group_i.py',active_diode_branch_route='scripts/append_native_group_m.py',checked_14_branches='reports/native_group_l/incomplete.json',pinned_mode_mapping='controls/pinned_route_state_source/TritonRoute.cpp:195',mode0_nonpassing_raw_DRC='reports/native_group_h_independent.rpt',shell_LF_audit='reports/planned_shell_LF_20261101.json',corner_geometry='reports/native_corner_geometry/obstacles.json',corner_plot='reports/native_corner_geometry/corner_layers.png',prepared_final_pipeline='scripts/run_final_candidate_c.sh')
p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
(C.parents[2]/'W25_CLOSURE_PROGRESS.md').write_text('# W25 核心檢查進度\n\nW25 尚未完成，沒有通過全部共同版本檢查的最終候選。\n\n目前完整獨立驗證的 group C 仍有 1 處 M2 短路、1 條天線違規，41,337 條多端訊號／時脈網路均幾何連通。\n\n正在執行兩項不同範圍的修復：group I 以大視窗重繞 9 條網路；group M 保留原始全部接線，只補接新增二極體支線。短支線方案已有 14／20 條通過局部 DRC，剩 6 條以保護原有 LI1 元件的方式續接。這些局部結果尚不是全晶片通過證據。\n\n手動路由模式以固定版本原始碼為準：0＝DRC、1＝ALL、2＝NEARDRC。group H 的內部零計數因模式誤用不採用；其獨立原始報告仍有短路，後續 context 檢查在 4GiB 上限退出 137。後續獨立 DRC 上限已調為 7GiB。已修正 Windows 產生的 shell 換行並保存前後雜湊。\n\n手工 LI1 支線曾通過路由檢查，但完整 GDS 有 43 個 li.3 標記，已淘汰；57 個 LI1 修補雖消除 GDS 標記，卻增加 82 個獨立原生 DRC 違規，也未採用。沒有豁免真實 short 或 minimum-width 錯誤。\n\n路由收斂後仍須在同一候選上完成完整 GDS DRC、核心介面 LVS、新 RCX／三 RC 條件 TT STA、功能與活動、IR／EM、最終密度／填充檢查及封存。已準備具雜湊與實際數值門檻的批次流程。製程／SRAM 多角落、內部簽核與 fill-aware RCX 的既有覆蓋限制保留。DFT／pad／ESD 依使用者指定完成審查與需求，不含硬體實作。W25 與正式 PPA 都完成前不交付 Notion。\n',encoding='utf-8')
print('CURRENT_NATIVE_ROUTING_AND_BRANCH_CHECKPOINT_WRITTEN')
