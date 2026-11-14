#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
pdk='/work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71'
trap 'rc=$?; printf "%s\n" "$rc" > logs/fill_tile.exit' EXIT
python3 scripts/prepare_fill_tile.py
docker run --rm --user 1000:1000 --memory=1000m -e PDK_ROOT="$pdk" -e PDK=sky130A -v "$root:/work" -w /work/week25_closure/fill_tile_trial "$image" python3 "$pdk/sky130A/libs.tech/magic/generate_fill.py" fault_v_asic_top.gds -keep -test > logs/fill_tile_prepare.log 2>&1
python3 - <<'PY'
from pathlib import Path
p=Path('fill_tile_trial/generate_fill.tcl');s=p.read_text()
line='set ytiles [expr {int(ceil(($fullheight + 0.0) / $stepheight))}]'
assert s.count(line)==1
s=s.replace(line,line+'\n# Diagnostic coverage: one native fill tile only.\nset xtiles 1\nset ytiles 1')
p.write_text(s)
PY
docker run --rm --name faultv-w25-fill-tile --user 1000:1000 --memory=5000m --cpus=1 -e PDK_ROOT="$pdk" -e PDK=sky130A -v "$root:/work" -w /work/week25_closure/fill_tile_trial "$image" magic -dnull -noconsole -T "$pdk/sky130A/libs.tech/magic/sky130A-GDS.tech" generate_fill.tcl > logs/fill_tile.log 2>&1
