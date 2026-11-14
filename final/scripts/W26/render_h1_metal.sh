#!/usr/bin/env bash
# H1 metal-only layout image (same settings as h0_layout_metal; pixel scale matched to H0: 3200 px per 2500 um).
cd "$(dirname "$0")/../.."
root="$PWD"
image='ghcr.io/librelane/librelane@sha256:02d50f259d483979e126ef188a50f5b61e1d285b9d538312f280b087439b0302'
lyp=/work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.tech/klayout/tech/sky130A.lyp
docker run --rm --name faultv-w26-render-h1m --user 1000:1000 --memory=8000m --cpus=4 \
    -e GDS=/work/ppa/h1/cand_gap90x95/runs/h1b_post/2-klayout-streamout/fault_v_asic_top.gds \
    -e OUT=/work/w26/competition/figures/h1_layout_metal.png -e LYP="$lyp" -e WIDTH=3162 -e BG='#000000' \
    -e LAYERS='68/20,69/20,70/20,71/20,72/20' \
    -v "$root:/work" -w /work "$image" klayout -zz -r /work/w26/scripts/render_layout.py >> w26/logs/render_layouts.log 2>&1
echo "h1_layout_metal rc=$?" >> w26/logs/render_layouts.log
