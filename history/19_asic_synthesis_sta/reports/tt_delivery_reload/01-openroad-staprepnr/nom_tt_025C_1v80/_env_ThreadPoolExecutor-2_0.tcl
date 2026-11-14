set ::env(STEP_ID) OpenROAD.STAPrePNR
set ::env(TECH_LEF) /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef
set ::env(MACRO_LEFS) /work/design/macros/vendor/sky130_sram_2kbyte_1rw1r_32x512_8.lef
set ::env(STD_CELL_LIBRARY) sky130_fd_sc_hd
set ::env(VDD_PIN) VPWR
set ::env(GND_PIN) VGND
set ::env(TECH_LEFS) "\"nom_*\" /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef \"min_*\" /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__min.tlef \"max_*\" /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__max.tlef"
set ::env(PRIMARY_GDSII_STREAMOUT_TOOL) magic
set ::env(DEFAULT_CORNER) nom_tt_025C_1v80
set ::env(STA_CORNERS) nom_tt_025C_1v80
set ::env(RT_MIN_LAYER) met1
set ::env(RT_MAX_LAYER) met5
set ::env(SCL_GROUND_PINS) "VGND VNB"
set ::env(SCL_POWER_PINS) "VPWR VPB"
set ::env(TRISTATE_CELLS) "\"sky130_fd_sc_hd__ebuf*\""
set ::env(FILL_CELLS) "sky130_fd_sc_hd__fill_2 sky130_fd_sc_hd__fill_1"
set ::env(DECAP_CELLS) sky130_fd_sc_hd__decap_3
set ::env(LIB) "\"*_tt_025C_1v80\" /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib \"*_ss_100C_1v60\" /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ss_100C_1v60.lib \"*_ff_n40C_1v95\" /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__ff_n40C_1v95.lib"
set ::env(CELL_LEFS) "/work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lef/sky130_ef_sc_hd.lef"
set ::env(CELL_GDS) /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/gds/sky130_fd_sc_hd.gds
set ::env(CELL_VERILOG_MODELS) "/work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v"
set ::env(CELL_BB_VERILOG_MODELS) "/work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd__blackbox.v /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd__blackbox_pp.v"
set ::env(CELL_SPICE_MODELS) "/work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_ef_sc_hd__decap_12.spice /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_ef_sc_hd__decap_20_12.spice /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_ef_sc_hd__decap_40_12.spice /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_ef_sc_hd__decap_60_12.spice /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_ef_sc_hd__decap_80_12.spice /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_ef_sc_hd__fill_12.spice /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_ef_sc_hd__fill_2.spice /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_ef_sc_hd__fill_4.spice /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_ef_sc_hd__fill_8.spice /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/spice/sky130_fd_sc_hd.spice"
set ::env(CELL_CDLS) /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/cdl/sky130_fd_sc_hd.cdl
set ::env(SYNTH_EXCLUDED_CELL_FILE) /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.tech/openlane/sky130_fd_sc_hd/no_synth.cells
set ::env(PNR_EXCLUDED_CELL_FILE) /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.tech/openlane/sky130_fd_sc_hd/drc_exclude.cells
set ::env(OUTPUT_CAP_LOAD) 33.442
set ::env(MAX_FANOUT_CONSTRAINT) 10
set ::env(MAX_TRANSITION_CONSTRAINT) 0.03
set ::env(MAX_CAPACITANCE_CONSTRAINT) 0.2
set ::env(CLOCK_UNCERTAINTY_CONSTRAINT) 0.25
set ::env(CLOCK_TRANSITION_CONSTRAINT) 0.1499999999999999944488848768742172978818416595458984375
set ::env(TIME_DERATING_CONSTRAINT) 5.0
set ::env(IO_DELAY_CONSTRAINT) 20.0
set ::env(SYNTH_DRIVING_CELL) sky130_fd_sc_hd__inv_2/Y
set ::env(SYNTH_TIEHI_CELL) sky130_fd_sc_hd__conb_1/HI
set ::env(SYNTH_TIELO_CELL) sky130_fd_sc_hd__conb_1/LO
set ::env(SYNTH_BUFFER_CELL) sky130_fd_sc_hd__buf_8/A/X
set ::env(PLACE_SITE) unithd
set ::env(CELL_PAD_EXCLUDE) "\"sky130_fd_sc_hd__tap*\" \"sky130_fd_sc_hd__decap*\" \"sky130_ef_sc_hd__decap*\" \"sky130_fd_sc_hd__fill*\""
set ::env(DIODE_CELL) sky130_fd_sc_hd__diode_2/DIODE
set ::env(WELLTAP_CELL) sky130_fd_sc_hd__tapvpwrvgnd_1
set ::env(ENDCAP_CELL) sky130_fd_sc_hd__decap_3
set ::env(DESIGN_NAME) fault_v_asic_top
set ::env(CLOCK_PERIOD) 40.0
set ::env(CLOCK_PORT) clk
set ::env(MACROS) "sky130_sram_2kbyte_1rw1r_32x512_8 \"gds /work/design/macros/vendor/sky130_sram_2kbyte_1rw1r_32x512_8.gds lef /work/design/macros/vendor/sky130_sram_2kbyte_1rw1r_32x512_8.lef instances \\\"\\\\\\\"u_soc.u_imem.banks\\\\\\\\\\\\\\\[0].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_imem.banks\\\\\\\\\\\\\\\[1].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_imem.banks\\\\\\\\\\\\\\\[2].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_imem.banks\\\\\\\\\\\\\\\[3].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_imem.banks\\\\\\\\\\\\\\\[4].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_imem.banks\\\\\\\\\\\\\\\[5].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_imem.banks\\\\\\\\\\\\\\\[6].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_imem.banks\\\\\\\\\\\\\\\[7].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_dmem.banks\\\\\\\\\\\\\\\[0].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_dmem.banks\\\\\\\\\\\\\\\[1].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_dmem.banks\\\\\\\\\\\\\\\[2].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_dmem.banks\\\\\\\\\\\\\\\[3].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_dmem.banks\\\\\\\\\\\\\\\[4].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_dmem.banks\\\\\\\\\\\\\\\[5].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_dmem.banks\\\\\\\\\\\\\\\[6].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_dmem.banks\\\\\\\\\\\\\\\[7].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_scratch.banks\\\\\\\\\\\\\\\[0].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\" \\\\\\\"u_soc.u_scratch.banks\\\\\\\\\\\\\\\[1].u_sram\\\\\\\" \\\\\\\"location None orientation None\\\\\\\"\\\" vh \\\"\\\" nl \\\"\\\" pnl \\\"\\\" spef \\\"\\\" lib \\\"\\\\\\\"*_tt_025C_1v80\\\\\\\" /work/design/macros/vendor/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib\\\" spice /work/design/macros/vendor/sky130_sram_2kbyte_1rw1r_32x512_8.lvs.sp sdf \\\"\\\" json_h None\""
set ::env(FALLBACK_SDC) /nix/store/7zqpr7slgvjfjcqfabb2fmlpvc8k23ax-python3-3.13.9-env/lib/python3.13/site-packages/librelane/scripts/base.sdc
set ::env(PAD_EDGE_SPACING) 0.0
set ::env(SET_RC_VERBOSE) 0
set ::env(PDN_CONNECT_MACROS_TO_GRID) 1
set ::env(PDN_ENABLE_GLOBAL_CONNECTIONS) 1
set ::env(PNR_SDC_FILE) /work/design/constraints.sdc
set ::env(DEDUPLICATE_CORNERS) 0
set ::env(STA_MACRO_PRIORITIZE_NL) 1
set ::env(CURRENT_NL) /work/design/eco/fault_v_asic_top.nl.v
set ::env(SAVE_SDC) /work/design/runs/tt_delivery_reload/01-openroad-staprepnr/fault_v_asic_top.sdc
set ::env(OPENLANE_SDC_IDEAL_CLOCKS) 1
