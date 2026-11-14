#!/usr/bin/env bash
# Render H0 and H1 core GDS images for the competition report (read only on the GDS; writes w26/competition/figures).
cd "$(dirname "$0")/../.."
root="$PWD"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
lyp=/work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.tech/klayout/tech/sky130A.lyp
out=w26/competition/figures
mkdir -p "$out" w26/logs
render() {  # name gds width bg layers
    docker run --rm --name "faultv-w26-render-$1" --user 1000:1000 --memory=8000m --cpus=4 \
        -e GDS="/work/$2" -e OUT="/work/$out/$1.png" -e LYP="$lyp" -e WIDTH="$3" -e BG="$4" -e LAYERS="$5" \
        -v "$root:/work" -w /work "$image" klayout -zz -r /work/w26/scripts/render_layout.py >> w26/logs/render_layouts.log 2>&1
    echo "$1 rc=$?" >> w26/logs/render_layouts.log
}
: > w26/logs/render_layouts.log
render h0_layout_all week25_closure/runs/focus_post_b/final/gds/fault_v_asic_top.gds 3200 '#000000' ''
render h1_layout_all ppa/h1/cand_gap90x95/runs/h1b_post/2-klayout-streamout/fault_v_asic_top.gds 3200 '#000000' ''
# metal-only views (met1..met5 drawing: 68/20 69/20 70/20 71/20 72/20)
render h0_layout_metal week25_closure/runs/focus_post_b/final/gds/fault_v_asic_top.gds 3200 '#000000' '68/20,69/20,70/20,71/20,72/20'
echo RENDER_END >> w26/logs/render_layouts.log
