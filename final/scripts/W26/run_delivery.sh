#!/usr/bin/env bash
# W26 delivery pipeline: copy (SHA-verified) -> OASIS + hierarchical equivalence -> flat XOR (+ negative controls)
# -> SHA256SUMS/manifest -> zip with per-member verification. Progress: w26/logs/delivery_chain.log, last line DELIVERY_END.
set -uo pipefail
cd "$(dirname "$0")/.."
log=logs/delivery_chain.log; mkdir -p logs work/xor_neg
say() { echo "$(date -Is) $*" >> "$log"; }
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
root="$(cd .. && pwd)"
P=delivery/Fault-V_W26
if [ -e delivery/Fault-V_W26.zip ]; then say "DELIVERY_END refused: zip exists"; exit 1; fi
say "start"
rm -rf "$P" delivery/sources.json work/xor_neg/*
python3 scripts/build_delivery.py copy > logs/delivery_copy.log 2>&1 || { say "DELIVERY_END copy failed"; exit 1; }
say "copy ok $(tail -n 1 logs/delivery_copy.log)"
fail=0
for v in H0 H1; do
  for k in core filled; do
    if [ $k = core ]; then src=$P/$v/layout/fault_v_asic_top.gds; oas=$P/$v/layout/fault_v_asic_top.oas; neg=--negative-control
    else src=$P/$v/layout/fault_v_asic_top_filled.gds.gz; oas=$P/$v/layout/fault_v_asic_top_filled.oas; neg=; fi
    bash scripts/run_oasis_one.sh "${v}_$k" "/work/w26/$src" "/work/w26/$oas" "/work/w26/$P/$v/layout/oasis_${k}_equivalence.json" $neg || fail=1
    bash scripts/run_xor_one.sh "${v}_$k" "/work/w26/$src" "/work/w26/$oas" "/work/w26/$P/$v/layout/xor_${k}.rdb"; xrc=$?
    python3 scripts/xor_summary.py "$P/$v/layout/xor_${k}.rdb" "logs/xor_${v}_$k.log" $xrc "$P/$v/layout/xor_${k}.json" >> "$log" 2>&1 || fail=1
    if [ $k = core ]; then
      docker run --rm --user 1000:1000 --memory=6000m -v "$root:/work" -w /work/w26 "$image" python3 scripts/make_xor_negative.py \
        "$oas" "work/xor_neg/${v}_neg.oas" "work/xor_neg/${v}_neg.json" >> "$log" 2>&1 || fail=1
      bash scripts/run_xor_one.sh "${v}_neg" "/work/w26/$src" "/work/w26/work/xor_neg/${v}_neg.oas" "/work/w26/work/xor_neg/${v}_neg.rdb" 68/20; nrc=$?
      python3 scripts/xor_summary.py "work/xor_neg/${v}_neg.rdb" "logs/xor_${v}_neg.log" $nrc "$P/$v/layout/xor_negative_control.json" "work/xor_neg/${v}_neg.json" >> "$log" 2>&1 || fail=1
    fi
  done
done
say "layout steps fail=$fail"
[ $fail = 0 ] || { say "DELIVERY_END layout step failed"; exit 1; }
python3 scripts/build_delivery.py finalize > logs/delivery_finalize.log 2>&1 || { say "DELIVERY_END finalize failed $(tail -n 2 logs/delivery_finalize.log | tr '\n' ' ')"; exit 1; }
say "finalize ok"
python3 "$P/check_package.py" > logs/delivery_check.log 2>&1 || { say "DELIVERY_END check_package failed"; exit 1; }
say "check_package ok $(tail -n 1 logs/delivery_check.log)"
python3 scripts/build_delivery.py zip > logs/delivery_zip.log 2>&1 || { say "DELIVERY_END zip failed $(tail -n 2 logs/delivery_zip.log | tr '\n' ' ')"; exit 1; }
say "DELIVERY_END ok $(tail -n 1 logs/delivery_zip.log)"
