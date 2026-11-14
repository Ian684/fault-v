#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
stem="$1";tag="$2"
[[ "$stem" =~ ^native_(upper_[a-z]|group_[a-z])$ && "$tag" =~ ^[a-z0-9_]+$ ]]
trap 'rc=$?; printf "%s\n" "$rc" > "logs/${tag}_checks.exit"' EXIT
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name "faultv-w25-${tag}-independent" --user 1000:1000 --memory=7000m --cpus=2 -e "ROUTE_DRC_ODB=/runtime_final/$stem.odb" -e "ROUTE_DRC_REPORT=/work/week25_closure/reports/${stem}_independent.json" -v "$root:/work" -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -w /work/week25_closure "$image" openroad -exit -python /work/routing/scripts/native_route_drc.py > "logs/${stem}_independent.log" 2>&1
docker run --rm --name "faultv-w25-${tag}-connectivity" --user 1000:1000 --memory=4000m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -w /work/week25_closure "$image" openroad -exit -python scripts/audit_all_signal_connectivity.py "/runtime_final/$stem.odb" "reports/${stem}_all_connectivity.json" > "logs/${stem}_connectivity.log" 2>&1
python3 scripts/prepare_native_verified_export.py "$stem" "$tag"
bash scripts/run_native_flow.sh "$tag" "config_$tag.json" "${tag}_state.json" scripts/native_verified_export_cli.py 4000m 2
docker run --rm --name "faultv-w25-${tag}-binding" --user 1000:1000 --memory=6000m --cpus=2 -v "$root:/work" -v "/var/tmp/faultv-w25-native-runs/$tag:/work/week25_closure/runs/$tag:ro" -w /work/week25_closure "$image" openroad -exit -python scripts/audit_manual_export_binding.py "$tag" "${stem}_independent.json" "${tag}_export_binding.json" > "logs/${tag}_export_binding.log" 2>&1
