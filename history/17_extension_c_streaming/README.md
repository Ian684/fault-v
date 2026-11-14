# Fault-V Extension C

CPU with 4 KiB scratchpad, word-copy DMA, an independent three-stage DOT4 vector accelerator and a three-master round-robin memory arbiter. The multicycle CPU and twelve custom instruction encodings remain unchanged.

Design notes: `Streaming_Architecture_Notion.md`. Actual evidence and limits: `Verification_Report.md`. Never substitute FPGA acceptance for ASIC sign-off.

Windows prerequisites: Python 3, Vivado 2022.2 with the xc7z020 part installed. Run from this directory. Use `powershell -ExecutionPolicy Bypass -File .\SCRIPT.ps1` for each PowerShell entry point; this only changes the policy of that process.

1. `python generate_streams.py` regenerates deterministic C fixtures and demonstration ROM.
2. `run_streams.ps1` tests the DOT4 pipeline, arbiter and 124 SoC scenarios in two latency modes with three repeats.
3. `run_regression.ps1` runs legacy instruction, custom execution, peripheral and stress tests.
4. `run_applications.ps1` runs the previous six application workloads on the new SoC with idle DMA/accelerator.
5. `run_stream_demo.ps1` checks the C ROM in two latency modes and corrupts early/late results to verify failure reporting. `run_payload.ps1` tests the actual FPGA wrapper, UART, ARM run control and BTN0 reset.
6. `run_build.ps1` builds the Z2 bitstream, checks implemented timing/DRC/DSP count and binds the image to an unchanged input-source snapshot.
7. `python deploy_and_receive.py` loads the image onto an authorized connected PYNQ-Z2 and receives three functional UART responses. Requires Paramiko, trusted host key, SSH password via prompt or `FAULT_V_SSH_PASSWORD`. Default address is 192.168.2.99. It replaces the current PL overlay.

`programs/stream_*.s` is readable generated assembly. Custom instruction assembly is encoded by the included small assembler rather than a modified GNU toolchain. `programs/stream_manifest.json` identifies each fixture; expected RAM values are mathematical golden outputs rather than a second asynchronous CPU simulator. `logs/stream_mode*.csv` contains RTL cycle and transaction measurements; these are not physical board benchmark-counter measurements.

The package excludes Vivado project caches and XSim generated binaries. Scripts rebuild these. `baseline_identity.json` permits checking the original RTL against Extension B. `fpga_identity.json` binds delivered bitstream and HWH to their RTL, constraints, board wrapper, ROM and Tcl inputs.

`python analyze_streams.py` verifies simulation evidence and creates the benchmark CSV. `python plot_streams.py` requires Matplotlib and produces the exportable performance plots. After a successful FPGA build and board test, `python finish_package.py` creates the report, validates image/source identity and verifies every file in the ZIP against the SHA-256 manifest. Re-run it after recording any additional manual board observations. `run_final_simulations.ps1` runs the four C/application simulation scripts sequentially; the legacy unit/ISA/peripheral suite uses `run_regression.ps1` separately.

The included `known_hosts` trusts this project's Z2. A different board requires an independently verified SSH host key before deployment. The sudo execution in the receiver script assumes the authorized board still uses its existing xilinx default password; adapt it to your board rather than storing personal credentials in the package.
