#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
trap 'rc=$?; printf "%s\n" "$rc" > logs/pg_g_stream_audits.exit' EXIT
test "$(cat logs/pg_g_stream_a.exit)" = 0
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name faultv-w25-pg-f-via-audit --user 1000:1000 --memory=2500m --cpus=1 -v "$root:/work" -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -w /work/week25_closure "$image" openroad -exit -python scripts/export_native_vias.py /runtime_final/pg_compact_g.odb reports/pg_g_native_vias.json > logs/pg_g_via_audit.log 2>&1
docker run --rm --name faultv-w25-pg-f-stream-audit --user 1000:1000 --memory=4000m --cpus=1 -e AUDIT_CORE_GDS=/work/week25_closure/runs/pg_g_stream_a/1-klayout-streamout/fault_v_asic_top.gds -e AUDIT_MACRO_GDS=/work/week25_closure/macros/sky130_sram_2kbyte_1rw1r_32x512_8.orphan_trim_dedup.gds -e AUDIT_REPORT=reports/pg_g_macro_audit.json -v "$root:/work" -w /work/week25_closure "$image" bash -c 'set -e; python3 scripts/audit_stream_macro.py; python3 scripts/audit_final_stdcell_stream.py runs/pg_g_stream_a/1-klayout-streamout/fault_v_asic_top.gds inputs/pg_compact_g.def reports/pg_g_stdcell_audit.json reports/pg_g_native_vias.json' > logs/pg_g_stream_audits.log 2>&1
