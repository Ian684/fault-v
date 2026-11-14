.section .text
.globl _start
_start:
    lui x1,0x20000
    addi x1,x1,4
    lw x2,0(x1)
