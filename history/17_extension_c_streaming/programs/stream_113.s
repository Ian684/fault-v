.section .text
.globl _start
_start:
    lui x28, 0x20000
    addi x28, x28, 1032
    lui x29, 0x10000
    addi x29, x29, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 1036
    lui x29, 0x10001
    addi x29, x29, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 1040
    lui x29, 0x10003
    addi x29, x29, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 1044
    addi x29, x0, 256
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 1024
    addi x29, x0, 1
    sw x29, 0(x28)
    lui x1, 0x20000
    addi x1, x1, 1024
    addi x2, x0, 2
    sw x2, 0(x1)
    ebreak
