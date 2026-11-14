#!/usr/bin/env bash
# PG-repaired H1 candidate (eco/pg_h1_f): full-chip native DRC + antenna -> package as runs/h1c_pg_r1 ECO-run layout ->
# signoff/run_signoff_c.sh h1c_pg_r1 -> signoff/run_activity_cov_c.sh. Log eco/logs/h1c_driver.log, last line H1C_DRIVER_END ...
set -uo pipefail
cd "$(dirname "$0")/.."
root="$(cd ../../.. && pwd)"; log=eco/logs/h1c_driver.log; W=/work/ppa/h1/cand_gap90x95
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
say() { echo "$(date -Is) $*" >> "$log"; }
ODB=$W/eco/pg_h1_f/fault_v_asic_top.odb
if [ ! -f eco/pg_h1_f/independent.json ]; then
  say "start: native DRC on $ODB"
  docker run --rm --name faultv-h1c-pgdrc --user 1000:1000 --memory=7000m --cpus=2 -e ROUTE_DRC_ODB=$ODB \
      -e ROUTE_DRC_REPORT=$W/eco/pg_h1_f/independent.json -v "$root:/work" -w $W "$image" \
      openroad -exit -python /work/routing/scripts/native_route_drc.py > eco/logs/h1c_pg_drc.log 2>&1
  say "native DRC rc=$?"
fi
if [ ! -f eco/logs/h1c_pg_antenna.log ]; then
  docker run --rm --name faultv-h1c-pgant --user 1000:1000 --memory=6000m --cpus=2 -e ODB=$ODB -e OUT_JSON=$W/eco/pg_h1_f/antenna.json \
      -v "$root:/work" -w $W "$image" openroad -exit -python eco/pg_antenna_check.py > eco/logs/h1c_pg_antenna.log 2>&1
fi
# check_antennas writes its counts to the log (ANT-0002 nets, ANT-0001 pins); the -report_file stays empty when clean
python3 - <<'EOF'
import json, re
from pathlib import Path
log = Path('eco/logs/h1c_pg_antenna.log').read_text()
nets = re.findall(r'ANT-0002\] Found (\d+) net violations', log); pins = re.findall(r'ANT-0001\] Found (\d+) pin violations', log)
assert len(nets) == 1 and len(pins) == 1
p = Path('eco/pg_h1_f/antenna.json'); d = json.loads(p.read_text()); d.update(net_violations=int(nets[0]), pin_violations=int(pins[0]), source='eco/logs/h1c_pg_antenna.log')
p.write_text(json.dumps(d, indent=2) + '\n')
EOF
say "antenna from log: $(grep -h -E 'ANT-000[12]' eco/logs/h1c_pg_antenna.log | tr '\n' ' ')"
python3 - >> "$log" 2>&1 <<'EOF'
import json, hashlib, shutil
from pathlib import Path
c = Path('.')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
drc = json.loads(Path('eco/pg_h1_f/independent.json').read_text()); ant = json.loads(Path('eco/pg_h1_f/antenna.json').read_text())
src = Path('eco/pg_h1_f/fault_v_asic_top.odb'); assert drc['odb_sha256'] == sha(src)
print('PG candidate native DRC unresolved', drc['unresolved_count'], 'raw', drc['raw_marker_count'], 'antenna', ant['net_violations'], ant['pin_violations'])
assert drc['unresolved_count'] == 0 and ant['net_violations'] == 0 and ant['pin_violations'] == 0
step = Path('runs/h1c_pg_r1/01-openroad-detailedrouting'); step.mkdir(parents=True, exist_ok=False)
for name in ('fault_v_asic_top.odb', 'eco_final.odb'): shutil.copyfile(src, step / name)
assert sha(step / 'eco_final.odb') == sha(src)
(step / 'fault_v_asic_top.drc').write_text('')
state = json.loads(Path('runs/h1b_eco_rf5/01-openroad-detailedrouting/state_out.json').read_text())
state['odb'] = '/work/ppa/h1/cand_gap90x95/runs/h1c_pg_r1/01-openroad-detailedrouting/fault_v_asic_top.odb'
(step / 'state_out.json').write_text(json.dumps(state, indent=2) + '\n')
(step / 'eco_result.json').write_text(json.dumps({'native_DRC': 0, 'antenna_nets': 0, 'cleared_nets': 0, 'iterations': 0,
    'source': 'h1b_eco_rf5 + PG via4 EM repair passes a-f (eco/pg_h1_a..f); signal wires, cells and graph unchanged',
    'independent_native_DRC': {'raw': drc['raw_marker_count'], 'partition_artifacts': drc['confirmed_partition_artifacts'], 'unresolved': 0},
    'antenna': {'nets': 0, 'pins': 0}, 'odb_sha256': sha(src)}, indent=2) + '\n')
print('H1C_PACKAGED', sha(src))
EOF
[ $? -eq 0 ] || { say "H1C_DRIVER_END packaging failed"; exit 1; }
say "signoff c start"
bash signoff/run_signoff_c.sh h1c_pg_r1
say "signoff c: $(tail -n 1 signoff/logs_c/chain.log)"
case "$(tail -n 1 signoff/logs_c/chain.log)" in *"SIGNOFF_END post=0 sta=0 lvs=0 lvs_bad=0 functional=0 power=0"*) ;; *) say "H1C_DRIVER_END signoff not clean"; exit 1 ;; esac
bash signoff/run_activity_cov_c.sh >> "$log" 2>&1
say "H1C_DRIVER_END activity cov rc=$?"
