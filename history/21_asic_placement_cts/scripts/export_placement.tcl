set_propagated_clock [all_clocks]
estimate_parasitics -placement -spef_file $::env(STEP_DIR)/estimated.spef
