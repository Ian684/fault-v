#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/li1_rule_replay.exit' EXIT
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name faultv-w25-li1-rule-baseline --user 1000:1000 --memory=4000m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" klayout -b -r controls/li3_replay.drc -rd input=/work/week25_closure/runs/focus_post_a/2-klayout-streamout/fault_v_asic_top.gds -rd report=/work/week25_closure/reports/li1_baseline_replay.rdb > logs/li1_baseline_replay.log 2>&1
docker run --rm --name faultv-w25-li1-rule-fixed --user 1000:1000 --memory=4000m --cpus=2 -v "$root:/work" -w /work/week25_closure "$image" klayout -b -r controls/li3_replay.drc -rd input=/work/week25_closure/inputs/li1_spacing_simulated.gds -rd report=/work/week25_closure/reports/li1_fixed_replay.rdb > logs/li1_fixed_replay.log 2>&1
