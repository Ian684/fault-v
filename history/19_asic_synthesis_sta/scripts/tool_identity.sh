#!/usr/bin/env bash
set -euo pipefail
IMAGE='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
docker run --rm "$IMAGE" bash -lc 'librelane --version; yosys -V; openroad -version; sta -version; verilator --version'
docker version --format '{{.Server.Version}}'
uname -a
