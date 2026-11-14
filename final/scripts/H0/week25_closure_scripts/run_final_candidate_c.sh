#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
stem="$1";tag="$2"
[[ "$stem" =~ ^native_(upper_[a-z]|group_[a-z])$ && "$tag" =~ ^[a-z0-9_]+$ ]]
root="$(cd .. && pwd)"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
mkdir -p locks
if ! mkdir locks/final_candidate_c; then
  printf '%s\n' 'Another verified-source final-candidate pipeline is active.' >&2
  exit 2
fi
trap 'rc=$?; rmdir locks/final_candidate_c; printf "%s\n" "$rc" > logs/final_candidate_c.exit' EXIT
test ! -e reports/final_route_selection_c.json

bash scripts/run_native_candidate_checks.sh "$stem" "$tag"
docker run --rm --name faultv-w25-stage-route-c --user 1000:1000 --memory=1500m --cpus=1 -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime -w /work/week25_closure "$image" python3 scripts/stage_durable_to_runtime.py "/work/week25_closure/runs/$tag/1-openroad-detailedrouting/native_final.odb" final_route_c.odb
docker run --rm --name faultv-w25-invariants-c --user 1000:1000 --memory=4000m --cpus=2 -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime:ro -v /var/tmp/faultv-w25-finalprep:/runtime_final:ro -w /work/week25_closure "$image" openroad -exit -python scripts/audit_final_route_invariants.py "$tag" final_route_c.odb final_route_c_invariants.json > logs/final_route_c_invariants.log 2>&1
python3 scripts/select_signal_candidate.py "$tag" "${stem}_independent.json" "${stem}_all_connectivity.json" final_c
bash scripts/run_final_post_b.sh
python3 scripts/verify_final_post.py
for pair in '1-openroad-fillinsertion/fault_v_asic_top.odb final_filled.odb' '2-klayout-streamout/fault_v_asic_top.gds final_core.gds'; do
  read -r relative alias <<< "$pair"
  docker run --rm --name "faultv-w25-stage-${alias//./-}" --user 1000:1000 --memory=1500m --cpus=1 -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime -w /work/week25_closure "$image" python3 scripts/stage_durable_to_runtime.py "/work/week25_closure/runs/focus_post_b/$relative" "$alias"
done

# These checks consume the same immutable candidate and write separate evidence trees.
bash scripts/run_final_core_lvs.sh > logs/final_core_lvs_host.log 2>&1 & lvs_pid=$!
bash scripts/run_final_stream_audits.sh > logs/final_stream_audits_host.log 2>&1 & stream_pid=$!
bash scripts/run_final_functional.sh > logs/final_functional_host.log 2>&1 & functional_pid=$!
rc=0
wait "$lvs_pid" || rc=$?
wait "$stream_pid" || rc=$?
wait "$functional_pid" || rc=$?
test "$rc" = 0
python3 scripts/verify_final_core_results.py
docker run --rm --name faultv-w25-stage-final-vcd --user 1000:1000 --memory=1500m --cpus=1 -v "$root:/work" -v /var/tmp/faultv-w25-closure-20261101:/runtime -w /work/week25_closure "$image" python3 scripts/stage_durable_to_runtime.py /work/week25_closure/functional/final_a/mixed/activity.vcd final_mixed.vcd
bash scripts/run_final_ir.sh > logs/final_ir_host.log 2>&1 & ir_pid=$!
FINAL_FILL_WAIT_FOR_IR=1 bash scripts/run_final_fill_parallel.sh > logs/final_fill_host.log 2>&1 & fill_pid=$!
rc=0
wait "$ir_pid" || rc=$?
wait "$fill_pid" || rc=$?
test "$rc" = 0
python3 scripts/verify_final_fill_result.py
printf '%s\n' 'FINAL_CANDIDATE_CHECK_JOBS_FINISHED: comprehensive gate/report still required.'
