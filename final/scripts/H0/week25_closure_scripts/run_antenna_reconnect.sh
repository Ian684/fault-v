#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/antenna_reconnect.exit' EXIT
test "$(cat logs/antenna_insert_b.exit)" = 0
native=/var/tmp/faultv-w25-closure-20261101/antenna_inserted.odb
test ! -e "$native"
cp runs/antenna_insert_b/1-openroad-detailedrouting/inserted.odb "$native"
test "$(sha256sum runs/antenna_insert_b/1-openroad-detailedrouting/inserted.odb | cut -d' ' -f1)" = "$(sha256sum "$native" | cut -d' ' -f1)"
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name faultv-w25-antenna-access --user 1000:1000 --memory=4500m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime:ro -v /var/tmp/faultv-w25-finalprep:/runtime_final -w /work/week25_closure "$image" openroad -exit -python scripts/prepare_antenna_access.py antenna_insert_b > logs/antenna_access.log 2>&1
docker run --rm --name faultv-w25-antenna-pins --user 1000:1000 --memory=2500m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -w /work/week25_closure "$image" openroad -exit -python scripts/audit_antenna_ready_pins.py > logs/antenna_ready_pins.log 2>&1
bash scripts/run_native_flow.sh antenna_route_a config_antenna_route.json antenna_route_state.json scripts/antenna_route_cli.py 6500m 4
