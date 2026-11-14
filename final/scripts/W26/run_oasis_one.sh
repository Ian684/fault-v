#!/usr/bin/env bash
# run_oasis_one.sh <name> <src under /work> <dst under /work> <report under /work> [--negative-control]
set -uo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
name="$1"; shift
mkdir -p logs
docker run --rm --name "faultv-w26-oas-$name" --user 1000:1000 --memory=12000m --cpus=2 -e PYTHONDONTWRITEBYTECODE=1 \
    -v "$root:/work" -w /work/w26 "$image" python3 scripts/gds_to_oasis.py "$@" > "logs/oasis_$name.log" 2>&1
rc=$?
echo "$(date -Is) OASIS_ONE_END $name rc=$rc $(tail -n 1 logs/oasis_$name.log)" >> logs/delivery_chain.log
exit $rc
