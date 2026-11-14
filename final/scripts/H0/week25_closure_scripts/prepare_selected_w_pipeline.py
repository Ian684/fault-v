from pathlib import Path
C=Path(__file__).resolve().parents[1]
code=(C/'scripts/run_final_candidate_c.sh').read_text()
needle='bash scripts/run_native_candidate_checks.sh "$stem" "$tag"';assert code.count(needle)==1
guard='test "$stem" = native_group_w\ntest "$tag" = antenna_native_w\ntest "$(cat logs/${tag}_checks.exit)" = 0\n'
guard+="python3 -c 'import json;r=json.load(open(\"reports/antenna_native_w_export_binding.json\"));assert r[\"all_exported_cells_graph_PG_wire_bytes_guides_obstructions_equal_checked_source\"]'"
code=code.replace(needle,guard)
p=C/'scripts/run_final_selected_w.sh';assert not p.exists();p.write_text(code,newline='\n');print('SELECTED_W_PIPELINE_READY')
