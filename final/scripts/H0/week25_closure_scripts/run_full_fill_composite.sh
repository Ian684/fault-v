#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
trap 'rc=$?; printf "%s\n" "$rc" > logs/full_fill_composite.exit' EXIT
python3 scripts/canonicalize_fill.py full_fill_development/fault_v_asic_top_fill_pattern.gds.gz full_fill_development/canonical_fill.gds.gz > logs/full_fill_conversion.log 2>&1
docker run --rm --name faultv-w25-fill-composite --user 1000:1000 --memory=5500m --cpus=1 -v "$root:/work" -w /work/week25_closure "$image" python3 scripts/compose_fill.py runs/trimmed_full_drc_a/1-klayout-streamout/fault_v_asic_top.gds full_fill_development/canonical_fill.gds.gz full_fill_development/fault_v_asic_top.filled.gds.gz > logs/full_fill_compose.log 2>&1
