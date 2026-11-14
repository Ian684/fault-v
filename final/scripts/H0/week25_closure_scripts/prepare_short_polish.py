"""Initialize a complete native routing pass without ripping up the connected B routes."""
from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1]
run=C/'runs/short_cover_b/1-openroad-detailedrouting'
proof=json.loads((C/'reports/short_b_final_independent.json').read_text())
stage=json.loads((C/'reports/runtime_signal_b_odb.json').read_text())
with (run/'native_final.odb').open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==proof['odb_sha256']==stage['sha256']
assert proof['unresolved_count']==4
state=json.loads((run/'state_out.json').read_text());state.update(odb='/runtime/signal_b.odb',metrics={})
for k in ('gds','klayout_gds','spef','def'):state.pop(k,None)
cfg=json.loads((C/'config_short_cover_b.json').read_text());cfg.update(DRT_THREADS=8,DRT_OPT_ITERS=12)
tcl=(C/'scripts/short_cover_b.tcl').read_text().replace('set_thread_count 4','set_thread_count 8').replace('-or_seed 7','-or_seed 19').replace('-droute_end_iter 32','-droute_end_iter 12').replace('SHORT_COVER_B_FINAL','SHORT_POLISH_FINAL')
for name,code in [('short_polish_state.json',json.dumps(state,indent=2)+'\n'),('config_short_polish.json',json.dumps(cfg,indent=2)+'\n'),('scripts/short_polish.tcl',tcl),('scripts/short_polish_cli.py',(C/'scripts/short_cover_b_cli.py').read_text().replace('short_cover_b.tcl','short_polish.tcl'))]:
    p=C/name;assert not p.exists();p.write_text(code)
(C/'reports/short_polish_input.json').write_text(json.dumps({'source_sha256':proof['odb_sha256'],'input_routes_unchanged':True,'input_independent_DRC':4,'accepted':False,'scope':'Complete detailed_route initialization and native optimization; independent full/context DRC and all-net geometry must verify the final output.'},indent=2)+'\n')
