.section .text
.globl _start
_start:
    lui x1, 0x20000
    addi x1, x1, 1032
    addi x2, x0, 1
    sb x2, 0(x1)
    ebreak
