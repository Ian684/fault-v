#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="${1:?new native tag}"
[[ ! -e runs/global_desktop_joint_corner ]]
owner=faultv-<host>_desktop_corner_bypass_20261026_145204
[[ "$(docker inspect -f '{{.State.Running}} {{.State.Paused}}' "$owner")" == 'true false' ]]
docker pause "$owner" >/dev/null
trap 'docker unpause "$owner" >/dev/null' EXIT
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name faultv-joint-corner-global --memory=6500m --memory-swap=6500m --cpus=16 --user 1000:1000 -v "$root:/work" -w /work/routing "$image" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/routing/desktop_joint_corner_global_state.json --run-tag global_desktop_joint_corner config_desktop_joint_corner_global.json > ../logs/global_desktop_joint_corner.log 2>&1
python3 scripts/check_global.py global_desktop_joint_corner
docker run --rm --memory=2500m --cpus=2 --user 1000:1000 -v "$root:/work" -w /work/routing "$image" openroad -exit -python scripts/prepare_desktop_joint_corner_native.py > ../logs/prepare_desktop_joint_corner_native.log 2>&1
bash scripts/run_desktop_joint_corner_native.sh "$tag"
# The child returns zero only after actual guarded acceptance; retire the obsolete paused trial.
docker stop --time 5 "$owner" > ../logs/joint_corner_retired_parent.log 2>&1
trap - EXIT
