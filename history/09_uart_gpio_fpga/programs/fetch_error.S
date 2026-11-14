.section .text
.globl _start
_start:
    lui x1,0x4
    addi x1,x1,0
    jalr x5,0(x1)
