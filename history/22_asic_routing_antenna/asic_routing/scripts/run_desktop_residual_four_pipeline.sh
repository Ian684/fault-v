#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="${1:?new native tag}"
owner=faultv-<host>_desktop_residual_two_20261026_172140
[[ "$(docker inspect -f '{{.State.Running}} {{.State.Paused}}' "$owner")" == 'true false' ]]
docker pause "$owner" >/dev/null
trap 'docker unpause "$owner" >/dev/null' EXIT
bash scripts/run_desktop_residual_four_native.sh "$tag"
# Success is returned only after all unchanged physical and electrical acceptance gates.
docker stop --time 5 "$owner" > ../logs/residual_four_retired_parent.log 2>&1 || true
docker stop --time 5 faultv-<host>_desktop_corner_bypass_20261026_145204 >> ../logs/residual_four_retired_parent.log 2>&1 || true
docker stop --time 5 faultv-<host>_desktop_refined_wide4_20261026_170943 >> ../logs/residual_four_retired_parent.log 2>&1 || true
trap - EXIT
