# Extract antenna areas from the exact supplied GDS; keep the original abstract intact.
if {[catch {
    drc off
    set VDD vccd1
    set GND vssd1
    set SUB vssd1
    gds ordering true
    gds readonly true
    gds read /work/routing/macros/sky130_sram_2kbyte_1rw1r_32x512_8.gds
    load sky130_sram_2kbyte_1rw1r_32x512_8
    lef read /work/routing/macros/sky130_sram_2kbyte_1rw1r_32x512_8.lef -annotate
    lef write /work/routing/reports/antenna_model/sram_gds_antenna.lef -hide
    puts "SRAM_GDS_ANTENNA_EXTRACTION_COMPLETE"
} message options]} {
    puts stderr "ANTENNA_EXTRACTION_FAILED $message"
    puts stderr [dict get $options -errorinfo]
    exit 1
}
quit -noprompt
