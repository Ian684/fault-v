#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="$1"; config="$2"; state="$3"; cli="$4"; memory="$5"; cpus="$6"
[[ "$tag" =~ ^[a-z0-9_]+$ ]]
root="$(cd .. && pwd)";native="/var/tmp/faultv-w25-native-runs/$tag"
test ! -e "$native"; test ! -e "runs/$tag"
install -d -m1777 "$native"
mkdir "runs/$tag"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
rc=0
docker run --rm --name "faultv-w25-$tag" --env SRAM_BUDGET_W --user 1000:1000 --memory="$memory" --cpus="$cpus" -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime:ro -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -v "$native:/work/week25_closure/runs/$tag" -w /work/week25_closure "$image" python3 "$cli" --pdk-root /work/pdk --with-initial-state "/work/week25_closure/$state" --run-tag "$tag" "$config" > "logs/$tag.log" 2>&1 || rc=$?
printf '%s\n' "$rc" > "logs/$tag.flow_exit"
docker run --rm --name "faultv-w25-$tag-archive" --user 1000:1000 --memory=1500m --cpus=1 -v "$root:/work" -v "$native:/native_run:ro" "$image" python3 /work/week25_closure/scripts/archive_native_run.py "/work/week25_closure/runs/$tag" "$tag" > "logs/$tag.archive.log" 2>&1
printf '%s\n' "$rc" > "logs/$tag.exit"
exit "$rc"
