#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source_tag="$1"
tag="$2"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ ]]
[[ ! -e "runs/$tag" ]]
python3 scripts/prepare_detailed.py "$source_tag" "$tag"
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
root="$(cd .. && pwd)"
docker run --rm --user "$(id -u):$(id -g)" -v "$root:/work" -w /work/routing "$IMAGE" python3 -m librelane --pdk-root /work/pdk --with-initial-state "/work/routing/detailed_state_${tag}.json" --run-tag "$tag" config_detailed.json > "$root/logs/$tag.log" 2>&1
