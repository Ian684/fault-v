#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="${1:-global_initial}"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ ]]
[[ ! -e "runs/$tag" ]]
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
root="$(cd .. && pwd)"
mkdir -p "$root/logs"
docker run --rm --user "$(id -u):$(id -g)" -v "$root:/work" -w /work/routing "$IMAGE" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/routing/initial_state.json --run-tag "$tag" config_global.json > "$root/logs/$tag.log" 2>&1
