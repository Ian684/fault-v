#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/final_core_lvs.exit' EXIT
test "$(cat logs/focus_post_b.exit)" = 0
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name faultv-w25-final-core-view --user 1000:1000 --memory=3000m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/build_core_lvs_view.py runs/focus_post_b/2-klayout-streamout/fault_v_asic_top.gds inputs/final_core_lvs.gds inputs/final_badpin_lvs.gds reports/final_core_lvs_view.json > logs/final_core_view.log 2>&1
native=/var/tmp/faultv-w25-closure-20261101/final_core_lvs.gds
test ! -e "$native"
cp inputs/final_core_lvs.gds "$native"
test "$(sha256sum inputs/final_core_lvs.gds | cut -d' ' -f1)" = "$(sha256sum "$native" | cut -d' ' -f1)"
python3 scripts/prepare_final_core_lvs.py
bash scripts/run_native_flow.sh final_core_lvs_a config_final_core_lvs.json final_core_lvs_state.json scripts/core_lvs_cli.py 3500m 1
