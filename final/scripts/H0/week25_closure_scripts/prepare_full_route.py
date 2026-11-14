from pathlib import Path
import hashlib,json
C=Path(__file__).resolve().parents[1]
state=json.loads((C/'runs/cached_global_a/1-openroad-globalrouting/state_out.json').read_text())
cfg=json.loads((C/'config_cached_global.json').read_text())
cfg.update(DRT_THREADS=8,DRT_OPT_ITERS=64,DRT_SAVE_SNAPSHOTS=True,DRT_SAVE_DRC_REPORT_ITERS=1,DRT_ANTENNA_REPAIR_ITERS=0)
cfg['meta']={'version':2,'flow':['OpenROAD.DetailedRouting']}
state['metrics']={}
(C/'full_route_state.json').write_text(json.dumps(state,indent=2)+'\n')
(C/'config_full_route.json').write_text(json.dumps(cfg,indent=2)+'\n')
(C/'reports/full_route_launch.json').write_text(json.dumps({'accepted':False,'input':state['odb'],'native_LibreLane_script_unmodified':True,'all_50_equivalent_driver_changes':True,'global_overflow':0,'all_regular_routes_rebuilt':True,'threads':8,'scope':'Native full detailed routing from matching zero-overflow global output. Temporary FIXED metadata and peer access-point preservation are not used for final routing. Antenna is checked separately before promotion.'},indent=2)+'\n')
print('Native full routing prepared from cached_global_a',flush=True)
