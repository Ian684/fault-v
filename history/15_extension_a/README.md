# Fault-V execution-unit extensions

XFaultVDSP v1.1 preserves DOT4/MUL16/ADDSAT/QNT8 and adds DOT4ACC, MAC16, ADD8SAT, SUB8SAT, RQNT8, DOT2SAT, DOT8, DOT4SU. The CPU still uses a two-read/one-write register file; accumulator instructions read old rd in one extra state. All six extension-A directions have a specific implementation. Application extensions and DMA/pipelining/ASIC analysis remain separate scopes.

Read Extension_A_Notion.md for Traditional Chinese design notes. Actual verification/performance/platform measurements are in Verification_Report.md, results.json and results.csv. The ZIP includes complete RTL, testbenches, programs, scripts, log/report evidence, and the paired FPGA bit/HWH.

Run from this folder with Python and Vivado 2022.2 at C:\Xilinx\Vivado\2022.2\bin:

```powershell
python .\generate.py
python .\build_extension_benchmarks.py
powershell -ExecutionPolicy Bypass -File .\run_regression.ps1
powershell -ExecutionPolicy Bypass -File .\run_custom.ps1
powershell -ExecutionPolicy Bypass -File .\run_benchmark.ps1
powershell -ExecutionPolicy Bypass -File .\run_payload.ps1
powershell -ExecutionPolicy Bypass -File .\run_unit_comparison.ps1
powershell -ExecutionPolicy Bypass -File .\run_build.ps1
python .\make_delivery.py
```

PowerShell Bypass applies to the invoked process. Simulation/build do not download the FPGA. For repeat physical verification, connect an SD-booted PYNQ-Z2 on the previously verified network, install paramiko on the PC, set FAULT_V_SSH_PASSWORD in the process environment (or enter it at the prompt), then run python .\deploy_and_receive.py. Default host is 192.168.2.99 and user xilinx. Host keys are checked using the included known_hosts; loading the overlay replaces the active PL design.

fpga_identity.json binds delivered bit/HWH to RTL, board source, constraints, ROM and build TCL. run_build.ps1 refreshes the identity only after a successful build. make_delivery.py rejects source/image mismatches. Actual board results are bound to image hashes; rebuilding a different image requires another board run before final packaging.

Cycle results come from RTL simulation. Times are converted at 50 MHz; hardware self-check confirms function and clock, not benchmark cycle counting. RQNT8's software benchmark uses declared inputs with signed INT32 products; its full 48-bit semantics are validated separately. Independent original-four-op resource comparison is synthesis only; full platform resource/timing is routed. Retained warnings and unverified scopes are enumerated in the report.
