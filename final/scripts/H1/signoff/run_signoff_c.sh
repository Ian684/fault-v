#!/usr/bin/env bash
# H1 signoff chain on the final antenna-ECO round (H0 methods, H1 inputs; nothing is written to week25_*):
#   1 h1c_post     fill insertion, KLayout stream-out, KLayout DRC (sky130_core_precheck deck), antenna check, RCX
#   2 h1c_sta      3-RC STA with OpenSTA 3.1 and the reviewed week25_signoff SDC
#   3 h1c_lvs      core / SRAM pin-interface LVS (Magic extraction + Netgen), plus the shifted-pin negative control
#   4 functional  reset/CDC and the four workloads on the exact netlist (VCDs for power)
#   5 power       VCD power, formal_h0 method (ppa/formal_h1)
# Steps 2-5 each run even if another of them fails; all of them need step 1.
# Usage (from cand_gap90x95): bash signoff/run_signoff_c.sh <final ECO run tag>
# Progress in signoff/logs_c/chain.log; the last line is SIGNOFF_END <summary>.
set -uo pipefail
cd "$(dirname "$0")/.."
root="$(cd ../../.. && pwd)"; wd="/work/${PWD#$root/}"
tag="$1"
mkdir -p signoff/logs_c signoff/reports_c
log=signoff/logs_c/chain.log
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
say() { echo "$(date -Is) $*" >> "$log"; }
dock() {  # dock <name> <memory> <cpus> <command...>
    local name="$1" mem="$2" cpus="$3"; shift 3
    docker run --rm --name "faultv-h1c-$name" --user 1000:1000 --memory="$mem" --cpus="$cpus" \
        -e PYTHONDONTWRITEBYTECODE=1 -v "$root:/work" -w "$wd" "$image" "$@"
}
export PYTHONDONTWRITEBYTECODE=1

say "start on $tag"
python3 signoff/prepare_post_c.py "$tag" >> "$log" 2>&1 || { say "SIGNOFF_END prepare_post failed"; exit 1; }
bash signoff/run_flow_c.sh h1c_post config_c_post.json signoff/state_c_post.json signoff/plain_cli.py 7000m 2 >> "$log" 2>&1
rc=$?; say "h1c_post rc=$rc"
[ "$rc" -eq 0 ] || { say "SIGNOFF_END h1c_post failed"; exit 1; }

sta=skipped
if python3 signoff/prepare_sta_c.py >> "$log" 2>&1; then
    bash signoff/run_flow_c.sh h1c_sta config_c_sta3.json signoff/state_c_sta.json /work/routing/scripts/sta310_cli.py 3000m 1 >> "$log" 2>&1
    sta=$?
fi
say "h1c_sta rc=$sta"

lvs=skipped; bad=skipped
gds="$(ls runs/h1c_post/*-klayout-streamout/fault_v_asic_top.gds)"
dock core-view 3000m 1 python3 /work/week25_closure/scripts/build_core_lvs_view.py "$gds" \
    signoff/h1c_core_lvs.gds signoff/h1c_badpin_lvs.gds signoff/reports_c/h1c_core_lvs_view.json > signoff/logs_c/core_view.log 2>&1
view=$?; say "core view rc=$view"
if [ "$view" -eq 0 ] && python3 signoff/prepare_lvs_c.py >> "$log" 2>&1; then
    bash signoff/run_flow_c.sh h1c_lvs config_c_lvs.json signoff/state_c_lvs.json signoff/h1_lvs_cli.py 3500m 1 >> "$log" 2>&1
    lvs=$?
    bash signoff/run_flow_c.sh h1c_lvs_bad config_c_lvs.json signoff/state_c_lvs_bad.json signoff/h1_lvs_cli.py 3500m 1 >> "$log" 2>&1
    bad=$?
fi
say "h1c_lvs rc=$lvs h1c_lvs_bad rc=$bad"

nl="$(ls runs/h1c_post/*-openroad-fillinsertion/fault_v_asic_top.nl.v)"
dock functional 2500m 2 python3 signoff/run_functional_c.py "$wd/$nl" h1c_a > signoff/logs_c/functional.log 2>&1
fun=$?; printf '%s\n' "$fun" > signoff/logs_c/functional.exit; say "functional rc=$fun"

pow=skipped
if [ "$fun" -eq 0 ]; then
    bash ../../formal_h1/scripts/run_power_h1c.sh >> "$log" 2>&1
    pow=$?
fi
say "power rc=$pow"
say "SIGNOFF_END post=0 sta=$sta lvs=$lvs lvs_bad=$bad functional=$fun power=$pow"
