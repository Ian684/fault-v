.section .text
.globl _start
_start:
    lui x1,0x10004
    addi x1,x1,0
    sw x0,0(x1)
