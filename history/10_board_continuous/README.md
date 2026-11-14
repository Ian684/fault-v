# Fault-V continuous board test

CPU/SoC RTL is unchanged from peripheral_z2. The FPGA Top defaults to board_loop.mem.

- Technical notes: Continuous_Board_Notion.md
- Generate and verify: `& ./run_sim.ps1`
- Build: `& ./build_fpga.ps1`
- JTAG download: Vivado batch `-source program_hardware.tcl` after successful verification/build.

The download script targets the already identified 1234-tulA JTAG cable and xc7z020_1. It refuses to select an ambiguous or different target. It replaces the active FPGA design; it does not write flash.

LED 5/A alternating: each transition follows a successful complete 4096-word RAM write/read sweep. LED F and EBREAK: software detected a read mismatch. A frozen LED also needs investigation; not all faults reach the software error path.

Real board clock: 25 MHz. UART and switches are not used by this program. Physical long-duration results must be supplied by the user; simulation cannot substitute for those observations.
