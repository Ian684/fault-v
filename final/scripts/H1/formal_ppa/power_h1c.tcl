# H1 formal PPA: VCD-annotated power on the H1 candidate (TT 25C 1.8V, nominal RC). Same commands as power_h0.tcl.
if {[catch {
read_liberty /work/pdk/ciel/sky130/versions/8afc8346a57fe1ab7934ba5a6056ea8b43078e71/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_liberty /work/routing/macros/sky130_sram_2kbyte_1rw1r_32x512_8_TT_1p8V_25C.lib
read_verilog /work/ppa/h1/cand_gap90x95/runs/h1c_post/final/nl/fault_v_asic_top.nl.v
link_design fault_v_asic_top
read_sdc /work/week25_signoff/constraints_reviewed.sdc
read_spef /work/ppa/h1/cand_gap90x95/runs/h1c_post/final/spef/nom/fault_v_asic_top.nom.spef
set srams [get_cells -hierarchical -filter "ref_name == sky130_sram_2kbyte_1rw1r_32x512_8"]
puts "FAULTV_SRAM_COUNT [llength $srams]"
foreach testcase {idle mixed dot64_rv32i dot64_custom} {
    puts "FAULTV_CASE_BEGIN $testcase"
    read_vcd -scope tb_activity/dut /work/ppa/h1/cand_gap90x95/functional/h1c_a/$testcase/activity.vcd
    report_activity_annotation
    report_power -digits 6
    report_power -instances $srams -digits 6
    puts "FAULTV_CASE_END $testcase"
}
puts "FAULTV_POWER_COMPLETED"
} err opts]} {
    puts stderr $err
    puts stderr [dict get $opts -errorinfo]
    exit 1
}
exit 0
