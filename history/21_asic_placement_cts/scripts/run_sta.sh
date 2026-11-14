#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
task_root="$(cd .. && pwd)"
tag="${1:-placement_initial}"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ ]]
python3 scripts/prepare_sta.py "$tag"
docker run --rm --user "$(id -u):$(id -g)" -v "$task_root:/work" -w /work/placement_cts "$IMAGE" python3 scripts/sta310_cli.py --pdk-root /work/pdk --only OpenROAD.STAPrePNR --with-initial-state "/work/placement_cts/sta_state_${tag}.json" --overwrite --run-tag "${tag}_sta310" config_sta.json > "$task_root/logs/${tag}_sta310.log" 2>&1
