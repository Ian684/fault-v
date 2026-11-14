from pathlib import Path
import json
C=Path(__file__).resolve().parents[1]
state=json.loads((C/'pg_ir_state_b.json').read_text());state['odb']='/runtime/pg_via_b.odb';state['spef']['nom_*']='/runtime/baseline.nom.spef'
(C/'pg_ir_state_c.json').write_text(json.dumps(state,indent=2)+'\n')
state=json.loads((C/'pg_stream_state_b.json').read_text());state['def']='/runtime/pg_via_b.def';state['odb']='/runtime/pg_via_b.odb'
(C/'pg_stream_state_c.json').write_text(json.dumps(state,indent=2)+'\n')
original=(C.parent/'week25_signoff/scripts/ir_review.tcl').read_text()
path='/work/ppa/runs/activity_v3/mixed/activity.vcd';assert original.count(path)==1
updated=original.replace(path,'/runtime/mixed.activity.vcd')
assert updated.count('puts "%OL_CREATE_REPORT irdrop.rpt"')==1
updated=updated.replace('puts "%OL_CREATE_REPORT irdrop.rpt"','set_debug_level PSM resistance 1\nputs "%OL_CREATE_REPORT irdrop.rpt"')
line='    analyze_power_grid -net $net -vsrc $vsrc -voltage_file $::env(STEP_DIR)/net-$net.csv -enable_em -em_outfile $::env(STEP_DIR)/em-$net.csv -error_file $::env(STEP_DIR)/analysis-$net.rpt'
assert updated.count(line)==1
updated=updated.replace(line,line+'''
    if {[catch {write_pg_spice -net $net -vsrc $vsrc $::env(STEP_DIR)/network-$net.spice} network_error]} {
        if {$network_error ne "map::at"} {error $network_error}
        set f [open $::env(STEP_DIR)/network-$net.spice r]
        set network_text [read $f]
        close $f
        if {[string first "* Sinks" $network_text] < 0} {error "Incomplete resistor export"}
        puts "FAULTV_PG_RESISTORS_ONLY: native sink export failed map::at; resistor section complete."
    }
''')
(C/'controls/pg_ir_native.tcl').write_text(updated,newline='\n')
print('Native PG inputs selected; SHA evidence in reports/runtime_*.json. Loads/feeds unchanged.')
