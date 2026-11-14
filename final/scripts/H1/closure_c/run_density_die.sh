#!/usr/bin/env bash
# Re-run the sliding density gate over the actual H1 die (2470x3217um). The first run used the H0 die extent
# hard-coded in check_sliding_density.py; its report is kept as reports/h1_sliding_density_H0die_misscoped.json.
set -uo pipefail
cd "$(dirname "$0")"
CB=/work/ppa/h1/cand_gap90x95/closure_c
root="$(cd ../../../.. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
GDS=/work/ppa/h1/cand_gap90x95/runs/h1c_post/2-klayout-streamout/fault_v_asic_top.gds
DEF=/work/ppa/h1/cand_gap90x95/runs/h1c_post/1-openroad-fillinsertion/fault_v_asic_top.def
[ -e reports/h1_sliding_density_H0die_misscoped.json ] || mv reports/h1_sliding_density.json reports/h1_sliding_density_H0die_misscoped.json
echo "$(date -Is) density over actual die start" >> logs/chain.log
docker run --rm --name faultv-h1cc-density --user 1000:1000 --memory=4500m --cpus=2 -e PYTHONDONTWRITEBYTECODE=1 \
    -v "$root:/work" -w "$CB" "$image" python3 scripts/check_sliding_density_die.py $GDS final_fill/fill_repaired.gds.gz \
    reports/h1_sliding_density.json $DEF > logs/sliding_density_die.log 2>&1
rc=$?
echo "$(date -Is) DENSITY_DIE_END rc=$rc $(tail -n 1 logs/sliding_density_die.log)" >> logs/chain.log
