from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/export_li1_drc_context.py').read_text().replace('runs/focus_post_a','runs/native_m_stream_a').replace('len(items)==43','len(items)==23').replace("'markers':43","'markers':23").replace('reports/li1_actual_context.json','reports/m_li1_actual_context.json')
p=C/'scripts/export_m_li1_context.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
code=(C/'scripts/prepare_native_group_o.py').read_text().replace('native_group_o','native_group_p').replace('from collections import Counter','from collections import Counter,defaultdict')
p=C/'scripts/prepare_native_group_p.py';assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('M_LI1_ANALYSIS_AND_P_REPLAY_PREPARED')
