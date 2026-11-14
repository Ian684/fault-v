#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="${1:?new run tag}"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ && ! -e "runs/$tag" && ! -e "../logs/$tag.exit" ]]
python3 scripts/check_inputs.py
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
python3 - "$tag" <<'PY'
from pathlib import Path
import hashlib,json,sys,datetime
r=Path('.'); tag=sys.argv[1]; sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((r/'reports/antenna_model/candidate_input.json').read_text())
assert a['pass'] and not a['accepted'] and a['routing_cells_graph_PG_guides_obstructions_unchanged']
assert sha(r/a['derived'])==a['derived_sha256'] and sha(r/a['source'])==a['source_sha256']
c=json.loads((r/'config_antenna_closure.json').read_text())
assert c['CLOCK_PERIOD']==40 and c['DRT_OPT_ITERS']==64 and c['ERROR_ON_TR_DRC'] is True
assert c['DRT_ANTENNA_REPAIR_ITERS']==5 and c['DRT_ANTENNA_REPAIR_DIODE_ONLY'] is True
c['DRT_THREADS']=8
(r/f'config_{tag}.json').write_text(json.dumps(c,indent=2)+'\n')
files=['scripts/antenna_closure_cli.py','scripts/drt_antenna_closure.tcl',f'config_{tag}.json','antenna_model_state.json','reports/antenna_model/candidate_input.json','reports/antenna_model/sram_antenna_model.json','macros/sky130_sram_2kbyte_1rw1r_32x512_8.antenna.lef']
receipt={'accepted':False,'run':tag,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'threads':8,'memory_mb':6500,'sha256':{p:sha(r/p) for p in files},'input_sha256':a['derived_sha256'],'scope':'Candidate antenna repair; all physical/RC/STA gates still required.'}
(r/f'reports/{tag}_launch.json').write_text(json.dumps(receipt,indent=2)+'\n')
PY
set +e
docker run --rm --name "faultv-$tag" --user 1000:1000 --memory=6500m --memory-swap=6500m --cpus=8 -v "$root:/work" -w /work/routing "$image" python3 scripts/antenna_closure_cli.py --pdk-root /work/pdk --with-initial-state /work/routing/antenna_model_state.json --run-tag "$tag" "config_${tag}.json" > "$root/logs/$tag.log" 2>&1
result=$?
printf '%s\n' "$result" > "$root/logs/$tag.exit"
python3 - "$tag" "$result" <<'PY'
from pathlib import Path
import json,sys,datetime
p=Path('reports')/(sys.argv[1]+'_launch.json'); a=json.loads(p.read_text()); a['native_exit']=int(sys.argv[2]); a['native_finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
p.write_text(json.dumps(a,indent=2)+'\n')
PY
exit "$result"
