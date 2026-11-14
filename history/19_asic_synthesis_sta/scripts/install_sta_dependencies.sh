#!/usr/bin/env bash
set -euo pipefail
apt-get update > <HOME>/fault-v-asic/logs/sta_dependencies.log 2>&1
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tcl-dev swig libeigen3-dev >> <HOME>/fault-v-asic/logs/sta_dependencies.log 2>&1
