set_propagated_clock [all_clocks]
estimate_parasitics -global_routing -spef_file $::env(STEP_DIR)/estimated_global.spef
