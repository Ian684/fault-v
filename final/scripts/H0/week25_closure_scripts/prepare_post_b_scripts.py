from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/prepare_final_post.py').read_text().replace('final_route_selection.json','final_route_selection_b.json').replace('runtime_final_route_odb.json','runtime_final_route_b_odb.json').replace('/runtime/final_route.odb','/runtime/final_route_b.odb').replace('final_post_state.json','final_post_state_b.json').replace('config_focus_post.json','config_focus_post_b.json')
targets={'prepare_final_post_b.py':code,'prepare_focus_post_sta_b.py':(C/'scripts/prepare_focus_post_sta.py').read_text().replace('focus_post_a','focus_post_b').replace('focus_post_sta','focus_post_sta_b')}
for name,code in targets.items():
    p=C/'scripts'/name;assert not p.exists();compile(code,str(p),'exec');p.write_text(code)
print('COMMON_POST_B_SCRIPTS_PREPARED')
