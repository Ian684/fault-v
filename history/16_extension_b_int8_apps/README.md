# Fault-V application extensions

This stage implements Conv1D INT8, dense INT8, their inference chain, FIR8 Q15, IIR1 Q15 and FFT16 complex Q15 in Assembly. All 16 CPU/SoC RTL files are byte-identical to accepted XFaultVDSP v1.1 from extension_a. No ISA, DMA, scratchpad or pipeline changes are introduced here. Optimization, novelty development and new research problems are deferred until the original A/B/C stages are complete.

Application_Extensions_Notion.md contains design notes only. Verification_Report.md and results.csv hold actual evidence and performance. Inputs/weights are synthetic fixed datasets, not a trained model or a classification accuracy evaluation.

From this directory, with Python and Vivado 2022.2:

```powershell
python .\generate_applications.py
powershell -ExecutionPolicy Bypass -File .\run_regression.ps1
powershell -ExecutionPolicy Bypass -File .\run_applications.ps1
powershell -ExecutionPolicy Bypass -File .\run_payload.ps1
powershell -ExecutionPolicy Bypass -File .\run_build.ps1
python .\plot_precision.py
python .\make_delivery.py
```

The simulation/build commands do not download the FPGA. For physical testing, connect SD-booted PYNQ-Z2 on the verified network, install paramiko on the PC, provide FAULT_V_SSH_PASSWORD in the process environment or at the prompt, and execute python .\deploy_and_receive.py. Default host is 192.168.2.99 and user xilinx; included known_hosts enforces the previously verified host key. Loading the overlay replaces the active PL design. The remote receiver is compatible with PYNQ's Python 3.6.

run_build.ps1 records the successful bit/HWH and RTL/ROM/TCL hashes in fpga_identity.json. Packaging rejects modified build sources or board results for different images. To rebuild, rerun build and physical testing before packaging.

The direct mathematical references, instruction-word interpreter, generated Assembly and RTL are distinct checks. FFT is scaled by 1/16 and uses stagewise Q15 shifts and INT16 clipping; it is not an unscaled float FFT. Reference float DFT is computed directly, not with the integer FFT algorithm. Full-scale FFT clipping distortion is retained and reported; improving numerical policy is outside the current scope.

Performance cycles are from RTL; microseconds are converted at 50 MHz. Board self-check validates functionality/clock/UART, not hardware cycle-counter measurements. DSP_Precision.png and .pdf are standalone figures of results against float references. There are no ASIC PPA or external Pmod electrical measurements.
