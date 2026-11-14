.section .text
.globl _start
_start:
    lui x1, 0x10000
    addi x1, x1, 0
    lui x2, 0x10010
    addi x2, x2, 0
    addi x3, x0, 16
copy:
    lw x4, 0(x1)
    sw x4, 0(x2)
    addi x1, x1, 4
    addi x2, x2, 4
    addi x3, x3, -1
    bne x3, x0, copy
    lui x1, 0x10010
    addi x1, x1, 0
    lui x2, 0x10001
    addi x2, x2, 0
    addi x3, x0, 16
    addi x5, x0, 0
dot:
    lw x6, 0(x1)
    lw x7, 0(x2)
    .insn r 0x0b, 0, 1, x5, x6, x7 # DOT4ACC
    addi x1, x1, 4
    addi x2, x2, 4
    addi x3, x3, -1
    bne x3, x0, dot
    lui x2, 0x10003
    addi x2, x2, 0
    sw x5, 0(x2)
    lui x28, 0x20000
    addi x28, x28, 0
    addi x29, x0, 1
    sw x29, 0(x28)
    ebreak
