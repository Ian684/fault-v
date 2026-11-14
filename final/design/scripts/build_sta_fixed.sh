#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
mkdir -p "$ROOT/tools" "$ROOT/logs"
cd "$ROOT/tools"
if [ ! -d cudd_3/.git ]; then git clone --depth 1 --branch 3.0.0 https://github.com/cuddorg/cudd.git cudd_3; fi
test "$(git -C cudd_3 rev-parse HEAD)" = f54f533303640afd5dbe47a05ebeabb3066f2a25
git -C cudd_3 rev-parse HEAD > "$ROOT/logs/cudd_source_commit.txt"
mkdir -p "$ROOT/tools/cudd_source"
git -C cudd_3 archive HEAD | tar -x -C "$ROOT/tools/cudd_source"
cd "$ROOT/tools/cudd_source"
./configure --prefix="$ROOT/tools/cudd_install" --disable-shared --enable-static > "$ROOT/logs/cudd_build.log" 2>&1
make -j4 >> "$ROOT/logs/cudd_build.log" 2>&1
make install >> "$ROOT/logs/cudd_build.log" 2>&1
cd "$ROOT/tools"
if [ ! -d opensta_fixed/.git ]; then
 git clone --no-checkout https://github.com/The-OpenROAD-Project/OpenSTA.git opensta_fixed
 git -C opensta_fixed checkout 0f2529d18218b87aa0e82de444395a830d5058a1
fi
cd opensta_fixed
test "$(git rev-parse HEAD)" = 0f2529d18218b87aa0e82de444395a830d5058a1
git diff --exit-code
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_CXX_FLAGS_RELWITHDEBINFO="-O2 -DNDEBUG" -DBUILD_TESTS=OFF -DUSE_TCL_READLINE=OFF -DCUDD_DIR="$ROOT/tools/cudd_install" > "$ROOT/logs/opensta_fixed_build.log" 2>&1
cmake --build build -j4 >> "$ROOT/logs/opensta_fixed_build.log" 2>&1
build/sta -version
