# Fault-V custom ISA specification package

Read Custom_ISA_Notion.md for the full Traditional Chinese specification and extension directions.

Four operations: DOT4, MUL16, ADDSAT, QNT8. Custom-0 (0x0B), funct7=0, funct3=0..3.

Run from this folder:

    python verify_spec.py

No external Python packages are required. The script regenerates directed_vectors.json, encoding.json and benchmark_vectors.json.

Specification_Verification.md and spec_verification.log contain actual checks.
This package defines semantics and CPU integration contracts. It does not implement the custom execution unit in RTL or report measured CPU cycles.

Machine words from this package are illegal on the current unmodified Fault-V CPU. Decoder, FSM and execution unit integration must be completed before running them.
