crashbackups disable
locking disable
drc off
path search /tmp
gds readonly false
gds read /work/week25_closure/controls/bitcell.gds
if {[lsearch -exact [cellname list allcells] faultv_bitcell] < 0} {error "Bitcell did not load"}
load faultv_bitcell
select top cell
drc style drc(full)
drc euclidean on
drc check
drc catchup
set f [open /work/week25_closure/reports/bitcell_DRC.txt w]
puts $f [drc listall why]
close $f
gds write /work/week25_closure/controls/bitcell_magic_roundtrip.gds
puts "FAULTV_BITCELL_DRC_COMPLETE"
quit -noprompt
