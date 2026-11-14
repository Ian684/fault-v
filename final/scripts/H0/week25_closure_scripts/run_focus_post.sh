#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/focus_post.exit' EXIT
install -d -m1777 /tmp/faultv-w25-finalprep
docker run --rm --name faultv-w25-focus-pg-prepare --user 1000:1000 --memory=3500m --cpus=1 -v "$root:/work" -v /tmp/faultv-w25-closure-20261030:/runtime:ro -v /tmp/faultv-w25-finalprep:/runtime_final -w /work/week25_closure "$image" openroad -exit -python scripts/prepare_focus_pg.py > logs/focus_pg_prepare.log 2>&1
docker run --rm --name faultv-w25-focus-post --user 1000:1000 --memory=7000m --cpus=2 -v "$root:/work" -v /tmp/faultv-w25-finalprep:/runtime_final:ro -w /work/week25_closure "$image" python3 -m librelane --pdk-root /work/pdk --with-initial-state /work/week25_closure/focus_post_state.json --run-tag focus_post_a config_focus_post.json > logs/focus_post.log 2>&1
python3 scripts/prepare_focus_post_sta.py
docker run --rm --name faultv-w25-focus-post-sta --user 1000:1000 --memory=3000m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" python3 /work/routing/scripts/sta310_cli.py --pdk-root /work/pdk --with-initial-state /work/week25_closure/focus_post_sta_state.json --run-tag focus_post_sta_a config_focus_post_sta.json > logs/focus_post_sta.log 2>&1
