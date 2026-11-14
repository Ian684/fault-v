.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10000
    addi x18, x18, 768
    lui x19, 0x10000
    addi x19, x19, 896
    addi x20, x0, 16
    lh x8, 832(x21)
    lh x9, 834(x21)
    lh x12, 836(x21)
    lh x13, 838(x21)
    lh x14, 840(x21)
    lh x15, 842(x21)
    lh x16, 844(x21)
    lh x17, 846(x21)
outer:
    addi x22, x0, 0
    lh x10, 0(x18)
    .insn r 0x0b, 1, 0, x10, x10, x8 # MUL16
    add x22, x22, 10
    lh x10, 2(x18)
    .insn r 0x0b, 1, 0, x10, x10, x9 # MUL16
    add x22, x22, 10
    lh x10, 4(x18)
    .insn r 0x0b, 1, 0, x10, x10, x12 # MUL16
    add x22, x22, 10
    lh x10, 6(x18)
    .insn r 0x0b, 1, 0, x10, x10, x13 # MUL16
    add x22, x22, 10
    lh x10, 8(x18)
    .insn r 0x0b, 1, 0, x10, x10, x14 # MUL16
    add x22, x22, 10
    lh x10, 10(x18)
    .insn r 0x0b, 1, 0, x10, x10, x15 # MUL16
    add x22, x22, 10
    lh x10, 12(x18)
    .insn r 0x0b, 1, 0, x10, x10, x16 # MUL16
    add x22, x22, 10
    lh x10, 14(x18)
    .insn r 0x0b, 1, 0, x10, x10, x17 # MUL16
    add x22, x22, 10
    sw x22, 0(x19)
    addi x18, x18, 2
    addi x19, x19, 4
    addi x20, x20, -1
    bne x20, x0, outer
kernel_end:
    addi x0, x0, 0
    lui x21, 0x20000
    addi x21, x21, 0
    addi x10, x0, 1
    sw x10, 0(x21)
    ebreak
