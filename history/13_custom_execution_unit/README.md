# Fault-V DSP／AI CPU implementation

Start with Custom_Execution_Notion.md for the Traditional Chinese technical notes.
Verification_Report.md records actual results and remaining validation.

Four custom operations: DOT4, MUL16, ADDSAT, QNT8.
The current RTL uses one shared signed 16x16 multiplier and a multicycle request/response unit.
The CPU has three custom states and a 32-bit result register.

From this directory:

    python .\generate.py
    powershell -ExecutionPolicy Bypass -File .\run_regression.ps1
    powershell -ExecutionPolicy Bypass -File .\run_custom.ps1
    powershell -ExecutionPolicy Bypass -File .\run_payload.ps1
    powershell -ExecutionPolicy Bypass -File .\run_build.ps1

Default tools: Vivado/XSim 2022.2 at C:\Xilinx\Vivado\2022.2\bin.
The simulator and Vivado commands are CLI tools; they do not require opening a GUI project.

Outputs:
- fault_v_custom.bit and fault_v_custom.hwh: matching PYNQ overlay pair.
- programs/custom_demo.S and custom_demo.mem: 127 self-checks across all four workloads and directed cases.
- programs/expected_outputs.json: full expected RAM output values.
- verify/: new unit/CPU/program tests plus the existing RV32I/IO/stress regression snapshot.
- logs/: actual simulator/build reports.

When the board is available:

    python .\deploy_and_receive.py

The PC needs paramiko and network access. This uploads into a new Jupyter directory and loads the PL overlay through PYNQ. It uses the existing user-confirmed SSH settings in remote_access.py and sudo for PYNQ access. It does not change SD/Linux boot configuration.

Board setup: PYNQ-Z2, PYNQ 2.5, Ethernet address 192.168.2.99, SD boot.
Expected program: DSP OK followed by CR/LF, LED 0x5, status 1, EBREAK cause 9.
The receive script repeats the program three times, checking exact bytes, FIFO errors and debug status.

The PS preset is derived from this board's earlier working PYNQ base overlay. Inherited negative DDR skew PSU-1 / PSU-2 warnings are retained. The board script does not execute ps7_init or reinitialize DDR.

Current scope excludes the 11 optional extension directions, full software-vs-custom performance benchmarking, ASIC sign-off and external Pmod electrical tests.
