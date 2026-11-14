#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/native_group_f.exit' EXIT
while docker inspect faultv-w25-native-group-e >/dev/null 2>&1; do sleep 3; done
docker run --rm --name faultv-w25-native-group-f --user 1000:1000 --memory=10000m --cpus=4 -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime:ro -v /var/tmp/faultv-w25-finalprep:/runtime_final -w /work/week25_closure "$image" openroad -exit -python scripts/route_native_group_f.py > logs/native_group_f.log 2> logs/native_group_f.err.log
python3 -c 'import json;d=json.load(open("reports/native_group_f/result.json"));assert d["router_reported_DRC"]==d["antenna_nets"]==0,d'
bash scripts/run_final_candidate_c.sh native_group_f antenna_native_f
