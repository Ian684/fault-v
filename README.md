# Fault-V: RISC-V Custom-Instruction SoC for Edge AI

Fault-V is a 32-bit RV32I multi-cycle processor extended with 12 custom
instructions for quantized neural-network inference. The SoC combines INT8
and INT4 dot products, saturating arithmetic, requantization, DMA, a DOT4
accelerator, and 18 x 2 KiB SRAM macros (36 KiB total).

The project covers the path from RTL through synthesis and SKY130
pre-tapeout physical design using open-source EDA tooling. It is a research
prototype: it has **not** been manufactured and has not received foundry
sign-off.

## Why it is interesting

- **Instruction-set extension:** 12 custom operations target quantized
  inference kernels rather than general-purpose workloads.
- **System integration:** CPU, DMA, accelerator, SRAM banks, arbitration, and
  boot/stream paths are verified together.
- **Reproducible flow:** tool versions, source hashes, test scripts, and
  release artifacts are recorded in the repository.
- **Open process:** `history/` and `docs/` preserve the design progression
  from decoder and control FSM to ASIC implementation.

## Headline results

| Measurement | Result | Qualification |
|---|---:|---|
| DOT64 latency | 21,708 -> 1,022 cycles | INT8, 64 multiply-accumulates |
| DOT64 energy | 28.9 -> 1.36 uJ | Analytical estimate, same workload |
| Reported speed/energy improvement | about 21.2x | Compared with RV32I without a hardware multiplier |
| Reported chip power | about 33 mW | 25 MHz, TT, mixed workload; estimated |
| H0 physical checks | DRC 0, LVS 0, antenna 0 | Pre-tapeout results |
| H1 area change | -3.7% | SRAM-channel compaction; checks reported as passing |

The numerical results above should be read together with the limitations in
the [Limitations](#limitations) section. They are not measurements from a
fabricated chip.

## SoC at a glance

```text
                         +----------------------+
                         |      RV32I CPU       |
                         |  12 custom NN ops    |
                         +----------+-----------+
                                    |
                         +----------v-----------+
                         |  bus / arbitration   |
                         +-----+-----------+----+
                               |           |
                     +---------v--+   +----v-----+
                     | DMA / SRAM |   |   DOT4   |
                     |  banks     |   | accelerator|
                     +------------+   +----------+
```

The definitive RTL and verification sources are under `final/design/rtl/`
and `final/design/verify/`. The diagram is intentionally simplified; consult
the RTL for the exact bus and arbitration behavior.

## Repository map

| Path | Contents |
|---|---|
| `final/design/` | Final RTL, testbenches, SRAM models, mapped netlist, and simulation scripts |
| `final/design/rtl/` | SoC RTL and packages |
| `final/design/verify/` | RTL, integration, stream, and gate-level testbenches |
| `final/design/scripts/` | Gate-flow and delivery scripts |
| `final/layout/` | H0/H1 OASIS layout artifacts and equivalence results |
| `final/results/` | PPA, sign-off, and delivery JSON reports |
| `final/macros/` | SRAM LEF, Liberty, and simulation models |
| `history/` | Development stages from decoder through physical design |
| `docs/notion/` | Design notes |
| `docs/competition/` | 2026 competition report |

Large GDSII, SPEF, DEF, and delivery-package files are published in GitHub
Releases rather than stored in the repository. Release artifacts include
SHA256 manifests and a self-check script.

## Reproduce the verification

### RTL integration tests (Windows + Vivado 2022.2)

From `final/design/`:

```powershell
.\run_xsim.ps1 -VivadoBin 'C:\Xilinx\Vivado\2022.2\bin'
.\run_regression.ps1 -VivadoBin 'C:\Xilinx\Vivado\2022.2\bin'
```

The scripts compile the RTL and SRAM model, elaborate the testbenches, run
XSim, save logs under `final/design/logs/`, and fail when an acceptance marker
is missing. The integration suite contains the reported 744 SoC tests.

### Gate-level simulation (Linux + Docker)

From `final/design/`:

```bash
bash scripts/run_gate_linux.sh
```

The script uses the pinned LibreLane image recorded in
`final/design/toolchain_identity.json`. Docker must be available, and the
generated logs are written to `final/logs/`.

### Physical-design flow

The physical-design flow uses LibreLane 3.0.16, OpenSTA 3.1, the SKY130A PDK,
and pinned source/container identities. See
`final/design/toolchain_identity.json` before reproducing results. Paths and
PDK setup are environment-specific; the repository records the expected
versions and hashes but does not silently install proprietary tools or PDKs.

## Custom-instruction groups

The custom instruction set is organized around these operations:

| Group | Purpose |
|---|---|
| INT8 dot product | Vectorized signed 8-bit multiply-accumulate |
| INT4 dot product | Packed low-precision inference arithmetic |
| Saturation | Clamp intermediate results to the target width |
| Requantization | Convert accumulator values to inference output ranges |
| Data movement | Support accelerator/DMA-oriented operand movement |

For the authoritative opcode encoding, operand layout, and cycle behavior,
use the instruction definitions and assembler support in
`final/design/rtl/` and `final/design/application_asm.py`; this summary avoids
duplicating a second source of truth.

## Toolchain identity

The checked-in identity record includes:

- Vivado XSim 2022.2 for Windows RTL simulation
- LibreLane 3.0.16 in a digest-pinned container
- Yosys 0.62, OpenROAD, and OpenSTA 3.1.0
- Verilator 5.044
- SKY130A revision
  `8afc8346a57fe1ab7934ba5a6056ea8b43078e71`
- SRAM macro repository and commit
- Source and mapped-netlist SHA256 values

See `final/design/toolchain_identity.json` and
`final/design/source_identity.json` for the complete records.

## Limitations

- SRAM timing data covers TT, 1.8 V, 25 C only.
- Power is an analytical estimate and does not distinguish SRAM read/write
  power.
- Timing is reported for TT only; fill-aware PEX is not included.
- IR/EM analysis is static and based on average current.
- The design has no pad ring, ESD, or DFT hardware.
- The project has no foundry sign-off, fabrication, or silicon measurements.

## License

The project-owned code and documentation are MIT licensed; see `LICENSE`.
Third-party SKY130-derived models and OpenRAM SRAM macros retain their
upstream licenses, documented under `final/design/licenses/`.

## Citation and contact

If you use Fault-V in a report or presentation, cite the repository and the
corresponding release tag so that the toolchain and result artifacts remain
traceable.
