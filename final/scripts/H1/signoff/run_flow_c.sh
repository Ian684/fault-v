#!/usr/bin/env bash
# One LibreLane custom-flow run for the H1 signoff (pinned image and CLI options as H0's run_native_flow.sh;
# the run directory is written directly to cand_gap90x95/runs/<tag>).
# Usage (from cand_gap90x95): bash signoff/run_flow_c.sh <tag> <config.json> <state.json> <cli.py> <memory> <cpus>
# Log signoff/logs_c/<tag>.log, exit code signoff/logs_c/<tag>.exit. Refuses to rerun an existing tag.
set -uo pipefail
cd "$(dirname "$0")/.."
root="$(cd ../../.. && pwd)"; wd="/work/${PWD#$root/}"
tag="$1"; config="$2"; state="$3"; cli="$4"; memory="$5"; cpus="$6"
[[ "$tag" =~ ^[a-z0-9_]+$ ]] || { echo "bad tag"; exit 1; }
if [ -e "runs/$tag" ] || [ -e "signoff/logs_c/$tag.exit" ]; then echo "$tag already ran"; exit 1; fi
mkdir -p signoff/logs_c
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm --name "faultv-h1c-$tag" --user 1000:1000 --memory="$memory" --cpus="$cpus" \
    -v "$root:/work" -w "$wd" "$image" \
    python3 "$cli" --pdk-root /work/pdk --with-initial-state "$wd/$state" --run-tag "$tag" "$config" \
    > "signoff/logs_c/$tag.log" 2>&1
rc=$?
printf '%s\n' "$rc" > "signoff/logs_c/$tag.exit"
exit "$rc"
