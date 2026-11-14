# Fault-V extension roadmap

| Order | Scope | Selected implementation |
| --- | --- | --- |
| Base custom ISA | DOT4, MUL16, ADDSAT, QNT8 | Shared multiplier core and paired software benchmark establish references |
| A: execution units | Parallel DOT4; MAC/DOT4ACC; packed saturation; requantization; INT16 dual lanes; INT4/mixed signed | Four multipliers; DOT4ACC/MAC16; ADD8SAT/SUB8SAT; RQNT8; DOT2SAT; DOT8/DOT4SU |
| B: applications | Convolution/fully connected; fixed-point FIR/IIR/FFT | Select concrete workloads, precision and golden outputs before implementation |
| C: data movement/architecture | Scratchpad/DMA; pipeline/independent accelerator | Choose from measured bottlenecks; specify ordering, backpressure, reset and data consistency |
| ASIC implementation | Process/library/memory and chip integration; synthesis/physical design/sign-off | Select authorized PDK and delivery rules before implementation |
| ASIC PPA extension | Area/performance/power comparison | Use actual library, constraints and switching activity; not FPGA resource proxies |

The eleven directions are grouped as A=1..6, B=7..8, C=9..10, ASIC PPA=11. Each direction chooses a defined implementable function; it does not promise every possible operation within a direction.
