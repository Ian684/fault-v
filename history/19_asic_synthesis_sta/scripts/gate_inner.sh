#!/usr/bin/env bash
set -euo pipefail
mkdir -p gate_sim_linux logs
cd gate_sim_linux
iverilog -V > ../logs/gate_simulator_version.txt 2>&1
iverilog -g2012 -DFUNCTIONAL -s tb_gate_accept -o tb_gate.vvp ../macros/primitives_xsim.v ../macros/sky130_fd_sc_hd_xsim.v ../macros/model.v ../mapped_top.v ../verify/tb_gate_accept.sv > ../logs/gate_iverilog_compile.log 2>&1
vvp -N tb_gate.vvp | tee ../logs/tb_gate.log
grep -q 'ALL MAPPED GATE PROGRAM CHECKS PASSED' ../logs/tb_gate.log
