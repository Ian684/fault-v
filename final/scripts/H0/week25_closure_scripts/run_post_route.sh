#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/post_route.exit' EXIT
docker run --rm --user 1000:1000 --memory=3500m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" openroad -exit -python scripts/normalize_protected_route.py > logs/normalization.log 2>&1
docker run --rm --name faultv-w25-post-route --user 1000:1000 --memory=6500m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/week25_closure/post_route_state.json --run-tag post_route_a config_post_route.json > logs/post_route.log 2>&1
python3 scripts/prepare_post_sta.py
docker run --rm --name faultv-w25-post-sta --user 1000:1000 --memory=3000m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" python3 /work/routing/scripts/sta310_cli.py --pdk-root /work/pdk --with-initial-state /work/week25_closure/post_sta_state.json --run-tag post_sta_a config_post_sta.json > logs/post_sta.log 2>&1
docker run --rm --name faultv-w25-independent-drc --user 1000:1000 --memory=4000m --cpus=4 -e ROUTE_DRC_ODB=/work/week25_closure/runs/post_route_a/1-openroad-fillinsertion/fault_v_asic_top.odb -e ROUTE_DRC_REPORT=/work/week25_closure/reports/post_route_native.json -v "$root:/work" -w /work/week25_closure "$image" openroad -exit -python /work/routing/scripts/native_route_drc.py > logs/post_independent_drc.log 2>&1
