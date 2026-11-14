# Fault-V RTL cycle benchmark

Read Benchmark_Notion.md for the complete Traditional Chinese methodology and result tables.
Verification_Report.md distinguishes measured RTL cycles from converted 50 MHz time and the earlier FPGA resource reference.

From this folder:

    python .\build_benchmarks.py
    powershell -ExecutionPolicy Bypass -File .\run_benchmark.ps1
    python .\make_results.py

Requires Python standard library and Vivado/XSim 2022.2.
Default Vivado bin: C:\Xilinx\Vivado\2022.2\bin; override with -VivadoBin.

Six workload pairs: DOT64, FIR8_RAW, FIR8_PACKED, FIR16, QNT16, SATADD64.
Each binary runs in two memory response configurations, twice per configuration: 48 RTL executions.
All outputs are checked against the fixed vectors. Pure RV32I binaries contain no custom or standard M instructions.

Both variants run on identical extended CPU RTL. This isolates instruction/software performance; it does not compare area between a smaller RV32I-only CPU and the extended CPU.
No benchmark bitstream is built or downloaded by these scripts. hardware_reference contains the already-validated DSP self-check platform's timing/resources and physical clock evidence, not physical timings of these benchmark programs.
FIR8_PACKED excludes window construction; FIR8_RAW includes CPU window packing. Input initialization is testbench setup, outside measurement.
