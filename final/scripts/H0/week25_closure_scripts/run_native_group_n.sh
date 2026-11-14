#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/native_group_n.exit' EXIT
while [[ ! -f reports/native_m_geometry_verified.json ]]; do
  if [[ -f logs/native_m_geometry.exit ]]; then test "$(cat logs/native_m_geometry.exit)" = 0; fi
  sleep 5
done
docker run --rm --name faultv-w25-native-group-n --user 1000:1000 --memory=5000m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime:ro -v /var/tmp/faultv-w25-finalprep:/runtime_final -w /work/week25_closure "$image" openroad -exit -python scripts/repair_native_group_n.py > logs/native_group_n.log 2> logs/native_group_n.err.log
while [[ ! -f logs/native_m_geometry.exit ]]; do sleep 5; done
test "$(cat logs/native_m_geometry.exit)" = 0
python3 -c 'import json;from pathlib import Path;C=Path(".");d=json.load(open("runs/native_m_stream_a/3-klayout-drc/state_out.json"));assert d["metrics"]["klayout__drc_error__count"]==0;assert json.load(open("runs/native_m_stream_a/native_archive_manifest.json"))["all_byte_exact"]'
bash scripts/run_final_candidate_c.sh native_group_n antenna_native_n
