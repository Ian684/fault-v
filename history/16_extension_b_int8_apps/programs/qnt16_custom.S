.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10000
    addi x18, x18, 448
    lui x19, 0x10000
    addi x19, x19, 512
    addi x20, x0, 16
    addi x11, x0, 3
outer:
    lw x10, 0(x18)
    .insn r 0x0b, 3, 0, x10, x10, x11 # QNT8
    sw x10, 0(x19)
    addi x18, x18, 4
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
