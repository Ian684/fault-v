#!/usr/bin/env bash
# run_xor_one.sh <name> <layout A under /work> <layout B under /work> <report.rdb under /work> [only L/D]
set -uo pipefail
cd "$(dirname "$0")/.."
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
name="$1"; a="$2"; b="$3"; rdb="$4"; only="${5:-}"
extra=(); [ -n "$only" ] && extra=(-rd "only=$only")
mkdir -p logs
docker run --rm --name "faultv-w26-xor-$name" --user 1000:1000 --memory=12000m --cpus=2 -v "$root:/work" -w /work/w26 "$image" \
    klayout -b -r scripts/xor_layouts.drc -rd "a=$a" -rd "b=$b" -rd "report=$rdb" "${extra[@]}" > "logs/xor_$name.log" 2>&1
rc=$?
items=$(grep -c '<item>' "${rdb/\/work/$root}" 2>/dev/null || true); [ -n "$items" ] || items=NA
echo "$(date -Is) XOR_ONE_END $name rc=$rc items=$items" >> logs/delivery_chain.log
echo "XOR_ONE_END $name rc=$rc items=$items"
exit $rc
