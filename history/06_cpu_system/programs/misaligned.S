.section .text
.globl _start
_start:
    lui x1,0x10000
    addi x1,x1,0
    lw x2,1(x1)
