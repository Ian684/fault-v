#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/pg_g_lvs_checks.exit' EXIT
test "$(cat logs/pg_g_stream_a.exit)" = 0
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name faultv-w25-pg-e-view --user 1000:1000 --memory=3000m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/build_core_lvs_view.py /work/week25_closure/runs/pg_g_stream_a/1-klayout-streamout/fault_v_asic_top.gds inputs/pg_g_core_lvs.gds inputs/pg_g_badpin_lvs.gds reports/pg_g_core_lvs_view.json > logs/pg_g_core_view.log 2>&1
test ! -e /var/tmp/faultv-w25-closure-20261101/pg_g_core_lvs.gds
cp inputs/pg_g_core_lvs.gds /var/tmp/faultv-w25-closure-20261101/pg_g_core_lvs.gds
test "$(sha256sum inputs/pg_g_core_lvs.gds | cut -d' ' -f1)" = "$(sha256sum /var/tmp/faultv-w25-closure-20261101/pg_g_core_lvs.gds | cut -d' ' -f1)"
python3 scripts/prepare_pg_g_lvs.py
bash scripts/run_native_flow.sh pg_g_core_lvs_a config_pg_g_core_lvs.json pg_g_core_lvs_state.json scripts/core_lvs_cli.py 3500m 1
