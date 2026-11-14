"""Reuse the calibrated PG check pipeline with fresh G-only tags and artifacts."""
from pathlib import Path
C=Path(__file__).resolve().parents[1]
for name in ('run_pg_f_checks.sh','prepare_pg_f_lvs.py','run_pg_f_lvs.sh','run_pg_f_stream_audits.sh','verify_pg_f_result.py'):
    source=C/'scripts'/name;dest=C/'scripts'/name.replace('pg_f','pg_g');assert not dest.exists()
    code=source.read_text().replace('pg_f','pg_g').replace('pg_compact_f','pg_compact_g').replace('PG_F','PG_G')
    if name=='verify_pg_f_result.py':
        code=code.replace("assert dr['unresolved_count']==0", "assert dr['unresolved_count']==0")
        needle="gds=C/'runs/pg_g_stream_a/1-klayout-streamout/fault_v_asic_top.gds'"
        assert code.count(needle)==1
        code=code.replace(needle,needle+"\ncontacts=read('reports/pg_g_contacts.json');baseline=read('reports/pg_baseline_contacts.json')\nassert contacts['source_ODB_sha256']==digest and contacts['no_VPWR_VGND_copper_contact'] and baseline['no_VPWR_VGND_copper_contact']\nassert baseline['source_ODB_sha256']=='fe627dd4b1ff4c152dcfa9dd5d08b05c13b7272ab4065d7f0cb8af3d87dd1380'")
        code=code.replace("'four_controlled_average_EM_cases_pass':True", "'four_controlled_average_EM_cases_pass':True,'PG_contact_geometry_pass':True,'via4_array_replacements':181,'via4_cuts_at_planned_positions':1430,'compacted_three_cut_row_feed':True")
    if dest.suffix=='.py':compile(code,str(dest),'exec')
    dest.write_text(code,newline='\n')
print('Prepared five G-only pipeline scripts.')
