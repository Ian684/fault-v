crashbackups disable
locking disable
drc off
path search /tmp
gds readonly false
gds read /work/week25_closure/controls/SRAM_exact_5nm.gds
drc style drc(full)
if {[lsearch -exact [cellname list allcells] sky130_sram_2kbyte_1rw1r_32x512_8] < 0} {error "SRAM GDS did not load"}
load sky130_sram_2kbyte_1rw1r_32x512_8
select top cell
set bbox [box values]
if {[lindex $bbox 2]-[lindex $bbox 0] < 10000 || [lindex $bbox 3]-[lindex $bbox 1] < 10000} {error "Empty/incorrect SRAM bounds"}
puts "FAULTV_SRAM_GEOMETRY_PRESENT $bbox"
drc euclidean on
drc check
drc catchup
set total [drc listall count total]
set file [open /work/week25_closure/reports/SRAM_exact_DRC_counts.txt w]
puts $file "UNIQUE_CELL_ERROR_TILES $total"
puts $file [drc listall count]
box values 0um 0um 20um 20um
puts $file "SAMPLE_BOX_UM 0 0 20 20"
foreach {rule boxes} [drc listall why] {
    puts $file [list $rule [llength $boxes] [lrange $boxes 0 2]]
}
close $file
puts "FAULTV_SRAM_EXACT_GRID_DRC_COMPLETE UNIQUE_CELL_ERROR_TILES=$total"
quit -noprompt
