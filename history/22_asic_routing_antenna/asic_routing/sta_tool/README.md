# OpenSTA runtime
OpenSTA 3.1.0, unmodified source commit `0f2529d18218b87aa0e82de444395a830d5058a1`.
`identity.json` records the binary and Tcl library hashes. Upstream GPL license is in `LICENSE`; upstream source is available at https://github.com/The-OpenROAD-Project/OpenSTA/tree/0f2529d18218b87aa0e82de444395a830d5058a1 .

`sta` is a loader wrapper. `sta.bin` and `lib/libtcl8.6.so` are bundled; remaining Nix runtime libraries come from the image pinned in `technology_identity.json`. Execute inside that image at `/work/routing/sta_tool/sta`, not as a generic Windows executable. `original_build_recipe.sh` records the original workspace build, including its historical paths.

The embedded OpenROAD STA 2.7.0 is retained for physical implementation, but its mixed-threshold slew defect is reproduced in `reports/threshold_regression.json`. Routing acceptance uses this 3.1.0 runtime on OpenRCX extracted routed SPEF with propagated clocks; global-route estimated RC is checked separately before detailed routing. This is not foundry signoff qualification.
