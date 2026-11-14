#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/sram_exact_drc.exit' EXIT
docker run --rm --name faultv-w25-sram-exact-drc --user 1000:1000 --memory=4000m --cpus=1 -e PDK_ROOT=/work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71 -v "$root:/work" -w /tmp "$image" magic -dnull -noconsole -rcfile /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.tech/magic/sky130A.magicrc /work/week25_closure/scripts/sram_exact_drc.tcl > logs/sram_exact_DRC.log 2>&1
python3 - <<'PY'
from pathlib import Path
log=Path('logs/sram_exact_DRC.log').read_text()
assert 'FAULTV_SRAM_GEOMETRY_PRESENT' in log and 'FAULTV_SRAM_EXACT_GRID_DRC_COMPLETE' in log
assert 'Error while reading' not in log and "couldn't be read" not in log and 'Cannot read this file' not in log
PY
