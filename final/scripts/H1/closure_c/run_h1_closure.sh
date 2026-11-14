#!/usr/bin/env bash
# H1 W25-closure gates (H0 method: week25_closure run_native_candidate_checks / run_final_stream_audits / run_final_ir /
# run_final_fill_parallel), on the H1 signoff candidate h1c_pg_r1 -> h1c_post. Each gate runs even if an earlier one
# fails; results are judged afterwards (verify_h1_closure.py). Progress: logs/chain.log, last line CLOSURE_END ...
set -uo pipefail
cd "$(dirname "$0")"
CB=/work/ppa/h1/cand_gap90x95/closure_c
root="$(cd ../../../.. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
ODB=/work/ppa/h1/cand_gap90x95/runs/h1c_post/1-openroad-fillinsertion/fault_v_asic_top.odb
DEF=/work/ppa/h1/cand_gap90x95/runs/h1c_post/1-openroad-fillinsertion/fault_v_asic_top.def
GDS=/work/ppa/h1/cand_gap90x95/runs/h1c_post/2-klayout-streamout/fault_v_asic_top.gds
MACRO=/work/week25_closure/macros/sky130_sram_2kbyte_1rw1r_32x512_8.orphan_trim_dedup.gds
log=logs/chain.log
say() { echo "$(date -Is) $*" >> "$log"; }
dock() {  # dock <name> <mem> <command...>
    local n="$1" m="$2"; shift 2
    docker run --rm --name "faultv-h1cc-$n" --user 1000:1000 --memory="$m" --cpus=2 -e PYTHONDONTWRITEBYTECODE=1 \
        -v "$root:/work" -w "$CB" "$image" "$@"
}
declare -A rc
say "start"
dock pdn 2000m openroad -exit -python scripts/h1_pdn_boundary.py > logs/pdn_boundary.log 2>&1; rc[pdn]=$?; say "pdn rc=${rc[pdn]}"

# 0 static IR / average EM, 14 and 28 mW per SRAM (first: H0 needed a PG via repair here)
for budget in 0.014 0.028; do
    tag="final_ir_${budget/./p}_h1"
    if [ -e "runs/$tag" ]; then say "skip existing runs/$tag"; continue; fi
    docker run --rm --name "faultv-h1cc-$tag" -e SRAM_BUDGET_W=$budget --user 1000:1000 --memory=5000m --cpus=2 \
        -v "$root:/work" -w "$CB" "$image" python3 scripts/h1_ir_cli.py --pdk-root /work/pdk \
        --with-initial-state $CB/h1_ir_state.json --run-tag "$tag" config_h1_ir.json > "logs/$tag.log" 2>&1
    rc[$tag]=$?; say "$tag rc=${rc[$tag]}"
done
dock em 4000m python3 scripts/audit_pg_em.py 'final_ir_{budget}_h1' reports/runtime_h1_filled_odb.json reports/h1_em_resistor_audit.json > logs/em_audit.log 2>&1
rc[em]=$?; say "EM audit rc=${rc[em]} $(tail -n 4 logs/em_audit.log | tr '\n' ' ')"

# 1 independent full-chip native DRC + all-net connectivity on the filled signoff ODB
docker run --rm --name faultv-h1cc-drc --user 1000:1000 --memory=7000m --cpus=2 -e ROUTE_DRC_ODB=$ODB \
    -e ROUTE_DRC_REPORT=$CB/reports/h1_filled_independent.json -v "$root:/work" -w "$CB" "$image" \
    openroad -exit -python /work/routing/scripts/native_route_drc.py > logs/filled_independent.log 2>&1; rc[drc]=$?; say "native drc rc=${rc[drc]}"
dock conn 4000m openroad -exit -python scripts/audit_all_signal_connectivity.py $ODB reports/h1_filled_all_connectivity.json > logs/filled_connectivity.log 2>&1
rc[conn]=$?; say "connectivity rc=${rc[conn]}"

# 2 stream audits (SRAM 39-layer geometry, standard cells and route vias vs library/ODB, PG contacts)
dock vias 3000m openroad -exit -python scripts/export_native_vias.py $ODB reports/h1_native_vias.json > logs/via_export.log 2>&1; rc[vias]=$?
dock pgg 3000m openroad -exit -python scripts/export_pg_contact_geometry.py $ODB reports/h1_pg_contact_geometry.json > logs/pg_geometry.log 2>&1; rc[pgg]=$?
docker run --rm --name faultv-h1cc-stream --user 1000:1000 --memory=4000m --cpus=2 -e AUDIT_CORE_GDS=$GDS -e AUDIT_MACRO_GDS=$MACRO \
    -e AUDIT_REPORT=reports/h1_macro_audit.json -v "$root:/work" -w "$CB" "$image" bash -c "set -e
python3 scripts/audit_stream_macro.py > logs/macro_audit.log 2>&1; echo macro_ok
python3 scripts/audit_final_stdcell_stream.py $GDS $DEF reports/h1_stdcell_audit.json reports/h1_native_vias.json
python3 scripts/audit_pg_contacts.py reports/h1_pg_contact_geometry.json reports/h1_pg_contacts.json" > logs/stream_audits.log 2>&1
rc[stream]=$?; say "via export rc=${rc[vias]} pg geometry rc=${rc[pgg]} stream audits rc=${rc[stream]}"

# 4 dummy metal fill from the actual H1 core GDS, repairs, sliding density, grid, FOM, compose, BEOL interaction
if [ ! -e final_fill ]; then
    docker run --rm --name faultv-h1cc-fill --user 1000:1000 --memory=5000m --cpus=2 \
        -e FILL_TECH_FILE=/work/week25_closure/controls/sky130A-GDS-dense-FOM-b.tech -v "$root:/work" -w "$CB" "$image" \
        python3 scripts/run_native_fill.py $GDS $CB/final_fill > logs/fill_generation.log 2>&1
    rc[fillgen]=$?
else rc[fillgen]=existing; fi
say "fill generation rc=${rc[fillgen]}"
dock fillchk 4500m bash -c "set -e
python3 scripts/repair_fom_fill.py $GDS final_fill/fault_v_asic_top_fill_pattern.gds.gz final_fill/fom_repaired.gds.gz reports/h1_fom_repair.json
python3 scripts/repair_li_fill.py $GDS final_fill/fom_repaired.gds.gz final_fill/fill_repaired.gds.gz reports/h1_li_repair.json
python3 scripts/check_sliding_density.py $GDS final_fill/fill_repaired.gds.gz reports/h1_sliding_density.json
python3 scripts/check_dummy_grid.py final_fill/fill_repaired.gds.gz reports/h1_dummy_grid.json
python3 scripts/canonicalize_fill.py final_fill/fill_repaired.gds.gz final_fill/canonical_fill.gds.gz
python3 scripts/compose_fill.py $GDS final_fill/canonical_fill.gds.gz final_fill/filled.gds.gz
python3 scripts/check_full_fom.py $GDS final_fill/fill_repaired.gds.gz reports/h1_fom_geometry.json" > logs/fill_checks.log 2>&1
rc[fillchk]=$?; say "fill checks rc=${rc[fillchk]}"
docker run --rm --name faultv-h1cc-beol --user 1000:1000 --memory=10000m --cpus=2 -v "$root:/work" -w "$CB" "$image" \
    klayout -b -r /work/week25_closure/controls/sky130_fill_interaction_tiled.drc -rd input=$CB/final_fill/filled.gds.gz \
    -rd top_cell=fault_v_asic_top -rd report=$CB/reports/h1_fill_beol.rdb > logs/fill_beol.log 2>&1
rc[beol]=$?; say "fill BEOL rc=${rc[beol]}"
summary=""; for k in pdn drc conn vias pgg stream final_ir_0p014_h1 final_ir_0p028_h1 em fillgen fillchk beol; do summary="$summary $k=${rc[$k]:-na}"; done
say "CLOSURE_END$summary"
