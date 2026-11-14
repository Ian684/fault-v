#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
task_root="$(cd .. && pwd)"
docker run --rm --user "$(id -u):$(id -g)" -v "$task_root:/work" -w /work/design "$IMAGE" bash scripts/gate_inner.sh > ../logs/gate_linux_console.txt 2>&1
