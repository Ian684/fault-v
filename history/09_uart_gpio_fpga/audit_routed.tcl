set_param general.maxThreads 2
open_checkpoint build/fault_v_routed.dcp
source audit_design.tcl
report_utilization -hierarchical -file logs/route_hierarchy.rpt
