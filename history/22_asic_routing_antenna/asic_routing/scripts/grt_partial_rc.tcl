source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
set_thread_count 8
set retained [dict create]
foreach net [$::block getNets] {
    if {[$net getSigType] in {POWER GROUND}} {continue}
    set wire [$net getWire]
    if {$wire ne "NULL"} {
        dict set retained [$net getName] [list $wire [$wire getLength]]
        $wire detach
        if {[$net getWire] ne "NULL"} {error "Wire detach failed"}
    }
}
# Guides are regenerated with all pins and nets; existing routes are not imported from another database.
source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl
dict for {name data} $retained {
    lassign $data wire length
    set net [$::block findNet $name]
    if {$net eq "NULL" || [$net getWire] ne "NULL"} {error "Unexpected net after GRT"}
    $wire attach $net
    if {[$wire getLength] != $length} {error "Retained wire changed during GRT"}
}
puts "FAULTV_SAME_DB_WIRES_REATTACHED [dict size $retained]"
write_views
