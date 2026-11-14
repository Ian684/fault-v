"""Promote the project only after a fresh independent full-manifest verification."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,subprocess,sys
C=Path(__file__).resolve().parents[1];root=C.parents[2]
result=json.loads((C/'reports/W25_closure_result.json').read_text());assert result['W25_complete'] and not result['foundry_signoff_complete'] and not result['formal_PPA_comparison_complete']
subprocess.run([sys.executable,str(C/'scripts/seal_w25_evidence.py'),'verify'],check=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
manifest=json.loads((C/'W25_Evidence_Manifest.json').read_text());now=datetime.now(timezone.utc).isoformat()
receipt=C/'reports/W25_final_verification_receipt.json';assert not receipt.exists()
receipt.write_text(json.dumps({'verified_utc':now,'fresh_all_manifest_bytes_checked':True,'file_count':manifest['file_count'],'bytes':manifest['bytes'],'manifest_sha256':sha(C/'W25_Evidence_Manifest.json'),'result_sha256':sha(C/'reports/W25_closure_result.json'),'W25_research_scope_complete':True,'foundry_signoff_complete':False,'formal_PPA_complete':False,'W26_complete':False},indent=2)+'\n')
state=json.loads((C/'WORK_STATE.json').read_text())
state.update(updated_utc=now,status='W25_research_core_specified_checks_complete',W25_complete=True,foundry_signoff_complete=False,formal_PPA_comparison_complete=False,W26_complete=False,in_progress=[],final_candidate=result['source_route_sha256'],final_report='W25_Closure_Report.md',final_result='reports/W25_closure_result.json',manifest='W25_Evidence_Manifest.json',fresh_final_verification_receipt='reports/W25_final_verification_receipt.json',remaining_research_core_gates=[],manufacturing_release_blockers=result['qualified_release_blockers'])
state['previous_partial_achievements']=state.get('completed',[])
state['completed']=[
 'Final common-candidate independent full/context DRC 0, full real-macro core open-rule GDS DRC 0, pin-interface LVS 0 with 125 unique SRAM ports, top antenna net/pin 0.',
 'All 41337 multi-terminal signal/clock nets connected; real macro/stdcell/via stream and PG physical-contact audits pass.',
 'Fresh final-netlist min/nom/max-RC TT setup/hold/slew/cap counts all 0; reset/CDC 97 cycles/8 phases and four workload/activity gates pass.',
 'Final mixed-activity 14/28mW per-SRAM static IR/average EM screens pass; regenerated full-source fill/density/grid/FOM/BEOL interaction gates pass.',
 'DFT/pad/ESD review and requirements complete under user scope; no scan/MBIST/pad-ring hardware qualification claimed.',
 'Final evidence manifest independently re-read and every recorded byte count and SHA256 verified before this status promotion.'
]
(C/'WORK_STATE.json').write_text(json.dumps(state,indent=2)+'\n')
post=json.loads((C/'reports/final_post_verified.json').read_text())
text='''# W25 核心檢查結案

W25 已依使用者確認的研究核心範圍完成，所有指定檢查已在同一個最終候選上通過，證據逐檔 SHA256 重讀驗證完成。

- 原生／完整鄰域 DRC 0、完整幾何核心開源 GDS DRC 0、核心／125-pin SRAM 介面 LVS 0、上層 antenna net／pin 0。
- 41,337 條多端訊號／時脈網路全部幾何連通；VPWR／VGND 無面積、邊緣或點接觸。
- Fresh RCX 三 RC 條件的 TT setup／hold／slew／cap 均無違規。
- Reset／CDC 97 cycles、8 種解除相位及四個活動工作負載通過；routed-net 映射 100%，未知狀態限制保留。
- 最終 fill 的七個數值密度層各 1,053 視窗通過，八層 5nm grid、FOM 幾何與 post-fill BEOL 互動通過。
- 最終 mixed 活動及 14／28mW 每 SRAM 假設下，四組靜態 IR／平均 EM 研究篩檢通過。
- DFT／pad／ESD 完成審查與需求，不含 scan／MBIST／pad ring 硬體實作。

完整報告：[W25_Closure_Report.md](work/fault-v-asic/week25_closure/W25_Closure_Report.md)。數值、模型覆蓋、修復前後、未解問題及製造阻擋項均列於報告。

這是研究版結案，完整 foundry／SRAM 內部、多 PVT、fill-aware PEX、類比 reset／CDC、封裝與可靠度仍未簽核，不能直接送廠。正式 PPA 比較尚未完成，W26 正式交付尚未開始；依使用者要求，W25 與正式 PPA 均完成前不交付 Notion。
'''
(root/'W25_CLOSURE_PROGRESS.md').write_text(text)
plan=(root/'PROJECT_PLAN.md').read_text()
plan=re.sub(r'(?m)^\| \*\*W25\*\* \|.*$', '| **W25** | STA、DRC、LVS、Antenna；物理修復、模型、reset／CDC、DFT／pad／ESD 審查需求、density 與 IR／EM | 同版指定檢查、修復前後、模型覆蓋與製造阻擋清單 | **研究核心指定範圍已完成**；完整 foundry／SRAM／多 PVT／fill-aware PEX 等製造資格仍未通過 |',plan)
start=plan.index('## W25：');end=plan.index('## ASIC PPA 延伸',start)
section='''## W25：研究核心指定檢查已完成

最終結果見 [W25 結案報告](E:/Codex/Fault_V_W24_Transfer/work/fault-v-asic/week25_closure/W25_Closure_Report.md)、[機器可讀結果](E:/Codex/Fault_V_W24_Transfer/work/fault-v-asic/week25_closure/reports/W25_closure_result.json) 及 [證據 manifest](E:/Codex/Fault_V_W24_Transfer/work/fault-v-asic/week25_closure/W25_Evidence_Manifest.json)。所有列入 manifest 的檔案已重新讀取核對 byte 數與 SHA256。

同一候選已完成原生／完整鄰域 DRC、完整幾何核心開源 GDS DRC、核心／125-pin SRAM 介面 LVS、上層 antenna、fresh 三 RC TT STA、41,337 條多端網路幾何連通、PG 接觸、reset／CDC 與四工作負載活動、兩種 SRAM 負載的靜態 IR／平均 EM，以及最終重新產生的 fill／density／BEOL 互動檢查。

使用者選定 DFT／pad／ESD 僅完成審查與需求，本輪已完成；沒有 scan／MBIST／pad ring 實作。研究版結案不代表可直接送廠：完整 foundry 與 SRAM 內部規則、多 PVT 模型、fill-aware PEX、類比 recovery／removal／CDC MTBF、package／thermal／transient／current crowding 等資格仍列為製造阻擋項。

歷史凍結預檢及失敗試跑保留；最新結論以 week25_closure 同版驗收為準，沒有用舊空宏或單項通過代替完整結果。W25 與正式 PPA 均完成後才分別交付 Notion。

'''
(root/'PROJECT_PLAN.md').write_text(plan[:start]+section+plan[end:])
print('W25_RESEARCH_SCOPE_STATUS_PROMOTED_AFTER_FRESH_MANIFEST_VERIFICATION',manifest['file_count'],now,flush=True)
