crashbackups disable
locking disable
drc off
path search /tmp
gds readonly true
gds read /work/week25_closure/controls/SRAM_tiled_5nm.gds
drc style drc(full)
load sky130_sram_2kbyte_1rw1r_32x512_8
select top cell
drc euclidean on
drc check
drc catchup
puts "FAULTV_SRAM_5NM_DRC_COMPLETE"
set f [open /work/week25_closure/reports/SRAM_grid_DRC_rules.txt w]
set total 0
foreach {rule boxes} [drc listall why] {
    set count [llength $boxes]
    incr total $count
    puts $f [list $rule $count [lrange $boxes 0 2]]
}
puts $f "RAW_MARKERS $total"
close $f
puts "FAULTV_SRAM_5NM_MARKERS $total"
quit -noprompt
