#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="${1:?new native tag}"
[[ ! -e runs/global_desktop_corner_refined ]]
[[ -z "$(docker ps -q)" ]]
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name faultv-corner-refined-global --memory=12000m --memory-swap=12000m --cpus=16 --user 1000:1000 -v "$root:/work" -w /work/routing "$image" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/routing/desktop_corner_refined_global_state.json --run-tag global_desktop_corner_refined config_desktop_corner_refined_global.json > ../logs/global_desktop_corner_refined.log 2>&1
python3 scripts/check_global.py global_desktop_corner_refined
docker run --rm --memory=2500m --cpus=2 --user 1000:1000 -v "$root:/work" -w /work/routing "$image" openroad -exit -python scripts/prepare_desktop_corner_refined_native.py > ../logs/prepare_desktop_corner_refined_native.log 2>&1
bash scripts/run_desktop_corner_refined_native.sh "$tag"
