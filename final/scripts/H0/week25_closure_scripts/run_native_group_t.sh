#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)";image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/native_group_t.exit' EXIT
docker run --rm --name faultv-w25-native-group-t --user 1000:1000 --memory=6000m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime:ro -v /var/tmp/faultv-w25-finalprep:/runtime_final -w /work/week25_closure "$image" openroad -exit -python scripts/append_native_group_t.py > logs/native_group_t.log 2> logs/native_group_t.err.log
python3 -c 'import json;assert json.load(open("reports/native_group_t/result.json"))["antenna_nets"]==0'
bash scripts/run_native_candidate_checks.sh native_group_t antenna_native_t
