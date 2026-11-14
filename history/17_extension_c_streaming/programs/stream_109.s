.section .text
.globl _start
_start:
    lui x28, 0x20000
    addi x28, x28, 776
    lui x29, 0x10000
    addi x29, x29, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 780
    lui x29, 0x10001
    addi x29, x29, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 784
    lui x29, 0x10010
    addi x29, x29, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 788
    addi x29, x0, 256
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 768
    addi x29, x0, 1
    sw x29, 0(x28)
    lui x1, 0x10010
    addi x1, x1, 1
    addi x2, x0, 1
    sb x2, 0(x1)
    ebreak
