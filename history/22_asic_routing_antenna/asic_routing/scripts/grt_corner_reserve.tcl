# Copyright 2020-2023 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb
source $::env(SCRIPTS_DIR)/openroad/common/dpl_cell_pad.tcl

set_propagated_clock [all_clocks]

# Reserve only the pinless corner GCell edges; physical LEF/PDN rules remain unchanged.
source $::env(SCRIPTS_DIR)/openroad/common/set_routing_layers.tcl
source $::env(SCRIPTS_DIR)/openroad/common/set_layer_adjustments.tcl
set_macro_extension $::env(GRT_MACRO_EXTENSION)
set ::grt_preamble 1
foreach layer {met1 met2 met3 met4} {
    log_cmd set_global_routing_region_adjustment {1580.1 634.8 1593.9 648.6} -layer $layer -adjustment 1.0
}
source $::env(SCRIPTS_DIR)/openroad/common/grt.tcl

source $::env(SCRIPTS_DIR)/openroad/common/set_rc.tcl
estimate_parasitics -global_routing

write_views
