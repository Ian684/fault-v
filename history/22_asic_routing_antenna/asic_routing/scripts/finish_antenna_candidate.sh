#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
tag="${1:?native antenna run tag}"
[[ "$tag" =~ ^[A-Za-z0-9_]+$ ]]
[[ ! -e "../logs/${tag}_followup.exit" ]]
trap 'result=$?; printf "%s\n" "$result" > "../logs/${tag}_followup.exit"' EXIT
while [[ ! -e "../logs/$tag.exit" ]]; do
  # Stop if the native process disappears without its exit receipt.
  [[ "$(docker inspect -f '{{.State.Running}}' "faultv-$tag" 2>/dev/null || true)" == true ]] || { echo 'Native process vanished without completion receipt' >&2; exit 1; }
  sleep 5
done
[[ "$(cat "../logs/$tag.exit")" == 0 ]] || { echo 'Native antenna repair did not pass' >&2; exit 1; }
bash scripts/run_antenna_checks.sh "$tag"
python3 scripts/accept_antenna_phase.py "$tag"
