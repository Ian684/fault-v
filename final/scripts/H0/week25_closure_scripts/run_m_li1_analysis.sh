#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)";image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/m_li1_analysis.exit' EXIT
docker run --rm --name faultv-w25-m-li1-export --user 1000:1000 --memory=4000m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" openroad -exit -python scripts/export_m_li1_context.py > logs/m_li1_export.log 2>&1
docker run --rm --name faultv-w25-m-li1-analysis --user 1000:1000 --memory=4000m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/analyze_m_li1_components.py > logs/m_li1_analysis.log 2>&1
docker run --rm --name faultv-w25-native-group-p --user 1000:1000 --memory=6000m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime:ro -v /var/tmp/faultv-w25-finalprep:/runtime_final -w /work/week25_closure "$image" openroad -exit -python scripts/prepare_native_group_p.py > logs/native_group_p.log 2> logs/native_group_p.err.log
