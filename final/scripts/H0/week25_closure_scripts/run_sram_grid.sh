#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/sram_grid.exit' EXIT
docker run --rm --name faultv-w25-sram-grid-prepare --user 1000:1000 --memory=3500m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" klayout -b -r scripts/prepare_sram_grid.py > logs/sram_grid_prepare.log 2>&1
docker run --rm --name faultv-w25-sram-grid-drc --user 1000:1000 --memory=6500m --cpus=1 -e PDK_ROOT=/work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71 -v "$root:/work" -w /tmp "$image" magic -dnull -noconsole -rcfile /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.tech/magic/sky130A.magicrc /work/week25_closure/scripts/sram_grid_drc.tcl > logs/sram_grid_DRC.log 2>&1
