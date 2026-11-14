#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)";image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/native_group_q.exit' EXIT
docker run --rm --name faultv-w25-q-mask-plan --user 1000:1000 --memory=4000m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/plan_q_li1_closure.py > logs/q_li1_plan.log 2>&1
docker run --rm --name faultv-w25-q-mask-replay --user 1000:1000 --memory=4000m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" klayout -b -r controls/li3_replay.drc -rd input=/work/week25_closure/inputs/m_li1_closed_wide.gds -rd report=/work/week25_closure/reports/q_li1_replay.rdb > logs/q_li1_replay.log 2>&1
python3 -c 'import xml.etree.ElementTree as E;from pathlib import Path;r=E.parse("reports/q_li1_replay.rdb").getroot();assert len(r.findall("categories/category"))==2 and not r.findall("items/item")'
docker run --rm --name faultv-w25-q-native-apply --user 1000:1000 --memory=5000m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-finalprep:/runtime_final -w /work/week25_closure "$image" openroad -exit -python scripts/apply_native_group_q.py > logs/q_native_apply.log 2>&1
bash scripts/run_final_candidate_c.sh native_group_q antenna_native_q
