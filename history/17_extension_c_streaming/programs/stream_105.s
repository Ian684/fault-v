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
    addi x29, x0, 0
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
    lui x28, 0x20000
    addi x28, x28, 1032
    lui x29, 0x10002
    addi x29, x29, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 1036
    lui x29, 0x10002
    addi x29, x29, 1024
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 1040
    lui x29, 0x10003
    addi x29, x29, 0
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 1044
    addi x29, x0, 64
    sw x29, 0(x28)
    lui x28, 0x20000
    addi x28, x28, 1024
    addi x29, x0, 1
    sw x29, 0(x28)
    addi x1, x0, 200
    addi x2, x0, 0
work:
    addi x2, x2, 1
    addi x1, x1, -1
    bne x1, x0, work
    lui x3, 0x10004
    addi x3, x3, -2048
    sw x2, 0(x3)
    lui x28, 0x20000
    addi x28, x28, 768
dma:
    lw x29, 4(x28)
    andi x30, x29, 1
    bne x30, x0, dma
    lui x28, 0x20000
    addi x28, x28, 1024
acc:
    lw x29, 4(x28)
    andi x30, x29, 1
    bne x30, x0, acc
    lui x28, 0x20000
    addi x28, x28, 0
    addi x29, x0, 1
    sw x29, 0(x28)
    ebreak
