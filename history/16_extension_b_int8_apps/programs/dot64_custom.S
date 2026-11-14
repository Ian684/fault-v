.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10000
    addi x18, x18, 0
    lui x19, 0x10000
    addi x19, x19, 64
    addi x20, x0, 16
    addi x22, x0, 0
outer:
    lw x10, 0(x18)
    lw x11, 0(x19)
    .insn r 0x0b, 0, 0, x10, x10, x11 # DOT4
    add x22, x22, 10
    addi x18, x18, 4
    addi x19, x19, 4
    addi x20, x20, -1
    bne x20, x0, outer
    sw x22, 128(x21)
kernel_end:
    addi x0, x0, 0
    lui x21, 0x20000
    addi x21, x21, 0
    addi x10, x0, 1
    sw x10, 0(x21)
    ebreak
