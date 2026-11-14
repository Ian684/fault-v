#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="${1:-routing_reproduce}"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ ]]
for t in "$tag" "${tag}_global" "${tag}_repair" "${tag}_repair_sta310" "${tag}_sta310"; do
  if [[ -e "runs/$t" ]]; then echo "Run already exists: $t" >&2;exit 1;fi
done
root="$(cd .. && pwd)"
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
python3 scripts/check_inputs.py
mkdir -p "$root/logs"
docker run --rm --user "$(id -u):$(id -g)" -v "$root:/work" -w /work/routing "$IMAGE" openroad -no_init -no_splash -exit -python scripts/prepare_clock_rules.py > "$root/logs/${tag}_clock_rules.log" 2>&1
bash scripts/run_global.sh "${tag}_global"
python3 scripts/check_global.py "${tag}_global"
bash scripts/run_repair.sh "${tag}_global" "${tag}_repair"
bash scripts/run_checks.sh "${tag}_repair" "${tag}_repair" global
bash scripts/run_detailed.sh "${tag}_repair" "$tag"
bash scripts/run_checks.sh "${tag}_repair" "$tag" routed
