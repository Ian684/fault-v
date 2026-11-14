#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="${1:-placement_release}"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ ]]
for t in "$tag" "${tag}_build" "${tag}_sta310"; do
  if [[ -e "runs/$t" ]]; then echo "Run already exists: $t" >&2; exit 1; fi
done
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
root="$(cd .. && pwd)"
mkdir -p "$root/logs"
python3 scripts/check_inputs.py
docker run --rm --user "$(id -u):$(id -g)" -v "$root:/work" -w /work/placement_cts "$IMAGE" openroad -exit -python scripts/anchor_inputs.py > "$root/logs/${tag}_anchors.log" 2>&1
bash scripts/run_placement.sh "${tag}_build"
bash scripts/run_late.sh "${tag}_build" "$tag"
bash scripts/run_sta.sh "$tag"
docker run --rm --user "$(id -u):$(id -g)" -e "PLACEMENT_RUN_TAG=$tag" -v "$root:/work" -w /work/placement_cts "$IMAGE" openroad -exit -python scripts/check_placement.py > "$root/logs/${tag}_checks.log" 2>&1
docker run --rm --user "$(id -u):$(id -g)" -e "PLACEMENT_RUN_TAG=$tag" -v "$root:/work" -w /work/placement_cts "$IMAGE" openroad -exit scripts/check_physical.tcl > "$root/logs/${tag}_physical.log" 2>&1
python3 scripts/check_timing.py "$tag"
python3 scripts/accept_phase.py "$tag"
echo "ALL PLACEMENT / CTS RELEASE CHECKS PASSED: $tag"
