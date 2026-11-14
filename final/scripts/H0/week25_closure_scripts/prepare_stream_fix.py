from pathlib import Path
import json
C=Path(__file__).resolve().parents[1]
config=json.loads((C.parent/'week25_front/config_fill.json').read_text())
config['meta']={'version':2,'flow':['KLayout.StreamOut']}
config['KLAYOUT_CONFLICT_RESOLUTION']='OverwriteCell'
assert next(iter(config['MACROS'].values()))['gds']
(C/'config_stream_fix.json').write_text(json.dumps(config,indent=2)+'\n')
print('Use the native stream-out with explicit OverwriteCell for cleared LEF shells.')
