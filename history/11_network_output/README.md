# Fault-V network bridge

Files:
- Network_Output_Notion.md: technical notes for Notion.
- Verification_Report.md: measured simulation, FPGA and board results.
- Fault_V_Network.ipynb: board Jupyter demonstration.
- receive_on_board.py: run on PYNQ as root.
- deploy_and_receive.py: PC SSH/SFTP upload and three-run verification.
- run_sim.ps1: wrapper/CPU/UART RTL simulation.
- run_build.ps1: Vivado synthesis, implementation and acceptance checks.

Windows commands (from this directory):

    powershell -ExecutionPolicy Bypass -File .\run_sim.ps1
    powershell -ExecutionPolicy Bypass -File .\run_build.ps1
    python .\deploy_and_receive.py

Default Vivado path: C:\Xilinx\Vivado\2022.2\bin
Python dependency: paramiko
Board: PYNQ-Z2, PYNQ 2.5, IP 192.168.2.99.
SSH connection settings are in remote_access.py; current demo uses the user-confirmed default account.

The bit and hwh files must have identical stems and remain paired.
The PS preset was extracted from this board's working PYNQ base.hwh by inspect_board.py.
It reuses existing DDR/MIO configuration; the receive script does not execute ps7_init or reinitialize DDR.
Vivado emits inherited PSU-1 and PSU-2 warnings for the board's negative DDR skew settings; see verification report.

This verifies an internal PL UART receiver and Ethernet output. It does not certify external Pmod electrical transmission or ASIC sign-off.
