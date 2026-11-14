.section .text
.globl _start
_start:
kernel_begin:
    lui x21, 0x10000
    addi x21, x21, 0
    lui x18, 0x10001
    addi x18, x18, 512
    lui x19, 0x10001
    addi x19, x19, 576
    lui x23, 0x10001
    addi x23, x23, 640
    lui x26, 0x10002
    addi x26, x26, -1920
    addi x20, x0, 16
outer:
    lw x24, 0(x18)
    lw x25, 0(x19)
    .insn r 0x0b, 2, 1, x22, x24, x25 # ADD8SAT
    sw x22, 0(x26)
    addi x18, x18, 4
    addi x19, x19, 4
    addi x26, x26, 4
    addi x20, x20, -1
    bne x20, x0, outer
kernel_end:
    lui x30, 0x20000
    addi x30, x30, 0
    addi x29, x0, 1
    sw x29, 0(x30)
    ebreak
