#!/usr/bin/env bash
# H1 VCD power with OpenSTA 3.1 in the pinned image (same options as formal_h0/scripts/run_power_h0.sh).
set -euo pipefail
cd "$(dirname "$0")/.."
root="$(cd ../.. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
mkdir -p logs
test ! -e logs/power_h1c.exit
set +e
docker run --rm --name faultv-ppa-h1c-power --user 1000:1000 --memory=6000m --cpus=1 -v "$root:/work" -w /work/ppa/formal_h1 "$image" /work/routing/sta_tool/sta -no_init -no_splash -exit scripts/power_h1c.tcl > logs/power_h1c.log 2>&1
rc=$?
printf '%s\n' "$rc" > logs/power_h1c.exit
exit "$rc"
