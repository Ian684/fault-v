#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="$1"
scope="$2"
python3 scripts/prepare_sta.py "$tag" "$scope"
chmod +x sta_tool/sta sta_tool/sta.bin
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
root="$(cd .. && pwd)"
docker run --rm --user "$(id -u):$(id -g)" -v "$root:/work" -w /work/routing "$IMAGE" python3 scripts/sta310_cli.py --pdk-root /work/pdk --only OpenROAD.STAPrePNR --with-initial-state "/work/routing/sta_state_${tag}.json" --overwrite --run-tag "${tag}_sta310" config_sta.json > "$root/logs/${tag}_sta310.log" 2>&1
