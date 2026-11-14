# Fault-V ASIC synthesis and pre-layout STA

The delivered version is tt_delivery_reload, including the buffer ECO and a fresh STA read of the serialized netlist. Read ASIC_Synthesis_Notion.md for the design and Verification_Report.md for measured results and limitations. The package contains RTL, real mapped netlists, historical and final synthesis/STA runs, macro views, tests and exact source hashes.

## Reproduce Windows RTL verification

Vivado 2022.2 was used. From this directory:

~~~powershell
powershell -ExecutionPolicy Bypass -File .\run_xsim.ps1
powershell -ExecutionPolicy Bypass -File .\run_regression.ps1
python scripts/selfcheck.py
~~~

The policy override applies only to that child PowerShell. Scripts accept -VivadoBin for another installation. run_xsim includes arbiter, SRAM bank modes, UART loader boundaries and the final-fill/error-priority regression. run_regression performs 744 SRAM-backed SoC runs. run_priority.ps1 is the small standalone priority test.

## Reproduce accepted mapped-gate verification

Use the same pinned Linux Docker image and layout described below:

~~~bash
bash scripts/run_gate_linux.sh
~~~

The four-state Icarus test uses the final mapped_top.v and functional standard-cell/SRAM models. It has separate cases:

1. Real 217 clocks/bit UART: reject an invalid CRC, then accept a complete one-word image, zero-fill the instruction tail and execute EBREAK.
2. CPU execution: the testbench preloads the 206-word firmware into SRAM and forces running to bypass the loader. It checks 12 custom instructions, DMA and the independent DOT4 accelerator, with 15 firmware checks.

The second case is a simulation preload, not a physical ASIC boot method. Neither case uses SDF. This is functional gate simulation, not post-route timing verification or formal equivalence.

run_gate.ps1 and verify/tb_gate.sv retain an OPTIONAL long XSim test that serially loads the entire 834-byte program packet. Earlier long attempts were interrupted or superseded; they are NOT counted as passing. The accepted final gate evidence is logs/tb_gate.log from verify/tb_gate_accept.sv in Linux.

Original cell/SRAM models are retained. scripts/prepare_models.py recreates simulation-only compatible copies: nettype wire, UNIT_DELAY #0, SRAM declaration ordering, timescale and verbosity. Liberty/LEF/GDS and cell truth tables are unchanged.

## Reproduce synthesis / pre-PnR STA

Actual environment: Ubuntu-22.04 WSL2, Docker 29.6.2, official digest-pinned LibreLane 3.0.16 image. Exact identities are in toolchain_identity.json. Nix was considered in preselection; the existing Docker runtime was used.

Use the Linux filesystem, with this layout:

~~~
fault-v-asic/
  design/       # package contents
  pdk/          # Ciel-managed PDK root
  logs/
  tools/        # pinned OpenSTA/CUDD source/build and runtime wrapper
~~~

1. Install Docker and permit the current user to run it. Pull the image digest in scripts/run_linux.sh.
2. Provision the locked SKY130 revision in toolchain_identity.json under pdk using the official LibreLane/Ciel setup or smoke test.
3. Copy this package to design, preserve UTF-8 / LF in shell scripts, and create logs in the parent directory.
4. Install WSL build prerequisites: a C++ compiler, CMake, Ninja, Git, Flex/Bison, zlib development files, tcl-dev, swig and libeigen3-dev. The last three were the only missing packages on this machine. Build the pinned official OpenSTA/CUDD with bash scripts/build_sta_fixed.sh. It fetches fmt through the upstream CMake recipe; network access is needed during provisioning.
5. Run python3 scripts/create_sta_wrapper.py. It creates tools/sta_fixed_bin/sta using the pinned image runtime and library paths. Both host binary and Docker runtime are required.
6. Run bash scripts/run_linux.sh tt_reproduce with a NEW tag. It performs synthesis, checked buffer ECO, buffer-transparent connectivity comparison, then a second STA pass on the emitted netlist, without repeating the ECO. It stops at pre-PnR; it does not perform physical design.
7. The accepted output is runs/tt_reproduce_reload/final/nl/fault_v_asic_top.nl.v, copied to mapped_top.v. Compare its final/metrics.json and source_identity.json. Run bash scripts/run_gate_linux.sh on that same file.

config.json is the synthesis/ECO configuration; config_reload.json is generated at the design root without the ECO hook. Its dir:: paths must resolve relative to design, not to eco/. The original full synthesis state retains the pre-ECO Yosys netlist; only the reload run is the accepted final-netlist state.

The ECO is deliberately bounded to this mapped design: 234 SRAM inputs, 2,925 FF, 18 macros and one named identity buffer. If the input RTL/tool mapping changes, assertions or electrical checks must fail until the driver selection is reviewed. Do not suppress those guards.

STA_EXTRA_CORNER_TCL_FILE executes the ECO before LibreLane reports timing. The stock image OpenSTA 2.7.0 has a reproducible mixed-threshold load-slew bug. scripts/sta310_cli.py explicitly selects the pinned upstream OpenSTA 3.1.0 executable; merely prepending PATH is ineffective because the image entrypoint resets it. The fixture in verify/threshold_probe.v and three targeted upstream regressions provide the recorded tool checks. The full upstream test suite was not run.

Existing local Linux workspace: <HOME>/fault-v-asic/design. From PowerShell:

~~~powershell
wsl -d Ubuntu-22.04 --cd <HOME>/fault-v-asic/design bash scripts/run_linux.sh tt_reproduce
~~~

Full PDK and tool images are not bundled; the locked SRAM views and their upstream license are included. The macro has only the supplied TT model: do not substitute another macro's SS/FF timing.

## Source and evidence helpers

Final RTL is already supplied. prepare.py intentionally restores copied CPU modules from reference/extension_c_rtl; do not run it over a modified design. optimize.py applies recorded width/process cleanups. prepare_regression.py regenerates the integration test from reference/tb_streams.sv. generate_gate_program.py uses the included assembler and independent integer reference. short_fixture.py makes the one-word boot packet.

configure.py regenerates config and source hashes after deliberate changes. Windows evidence collection helpers read D:\Codex\WSL\fault-v-asic directly. Runtime synthesis/test scripts depend only on the documented directory layout.

The accepted logs are tb_mem_arbiter.log, tb_sram_banks.log, tb_asic_boot.log, tb_loader_priority.log, tb_asic_streams.log and tb_gate.log. The intentionally failing loader_priority_before_fix.log demonstrates the fixed race; earlier compile/partial-run logs are historical evidence.

## Firmware loading

~~~powershell
python scripts/encode_image.py input.bin packet.bin
~~~

This converts a raw little-endian instruction image into the boot packet and does not open a serial port. Transmit raw packet bytes at 115200 8N1 with the default 25 MHz clock. UART ports are 1.8 V core signals; physical pads, package and voltage conversion require separate integration.

A new program requires external reset. CRC validation and unused instruction-word zero fill precede CPU reset release; errors take priority over a simultaneous completion. Data RAM and scratchpad are not reset-initialized and must be initialized by firmware.

## Packaging and scope

After the required logs and identity checks pass:

~~~powershell
python scripts/collect_results.py
python scripts/collect_gate.py
python scripts/finalize_evidence.py
python scripts/check_threshold_probe.py
python scripts/selfcheck.py
python scripts/generate_report.py
python scripts/package.py
~~~

The archive excludes compiled simulation caches and includes a SHA-256 manifest. Packaging checks archive CRC and every manifest entry.

No floorplan, placement, CTS, routing, extracted SPEF, pad ring, power integrity or foundry signoff is included. TT setup/hold have positive slack and the final pre-PnR slew/capacitance counts are zero. This does not establish closure after placement/CTS/routing. The SRAM needs corner and delivery qualification. These results do not establish tape-out readiness.

Historical configurations/scripts (buffered/slew/electrical/closed experiments) and history/baseline_* are retained for provenance; they are not the current acceptance commands. Reports from tt_initial through tt_release use the old STA and cannot be directly compared to the final electrical counts. tt_sta310 is the same-engine pre-ECO comparison.


## Workspace storage

The actual WSL ASIC workspace is D:\Codex\WSL\fault-v-asic. Ubuntu mounts the drive at /mnt/fault-v-d using metadata and case=dir, and <HOME>/fault-v-asic remains a Linux symlink to /mnt/fault-v-d/Codex/WSL/fault-v-asic.

Use the D-drive path for Windows file access. Windows cannot follow the old WSL UNC entry through this Linux-to-DrvFS symlink; collection helpers now use the direct D path. Linux scripts retain the original <HOME> entry.

Migration evidence and restoration instructions are in D:\Codex\WSL\fault-v-asic-migration. Ubuntu itself and Docker image storage were not moved. The external D drive must be connected while using the project.
