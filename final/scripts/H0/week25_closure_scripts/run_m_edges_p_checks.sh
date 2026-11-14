#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)";image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/m_edges_p_checks.exit' EXIT
docker run --rm --name faultv-w25-m-edge-ownership --user 1000:1000 --memory=4000m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/analyze_m_edge_ownership.py > logs/m_li1_edges.log 2>&1
bash scripts/run_native_candidate_checks.sh native_group_p antenna_native_p
