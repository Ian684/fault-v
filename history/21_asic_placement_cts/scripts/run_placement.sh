#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
task_root="$(cd .. && pwd)"
tag="${1:-placement_initial}"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ ]]
mkdir -p "$task_root/logs"
docker run --rm --user "$(id -u):$(id -g)" -v "$task_root:/work" -w /work/placement_cts "$IMAGE" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/placement_cts/initial_state.json --from OpenROAD.GlobalPlacement --to OpenROAD.STAMidPNR-2 --run-tag "$tag" config.json > "$task_root/logs/$tag.log" 2>&1
